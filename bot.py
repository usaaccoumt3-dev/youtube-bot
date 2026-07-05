import os, time, requests, random, re
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy import *

# ═══════════════════════════════════
# CONFIG
# ═══════════════════════════════════
GROQ_API_KEY     = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY   = os.environ["PEXELS_API_KEY"]
NEWS_API_KEY     = os.environ["NEWS_API_KEY"]

CHANNEL_NAME     = "Smart Money Tips"
TARGET_MARKETS   = "UK, Germany, Switzerland"
SCENE_DURATION   = 6
VIDEO_FPS        = 24
VIDEO_SIZE       = (1280, 720)
USED_TOPICS_FILE = "used_topics.txt"

# ═══════════════════════════════════
# HIGH RPM NICHES — evergreen, never expire
# ═══════════════════════════════════
HIGH_RPM_NICHES = [
    "The psychological trap that keeps 80 percent of Europeans broke forever",
    "UK property market collapse — what smart money is doing right now",
    "Swiss banking secrets that protect wealth during inflation crisis",
    "German real estate bubble — where to move your money before it bursts",
    "European pension funds quietly going bankrupt — what you must do now",
    "The wealth gap in Germany is wider than the 1920s — here is the proof",
    "UK mortgage trap — why millions will lose their homes in 2025",
    "Why saving money in Europe is making you poorer every single year",
    "The financial myth that banks teach Europeans to keep them dependent",
    "How the European Central Bank is silently destroying your savings",
    "Why 73 percent of Europeans retire broke despite working their whole life",
    "The hidden tax destroying middle class wealth across the EU right now",
    "Why renting in Germany is smarter than buying — the truth banks hide",
    "The investment strategy Swiss billionaires use that Europeans never hear about",
    "How inflation is stealing 40 percent of European savings without anyone noticing",
    "Why the UK housing market is about to experience its worst crash in 40 years",
    "The financial education gap — why European schools teach you to stay poor",
    "How European governments use tax policy to keep the middle class trapped",
    "Why most European financial advisors are legally allowed to give bad advice",
    "The compound interest secret that could make any European financially free",
]

# ═══════════════════════════════════
# DUPLICATE GUARD
# ═══════════════════════════════════
def load_used_topics():
    if not os.path.exists(USED_TOPICS_FILE):
        return []
    with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f.readlines() if line.strip()]

def save_used_topic(topic):
    with open(USED_TOPICS_FILE, "a", encoding="utf-8") as f:
        f.write(topic.strip() + "\n")

def is_duplicate(topic, used_list):
    topic_words = set(topic.lower().split())
    for u in used_list:
        u_words = set(u.split())
        overlap = len(topic_words & u_words) / max(len(topic_words), 1)
        if overlap > 0.55:
            return True
    return False

# ═══════════════════════════════════
# NEWS
# ═══════════════════════════════════
def get_trending_news():
    print("📰 Fetching financial niche news...")
    try:
        # Finance se related keywords ka filter
        finance_keywords = ["economy", "inflation", "interest rates", "property", "market", "bank", "invest"]
        url = (
            f"https://newsapi.org/v2/everything"
            f"?q=European+economy+OR+UK+finance+OR+Germany+market"
            f"&language=en&sortBy=publishedAt&pageSize=5"
            f"&apiKey={NEWS_API_KEY}"
        )
        r = requests.get(url, timeout=15)
        articles = [a for a in r.json().get("articles", []) if a.get("title")]
        
        # Sirf relevant headlines select karo
        for article in articles:
            title = article["title"].lower()
            if any(k in title for k in finance_keywords):
                print(f"✅ Finance News found: {article['title'][:80]}...")
                return article["title"]
    except Exception as e:
        print(f"⚠️ News error: {e}")
    return None


