import os, time, requests, random, re
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from moviepy import *
from pytrends.request import TrendReq

# ═══════════════════════════════════
# CONFIG
# ═══════════════════════════════════
GROQ_API_KEY     = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY   = os.environ["PEXELS_API_KEY"]
NEWS_API_KEY     = os.environ["NEWS_API_KEY"]

CHANNEL_NAME     = "Smart Money Tips"
TARGET_MARKETS   = "UK, Germany, France, Switzerland"
SCENE_DURATION   = 6
VIDEO_FPS        = 24
VIDEO_SIZE       = (1280, 720)
USED_TOPICS_FILE = "used_topics.txt"

# High RPM countries for Google Trends
TREND_COUNTRIES  = {
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "CH": "Switzerland",
}

# Finance seed keywords for trends research
FINANCE_SEEDS = [
    "investment", "savings", "mortgage", "inflation",
    "pension", "property", "housing", "interest rate",
    "cost of living", "retirement", "stock market",
    "real estate", "bank", "financial crisis",
    "wealth", "debt", "economy",
]

# Evergreen niches — fallback
HIGH_RPM_NICHES = [
    "The psychological trap keeping 80 percent of Europeans broke forever",
    "UK property market — what smart money is doing right now 2025",
    "Swiss banking secrets that protect wealth during inflation crisis",
    "German real estate bubble — where to move your money before it bursts",
    "European pension funds quietly going bankrupt — what you must do now",
    "The wealth gap in Germany is wider than the 1920s — proof inside",
    "UK mortgage trap — why millions will lose their homes in 2025",
    "Why saving money in Europe is making you poorer every single year",
    "The financial myth that banks teach Europeans to keep them dependent",
    "How the European Central Bank is silently destroying your savings",
    "Why 73 percent of Europeans retire broke despite working their whole life",
    "The hidden tax destroying middle class wealth across the EU right now",
    "Why renting in Germany beats buying — the truth banks hide from you",
    "The investment strategy Swiss billionaires use that Europeans never hear",
    "How inflation is stealing 40 percent of European savings unnoticed",
    "Why UK housing market faces its worst crash in 40 years",
    "The financial education gap — why European schools teach you to stay poor",
    "How European governments use tax to keep the middle class trapped",
    "Why most European financial advisors are legally allowed to mislead you",
    "The compound interest secret that could make any European financially free",
]

# ═══════════════════════════════════
# DUPLICATE GUARD
# ═══════════════════════════════════
def load_used_topics():
    if not os.path.exists(USED_TOPICS_FILE):
        return []
    with open(USED_TOPICS_FILE, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]

def save_used_topic(topic):
    with open(USED_TOPICS_FILE, "a", encoding="utf-8") as f:
        f.write(topic.strip() + "\n")

def is_duplicate(topic, used_list):
    topic_words = set(topic.lower().split())
    for u in used_list:
        u_words  = set(u.split())
        overlap  = len(topic_words & u_words) / max(len(topic_words), 1)
        if overlap > 0.55:
            return True
    return False

# ═══════════════════════════════════
# GOOGLE TRENDS RESEARCH ENGINE
# ═══════════════════════════════════
def get_trends_for_country(pytrends_obj, country_code, seed_keyword):
    """Get rising queries for a seed keyword in a country."""
    rising_topics = []
    try:
        pytrends_obj.build_payload(
            [seed_keyword],
            timeframe='now 1-d',
            geo=country_code
        )
        related = pytrends_obj.related_queries()
        rising  = related.get(seed_keyword, {}).get('rising')
        if rising is not None and not rising.empty:
            for _, row in rising.head(5).iterrows():
                query = str(row.get('query', '')).strip()
                value = int(row.get('value', 0))
                if query and value > 0:
                    rising_topics.append({
                        'query':   query,
                        'value':   value,
                        'country': country_code,
                        'seed':    seed_keyword,
                    })
    except Exception as e:
        print(f"  ⚠️ Trends [{country_code}][{seed_keyword}]: {e}")
    return rising_topics

