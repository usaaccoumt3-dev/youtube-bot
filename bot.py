import os, time, requests
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import *

GROQ_API_KEY   = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
NEWS_API_KEY   = os.environ["NEWS_API_KEY"]

def get_trending_news():
    print("📰 Fetching news...")
    try:
        url = (f"https://newsapi.org/v2/top-headlines"
               f"?category=business&language=en&pageSize=5"
               f"&apiKey={NEWS_API_KEY}")
        r = requests.get(url, timeout=15)
        data = r.json()
        articles = data.get("articles", [])
        if articles:
            headlines = [a["title"] for a in articles if a.get("title")]
            combined = " | ".join(headlines[:3])
            print(f"✅ News: {combined[:80]}...")
            return combined
    except Exception as e:
        print(f"⚠️ News error: {e}")
    return None

def get_topic_from_groq():
    print("🤖 Groq picking topic...")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            "Give me ONE shocking YouTube finance topic for European audience 2025. Just the title, nothing else."}],
        "max_tokens": 80
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=30)
    return r.json()["choices"][0]["message"]["content"].strip()

def get_topic():
    news = get_trending_news()
    if news:
        return f"Today's breaking news: {news} — financial impact for Europeans"
    return get_topic_from_groq()

def generate_script(topic):
    print("📝 Writing script...")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt = f"""Write a YouTube video script for European finance audience about: "{topic}"

VERY IMPORTANT - Follow this EXACT structure:

[HOOK]
Start with a shocking statement or question. Example: "What if I told you that 73% of Europeans will run out of money before they die?" Make it dramatic and suspenseful. 2-3 sentences only.

[WELCOME]
"Welcome to Smart Money Tips — the channel that gives you the financial truth they don't want you to know. I'm your host, and today we're diving deep into [topic]. If you care about your money, hit subscribe right now — because what I'm about to reveal could change everything."

[PROBLEM]
Explain the problem with real European statistics and stories. 2 minutes of content.

[MAIN CONTENT]
3 key points with real examples, numbers, European context. 4 minutes of content.

[SOLUTION]
Practical actionable tips for Europeans. 1 minute.

[OUTRO]
"That's everything for today. If this opened your eyes, smash that like button — it helps more Europeans find this truth. Subscribe for daily financial insights. I'll see you in the next one. Stay smart, stay wealthy."

Requirements:
- Conversational, NOT robotic
- European context (euros, EU, specific countries)
- Real statistics and numbers
- Total 900-1000 words
- NO stage directions — just spoken words only

---
After the script, on NEW LINES write exactly:

BEST_TITLE: [single most clickable title]
ALL_TITLES: [5 title options numbered]
TAGS: [30 comma separated tags]
DESCRIPTION: [250 word SEO description with keywords]
THUMBNAIL: [5-6 word shocking hook NO asterisks NO special chars]
SEARCH_TERMS: [5 pexels search terms comma separated]"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.8
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=60)
    return r.json()["choices"][0]["message"]["content"]

def parse_script(full_text):
    lines = full_text.strip().split("\n")
    script_lines = []
    meta = {
        "best_title": "Smart Money Tips",
        "all_titles": "",
        "tags": "",
        "description": "",
        "thumbnail": "SHOCKING MONEY TRUTH REVEALED",
        "search_terms": "money,finance,investment,europe,savings"
    }
    in_meta = False
    for line in lines:
        l = line.strip()
        if l.startswith("BEST_TITLE:"):
            in_meta = True
            meta["best_title"] = l.replace("BEST_TITLE:", "").strip().strip("*").strip()
        elif l.startswith("ALL_TITLES:"):
            meta["all_titles"] = l.replace("ALL_TITLES:", "").strip()
        elif l.startswith("TAGS:"):
            meta["tags"] = l.replace("TAGS:", "").strip()
        elif l.startswith("DESCRIPTION:"):
            meta["description"] = l.replace("DESCRIPTION:", "").strip()
        elif l.startswith("THUMBNAIL:"):
            raw = l.replace("THUMBNAIL:", "").strip()
            meta["thumbnail"] = raw.replace("*","").replace("[","").replace("]","").strip()
        elif l.startswith("SEARCH_TERMS:"):
            meta["search_terms"] = l.replace("SEARCH_TERMS:", "").strip()
        elif not in_meta and l:
            script_lines.append(l)

    script = " ".join(script_lines)
    return script, meta["best_title"], meta

def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating voiceover...")
    tts = gTTS(text=script, lang="en", tld="co.uk", slow=False)
    tts.save(filename)
    return filename

def get_pexels_videos(search_terms, count=6):
    print("🎬 Fetching footage...")
    videos = []
    terms = [t.strip() for t in search_terms.split(",")][:4]
    headers = {"Authorization": PEXELS_API_KEY}
    for term in terms:
        url = f"https://api.pexels.com/videos/search?query={term}&per_page=3&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            for v in r.json().get("videos", []):
                for vf in v.get("video_files", []):
                    if vf.get("quality") in ["hd","sd"] and vf.get("width",0) >= 1280:
                        videos.append(vf["link"])
                        break
        if len(videos) >= count:
            break
    print(f"✅ {len(videos)} videos found")
    return videos[:count]

def download_video(url, filename):
    r = requests.get(url, timeout=60, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

def create_thumbnail(thumbnail_text, title, filename="thumbnail.jpg"):
    print("🖼️ Creating thumbnail...")
    img = Image.new("RGB", (1280, 720), color=(15, 15, 35))
    draw = ImageDraw.Draw(img)

    # Dark gradient
    for y in range(720):
        rv = int(15 + (y/720)*25)
        gv = int(10 + (y/720)*15)
        bv = int(35 + (y/720)*50)
        draw.line([(0,y),(1280,y)], fill=(rv,gv,bv))

    # Red accent bar left
    draw.rectangle([0,0,12,720], fill=(220,30,30))
    # Yellow bottom bar
    draw.rectangle([0,665,1280,720], fill=(255,200,0))
    # Yellow bottom text area
    draw.rectangle([0,665,1280,720], fill=(255,200,0))

    try:
        font_huge  = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 95)
        font_med   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 42)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
    except:
        font_huge = font_med = font_small = ImageFont.load_default()

    # Clean thumbnail text
    clean = thumbnail_text.upper().replace("*","").replace("[","").replace("]","").strip()
    words = clean.split()
    lines, current = [], []
    for w in words:
        current.append(w)
        if len(" ".join(current)) > 16:
            if len(current) > 1:
                lines.append(" ".join(current[:-1]))
                current = [w]
            else:
                lines.append(" ".join(current))
                current = []
    if current:
        lines.append(" ".join(current))

    y_pos = 80
    for i, line in enumerate(lines[:3]):
        color = (255,220,0) if i==0 else (255,255,255)
        # Shadow
        draw.text((32,y_pos+5), line, font=font_huge, fill=(0,0,0))
        draw.text((28,y_pos), line, font=font_huge, fill=color)
        y_pos += 105

    # Channel name on yellow bar
    draw.text((30,672), "SMART MONEY TIPS", font=font_small, fill=(20,20,20))

    # Breaking news badge
    draw.rectangle([850,30,1250,90], fill=(220,30,30))
    draw.text((865,38), "BREAKING NEWS", font=font_med, fill=(255,255,255))

    img.save(filename, quality=95)
    return filename

def create_video(audio_file, video_urls, title, output="final_video.mp4"):
    print("🎞️ Assembling video...")
    audio = AudioFileClip(audio_file)
    total_dur = audio.duration
    print(f"⏱️ {total_dur:.0f}s = {total_dur/60:.1f} min")

    clips = []
    downloaded = []

    if video_urls:
        seg = total_dur / max(len(video_urls), 1)
        for i, url in enumerate(video_urls):
            fname = f"clip_{i}.mp4"
            try:
                print(f"⬇️ Clip {i+1}/{len(video_urls)}...")
                download_video(url, fname)
                clip = VideoFileClip(fname).resized((1280,720))
                if clip.duration < seg:
                    clip = clip.with_effects([vfx.Loop(duration=seg)])
                else:
                    clip = clip.subclipped(0, seg)
                # Ken Burns zoom
                clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.015*t)])
                clips.append(clip)
                downloaded.append(fname)
            except Exception as e:
                print(f"⚠️ Clip {i}: {e}")

    if not clips:
        clips = [ColorClip(size=(1280,720), color=[15,15,35], duration=total_dur)]

    video = concatenate_videoclips(clips, method="compose")
    if video.duration < total_dur:
        video = video.with_effects([vfx.Loop(duration=total_dur)])
    video = video.subclipped(0, total_dur)
    final = video.with_audio(audio)

    # Watermark
    wm = TextClip(
        text="Smart Money Tips",
        font_size=26,
        color="white",
        font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ).with_position((30, 30)).with_duration(total_dur)

    final = CompositeVideoClip([final, wm])
    final.write_videofile(output, fps=24, codec="libx264",
                          audio_codec="aac", logger=None)

    for f in downloaded:
        try: os.remove(f)
        except: pass
    return output

def save_metadata(title, meta, topic):
    content = f"""# VIDEO METADATA — Smart Money Tips