# ═══════════════════════════════════
# GROQ TOPIC
# ═══════════════════════════════════
def get_topic_from_groq(used_list):
    print("🤖 Groq generating unique topic...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    niche_hint = random.choice(HIGH_RPM_NICHES)
    used_sample = "; ".join(used_list[-15:]) if used_list else "none"
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"Generate ONE shocking, curiosity-driven YouTube finance topic for UK, Germany, and Switzerland audiences in 2025. "
            f"Focus on: wealth psychology, property market crisis, or financial myths. "
            f"Inspiration angle: {niche_hint}. "
            f"AVOID topics similar to these already used: {used_sample}. "
            f"Return ONLY the topic — no quotes, no explanation, no extra text."}],
        "max_tokens": 120,
        "temperature": 0.95
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=data, timeout=30
    )
    return r.json()["choices"][0]["message"]["content"].strip()

# ═══════════════════════════════════
# TOPIC SELECTOR — with duplicate guard + retry
# ═══════════════════════════════════
def get_topic():
    used = load_used_topics()

    # Try news first
    news = get_trending_news()
    if news:
        candidate = (
            f"Breaking European financial news — {news} "
            f"and what it means for your money in {TARGET_MARKETS}"
        )
        if not is_duplicate(candidate, used):
            save_used_topic(candidate)
            return candidate
        print("⚠️ News topic duplicate — trying Groq...")

    # Try Groq with up to 5 attempts
    for attempt in range(5):
        candidate = get_topic_from_groq(used)
        if not is_duplicate(candidate, used):
            save_used_topic(candidate)
            print(f"✅ Topic: {candidate[:80]}")
            return candidate
        print(f"⚠️ Duplicate attempt {attempt+1} — retrying...")

    # Absolute fallback — date ensures uniqueness
    today    = time.strftime('%B %d %Y')
    fallback = random.choice(HIGH_RPM_NICHES) + f" — the {today} reality check"
    save_used_topic(fallback)
    print(f"✅ Fallback topic: {fallback[:80]}")
    return fallback

