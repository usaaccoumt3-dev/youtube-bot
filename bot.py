import os, re, time, textwrap, requests, numpy as np
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont
from moviepy import *

GROQ_API_KEY  = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY = os.environ["PEXELS_API_KEY"]

TOPICS = [
    "Why most Europeans will retire broke and how to avoid it",
    "The secret investment strategy rich Europeans use",
    "How to save 1000 euros in 30 days on any salary",
    "Why your savings account is making you poorer",
    "The 5 money mistakes destroying European families",
    "How compound interest can make you rich by 40",
    "Why Europeans dont invest and how to start today",
    "The truth about European pension crisis 2025",
    "How to build passive income with just 100 euros",
    "Why inflation is stealing your wealth silently",
]

def get_topic():
    day = int(time.strftime("%j"))
    return TOPICS[day % len(TOPICS)]

def generate_script(topic):
    print(f"📝 Generating script for: {topic}")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""Write a compelling YouTube video script for European audience about: "{topic}"

Structure:
- HOOK (30 seconds): Shocking fact or question that grabs attention immediately
- PROBLEM (1 minute): Explain the problem with real European statistics
- MAIN CONTENT (5 minutes): Deep dive with 3 key points, stories, examples
- SOLUTION (2 minutes): Practical actionable tips
- CTA (30 seconds): Subscribe and comment call to action

Requirements:
- Conversational tone, not robotic
- Use European context (euros, EU countries, European culture)
- Include specific numbers and statistics
- Total length: 800-1000 words
- NO stage directions, just the spoken words

Also provide at END (after script):
TITLE: [5 catchy YouTube title options]
TAGS: [30 relevant tags comma separated]
DESCRIPTION: [300 word SEO description]
THUMBNAIL_TEXT: [Bold 5-6 word hook for thumbnail]
SEARCH_TERMS: [5 Pexels search terms for background footage, comma separated]"""

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
    meta = {"titles": "", "tags": "", "description": "", "thumbnail": "", "search_terms": "money,finance,investment,europe,savings"}
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
    title = meta["titles"].split("\n")[0].strip("1. ").strip() if meta["titles"] else "Finance Tips"
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

    # Gradient background
    for y in range(720):
        r_val = int(10 + (y/720) * 30)
        g_val = int(10 + (y/720) * 20)
        b_val = int(40 + (y/720) * 60)
        draw.line([(0, y), (1280, y)], fill=(r_val, g_val, b_val))

    # Accent bar
    draw.rectangle([0, 0, 8, 720], fill=(255, 200, 0))
    draw.rectangle([0, 680, 1280, 720], fill=(255, 200, 0))

    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 90)
        font_med = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 45)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except:
        font_big = ImageFont.load_default()
        font_med = font_big
        font_small = font_big

    # Main hook text
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
        # Shadow
        draw.text((44, y_start + 4), line, font=font_big, fill=(0, 0, 0))
        draw.text((40, y_start), line, font=font_big, fill=color)
        y_start += 110

    # Bottom title
    short_title = title[:60] + "..." if len(title) > 60 else title
    draw.text((40, 620), short_title, font=font_small, fill=(200, 200, 200))

    img.save(filename, quality=95)
    return filename

def create_video(audio_file, video_urls, thumbnail_text, output="final_video.mp4"):
    print("🎞️ Assembling video...")
    audio = AudioFileClip(audio_file)
    total_duration = audio.duration
    print(f"⏱️ Audio duration: {total_duration:.1f}s")

    clips = []
    downloaded = []

    if video_urls:
        segment_duration = total_duration / max(len(video_urls), 1)
        for i, url in enumerate(video_urls):
            fname = f"clip_{i}.mp4"
            try:
                print(f"⬇️ Downloading clip {i+1}/{len(video_urls)}...")
                download_video(url, fname)
                clip = VideoFileClip(fname).resized((1280, 720))
                if clip.duration < segment_duration:
                    clip = clip.with_effects([vfx.Loop(duration=segment_duration)])
                else:
                    clip = clip.subclipped(0, segment_duration)
                # Ken Burns zoom effect
                clip = clip.with_effects([vfx.Resize(lambda t: 1 + 0.02 * t)])
                clips.append(clip)
                downloaded.append(fname)
            except Exception as e:
                print(f"⚠️ Clip {i} error: {e}")

    if not clips:
        print("⚠️ No clips — using black background")
        clips = [ColorClip(size=(1280, 720), color=[10, 10, 40], duration=total_duration)]

    # Concatenate all clips
    video = concatenate_videoclips(clips, method="compose")
    if video.duration < total_duration:
        video = video.with_effects([vfx.Loop(duration=total_duration)])
    video = video.subclipped(0, total_duration)

    # Add audio
    final = video.with_audio(audio)

    # Add watermark text
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
    titles = meta.get("titles", title)
    first_title = titles.split("\n")[0].strip().lstrip("1234567890. ").strip()
    content = f"""# VIDEO METADATA
## Topic: {topic}

## BEST TITLE:
{first_title}

## ALL TITLE OPTIONS:
{meta.get('titles', '')}

## TAGS:
{meta.get('tags', '')}

## DESCRIPTION:
{meta.get('description', '')}

## THUMBNAIL TEXT:
{meta.get('thumbnail', '')}

## Upload Checklist:
- [ ] Upload final_video.mp4 to YouTube
- [ ] Use best title above
- [ ] Add all tags
- [ ] Copy description
- [ ] Upload thumbnail.jpg
- [ ] Set category: Education
- [ ] Add end screen at last 20 seconds
"""
    with open("metadata.txt", "w") as f:
        f.write(content)
    print("📄 Metadata saved!")

def main():
    print("🚀 YouTube Bot Starting...")
    topic = get_topic()
    print(f"📌 Today's topic: {topic}")

    full_text = generate_script(topic)
    script, title, meta = parse_script(full_text)
    print(f"✅ Script ready ({len(script.split())} words)")

    audio_file = generate_audio(script)
    search_terms = meta.get("search_terms", "money finance europe investment")
    video_urls = get_pexels_videos(search_terms)
    thumbnail = create_thumbnail(meta.get("thumbnail", topic[:30]), title)
    video = create_video(audio_file, video_urls, meta.get("thumbnail", ""))
    save_metadata(title, meta, topic)

    print("\n✅ ALL DONE!")
    print(f"📹 Video: {video}")
    print(f"🖼️ Thumbnail: {thumbnail}")
    print(f"📄 Metadata: metadata.txt")

main()
