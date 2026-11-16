---
title: YouTube Downloader Web
emoji: 🎥
colorFrom: red
colorTo: purple
sdk: docker
app_port: 5000
pinned: false
license: mit
---

# 🎥 YouTube Video & Audio Downloader Web App

একটি আধুনিক, দ্রুতগতির এবং রেসপন্সিভ ইউটিউব ডাউনলোডার ওয়েব অ্যাপ্লিকেশন। এটি পাইথন (`Flask`), `yt-dlp` এবং `FFmpeg` ইঞ্জিন ব্যবহার করে যেকোনো ইউটিউব ভিডিওর বিভিন্ন রেজোলিউশন (1080p, 720p, 480p) এবং হাই-কোয়ালিটি MP3 অডিও ডাউনলোড করতে পারে।

---

## ✨ প্রধান ফিচারসমূহ (Features)

- **📱 রেসপন্সিভ মোবাইল-ফার্স্ট ডিজাইন:** Tailwind CSS দিয়ে তৈরি ডার্ক মোড ইন্টারফেস।
- **📋 ওয়ান-ক্লিক পেস্ট বাটন:** ক্লিপবোর্ড থেকে সরাসরি লিঙ্ক পেস্ট করার সুবিধা।
- **🔍 অটোমেটিক মেটাডাটা প্রিভিউ:** ভিডিও থাম্বনেইল, শিরোনাম, সময়কাল, চ্যানেল এবং ভিউজ দেখা যায়।
- **🎥 বিভিন্ন কোয়ালিটি অপশন:** 
  - 1080p Full HD (MP4)
  - 720p HD (MP4)
  - 480p SD (MP4)
  - 360p Standard (MP4)
- **🎵 অডিও এক্সট্র্যাক্টর:** 192kbps ক্রিস্টাল ক্লিয়ার MP3 এবং অরিজিনাল M4A ট্র্যাক ডাউনলোড।
- **⚡ লাইভ প্রোগ্রেস বার:** ডাউনলোড স্পিড (MB/s), সাইজ, সময় (ETA) ও FFmpeg মার্জিং স্ট্যাটাস।
- **💾 ডুয়াল সেভ অপশন:** সরাসরি ব্রাউজারে ডাউনলোড অথবা ডিভাইসের নিজস্ব ডাউনলোড ফোল্ডারে সেভ।

---

## 🚀 লোকাল সেটআপ (Termux / Linux / PC)

```bash
# ১. ডিপেনডেন্সি ইনস্টল করুন
pip install -r requirements.txt

# ২. সার্ভার রান করুন
python app.py
```
ব্রাউজারে যান: `http://localhost:5000`

---

## ☁️ ক্লাউডে ফ্রি ডিপ্লয়মেন্ট (Free Cloud Hosting)

এই রিপোজিটরিটি যেকোনো ক্লাউড প্রোভাইডারে খুব সহজে ফ্রিতে ডিপ্লয় করা যাবে:

1. **[Render.com](https://render.com/)**:
   - `New +` -> `Web Service` সিলেক্ট করুন।
   - আপনার এই GitHub রিপোজিটরিটি কানেক্ট করুন।
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python app.py`

2. **[Hugging Face Spaces](https://huggingface.co/spaces)**:
   - `Create new Space` -> Space SDK: `Docker`
   - এই রিপোজিটরির ফাইলগুলো আপলোড করুন অথবা কানেক্ট করুন।
   - সম্পূর্ণ ফ্রিতে ২৪ ঘণ্টা লাইভ চলবে!

3. **[Koyeb](https://www.koyeb.com/)**:
   - GitHub দিয়ে লগইন করে Dockerfile বা Python সিলেক্ট করলেই অটো ডিপ্লয় হয়ে যাবে।

---

## 🛠️ টেকনোলজি স্ট্যাক
- **Backend:** Python 3, Flask
- **Media Engine:** yt-dlp, FFmpeg
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Fetch API + SSE Polling)