# ═══════════════════════════════════
# SCRIPT — Hypnotic storytelling
# ═══════════════════════════════════
def generate_script(topic):
    print("📝 Writing hypnotic script...")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    prompt = f"""You are the most viral YouTube scriptwriter for high-income audiences in UK, Germany, and Switzerland.

Write a HYPNOTIC financial video script about: "{topic}"

ABSOLUTE RULES — violate any of these and the script fails:
1. BANNED: "Welcome to my channel" — never write this
2. BANNED: "Today we will discuss" — never write this
3. BANNED: Robotic transitions like "Moving on" or "In conclusion"
4. REQUIRED: Start with ONE devastating counter-intuitive fact in the first 2 sentences that stops scrolling instantly
5. REQUIRED: Every 90 words, end the paragraph with a one-sentence curiosity tease that forces reading the next paragraph
6. REQUIRED: Real European statistics with specific percentages, years, and country names
7. REQUIRED: Tone is analytical, slightly conspiratorial, authoritative — like someone revealing secrets
8. REQUIRED: 950 to 1050 words of pure spoken content — zero stage directions, zero brackets, zero formatting

EXACT STRUCTURE TO FOLLOW:

[PATTERN INTERRUPT — first 40 words]
One devastating ironic fact. Example: "The country where people work the most hours in Europe is also the country where people retire the poorest. That country is not Greece. It is Germany. And the reason has nothing to do with laziness."

[DARK REVELATION — next 120 words]
Expose the real problem with brutal specificity. Real numbers. Named cities. Named institutions. End with a one-sentence curiosity hook.

[FIRST KEY INSIGHT — next 150 words]
Deep dive with European case study. Real people, real numbers. End paragraph with tease.

[SECOND KEY INSIGHT — next 150 words]
The mechanism nobody explains. How the system actually works against ordinary Europeans. End paragraph with tease.

[THIRD KEY INSIGHT — next 150 words]
The psychological dimension — why people choose to stay trapped. End with the darkest tease yet.

[SOLUTION — next 120 words]
Three specific actionable steps. European-specific. Name the exact accounts, strategies, or moves. No generic advice.

[POWER OUTRO — final 60 words]
"If you are still watching, you are already thinking differently from 95 percent of Europeans. Most people will watch this and do nothing. You are not most people. If this changed one thing in how you see money, press like — it takes one second and it helps more Europeans find this truth. Subscribe. Tomorrow I am covering something that will make today look like a warm-up. I will see you there."

---
After the script write EXACTLY on new lines:

BEST_TITLE: [max 60 characters, format: Shocking Result + Specific Reason + 2025]
ALL_TITLES: [5 numbered title options]
TAGS: [30 comma-separated YouTube SEO tags]
DESCRIPTION: [250 words: opening hook paragraph, What You Will Learn bullets, European CTA at end]
THUMBNAIL: [exactly 3 to 4 words, ALL CAPS, zero special characters, creates open-loop curiosity]
SEARCH_TERMS: [12 specific Pexels terms: use european architecture, financial charts, cash euro, bank buildings, real estate, city skylines — NOT generic laptop or coffee]"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4500,
        "temperature": 0.88
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=data, timeout=90
    )
    return r.json()["choices"][0]["message"]["content"]

# ═══════════════════════════════════
# PARSE SCRIPT
# ═══════════════════════════════════
def parse_script(full_text):
    lines = full_text.strip().split("\n")
    meta  = {
        "best_title":   "The Financial Truth Europe Is Hiding 2025",
        "all_titles":   "",
        "tags":         "",
        "description":  "",
        "thumbnail":    "THEY LIED TO YOU",
        "search_terms": "european bank building,euro cash money,property market chart,real estate germany,london financial district,swiss bank,inflation graph,stock market crash,housing crisis,pension fund,wealth gap,money falling"
    }
    script_lines = []
    in_meta      = False

    for line in lines:
        l = line.strip()
        if   l.startswith("BEST_TITLE:"):   in_meta = True;  meta["best_title"]   = l.replace("BEST_TITLE:","").strip().strip("*[]\"'")
        elif l.startswith("ALL_TITLES:"):   meta["all_titles"]   = l.replace("ALL_TITLES:","").strip()
        elif l.startswith("TAGS:"):         meta["tags"]         = l.replace("TAGS:","").strip()
        elif l.startswith("DESCRIPTION:"):  meta["description"]  = l.replace("DESCRIPTION:","").strip()
        elif l.startswith("THUMBNAIL:"):
            raw = l.replace("THUMBNAIL:","").strip()
            meta["thumbnail"] = raw.replace("*","").replace("[","").replace("]","").replace('"',"").strip()
        elif l.startswith("SEARCH_TERMS:"): meta["search_terms"] = l.replace("SEARCH_TERMS:","").strip()
        elif not in_meta and l:
            # Remove any leftover bracket markers
            clean = re.sub(r'\[.*?\]', '', l).strip()
            if clean:
                script_lines.append(clean)

    script = " ".join(script_lines)
    print(f"✅ Script ready: {len(script.split())} words")
    return script, meta["best_title"], meta

# ═══════════════════════════════════
# AUDIO — UK English, sentence-chunked
# ═══════════════════════════════════
def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating UK English voiceover...")
    sentences  = re.split(r'(?<=[.!?])\s+', script)
    chunk_size = 6
    chunks     = [" ".join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]

    audio_parts = []
    for idx, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
        fname = f"audio_part_{idx}.mp3"
        try:
            tts = gTTS(text=chunk, lang="en", tld="co.uk", slow=False)
            tts.save(fname)
            audio_parts.append(fname)
        except Exception as e:
            print(f"⚠️ Audio chunk {idx}: {e}")

    if not audio_parts:
        tts = gTTS(text=script, lang="en", tld="co.uk", slow=False)
        tts.save(filename)
        return filename

    if len(audio_parts) == 1:
        os.rename(audio_parts[0], filename)
    else:
        clips = [AudioFileClip(p) for p in audio_parts]
        combined = concatenate_audioclips(clips)
        combined.write_audiofile(filename, logger=None)
        for c in clips:
            try: c.close()
            except: pass
        for p in audio_parts:
            try: os.remove(p)
            except: pass

    print("✅ Audio ready")
    return filename

# ═══════════════════════════════════
# PEXELS — 40 specific finance scenes
# ═══════════════════════════════════
def get_pexels_videos(search_terms_str, target_count=40):
    print(f"🎬 Fetching {target_count} footage clips...")
    videos   = []
    terms    = [t.strip() for t in search_terms_str.split(",") if t.strip()]
    fallback = [
        "european city architecture", "euro banknotes cash",
        "stock market trading screen", "real estate luxury house",
        "bank building facade", "london skyline financial",
        "frankfurt skyscraper", "swiss city street",
        "housing market graph", "pension retirement elderly",
        "inflation grocery prices", "businessman city walking",
        "property investment", "financial chart analysis",
        "mortgage documents", "wealth gap inequality",
    ]
    all_terms = terms + [t for t in fallback if t not in terms]
    headers   = {"Authorization": PEXELS_API_KEY}

    for term in all_terms:
        if len(videos) >= target_count:
            break
        try:
            url = (
                f"https://api.pexels.com/videos/search"
                f"?query={requests.utils.quote(term)}"
                f"&per_page=5&orientation=landscape&size=medium"
            )
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            for v in r.json().get("videos", []):
                for vf in v.get("video_files", []):
                    if vf.get("quality") in ["hd","sd"] and vf.get("width",0) >= 1280:
                        videos.append({"url": vf["link"], "term": term})
                        break
        except Exception as e:
            print(f"⚠️ Pexels [{term}]: {e}")

    random.shuffle(videos)
    print(f"✅ {len(videos)} clips found")
    return videos[:target_count]

def download_video(url, filename):
    r = requests.get(url, timeout=90, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

# ═══════════════════════════════════
# THUMBNAIL — Red/Black/Gold
# High contrast, open-loop curiosity
# ═══════════════════════════════════
def load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def create_thumbnail(thumbnail_text, title, filename="thumbnail.jpg"):
    print("🖼️ Creating high-impact thumbnail...")
    W, H = 1280, 720
    img  = Image.new("RGB", (W, H), color=(8, 6, 6))
    draw = ImageDraw.Draw(img)

    # Deep dark gradient — top dark red to near black
    for y in range(H):
        ratio = y / H
        r     = int(25 + ratio * 8)
        g     = int(4  + ratio * 4)
        b     = int(4  + ratio * 8)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Subtle diagonal gold accent lines
    for x in range(-200, W+200, 90):
        draw.line([(x,0),(x+200,H)], fill=(120,90,0), width=1)

    # Bold left red power bar
    for x in range(20):
        intensity = max(0, 230 - x*8)
        draw.rectangle([x,0,x,H], fill=(intensity,0,0))

    # Bottom gold bar
    for y in range(H-75, H):
        ratio = (y-(H-75))/75
        r     = int(160 + ratio*95)
        g     = int(110 + ratio*90)
        b     = 0
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Fonts
    font_xl  = load_font(108)
    font_lg  = load_font(58)
    font_md  = load_font(36)
    font_sm  = load_font(26)
    font_xs  = load_font(22)

    # Thumbnail text — clean, 3-4 words max
    clean = thumbnail_text.upper().replace("*","").replace("[","").replace("]","").replace('"',"").strip()
    words = clean.split()[:4]

    if len(words) <= 2:
        lines = [" ".join(words)]
    elif len(words) == 3:
        lines = [words[0], " ".join(words[1:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:])]

    # Draw main text — shadow + glow + main
    y_pos  = 75
    colors = [(255,210,0), (255,255,255)]
    for i, line in enumerate(lines[:2]):
        color = colors[i] if i < len(colors) else (255,255,255)
        font  = font_xl
        # Deep shadow
        for sx, sy in [(8,8),(6,6),(4,4),(2,2)]:
            draw.text((28+sx, y_pos+sy), line, font=font, fill=(0,0,0))
        # Red glow behind gold text
        if i == 0:
            draw.text((27, y_pos+2), line, font=font, fill=(180,30,0))
        # Main text
        draw.text((26, y_pos), line, font=font, fill=color)
        y_pos += 118

    # Top-right badge — dark red
    badge = "BANKS WON'T SHOW YOU"
    bw, bh = 370, 50
    bx, by = W - bw - 20, 22
    draw.rectangle([bx-6, by-6, bx+bw+6, by+bh+6], fill=(100,0,0))
    draw.rectangle([bx, by, bx+bw, by+bh], fill=(200,15,15))
    draw.text((bx+10, by+9), badge, font=font_xs, fill=(255,240,200))

    # Channel name on gold bar
    draw.text((34, H-58), CHANNEL_NAME.upper(), font=font_md, fill=(15,10,5))

    # 2025 year pill — right side of gold bar
    draw.rectangle([W-130, H-68, W-12, H-12], fill=(180,15,15))
    draw.text((W-118, H-56), "2025", font=font_md, fill=(255,255,255))

    # Vignette overlay — edges darker
    vignette = Image.new("RGBA", (W,H), (0,0,0,0))
    vd = ImageDraw.Draw(vignette)
    for i in range(150):
        alpha = int(i * 1.1)
        vd.rectangle([i,i,W-i,H-i], outline=(0,0,0,alpha))

    img_rgba = img.convert("RGBA")
    img_rgba = Image.alpha_composite(img_rgba, vignette)
    img_final = img_rgba.convert("RGB")

    # Slight contrast boost
    from PIL import ImageEnhance
    img_final = ImageEnhance.Contrast(img_final).enhance(1.15)
    img_final = ImageEnhance.Sharpness(img_final).enhance(1.2)

    img_final.save(filename, quality=97)
    print("✅ Thumbnail saved")
    return filename

# ═══════════════════════════════════
# VIDEO — 30-40 scenes @ 6s each
# ═══════════════════════════════════
def create_video(audio_file, video_clips, title, output="final_video.mp4"):
    print("🎞️ Assembling hypnotic video...")
    audio     = AudioFileClip(audio_file)
    total_dur = audio.duration
    print(f"⏱️ Duration: {total_dur:.0f}s = {total_dur/60:.1f} min")

    target_scenes = max(int(total_dur / SCENE_DURATION), 30)
    scene_dur     = total_dur / target_scenes
    print(f"🎬 Scenes: {target_scenes} @ {scene_dur:.1f}s each")

    # Download clips
    raw_clips  = []
    downloaded = []
    for i, vc in enumerate(video_clips[:target_scenes]):
        fname = f"raw_{i}.mp4"
        try:
            print(f"  ⬇️ {i+1}/{min(len(video_clips),target_scenes)} [{vc.get('term','')}]")
            download_video(vc["url"], fname)
            clip = VideoFileClip(fname).resized(VIDEO_SIZE)
            raw_clips.append((clip, fname))
            downloaded.append(fname)
        except Exception as e:
            print(f"  ⚠️ Clip {i}: {e}")

    compiled = []
    if raw_clips:
        for idx in range(target_scenes):
            src, _ = raw_clips[idx % len(raw_clips)]
            try:
                # Cut random section to vary the look
                max_start = max(0, src.duration - scene_dur - 0.5)
                start     = random.uniform(0, max_start) if max_start > 0 else 0

                if src.duration >= scene_dur:
                    c = src.subclipped(start, start + scene_dur)
                else:
                    c = src.with_effects([vfx.Loop(duration=scene_dur)])
                    c = c.subclipped(0, scene_dur)

                # Ken Burns zoom
                zs = random.uniform(1.0, 1.02)
                ze = zs + 0.018
                c  = c.with_effects([
                    vfx.Resize(lambda t, a=zs, b=ze, d=scene_dur: a + (b-a)*(t/d))
                ])

                # Smooth fade between scenes
                if idx > 0:
                    c = c.with_effects([vfx.FadeIn(0.12)])

                compiled.append(c)
            except Exception as e:
                print(f"  ⚠️ Scene {idx}: {e}")
                compiled.append(ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=scene_dur))
    else:
        print("⚠️ No clips downloaded — using solid background")
        compiled = [ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=total_dur)]

    print("🔗 Concatenating scenes...")
    video = concatenate_videoclips(compiled, method="compose")

    if video.duration < total_dur:
        video = video.with_effects([vfx.Loop(duration=total_dur)])
    video = video.subclipped(0, total_dur)
    final = video.with_audio(audio)

    # Subtle watermark
    try:
        wm    = (TextClip(text=CHANNEL_NAME, font_size=20, color="white",
                          font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
                 .with_opacity(0.45)
                 .with_position(("right","bottom"))
                 .with_duration(total_dur))
        final = CompositeVideoClip([final, wm])
    except Exception as e:
        print(f"⚠️ Watermark skip: {e}")

    print("💾 Rendering...")
    final.write_videofile(
        output, fps=VIDEO_FPS, codec="libx264",
        audio_codec="aac", bitrate="3000k", logger=None
    )

    # Cleanup
    for c, _ in raw_clips:
        try: c.close()
        except: pass
    for f in downloaded:
        try: os.remove(f)
        except: pass

    print(f"✅ Video ready: {output}")
    return output

# ═══════════════════════════════════
# METADATA
# ═══════════════════════════════════
def save_metadata(title, meta, topic):
    pkt_time  = "21:30 PKT (Pakistan Time)"
    uk_time   = "17:00-19:00 BST (UK Time)"
    content   = f"""# VIDEO METADATA — {CHANNEL_NAME}