def get_trending_searches_country(country_name):
    """Get today's trending searches for a country."""
    try:
        pt      = TrendReq(hl='en-US', tz=0, timeout=(10,25))
        trends  = pt.trending_searches(pn=country_name)
        results = trends[0].tolist()[:20]
        print(f"  📈 Trending [{country_name}]: {results[:5]}")
        return results
    except Exception as e:
        print(f"  ⚠️ Trending searches [{country_name}]: {e}")
        return []

def is_finance_related(query):
    """Check if a query is related to finance niche."""
    finance_words = {
        'money', 'bank', 'invest', 'saving', 'saving', 'mortgage',
        'inflation', 'pension', 'property', 'housing', 'rent',
        'loan', 'debt', 'interest', 'rate', 'economy', 'financial',
        'wealth', 'stock', 'market', 'tax', 'income', 'salary',
        'cost', 'price', 'energy', 'bills', 'insurance', 'fund',
        'crypto', 'euro', 'pound', 'recession', 'budget', 'retire',
        'credit', 'profit', 'loss', 'trade', 'earning', 'wage',
    }
    query_lower = query.lower()
    return any(word in query_lower for word in finance_words)

def research_google_trends():
    """
    Main research engine:
    Step A: Identify top finance queries per Tier-1 country
    Step B: Filter rising only
    Step C: Cross-reference across 3+ countries
    Step D: Select strongest common rising topic
    Returns: (topic_string, research_data)
    """
    print("\n🔍 Google Trends Research Engine starting...")
    print(f"🌍 Scanning: {', '.join(TREND_COUNTRIES.values())}")

    pt = TrendReq(hl='en-US', tz=0, timeout=(10,25), retries=2, backoff_factor=0.5)

    all_rising   = {}   # query -> list of countries where rising
    country_data = {}   # country -> list of rising queries

    # Step A + B: Get rising queries per country per seed
    seeds_to_check = random.sample(FINANCE_SEEDS, min(8, len(FINANCE_SEEDS)))
    print(f"🌱 Seeds: {seeds_to_check}")

    for country_code in TREND_COUNTRIES.keys():
        country_data[country_code] = []
        for seed in seeds_to_check:
            time.sleep(random.uniform(1.5, 3.0))  # respect rate limits
            rising = get_trends_for_country(pt, country_code, seed)
            for item in rising:
                q = item['query']
                country_data[country_code].append(q)
                if q not in all_rising:
                    all_rising[q] = {'countries': [], 'max_value': 0, 'seed': seed}
                if country_code not in all_rising[q]['countries']:
                    all_rising[q]['countries'].append(country_code)
                all_rising[q]['max_value'] = max(all_rising[q]['max_value'], item['value'])

    # Also check trending searches (broader signal)
    country_name_map = {
        "GB": "united_kingdom",
        "DE": "germany",
        "FR": "france",
        "CH": "switzerland",
    }
    trending_raw = {}
    for code, name in country_name_map.items():
        time.sleep(1.5)
        t_results = get_trending_searches_country(name)
        finance_filtered = [q for q in t_results if is_finance_related(q)]
        trending_raw[code] = finance_filtered

    # Add trending to all_rising
    for code, queries in trending_raw.items():
        for q in queries:
            if q not in all_rising:
                all_rising[q] = {'countries': [], 'max_value': 50, 'seed': 'trending'}
            if code not in all_rising[q]['countries']:
                all_rising[q]['countries'].append(code)

    print(f"\n📊 Total rising queries found: {len(all_rising)}")

    # Step C: Cross-reference — find queries common in 3+ countries
    common_topics = {
        q: d for q, d in all_rising.items()
        if len(d['countries']) >= 3 and is_finance_related(q)
    }
    print(f"🌐 Cross-country (3+) topics: {len(common_topics)}")

    # Step D: Selection logic
    best_query    = None
    best_score    = 0
    best_data     = {}

    if common_topics:
        # Score: country_count * 30 + max_value
        for q, d in common_topics.items():
            score = len(d['countries']) * 30 + d['max_value']
            if score > best_score:
                best_score = score
                best_query = q
                best_data  = d
        print(f"✅ Common rising topic: '{best_query}' | countries:{best_data['countries']} | score:{best_score}")
    else:
        # Fallback: strongest single-country rising topic
        for q, d in all_rising.items():
            if not is_finance_related(q):
                continue
            score = len(d['countries']) * 30 + d['max_value']
            if score > best_score:
                best_score = score
                best_query = q
                best_data  = d
        if best_query:
            print(f"✅ Single-country rising: '{best_query}' | score:{best_score}")

    research_summary = {
        'raw_query':    best_query,
        'countries':    best_data.get('countries', []),
        'score':        best_score,
        'seed':         best_data.get('seed', ''),
        'total_found':  len(all_rising),
        'common_found': len(common_topics),
    }

    return best_query, research_summary

