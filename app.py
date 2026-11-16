import os
import sys
import uuid
import threading
import time
import shutil
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_file, Response

app = Flask(__name__)

# Base directories
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "downloads"
DOWNLOADS_DIR.mkdir(exist_ok=True)

SDCARD_DOWNLOAD = Path("/sdcard/Download")

# Global task storage
tasks = {}
tasks_lock = threading.Lock()

def format_duration(seconds):
    if not seconds:
        return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_bytes(bytes_count):
    if not bytes_count:
        return "Unknown size"
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_count < 1024:
            return f"{bytes_count:.1f} {unit}"
        bytes_count /= 1024
    return f"{bytes_count:.1f} TB"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/info", methods=["POST"])
def get_video_info():
    try:
        import yt_dlp
    except ImportError:
        return jsonify({"error": "yt-dlp is not installed. Please install it with 'pip install yt-dlp'"}), 500

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "URL cannot be empty"}), 400

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extract_flat": False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return jsonify({"error": "Failed to retrieve video information"}), 404

            # Extract quality formats
            formats = info.get("formats", [])
            available_qualities = []
            seen_heights = set()

            # Target resolutions
            targets = [
                {"height": 2160, "label": "4K Ultra HD (2160p)"},
                {"height": 1440, "label": "2K Quad HD (1440p)"},
                {"height": 1080, "label": "Full HD (1080p)"},
                {"height": 720, "label": "HD (720p)"},
                {"height": 480, "label": "SD (480p)"},
                {"height": 360, "label": "Standard (360p)"},
            ]

            available_heights = {f.get("height") for f in formats if f.get("height")}

            for target in targets:
                h = target["height"]
                # Check if available or if nearest height is close
                if any(curr_h and curr_h >= h for curr_h in available_heights):
                    if h not in seen_heights:
                        seen_heights.add(h)
                        available_qualities.append({
                            "type": "video",
                            "height": h,
                            "label": target["label"],
                            "ext": "mp4",
                            "format_spec": f"bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<={h}]+bestaudio/best[height<={h}]"
                        })

            # Always ensure at least default Best MP4 option
            if not available_qualities:
                available_qualities.append({
                    "type": "video",
                    "height": 720,
                    "label": "Best Quality Video (MP4)",
                    "ext": "mp4",
                    "format_spec": "bestvideo+bestaudio/best"
                })

            # Audio options
            audio_options = [
                {
                    "type": "audio",
                    "label": "MP3 High Quality (Audio)",
                    "ext": "mp3",
                    "codec": "mp3",
                    "format_spec": "bestaudio/best"
                },
                {
                    "type": "audio",
                    "label": "M4A Original Audio",
                    "ext": "m4a",
                    "codec": "m4a",
                    "format_spec": "bestaudio[ext=m4a]/bestaudio/best"
                }
            ]

            thumbnail = info.get("thumbnail") or (info.get("thumbnails")[-1]["url"] if info.get("thumbnails") else "")

            return jsonify({
                "id": info.get("id"),
                "title": info.get("title", "Unknown Title"),
                "uploader": info.get("uploader") or info.get("channel", "Unknown Channel"),
                "duration": format_duration(info.get("duration")),
                "thumbnail": thumbnail,
                "view_count": f"{info.get('view_count', 0):,}" if info.get("view_count") else "N/A",
                "video_qualities": available_qualities,
                "audio_qualities": audio_options,
                "webpage_url": info.get("webpage_url", url)
            })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def run_download_thread(task_id, url, format_spec, is_audio, audio_codec, save_to_sdcard):
    import yt_dlp

    def progress_hook(d):
        with tasks_lock:
            task = tasks.get(task_id)
            if not task:
                return

            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes") or 0
                speed = d.get("speed") or 0
                eta = d.get("eta") or 0

                pct = round((downloaded / total * 100), 1) if total > 0 else 0

                # Format speed
                if speed > 1024 * 1024:
                    speed_str = f"{speed / (1024 * 1024):.1f} MB/s"
                elif speed > 1024:
                    speed_str = f"{speed / 1024:.0f} KB/s"
                else:
                    speed_str = "0 KB/s"

                eta_str = f"{eta}s" if eta else "Calculating..."

                task["status"] = "downloading"
                task["progress"] = pct
                task["speed"] = speed_str
                task["eta"] = eta_str
                task["downloaded_bytes"] = format_bytes(downloaded)
                task["total_bytes"] = format_bytes(total)

            elif d["status"] == "finished":
                task["status"] = "processing"
                task["progress"] = 99
                task["speed"] = "Finalizing..."
                task["eta"] = "A few seconds"
                if "filename" in d:
                    task["filepath"] = d["filename"]

    output_template = str(DOWNLOADS_DIR / f"{task_id}_%(title).100s.%(ext)s")

    ydl_opts = {
        "format": format_spec,
        "outtmpl": output_template,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }

    if is_audio:
        if audio_codec == "mp3":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]
    else:
        # Merge into standard MP4 container
        ydl_opts["merge_output_format"] = "mp4"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the final created file
        matched_files = list(DOWNLOADS_DIR.glob(f"{task_id}_*"))
        if not matched_files:
            raise Exception("Downloaded file could not be found.")

        final_path = matched_files[0]
        final_filename = final_path.name.replace(f"{task_id}_", "")

        saved_sdcard_path = None
        if save_to_sdcard and SDCARD_DOWNLOAD.exists():
            target_path = SDCARD_DOWNLOAD / final_filename
            try:
                shutil.copy2(final_path, target_path)
                saved_sdcard_path = str(target_path)
            except Exception as se:
                print(f"Warning: Could not copy to /sdcard/Download: {se}", file=sys.stderr)

        with tasks_lock:
            tasks[task_id]["status"] = "completed"
            tasks[task_id]["progress"] = 100
            tasks[task_id]["filepath"] = str(final_path)
            tasks[task_id]["filename"] = final_filename
            tasks[task_id]["filesize"] = format_bytes(final_path.stat().st_size)
            tasks[task_id]["saved_sdcard_path"] = saved_sdcard_path

    except Exception as e:
        with tasks_lock:
            tasks[task_id]["status"] = "error"
            tasks[task_id]["error"] = str(e)