Generated: {time.strftime('%Y-%m-%d %H:%M UTC')}
Target Audience: {TARGET_MARKETS}

{'═'*55}
📌 TOPIC:
{topic}

{'═'*55}
🏆 BEST TITLE — USE THIS:
{meta.get('best_title', title)}

{'═'*55}
📋 ALL TITLE OPTIONS:
{meta.get('all_titles', '')}

{'═'*55}
🏷️ TAGS — COPY ALL 30:
{meta.get('tags', '')}

{'═'*55}
📄 DESCRIPTION — SEO OPTIMISED:
{meta.get('description', '')}

{'═'*55}
🖼️ THUMBNAIL TEXT:
{meta.get('thumbnail', '')}

{'═'*55}
⏰ BEST UPLOAD TIMES:
Pakistan: {pkt_time}
UK: {uk_time}
→ Upload EVERY day at same time for algorithm trust

{'═'*55}
✅ UPLOAD CHECKLIST:
[ ] Upload final_video.mp4
[ ] Paste BEST TITLE exactly
[ ] Copy ALL 30 TAGS
[ ] Copy full DESCRIPTION
[ ] Upload thumbnail.jpg
[ ] Category: Education
[ ] Language: English (United Kingdom)
[ ] Enable auto-subtitles
[ ] Add end screen at final 20 seconds
[ ] Add card at 40% and 70% of video
[ ] Pin a comment immediately after upload
[ ] Reply to every comment in first 2 hours
[ ] Post 30s teaser to Instagram Reels same day