Generated: {time.strftime('%Y-%m-%d %H:%M UTC')}

━━━━━━━━━━━━━━━━━━━━━━━━
📌 TOPIC:
{topic}

━━━━━━━━━━━━━━━━━━━━━━━━
🏆 BEST TITLE (use this):
{meta.get('best_title', title)}

━━━━━━━━━━━━━━━━━━━━━━━━
📋 ALL TITLE OPTIONS:
{meta.get('all_titles', '')}

━━━━━━━━━━━━━━━━━━━━━━━━
🏷️ TAGS (copy all):
{meta.get('tags', '')}

━━━━━━━━━━━━━━━━━━━━━━━━
📄 DESCRIPTION (copy all):
{meta.get('description', '')}

━━━━━━━━━━━━━━━━━━━━━━━━
🖼️ THUMBNAIL TEXT:
{meta.get('thumbnail', '')}

━━━━━━━━━━━━━━━━━━━━━━━━
✅ UPLOAD CHECKLIST:
[ ] Upload final_video.mp4 to YouTube
[ ] Paste BEST TITLE above
[ ] Copy all TAGS
[ ] Copy DESCRIPTION
[ ] Upload thumbnail.jpg
[ ] Category: Education or News & Politics
[ ] Add end screen (last 20 seconds)
[ ] Add cards at 40% and 70% of video
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("📄 Metadata saved!")

def main():
    print("🚀 Smart Money Tips Bot Starting...")
    topic = get_topic()
    print(f"📌 Topic: {topic[:80]}...")

    full_text = generate_script(topic)
    script, title, meta = parse_script(full_text)
    print(f"✅ Script ready: {len(script.split())} words")

    audio_file  = generate_audio(script)
    search_terms = meta.get("search_terms", "money finance europe investment")
    video_urls  = get_pexels_videos(search_terms)
    create_thumbnail(meta.get("thumbnail","SHOCKING MONEY TRUTH"), title)
    create_video(audio_file, video_urls, title)
    save_metadata(title, meta, topic)

    print("\n🎉 ALL DONE!")
    print(f"📹 Video ready to upload!")

main()
