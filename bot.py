import os, re, time, requests, numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import *

GROQ_API_KEY   = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]
NEWS_API_KEY   = os.environ["NEWS_API_KEY"]

def get_trending_news():
    print("📰 Fetching trending European finance news...")
    try:
        url = (
            "https://newsapi.org/v2/top-headlines"
            "?category=business"
            "&language=en"
            "&pageSize=5"
            f"&apiKey={NEWS_API_KEY}"
        )
        r = requests.get(url, timeout=15)
        data = r.json()
        articles = data.get("articles", [])
        if articles:
            headlines = [a["title"] for a in articles if a.get("title")]
            combined = " | ".join(headlines[:3])
            print(f"✅ News found: {combined[:100]}...")
            return combined
    except Exception as e:
        print(f"⚠️ News fetch error: {e}")
    return None

def get_topic_from_groq():
    print("🤖 Groq generating topic...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": 
            "Suggest ONE compelling YouTube video topic about personal finance or investing for European audience in 2025. Just the topic title, nothing else. Make it shocking or curiosity-triggering."}],
        "max_tokens": 100
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=30)
    result = r.json()
    topic = result["choices"][0]["message"]["content"].strip()
    print(f"✅ Groq topic: {topic}")
    return topic

def get_topic():
    news = get_trending_news()
    if news:
        return f"Based on today's news: {news} — explain the financial impact for everyday Europeans"
    else:
        return get_topic_from_groq()

def generate_script(topic):
    print(f"📝 Generating script...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""Write a compelling YouTube video script for European audience about: "{topic}"

Structure:
- HOOK (30 seconds): Shocking fact or question
- PROBLEM (1 minute): Real European statistics
- MAIN CONTENT (5 minutes): 3 key points with stories
- SOLUTION (2 minutes): Practical actionable tips
- CTA (30 seconds): Subscribe and comment

Requirements:
- Conversational tone
- European context (euros, EU countries)
- Specific numbers and statistics
- 800-1000 words
- NO stage directions, just spoken words

After script provide:
TITLE: [5 catchy title options]
TAGS: [30 relevant tags comma separated]
DESCRIPTION: [300 word SEO description]
THUMBNAIL_TEXT: [Bold 5-6 word hook]
SEARCH_TERMS: [5 Pexels search terms comma separated]"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4000,
        "temperature": 0.8
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=60)
    result = r.json()
    return result["choices"][0]["message"]["content"]

def parse_script(full_text):
    lines = full_text.strip().split("\n")
    script_lines = []
    meta = {
        "titles": "", "tags": "", "description": "",
        "thumbnail": "", "search_terms": "money,finance,investment,europe,savings"
    }
    in_meta = False
    for line in lines:
        l = line.strip()
        if l.startswith("TITLE:"):
            in_meta = True
            meta["titles"] = l.replace("TITLE:", "").strip()
        elif l.startswith("TAGS:"):
            meta["tags"] = l.replace("TAGS:", "").strip()
        elif l.startswith("DESCRIPTION:"):
            meta["description"] = l.replace("DESCRIPTION:", "").strip()
        elif l.startswith("THUMBNAIL_TEXT:"):
            meta["thumbnail"] = l.replace("THUMBNAIL_TEXT:", "").strip()
        elif l.startswith("SEARCH_TERMS:"):
            meta["search_terms"] = l.replace("SEARCH_TERMS:", "").strip()
        elif not in_meta and l:
            script_lines.append(l)
    script = " ".join(script_lines)
    title = meta["titles"].split("\n")[0].strip("1234567890. ").strip() if meta["titles"] else "Finance Tips"
    return script, title, meta

def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating voiceover...")
    tts = gTTS(text=script, lang="en", tld="co.uk", slow=False)
    tts.save(filename)
    return filename

def get_pexels_videos(search_terms, count=5):
    print("🎬 Fetching stock footage...")
    videos = []
    terms = [t.strip() for t in search_terms.split(",")][:3]
    headers = {"Authorization": PEXELS_API_KEY}
    for term in terms:
        url = f"https://api.pexels.com/videos/search?query={term}&per_page=3&orientation=landscape"
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            data = r.json()
            for v in data.get("videos", []):
                for vf in v.get("video_files", []):
                    if vf.get("quality") in ["hd", "sd"] and vf.get("width", 0) >= 1280:
                        videos.append(vf["link"])
                        break
        if len(videos) >= count:
            break
    print(f"✅ Found {len(videos)} videos")
    return videos[:count]