{'═'*55}
💡 GROWTH TIPS:
→ Post daily for minimum 30 days before judging results
→ Reply to comments in the first 2 hours — YouTube rewards this
→ Use the exact BEST TITLE — do not change it
→ Thumbnail + Title = 80% of click through rate
→ First 30 seconds determines if YouTube pushes it
→ Share to UK/Germany finance Facebook groups after upload
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("📄 Metadata saved!")

# ═══════════════════════════════════
# MAIN
# ═══════════════════════════════════
def main():
    print(f"\n🚀 {CHANNEL_NAME} Bot v3 Starting...")
    print(f"🎯 Target: {TARGET_MARKETS}\n")

    # 1. Fresh unique topic
    topic = get_topic()
    print(f"📌 Topic locked: {topic[:100]}...")

    # 2. Hypnotic script
    full_text           = generate_script(topic)
    script, title, meta = parse_script(full_text)

    # 3. UK English audio
    audio_file = generate_audio(script)

    # 4. 40 relevant video scenes
    search_terms = meta.get(
        "search_terms",
        "european bank building,euro cash money,property market chart,real estate germany,london financial district,swiss bank,inflation graph,stock market crash"
    )
    video_clips = get_pexels_videos(search_terms, target_count=40)

    # 5. High-impact thumbnail
    create_thumbnail(meta.get("thumbnail", "THEY LIED TO YOU"), title)

    # 6. Assemble video
    create_video(audio_file, video_clips, title)

    # 7. Save metadata
    save_metadata(title, meta, topic)

    # Cleanup audio
    try: os.remove(audio_file)
    except: pass

    print(f"\n{'═'*50}")
    print(f"🎉 DONE!")
    print(f"📹 Title:     {meta.get('best_title', title)}")
    print(f"🖼️  Thumbnail: {meta.get('thumbnail','')}")
    print(f"⏰ Upload at: 21:30 PKT every day")
    print(f"{'═'*50}\n")

main()