def enrich_topic_with_groq(raw_query, research_data, used_list):
    """
    Turn a raw Google Trends query into a full YouTube-optimized topic
    using Groq, ensuring it fits our finance niche and is not duplicate.
    """
    print(f"🤖 Enriching trend: '{raw_query}'")
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    countries_str = ", ".join([TREND_COUNTRIES.get(c, c) for c in research_data.get('countries', [])])
    used_sample   = "; ".join(used_list[-10:]) if used_list else "none"

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"The Google Trend '{raw_query}' is currently rising in: {countries_str}.\n"
            f"Transform this into ONE shocking, curiosity-driven YouTube finance topic "
            f"for high-income audiences in UK, Germany, France, and Switzerland.\n"
            f"Focus on: wealth psychology, property market, financial myths, or savings crisis.\n"
            f"Make it feel urgent and like a revelation — not generic news.\n"
            f"AVOID topics similar to: {used_sample}\n"
            f"Return ONLY the topic — no quotes, no explanation."}],
        "max_tokens": 120,
        "temperature": 0.9
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=data, timeout=30
    )
    return r.json()["choices"][0]["message"]["content"].strip()

def get_topic_from_groq_fallback(used_list):
    """Pure Groq topic when trends fail."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    niche     = random.choice(HIGH_RPM_NICHES)
    used_s    = "; ".join(used_list[-10:]) if used_list else "none"
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"Generate ONE shocking, curiosity-driven YouTube finance topic for UK, Germany, France, Switzerland 2025.\n"
            f"Angle inspiration: {niche}\n"
            f"AVOID: {used_s}\n"
            f"Return ONLY the topic."}],
        "max_tokens": 120,
        "temperature": 0.95
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=data, timeout=30
    )
    return r.json()["choices"][0]["message"]["content"].strip()

# ═══════════════════════════════════
# TOPIC SELECTOR — Google Trends first
# ═══════════════════════════════════
def get_topic():
    used = load_used_topics()

    # Step 1: Google Trends research
    try:
        raw_query, research_data = research_google_trends()
        if raw_query and research_data['score'] > 0:
            for attempt in range(3):
                candidate = enrich_topic_with_groq(raw_query, research_data, used)
                if not is_duplicate(candidate, used):
                    save_used_topic(candidate)
                    print(f"✅ Trend-based topic: {candidate[:90]}")
                    return candidate, research_data
                print(f"⚠️ Duplicate enrichment attempt {attempt+1}")
    except Exception as e:
        print(f"⚠️ Trends research failed: {e}")

    # Step 2: Groq fallback with retry
    print("📌 Falling back to Groq topic generation...")
    for attempt in range(5):
        candidate = get_topic_from_groq_fallback(used)
        if not is_duplicate(candidate, used):
            save_used_topic(candidate)
            print(f"✅ Groq topic: {candidate[:90]}")
            return candidate, {}
        print(f"⚠️ Groq duplicate attempt {attempt+1}")

    # Step 3: Evergreen fallback — date ensures uniqueness
    today    = time.strftime('%B %d %Y')
    fallback = random.choice(HIGH_RPM_NICHES) + f" — {today} update"
    save_used_topic(fallback)
    return fallback, {}

# ═══════════════════════════════════
# SCRIPT — Hypnotic storytelling
# ═══════════════════════════════════
def generate_script(topic, research_data=None):
    print("📝 Writing hypnotic script...")
    trend_context = ""
    if research_data and research_data.get('raw_query'):
        country_names = [TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])]
        trend_context = (
            f"NOTE: This topic is based on the REAL trending search '{research_data['raw_query']}' "
            f"currently rising in {', '.join(country_names)}. "
            f"Reference this real-world momentum naturally in the script."
        )

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type":  "application/json"
    }
    prompt = f"""You are the most viral YouTube scriptwriter for high-income audiences in UK, Germany, France, and Switzerland.