def download_video(url, filename):
    r = requests.get(url, timeout=60, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

def create_thumbnail(thumbnail_text, title, filename="thumbnail.jpg"):
    print("🖼️ Creating thumbnail...")
    img = Image.new("RGB", (1280, 720), color=(10, 10, 40))
    draw = ImageDraw.Draw(img)
    for y in range(720):
        r_val = int(10 + (y/720) * 30)
        g_val = int(10 + (y/720) * 20)
        b_val = int(40 + (y/720) * 60)
        draw.line([(0, y), (1280, y)], fill=(r_val, g_val, b_val))
    draw.rectangle([0, 0, 8, 720], fill=(255, 200, 0))
    draw.rectangle([0, 680, 1280, 720], fill=(255, 200, 0))
    try:
        font_big   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font_big   = ImageFont.load_default()
        font_small = font_big
    words = thumbnail_text.upper().split()
    lines = []
    current = []
    for w in words:
        current.append(w)
        if len(" ".join(current)) > 18:
            lines.append(" ".join(current[:-1]))
            current = [w]
    if current:
        lines.append(" ".join(current))
    y_start = 120
    for i, line in enumerate(lines[:3]):
        color = (255, 220, 0) if i == 0 else (255, 255, 255)
        draw.text((44, y_start + 4), line, font=font_big, fill=(0, 0, 0))
        draw.text((40, y_start), line, font=font_big, fill=color)
        y_start += 110
    short_title = title[:60] + "..." if len(title) > 60 else title
    draw.text((40, 620), short_title, font=font_small, fill=(200, 200, 200))
    img.save(filename, quality=95)
    return filename

def create_video(audio_file, video_urls, thumbnail_text, output="final_video.mp4"):
    print("🎞️ Assembling video...")
    audio = AudioFileClip(audio_file)
    total_duration = audio.duration
    print(f"⏱️ Duration: {total_duration:.1f}s")
    clips = []
    downloaded = []
    if video_urls:
        segment_duration = total_duration / max(len(video_urls), 1)
        for i, url in enumerate(video_urls):
            fname = f"clip_{i}.mp4"
            try:
                print(f"⬇️ Clip {i+1}/{len(video_urls)}...")
                download_video(url, fname)
                clip = VideoFileClip(fname).resized((1280, 720))
                if clip.duration < segment_duration:
                    clip = clip.with_effects([vfx.Loop(duration=segment_duration)])
                else:
                    clip = clip.subclipped(0, segment_duration)
                clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.02 * t)])
                clips.append(clip)
                downloaded.append(fname)
            except Exception as e:
                print(f"⚠️ Clip {i} error: {e}")
    if not clips:
        clips = [ColorClip(size=(1280, 720), color=[10, 10, 40], duration=total_duration)]
    video = concatenate_videoclips(clips, method="compose")
    if video.duration < total_duration:
        video = video.with_effects([vfx.Loop(duration=total_duration)])
    video = video.subclipped(0, total_duration)
    final = video.with_audio(audio)
    txt = TextClip(
        text="Smart Money Tips",
        font_size=28,
        color="white",
        font="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ).with_position(("right", "bottom")).with_duration(total_duration)
    final = CompositeVideoClip([final, txt])
    final.write_videofile(output, fps=24, codec="libx264",
                          audio_codec="aac", logger=None)
    for f in downloaded:
        try: os.remove(f)
        except: pass
    return output

def save_metadata(title, meta, topic):
    first_title = meta.get("titles", title).split("\n")[0].strip("1234567890. ").strip()
    content = f"""# VIDEO METADATA
## Topic: {topic}

## BEST TITLE:
{first_title}

## ALL TITLES:
{meta.get('titles', '')}

## TAGS:
{meta.get('tags', '')}

## DESCRIPTION:
{meta.get('description', '')}

## THUMBNAIL TEXT:
{meta.get('thumbnail', '')}

## Upload Checklist:
- [ ] Upload final_video.mp4
- [ ] Use best title
- [ ] Add all tags
- [ ] Copy description
- [ ] Upload thumbnail.jpg
- [ ] Category: Education
"""
    with open("metadata.txt", "w") as f:
        f.write(content)
    print("📄 Metadata saved!")

def main():
    print("🚀 YouTube Bot Starting...")
    topic = get_topic()
    print(f"📌 Topic: {topic}")
    full_text = generate_script(topic)
    script, title, meta = parse_script(full_text)
    print(f"✅ Script: {len(script.split())} words")
    audio_file = generate_audio(script)
    search_terms = meta.get("search_terms", "money finance europe")
    video_urls = get_pexels_videos(search_terms)
    create_thumbnail(meta.get("thumbnail", topic[:30]), title)
    create_video(audio_file, video_urls, meta.get("thumbnail", ""))
    save_metadata(title, meta, topic)
    print("\n✅ ALL DONE!")

main()