@app.route("/api/start-download", methods=["POST"])
def start_download():
    try:
        import yt_dlp
    except ImportError:
        return jsonify({"error": "yt-dlp is not installed"}), 500

    data = request.get_json(silent=True) or {}
    url = data.get("url", "").strip()
    format_spec = data.get("format_spec", "bestvideo+bestaudio/best")
    is_audio = data.get("is_audio", False)
    audio_codec = data.get("audio_codec", "mp3")
    save_to_sdcard = data.get("save_to_sdcard", False)
    title = data.get("title", "Video")

    if not url:
        return jsonify({"error": "URL is required"}), 400

    task_id = str(uuid.uuid4())[:8]

    with tasks_lock:
        tasks[task_id] = {
            "task_id": task_id,
            "status": "starting",
            "progress": 0,
            "speed": "Starting...",
            "eta": "...",
            "downloaded_bytes": "0 B",
            "total_bytes": "Estimating...",
            "filename": None,
            "filepath": None,
            "title": title,
            "saved_sdcard_path": None,
            "error": None,
            "created_at": time.time()
        }

    thread = threading.Thread(
        target=run_download_thread,
        args=(task_id, url, format_spec, is_audio, audio_codec, save_to_sdcard),
        daemon=True
    )
    thread.start()

    return jsonify({"task_id": task_id})

@app.route("/api/progress/<task_id>")
def get_progress(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            return jsonify({"error": "Task not found"}), 404
        return jsonify(task)

@app.route("/api/get-file/<task_id>")
def download_file(task_id):
    with tasks_lock:
        task = tasks.get(task_id)
        if not task:
            return "Task not found", 404
        if task.get("status") != "completed" or not task.get("filepath"):
            return "File is not ready yet", 400

        filepath = Path(task["filepath"])
        filename = task.get("filename", filepath.name)

    if not filepath.exists():
        return "File does not exist on disk", 404

    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"\n=======================================================")
    print(f" 🚀 YouTube Downloader Web App is running!")
    print(f" 📱 Open in browser: http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=False)