Write a HYPNOTIC financial video script about: "{topic}"
{trend_context}

ABSOLUTE RULES:
1. BANNED: "Welcome to my channel" — never write this
2. BANNED: "Today we will discuss" — never write this
3. BANNED: Robotic filler like "Moving on" or "In conclusion"
4. REQUIRED: First 2 sentences = PATTERN INTERRUPT — one devastating counter-intuitive fact
5. REQUIRED: Every 90-100 words end with ONE sentence curiosity tease forcing the next paragraph
6. REQUIRED: Real European statistics — specific percentages, years, city names
7. REQUIRED: Tone is analytical, slightly conspiratorial, authoritative
8. REQUIRED: 950-1050 words — pure spoken content only, zero stage directions

EXACT STRUCTURE:

[PATTERN INTERRUPT — 40 words]
One devastating ironic fact that STOPS scrolling. Use a specific number and a specific country. Example: "In 2024, the average German household saved 11 percent of its income. Yet 68 percent of those same Germans will retire with less money than they need to survive. The savings did not fail. The system they were saving into did."

[DARK REVELATION — 120 words]
Brutal specificity. Named institutions. Named cities. Real mechanisms. End with curiosity hook sentence.

[FIRST KEY INSIGHT — 150 words]
Deep dive — European case study with real person or real scenario. Specific numbers. End with tease.

[SECOND KEY INSIGHT — 150 words]
The hidden mechanism nobody explains. How the financial system works against ordinary Europeans. End with tease.

[THIRD KEY INSIGHT — 150 words]
The psychological dimension. Why ordinary people choose to stay trapped. End with darkest tease.

[WEALTH PSYCHOLOGY LAYER — 100 words]
The mindset shift — how wealthy Europeans think differently about the exact same situation.

[SOLUTION — 120 words]
Three specific actionable steps. Name exact account types, specific strategies, specific European platforms. Zero generic advice.

[POWER OUTRO — 60 words]
"If you are still here, you already think differently from 95 percent of Europeans. Most people will watch this and do nothing. You are not most people. Press like — it takes one second and it sends this to someone who needs it. Subscribe — because tomorrow I am covering something that will make today look like a warm-up. I will see you there."

---
After the script write EXACTLY on new lines:

BEST_TITLE: [max 58 characters — format: Shocking Number + Specific Claim + 2025. Example: "Why 68% of Germans Will Die Broke — 2025 Reality"]
ALL_TITLES: [5 numbered title options all using numbers]
TAGS: [30 comma-separated YouTube SEO tags — include country-specific tags like "uk finance 2025" "german economy"]
DESCRIPTION: [250 words: hook paragraph, What You Will Learn bullets, European CTA]
THUMBNAIL: [exactly 3-4 ALL CAPS words, zero special characters, creates open-loop curiosity, use a number if possible]
SEARCH_TERMS: [12 specific Pexels terms — european architecture, cash euro, property market, bank building, real estate germany, london city, chart graph, pension retirement, housing crisis, inflation grocery, wealth inequality, financial district]"""

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
        "best_title":   "Why 68% of Europeans Will Die Broke — 2025",
        "all_titles":   "",
        "tags":         "",
        "description":  "",
        "thumbnail":    "68 PERCENT BROKE",
        "search_terms": "european bank building,euro cash money,property market chart,real estate germany,london financial district,swiss bank,inflation graph,stock market crash,housing crisis,pension retirement,wealth gap inequality,financial district city"
    }
    script_lines = []
    in_meta      = False

    for line in lines:
        l = line.strip()
        if   l.startswith("BEST_TITLE:"):   in_meta = True; meta["best_title"]   = l.replace("BEST_TITLE:","").strip().strip('*[]"\'')
        elif l.startswith("ALL_TITLES:"):   meta["all_titles"]   = l.replace("ALL_TITLES:","").strip()
        elif l.startswith("TAGS:"):         meta["tags"]         = l.replace("TAGS:","").strip()
        elif l.startswith("DESCRIPTION:"):  meta["description"]  = l.replace("DESCRIPTION:","").strip()
        elif l.startswith("THUMBNAIL:"):
            raw = l.replace("THUMBNAIL:","").strip()
            meta["thumbnail"] = raw.replace("*","").replace("[","").replace("]","").replace('"',"").strip()
        elif l.startswith("SEARCH_TERMS:"): meta["search_terms"] = l.replace("SEARCH_TERMS:","").strip()
        elif not in_meta and l:
            clean = re.sub(r'\[.*?\]','',l).strip()
            if clean:
                script_lines.append(clean)

    script = " ".join(script_lines)
    print(f"✅ Script: {len(script.split())} words")
    return script, meta["best_title"], meta

# ═══════════════════════════════════
# AUDIO — UK English, sentence-chunked
# ═══════════════════════════════════
def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating UK English voiceover...")
    sentences   = re.split(r'(?<=[.!?])\s+', script)
    chunk_size  = 6
    chunks      = [" ".join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]
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
        gTTS(text=script, lang="en", tld="co.uk", slow=False).save(filename)
        return filename

    if len(audio_parts) == 1:
        os.rename(audio_parts[0], filename)
    else:
        clips    = [AudioFileClip(p) for p in audio_parts]
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
# PEXELS — 40 specific scenes
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
        "housing market decline", "pension retirement elderly",
        "inflation grocery prices rise", "businessman walking city",
        "property investment sign", "financial chart analysis",
        "mortgage documents paper", "wealth gap inequality protest",
        "tax documents", "credit card debt",
        "economy news", "central bank",
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
# THUMBNAIL — Red/Black/Gold + Numbers
# High CTR formula
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
    print("🖼️ Creating high-CTR thumbnail...")
    W, H = 1280, 720
    img  = Image.new("RGB", (W, H), color=(8,6,6))
    draw = ImageDraw.Draw(img)

    # Deep dark-red gradient
    for y in range(H):
        ratio = y / H
        r     = int(22 + ratio * 10)
        g     = int(4  + ratio * 4)
        b     = int(4  + ratio * 8)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Subtle diagonal lines
    for x in range(-200, W+200, 85):
        draw.line([(x,0),(x+200,H)], fill=(100,75,0), width=1)

    # Left red power bar
    for x in range(22):
        intensity = max(0, 235 - x*8)
        draw.rectangle([x,0,x,H], fill=(intensity,0,0))

    # Bottom gold bar
    for y in range(H-78, H):
        ratio = (y-(H-78))/78
        r     = int(155 + ratio*100)
        g     = int(105 + ratio*95)
        b     = 0
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Fonts
    font_xl = load_font(106)
    font_lg = load_font(60)
    font_md = load_font(36)
    font_sm = load_font(26)
    font_xs = load_font(21)

    # Main thumbnail text — 3-4 words max
    clean = thumbnail_text.upper().replace("*","").replace("[","").replace("]","").replace('"',"").strip()
    words = clean.split()[:4]
    lines = []
    if len(words) <= 2:
        lines = [" ".join(words)]
    elif len(words) == 3:
        lines = [words[0], " ".join(words[1:])]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:])]

    # Draw text — multi-layer shadow + glow
    y_pos  = 72
    colors = [(255,215,0), (255,255,255)]
    for i, line in enumerate(lines[:2]):
        color = colors[i] if i < len(colors) else (255,255,255)
        font  = font_xl
        for sx, sy in [(9,9),(7,7),(5,5),(3,3)]:
            draw.text((28+sx, y_pos+sy), line, font=font, fill=(0,0,0))
        if i == 0:
            draw.text((27, y_pos+2), line, font=font, fill=(170,25,0))
        draw.text((26, y_pos), line, font=font, fill=color)
        y_pos += 120

    # Top-right red urgency badge
    badge = "BANKS WON'T TELL YOU"
    bw, bh = 385, 52
    bx, by = W - bw - 18, 20
    draw.rectangle([bx-7,by-7,bx+bw+7,by+bh+7], fill=(90,0,0))
    draw.rectangle([bx,by,bx+bw,by+bh], fill=(205,18,18))
    draw.text((bx+10, by+10), badge, font=font_xs, fill=(255,240,200))

    # Channel name on gold bar
    draw.text((34, H-60), CHANNEL_NAME.upper(), font=font_md, fill=(15,10,5))

    # Year pill
    draw.rectangle([W-130,H-70,W-12,H-12], fill=(185,15,15))
    draw.text((W-118, H-58), "2025", font=font_md, fill=(255,255,255))

    # Vignette
    vignette = Image.new("RGBA", (W,H), (0,0,0,0))
    vd = ImageDraw.Draw(vignette)
    for i in range(160):
        vd.rectangle([i,i,W-i,H-i], outline=(0,0,0,int(i*1.1)))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

    # Contrast + sharpness boost
    img = ImageEnhance.Contrast(img).enhance(1.18)
    img = ImageEnhance.Sharpness(img).enhance(1.25)

    img.save(filename, quality=97)
    print("✅ Thumbnail saved")
    return filename

# ═══════════════════════════════════
# VIDEO — 30-40 scenes @ 6s
# ═══════════════════════════════════
def create_video(audio_file, video_clips, title, output="final_video.mp4"):
    print("🎞️ Assembling hypnotic video...")
    audio     = AudioFileClip(audio_file)
    total_dur = audio.duration
    print(f"⏱️ Duration: {total_dur:.0f}s = {total_dur/60:.1f} min")

    target_scenes = max(int(total_dur / SCENE_DURATION), 30)
    scene_dur     = total_dur / target_scenes
    print(f"🎬 Scenes: {target_scenes} @ {scene_dur:.1f}s each")

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
                max_start = max(0, src.duration - scene_dur - 0.5)
                start     = random.uniform(0, max_start) if max_start > 0 else 0
                if src.duration >= scene_dur:
                    c = src.subclipped(start, start + scene_dur)
                else:
                    c = src.with_effects([vfx.Loop(duration=scene_dur)])
                    c = c.subclipped(0, scene_dur)
                zs = random.uniform(1.0, 1.02)
                ze = zs + 0.018
                c  = c.with_effects([
                    vfx.Resize(lambda t, a=zs, b=ze, d=scene_dur: a + (b-a)*(t/d))
                ])
                if idx > 0:
                    c = c.with_effects([vfx.FadeIn(0.12)])
                compiled.append(c)
            except Exception as e:
                print(f"  ⚠️ Scene {idx}: {e}")
                compiled.append(ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=scene_dur))
    else:
        compiled = [ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=total_dur)]

    print("🔗 Concatenating...")
    video = concatenate_videoclips(compiled, method="compose")
    if video.duration < total_dur:
        video = video.with_effects([vfx.Loop(duration=total_dur)])
    video = video.subclipped(0, total_dur)
    final = video.with_audio(audio)

    try:
        wm    = (TextClip(text=CHANNEL_NAME, font_size=20, color="white",
                          font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
                 .with_opacity(0.45)
                 .with_position(("right","bottom"))
                 .with_duration(total_dur))
        final = CompositeVideoClip([final, wm])
    except Exception as e:
        print(f"⚠️ Watermark: {e}")

    print("💾 Rendering...")
    final.write_videofile(output, fps=VIDEO_FPS, codec="libx264",
                          audio_codec="aac", bitrate="3000k", logger=None)
    for c,_ in raw_clips:
        try: c.close()
        except: pass
    for f in downloaded:
        try: os.remove(f)
        except: pass

    print(f"✅ Video: {output}")
    return output

# ═══════════════════════════════════
# METADATA
# ═══════════════════════════════════
def save_metadata(title, meta, topic, research_data=None):
    trend_info = ""
    if research_data and research_data.get('raw_query'):
        countries = [TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])]
        trend_info = f"""
{'═'*55}
📈 GOOGLE TRENDS DATA:
Raw Trend: {research_data.get('raw_query','')}
Rising In: {', '.join(countries)}
Score: {research_data.get('score',0)}
Total queries found: {research_data.get('total_found',0)}
Cross-country matches: {research_data.get('common_found',0)}"""

    content = f"""# VIDEO METADATA — {CHANNEL_NAME}
Generated: {time.strftime('%Y-%m-%d %H:%M UTC')}
Target: {TARGET_MARKETS}
{trend_info}

{'═'*55}
📌 TOPIC:
{topic}

{'═'*55}
🏆 BEST TITLE — USE EXACTLY AS IS:
{meta.get('best_title', title)}

{'═'*55}
📋 ALL TITLE OPTIONS:
{meta.get('all_titles', '')}

{'═'*55}
🏷️ TAGS — COPY ALL 30:
{meta.get('tags', '')}

{'═'*55}
📄 DESCRIPTION — SEO:
{meta.get('description', '')}

{'═'*55}
🖼️ THUMBNAIL TEXT:
{meta.get('thumbnail', '')}

{'═'*55}
⏰ UPLOAD TIMES:
Pakistan: 21:30 PKT (EVERY DAY — same time)
UK equivalent: 17:00-17:30 BST

{'═'*55}
✅ UPLOAD CHECKLIST:
[ ] Upload final_video.mp4
[ ] Paste BEST TITLE exactly — do not change
[ ] Copy ALL 30 TAGS
[ ] Copy full DESCRIPTION
[ ] Upload thumbnail.jpg
[ ] Category: Education
[ ] Language: English (United Kingdom)
[ ] Enable auto-subtitles
[ ] Add end screen — last 20 seconds
[ ] Add card at 40% and 70%
[ ] Pin a comment immediately after upload
[ ] Reply every comment in first 2 hours
[ ] Share to UK/Germany finance Facebook groups

{'═'*55}
💡 CTR FIX — Why You Had Impressions But No Views:
→ Thumbnail must have a NUMBER (e.g. "68% BROKE")
→ Title must create a knowledge gap — they must click to close it
→ First 30 seconds of video = retention or death
→ Consistency wins — 30 days daily minimum before judging
→ Reply to comments in first 2 hours — YouTube rewards this
→ Upload at 21:30 PKT every single day — same time builds subscribers
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("📄 Metadata saved!")

# ═══════════════════════════════════
# REQUIREMENTS CHECK
# ═══════════════════════════════════
def check_requirements():
    try:
        from pytrends.request import TrendReq
        print("✅ pytrends installed")
    except ImportError:
        print("⚠️ Installing pytrends...")
        os.system("pip install pytrends -q")

# ═══════════════════════════════════
# MAIN
# ═══════════════════════════════════
def main():
    check_requirements()
    print(f"\n🚀 {CHANNEL_NAME} Bot v4 — Google Trends Edition")
    print(f"🎯 Target: {TARGET_MARKETS}\n")

    # 1. Research + Topic
    topic, research_data = get_topic()
    print(f"📌 Topic: {topic[:100]}...")

    # 2. Script
    full_text           = generate_script(topic, research_data)
    script, title, meta = parse_script(full_text)

    # 3. Audio
    audio_file = generate_audio(script)

    # 4. Video clips
    search_terms = meta.get(
        "search_terms",
        "european bank building,euro cash money,property chart,real estate germany,london financial,swiss bank,inflation graph,stock market crash"
    )
    video_clips = get_pexels_videos(search_terms, target_count=40)

    # 5. Thumbnail
    create_thumbnail(meta.get("thumbnail","68 PERCENT BROKE"), title)

    # 6. Video
    create_video(audio_file, video_clips, title)

    # 7. Metadata
    save_metadata(title, meta, topic, research_data)

    try: os.remove(audio_file)
    except: pass

    print(f"\n{'═'*55}")
    print(f"🎉 DONE!")
    print(f"📹 Title:     {meta.get('best_title', title)}")
    print(f"🖼️  Thumbnail: {meta.get('thumbnail','')}")
    print(f"📈 Trend:     {research_data.get('raw_query','Groq generated')}")
    print(f"⏰ Upload:    21:30 PKT every day")
    print(f"{'═'*55}\n")

main()
