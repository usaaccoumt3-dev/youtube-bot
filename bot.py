import os, time, requests, random, re
from gtts import gTTS
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from moviepy import *

# ════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════
GROQ_API_KEY     = os.environ["GROQ_API_KEY"]
PEXELS_API_KEY   = os.environ["PEXELS_API_KEY"]
NEWS_API_KEY     = os.environ["NEWS_API_KEY"]

CHANNEL_NAME     = "Smart Money Tips"
TARGET_MARKETS   = "UK, Germany, France, Switzerland"
SCENE_DURATION   = 6
VIDEO_FPS        = 24
VIDEO_SIZE       = (1280, 720)
USED_TOPICS_FILE = "used_topics.txt"

TREND_COUNTRIES = {
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "CH": "Switzerland",
}

FINANCE_SEEDS = [
    "investment", "savings", "mortgage", "inflation",
    "pension", "property", "housing", "interest rate",
    "cost of living", "retirement", "stock market",
    "real estate", "bank", "financial crisis",
    "wealth", "debt", "economy", "tax",
]

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

SHOCK_TOPIC_TEMPLATES = [
    "I Made £{amount} in {time} Doing This — Here Is Exactly How",
    "How a 24-Year-Old in {city} Retired With £{amount} — No Inheritance",
    "This {country} Bank Trick Grows Your Money {x}x Faster — Nobody Tells You",
    "I Lost £{amount} Investing — Then Made It All Back Using This Strategy",
    "Why {pct}% of {country} Workers Will Never Retire — And How To Beat The System",
    "The {city} Property Strategy That Made £{amount} With Zero Deposit",
    "How I Built a £{amount} Portfolio on a {salary} Salary in {country}",
    "I Interviewed {n} European Millionaires — They All Said The Same {n2} Things",
    "The {pct}-Minute Money Trick That Saves Europeans £{amount} Per Year",
    "This Legal {country} Tax Hack Could Save You £{amount} — Nobody Talks About It",
]

SHOCK_VARS = {
    'amount':  ['50,000','100,000','250,000','1 Million','500,000'],
    'time':    ['6 Months','1 Year','18 Months','2 Years'],
    'city':    ['London','Berlin','Zurich','Munich','Frankfurt'],
    'country': ['UK','German','Swiss','French','European'],
    'x':       ['3','4','5','10'],
    'pct':     ['73','68','81','76','89'],
    'salary':  ['£28,000','€35,000','£32,000','€40,000'],
    'n':       ['50','100','30','75'],
    'n2':      ['3','5','7'],
}

# ════════════════════════════════════════
# DUPLICATE GUARD
# ════════════════════════════════════════
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
        u_words = set(u.split())
        overlap = len(topic_words & u_words) / max(len(topic_words), 1)
        if overlap > 0.55:
            return True
    return False

# ════════════════════════════════════════
# GOOGLE TRENDS RESEARCH
# ════════════════════════════════════════
def install_pytrends():
    try:
        from pytrends.request import TrendReq
        return True
    except ImportError:
        print("📦 Installing pytrends...")
        os.system("pip install pytrends requests-cache -q")
        time.sleep(3)
        try:
            from pytrends.request import TrendReq
            return True
        except Exception:
            return False

def is_finance_related(query):
    finance_words = {
        'money','bank','invest','saving','mortgage','inflation',
        'pension','property','housing','rent','loan','debt',
        'interest','rate','economy','financial','wealth','stock',
        'market','tax','income','salary','cost','price','energy',
        'bills','insurance','fund','crypto','euro','pound',
        'recession','budget','retire','credit','profit','trade',
        'earning','wage','cash','finance','payment','benefit',
    }
    q = query.lower()
    return any(w in q for w in finance_words)

def get_trends_rising(country_code, seed):
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl='en-US', tz=0)
        time.sleep(random.uniform(2.0, 4.0))
        pt.build_payload([seed], timeframe='now 1-d', geo=country_code)
        related = pt.related_queries()
        rising  = related.get(seed, {}).get('rising')
        if rising is not None and not rising.empty:
            results = []
            for _, row in rising.head(8).iterrows():
                q = str(row.get('query', '')).strip()
                v = int(row.get('value', 0))
                if q and v > 0:
                    results.append({'query': q, 'value': v})
            return results
    except Exception as e:
        print(f"  ⚠️ Trends [{country_code}][{seed}]: {e}")
    return []

def research_google_trends():
    print("\n🔍 Google Trends Research Engine...")
    if not install_pytrends():
        print("⚠️ pytrends unavailable — skipping trends")
        return None, {}

    all_rising   = {}
    seeds_sample = random.sample(FINANCE_SEEDS, min(6, len(FINANCE_SEEDS)))
    print(f"🌱 Seeds: {seeds_sample}")
    print(f"🌍 Countries: {list(TREND_COUNTRIES.keys())}")

    for country_code in list(TREND_COUNTRIES.keys()):
        for seed in seeds_sample:
            results = get_trends_rising(country_code, seed)
            for item in results:
                q = item['query']
                if not is_finance_related(q):
                    continue
                if q not in all_rising:
                    all_rising[q] = {'countries': [], 'max_value': 0, 'seed': seed}
                if country_code not in all_rising[q]['countries']:
                    all_rising[q]['countries'].append(country_code)
                all_rising[q]['max_value'] = max(all_rising[q]['max_value'], item['value'])

    print(f"📊 Rising queries found: {len(all_rising)}")

    # Cross-country: 3+ countries = stronger signal
    common = {q: d for q, d in all_rising.items() if len(d['countries']) >= 3}
    print(f"🌐 Cross-country (3+ countries): {len(common)}")

    best_query = None
    best_score = 0
    best_data  = {}

    pool = common if common else all_rising
    for q, d in pool.items():
        score = len(d['countries']) * 30 + d['max_value']
        if score > best_score:
            best_score = score
            best_query = q
            best_data  = d

    if best_query:
        countries_str = [TREND_COUNTRIES.get(c,c) for c in best_data.get('countries',[])]
        print(f"✅ Best trend: '{best_query}' | {countries_str} | score:{best_score}")
    else:
        print("⚠️ No strong trend found — will use fallback")

    return best_query, {
        'raw_query':    best_query,
        'countries':    best_data.get('countries', []),
        'score':        best_score,
        'seed':         best_data.get('seed', ''),
        'total_found':  len(all_rising),
        'common_found': len(common),
    }

# ════════════════════════════════════════
# NEWS
# ════════════════════════════════════════
def get_trending_news():
    print("📰 Fetching business news...")
    try:
        url = (
            f"https://newsapi.org/v2/top-headlines"
            f"?category=business&language=en&pageSize=10"
            f"&apiKey={NEWS_API_KEY}"
        )
        r        = requests.get(url, timeout=15)
        articles = [a for a in r.json().get("articles", []) if a.get("title")]
        if articles:
            headlines = [a["title"] for a in articles[:5]]
            combined  = " | ".join(headlines[:3])
            print(f"✅ News: {combined[:80]}...")
            return combined
    except Exception as e:
        print(f"⚠️ News error: {e}")
    return None

# ════════════════════════════════════════
# GROQ TOPIC ENRICHMENT
# ════════════════════════════════════════
def enrich_with_groq(raw_query, research_data, used_list):
    print(f"🤖 Enriching trend: '{raw_query}'")
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    countries_str = ", ".join([TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])])
    used_sample   = "; ".join(used_list[-10:]) if used_list else "none"
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"The Google Trend '{raw_query}' is rising in: {countries_str}.\n"
            f"Transform this into ONE shocking YouTube finance title for UK, Germany, France, Switzerland audiences.\n"
            f"Use this formula: [Shocking Number or Result] + [Specific Claim] + [Year 2025]\n"
            f"Example: 'Why 73% of UK Workers Will Die Broke in 2025 — The Hidden Truth'\n"
            f"AVOID: {used_sample}\n"
            f"Return ONLY the title — no quotes, no explanation."}],
        "max_tokens": 120,
        "temperature": 0.9
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=30)
    return r.json()["choices"][0]["message"]["content"].strip()

def get_topic_groq_fallback(used_list):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    niche   = random.choice(HIGH_RPM_NICHES)
    used_s  = "; ".join(used_list[-10:]) if used_list else "none"
    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content":
            f"Generate ONE shocking YouTube finance topic for UK, Germany, France, Switzerland 2025.\n"
            f"Formula: [Number]% of [Country] People [Shocking Fact] — [Curiosity Hook]\n"
            f"Angle: {niche}\n"
            f"AVOID: {used_s}\n"
            f"Return ONLY the topic."}],
        "max_tokens": 120,
        "temperature": 0.95
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=30)
    return r.json()["choices"][0]["message"]["content"].strip()

def generate_shock_topic(used_list):
    template = random.choice(SHOCK_TOPIC_TEMPLATES)
    for key, values in SHOCK_VARS.items():
        if f"{{{key}}}" in template:
            template = template.replace(f"{{{key}}}", random.choice(values))
    if not is_duplicate(template, used_list):
        return template
    for _ in range(8):
        t2 = random.choice(SHOCK_TOPIC_TEMPLATES)
        for key, values in SHOCK_VARS.items():
            if f"{{{key}}}" in t2:
                t2 = t2.replace(f"{{{key}}}", random.choice(values))
        if not is_duplicate(t2, used_list):
            return t2
    return template

# ════════════════════════════════════════
# TOPIC SELECTOR
# Priority: Trends > News > Groq > Shock Template
# ════════════════════════════════════════
def get_topic():
    used = load_used_topics()
    research_data = {}

    # 1. Google Trends
    try:
        raw_query, research_data = research_google_trends()
        if raw_query:
            for attempt in range(3):
                candidate = enrich_with_groq(raw_query, research_data, used)
                if not is_duplicate(candidate, used):
                    save_used_topic(candidate)
                    print(f"✅ Trend topic: {candidate[:90]}")
                    return candidate, research_data
                print(f"⚠️ Duplicate enrichment {attempt+1}")
    except Exception as e:
        print(f"⚠️ Trends failed: {e}")

    # 2. News-based
    try:
        news = get_trending_news()
        if news:
            candidate = f"Breaking: {news[:80]} — What This Means For European Money 2025"
            if not is_duplicate(candidate, used):
                save_used_topic(candidate)
                print(f"✅ News topic: {candidate[:90]}")
                return candidate, research_data
    except Exception as e:
        print(f"⚠️ News failed: {e}")

    # 3. Groq generation
    for attempt in range(4):
        try:
            candidate = get_topic_groq_fallback(used)
            if not is_duplicate(candidate, used):
                save_used_topic(candidate)
                print(f"✅ Groq topic: {candidate[:90]}")
                return candidate, research_data
            print(f"⚠️ Groq duplicate {attempt+1}")
        except Exception as e:
            print(f"⚠️ Groq error: {e}")

    # 4. Shock template
    candidate = generate_shock_topic(used)
    save_used_topic(candidate)
    print(f"✅ Shock template: {candidate[:90]}")
    return candidate, research_data

# ════════════════════════════════════════
# SCRIPT GENERATION
# ════════════════════════════════════════
def generate_script(topic, research_data=None):
    print("📝 Writing hypnotic script...")
    trend_context = ""
    if research_data and research_data.get('raw_query'):
        c_names = [TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])]
        trend_context = (
            f"\nNOTE: This topic is based on REAL trending search '{research_data['raw_query']}' "
            f"rising in {', '.join(c_names)}. Reference this naturally."
        )

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt  = f"""You are the most viral YouTube scriptwriter for high-income audiences in UK, Germany, France, Switzerland.

Write a HYPNOTIC financial video script about: "{topic}"{trend_context}

ABSOLUTE RULES:
1. NEVER write "Welcome to my channel" — banned
2. NEVER write "Today we will discuss" — banned
3. NEVER write robotic filler phrases — banned
4. First 2 sentences MUST be a PATTERN INTERRUPT — devastating counter-intuitive fact with a specific number
5. Every 90-100 words end the paragraph with ONE curiosity tease sentence
6. Use REAL European statistics — specific percentages, years, country names, cities
7. Tone: analytical, authoritative, slightly conspiratorial — like revealing secrets
8. Total: 950-1050 words of pure spoken content — ZERO stage directions, ZERO brackets

STRUCTURE:

[PATTERN INTERRUPT]
One devastating ironic fact. Specific number. Specific country. Stops scrolling instantly.
Example: "In 2024, the average German household saved 11 percent of its income. Yet 68 percent of those same Germans will retire with less money than they need to survive. The savings did not fail. The system they were saving into did."

[DARK REVELATION — 120 words]
Brutal specificity. Named institutions. Named cities. Real mechanisms. End with one curiosity hook sentence.

[FIRST KEY INSIGHT — 150 words]
Deep dive with European case study. Specific numbers. Real scenario. End with tease.

[SECOND KEY INSIGHT — 150 words]
Hidden mechanism nobody explains. How the system works against Europeans. End with tease.

[THIRD KEY INSIGHT — 150 words]
Psychological dimension. Why people stay trapped. End with darkest tease.

[WEALTH PSYCHOLOGY — 100 words]
How wealthy Europeans think differently about the exact same situation.

[SOLUTION — 120 words]
Three specific actionable steps. Name exact account types, strategies, platforms. Zero generic advice.

[POWER OUTRO — 60 words]
"If you are still watching, you already think differently from 95 percent of Europeans. Most people will watch this and do nothing. You are not most people. Press like — it takes one second and helps more Europeans find this truth. Subscribe — because tomorrow I am covering something that will make today look like a warm-up. I will see you there."

---
After the script write EXACTLY on new lines:

BEST_TITLE: [max 58 chars — Shocking Number + Specific Claim + 2025]
ALL_TITLES: [5 numbered options all using numbers]
TAGS: [30 comma-separated YouTube SEO tags including country-specific ones]
DESCRIPTION: [250 words: hook paragraph, What You Will Learn bullets, European CTA]
THUMBNAIL: [3-4 ALL CAPS words, zero special characters, must include a number if possible]
SEARCH_TERMS: [12 specific Pexels terms: european architecture, financial chart, cash euro, bank building, real estate, city skyline, pension elderly, housing market, inflation grocery, wealth inequality, stock market screen, mortgage document]"""

    data = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 4500,
        "temperature": 0.88
    }
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers=headers, json=data, timeout=90)
    return r.json()["choices"][0]["message"]["content"]

# ════════════════════════════════════════
# PARSE SCRIPT
# ════════════════════════════════════════
def parse_script(full_text):
    lines = full_text.strip().split("\n")
    meta  = {
        "best_title":   "Why 73% of Europeans Will Die Broke in 2025",
        "all_titles":   "",
        "tags":         "",
        "description":  "",
        "thumbnail":    "73 PERCENT BROKE",
        "search_terms": "european bank building,euro cash money,property market chart,real estate germany,london financial district,swiss bank,inflation graph,stock market screen,housing crisis,pension elderly,wealth gap,financial district city"
    }
    script_lines = []
    in_meta      = False

    for line in lines:
        l = line.strip()
        if   l.startswith("BEST_TITLE:"):   in_meta = True;  meta["best_title"]   = l.replace("BEST_TITLE:","").strip().strip('*[]"\'')
        elif l.startswith("ALL_TITLES:"):   meta["all_titles"]   = l.replace("ALL_TITLES:","").strip()
        elif l.startswith("TAGS:"):         meta["tags"]         = l.replace("TAGS:","").strip()
        elif l.startswith("DESCRIPTION:"):  meta["description"]  = l.replace("DESCRIPTION:","").strip()
        elif l.startswith("THUMBNAIL:"):
            meta["thumbnail"] = l.replace("THUMBNAIL:","").strip().replace("*","").replace("[","").replace("]","").replace('"',"").strip()
        elif l.startswith("SEARCH_TERMS:"): meta["search_terms"] = l.replace("SEARCH_TERMS:","").strip()
        elif not in_meta and l:
            clean = re.sub(r'\[.*?\]', '', l).strip()
            if clean:
                script_lines.append(clean)

    script = " ".join(script_lines)
    print(f"✅ Script: {len(script.split())} words")
    return script, meta["best_title"], meta

# ════════════════════════════════════════
# AUDIO — pydub seamless merge, zero gaps
# News anchor style (slower, clear, warm)
# ════════════════════════════════════════
def install_pydub():
    try:
        from pydub import AudioSegment
        return True
    except ImportError:
        print("📦 Installing pydub...")
        os.system("pip install pydub -q")
        time.sleep(2)
        try:
            from pydub import AudioSegment
            return True
        except Exception:
            return False

def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating news anchor voiceover (zero gaps)...")

    has_pydub = install_pydub()

    # Clean script — remove any bracket markers
    clean = re.sub(r'\[.*?\]', '', script).strip()

    # Split into sentences for natural pacing
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    sentences = [s.strip() for s in sentences if s.strip()]
    print(f"  📝 {len(sentences)} sentences")

    # Group into chunks of 6 sentences
    chunk_size = 6
    chunks     = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i:i+chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    print(f"  🔊 {len(chunks)} chunks to process")

    temp_files = []

    if has_pydub:
        from pydub import AudioSegment
        from pydub.effects import normalize

        segments = []
        for idx, chunk in enumerate(chunks):
            temp = f"chunk_{idx}.mp3"
            try:
                tts = gTTS(text=chunk, lang="en", tld="co.uk", slow=False)
                tts.save(temp)
                seg = AudioSegment.from_mp3(temp)

                # Normalize volume
                seg = normalize(seg)

                # Slow down 7% for news anchor pace
                new_rate = int(seg.frame_rate * 0.93)
                seg      = seg._spawn(seg.raw_data, overrides={"frame_rate": new_rate})
                seg      = seg.set_frame_rate(44100)

                # Warm low-pass filter
                seg = seg.low_pass_filter(8000)

                # 100ms natural breath pause after each chunk
                pause = AudioSegment.silent(duration=100)
                seg   = seg + pause

                segments.append(seg)
                temp_files.append(temp)
                print(f"  ✅ Chunk {idx+1}/{len(chunks)}")

            except Exception as e:
                print(f"  ⚠️ Chunk {idx}: {e}")

        if segments:
            print("  🔗 Merging with crossfade (zero gaps)...")
            final = segments[0]
            for seg in segments[1:]:
                final = final.append(seg, crossfade=25)

            final = normalize(final)
            final.export(filename, format="mp3", bitrate="192k", parameters=["-q:a", "0"])

            for f in temp_files:
                try: os.remove(f)
                except: pass

            duration = len(final) / 1000
            print(f"✅ Audio: {duration:.0f}s = {duration/60:.1f} min (ZERO GAPS)")
            return filename

    # Fallback — single gTTS call if pydub failed
    print("  ⚠️ pydub unavailable — single gTTS fallback")
    tts = gTTS(text=clean, lang="en", tld="co.uk", slow=False)
    tts.save(filename)
    print("✅ Audio ready (fallback)")
    return filename

# ════════════════════════════════════════
# PEXELS VIDEO FETCH
# ════════════════════════════════════════
def get_pexels_videos(search_terms_str, target_count=40):
    print(f"🎬 Fetching {target_count} footage clips...")
    videos   = []
    terms    = [t.strip() for t in search_terms_str.split(",") if t.strip()]
    fallback = [
        "european city architecture","euro banknotes cash",
        "stock market trading screen","real estate luxury house",
        "bank building facade","london skyline financial",
        "frankfurt skyscraper","swiss city street",
        "housing market decline","pension retirement elderly",
        "inflation grocery prices","businessman walking city",
        "property investment","financial chart analysis",
        "mortgage documents","wealth gap inequality",
        "tax documents","credit card debt",
        "economic news","central bank building",
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
            print(f"  ⚠️ Pexels [{term}]: {e}")

    random.shuffle(videos)
    print(f"✅ {len(videos)} clips found")
    return videos[:target_count]

def download_video(url, filename):
    r = requests.get(url, timeout=90, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

# ════════════════════════════════════════
# THUMBNAIL — Professional 10-layer system
# Black/Gold/Red — MrBeast finance style
# ════════════════════════════════════════
def load_font(size):
    for path in [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf",
        "/usr/share/fonts/truetype/ubuntu/Ubuntu-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()

def draw_text_shadow(draw, pos, text, font, color, shadow=(0,0,0), offset=7):
    x, y = pos
    for o in [offset, offset-2, offset-4]:
        if o > 0:
            draw.text((x+o, y+o), text, font=font, fill=shadow)
    r,g,b  = color
    glow   = (max(0,r-90), max(0,g-90), max(0,b-90))
    draw.text((x+1, y+2), text, font=font, fill=glow)
    draw.text((x, y),     text, font=font, fill=color)

def create_thumbnail(thumbnail_text, title, filename="thumbnail.jpg"):
    print("🖼️ Creating professional thumbnail...")
    W, H = 1280, 720
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    # Layer 1: Dark gradient background (black to very dark warm)
    for y in range(H):
        ratio = y / H
        r = int(10 + ratio * 20)
        g = int(8  + ratio * 12)
        b = int(8  + ratio * 15)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    # Layer 2: Radial spotlight — center-left warmth
    cx, cy = int(W*0.40), int(H*0.40)
    for radius in range(300, 0, -5):
        alpha = int(20 * (1 - radius/300))
        rv = min(255, 38+alpha*2)
        gv = min(255, 22+alpha)
        bv = min(255, 8+alpha)
        draw.ellipse([cx-radius,cy-radius,cx+radius,cy+radius], fill=(rv,gv,bv))

    # Layer 3: Subtle diagonal texture lines
    for x in range(-200, W+200, 80):
        draw.line([(x,0),(x+180,H)], fill=(25,18,0), width=1)

    # Layer 4: LEFT GOLD BAR — thick, gradient
    for x in range(18):
        gval = max(0, int(220 - x*7))
        rval = min(255, gval+35)
        draw.rectangle([x,0,x,H], fill=(rval, gval, 0))

    # Layer 5: TOP RED STRIP (urgency bar)
    for y in range(6):
        intensity = int(220 - y*15)
        draw.line([(18,y),(W,y)], fill=(intensity, 8, 8))

    # Layer 6: Parse and render main text
    clean = thumbnail_text.upper().replace("*","").replace("[","").replace("]","").replace('"',"").strip()
    words = clean.split()[:5]

    # Smart layout — max 3 lines
    if len(words) == 1:
        lines = [words[0], "", ""]
    elif len(words) == 2:
        lines = [words[0], words[1], ""]
    elif len(words) == 3:
        lines = [words[0], words[1], words[2]]
    elif len(words) == 4:
        lines = [" ".join(words[:2]), " ".join(words[2:4]), ""]
    else:
        lines = [" ".join(words[:2]), " ".join(words[2:4]), words[4]]

    font_mega = load_font(118)   # Line 1 — GOLD
    font_xl   = load_font(90)    # Line 2 — WHITE
    font_lg   = load_font(62)    # Line 3 — RED
    font_md   = load_font(38)
    font_sm   = load_font(28)
    font_xs   = load_font(22)

    LEFT = 30
    y_pos = 55

    # Line 1 — GOLD (number or shock word)
    if lines[0]:
        draw_text_shadow(draw, (LEFT, y_pos), lines[0], font_mega,
                         color=(255,215,0), shadow=(0,0,0), offset=9)
        y_pos += 128

    # Line 2 — WHITE (context)
    if lines[1]:
        draw_text_shadow(draw, (LEFT, y_pos), lines[1], font_xl,
                         color=(255,255,255), shadow=(0,0,0), offset=7)
        y_pos += 98

    # Line 3 — BRIGHT RED (CTA or reveal)
    if lines[2]:
        draw_text_shadow(draw, (LEFT, y_pos), lines[2], font_lg,
                         color=(255,55,55), shadow=(0,0,0), offset=5)

    # Layer 7: Top-right shock badge
    badge_text = "SHOCKING"
    bw, bh     = 225, 52
    bx, by     = W - bw - 18, 18
    draw.rectangle([bx+4,by+4,bx+bw+4,by+bh+4], fill=(0,0,0))
    draw.rectangle([bx,by,bx+bw,by+bh], fill=(205,15,15))
    draw.rectangle([bx,by,bx+bw,by+5], fill=(235,40,40))
    draw.text((bx+12, by+10), badge_text, font=font_sm, fill=(255,255,255))

    # Layer 8: BOTTOM CHANNEL STRIP
    sy = H - 75
    for y in range(sy, H):
        ratio = (y-sy)/(H-sy)
        rv    = int(115 + ratio*90)
        gv    = int(8   + ratio*5)
        bv    = int(8   + ratio*5)
        draw.line([(0,y),(W,y)], fill=(rv,gv,bv))

    draw.text((LEFT+6, sy+16), CHANNEL_NAME.upper(), font=font_md, fill=(255,235,200))

    # Year pill
    draw.rectangle([W-128,sy+8,W-12,H-10], fill=(0,0,0))
    draw.text((W-116, sy+14), "2025", font=font_md, fill=(255,215,0))

    # Layer 9: Vignette (darkens edges for depth)
    vignette = Image.new("RGBA", (W,H), (0,0,0,0))
    vd = ImageDraw.Draw(vignette)
    for i in range(170):
        vd.rectangle([i,i,W-i,H-i], outline=(0,0,0,int((i/170)**1.4 * 190)))
    img = Image.alpha_composite(img.convert("RGBA"), vignette).convert("RGB")

    # Layer 10: Final polish
    img = ImageEnhance.Contrast(img).enhance(1.20)
    img = ImageEnhance.Sharpness(img).enhance(1.30)
    img = ImageEnhance.Color(img).enhance(1.15)

    img.save(filename, quality=97)
    print(f"✅ Thumbnail: {filename}")
    return filename

# ════════════════════════════════════════
# VIDEO ASSEMBLY — 30-40 scenes @ 6s
# ════════════════════════════════════════
def create_video(audio_file, video_clips, title, output="final_video.mp4"):
    print("🎞️ Assembling video...")
    audio     = AudioFileClip(audio_file)
    total_dur = audio.duration
    print(f"⏱️ {total_dur:.0f}s = {total_dur/60:.1f} min")

    target_scenes = max(int(total_dur / SCENE_DURATION), 30)
    scene_dur     = total_dur / target_scenes
    print(f"🎬 {target_scenes} scenes @ {scene_dur:.1f}s each")

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
                    vfx.Resize(lambda t, a=zs, b=ze, d=scene_dur: a+(b-a)*(t/d))
                ])
                if idx > 0:
                    c = c.with_effects([vfx.FadeIn(0.12)])
                compiled.append(c)
            except Exception as e:
                print(f"  ⚠️ Scene {idx}: {e}")
                compiled.append(ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=scene_dur))
    else:
        compiled = [ColorClip(size=VIDEO_SIZE, color=[10,6,6], duration=total_dur)]

    print("🔗 Concatenating scenes...")
    video = concatenate_videoclips(compiled, method="compose")
    if video.duration < total_dur:
        video = video.with_effects([vfx.Loop(duration=total_dur)])
    video = video.subclipped(0, total_dur)
    final = video.with_audio(audio)

    try:
        wm = (TextClip(text=CHANNEL_NAME, font_size=20, color="white",
                       font="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
              .with_opacity(0.45)
              .with_position(("right","bottom"))
              .with_duration(total_dur))
        final = CompositeVideoClip([final, wm])
    except Exception as e:
        print(f"⚠️ Watermark skip: {e}")

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

# ════════════════════════════════════════
# METADATA
# ════════════════════════════════════════
def save_metadata(title, meta, topic, research_data=None):
    trend_info = ""
    if research_data and research_data.get('raw_query'):
        c_names = [TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])]
        trend_info = f"""
{'═'*55}
📈 GOOGLE TRENDS DATA:
Raw Trend Query : {research_data.get('raw_query','')}
Rising In       : {', '.join(c_names)}
Trend Score     : {research_data.get('score',0)}
Total Queries   : {research_data.get('total_found',0)}
Cross-Country   : {research_data.get('common_found',0)}"""

    content = f"""# VIDEO METADATA — {CHANNEL_NAME}
Generated : {time.strftime('%Y-%m-%d %H:%M UTC')}
Target    : {TARGET_MARKETS}
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
📄 DESCRIPTION:
{meta.get('description', '')}

{'═'*55}
🖼️ THUMBNAIL TEXT USED:
{meta.get('thumbnail', '')}

{'═'*55}
⏰ UPLOAD TIME:
Pakistan : 21:30 PKT (every day — same time)
UK       : 17:00-17:30 BST

{'═'*55}
✅ UPLOAD CHECKLIST:
[ ] Upload final_video.mp4
[ ] Paste BEST TITLE exactly — do not change a word
[ ] Copy ALL 30 TAGS
[ ] Copy full DESCRIPTION
[ ] Upload thumbnail.jpg
[ ] Category: Education
[ ] Language: English (United Kingdom)
[ ] Enable auto-subtitles
[ ] Add end screen — last 20 seconds
[ ] Add card at 40% and 70%
[ ] Pin a comment immediately after upload
[ ] Reply to EVERY comment in first 2 hours
[ ] Share to UK/Germany finance Facebook groups same day

{'═'*55}
💡 CTR FORMULA — Why Numbers Work:
→ "73% BROKE" beats "MONEY TRUTH" — always
→ Numbers create a knowledge gap — brain must click to close it
→ First 30 seconds = retention or death — hook immediately
→ Same upload time daily = algorithm trust
→ Minimum 30 days consistent before judging results
"""
    with open("metadata.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("📄 Metadata saved")

# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════
def main():
    print(f"\n🚀 {CHANNEL_NAME} Bot v4 — Complete Edition")
    print(f"🎯 Target: {TARGET_MARKETS}\n")

    # 1. Topic research
    topic, research_data = get_topic()
    print(f"📌 Topic: {topic[:100]}...")

    # 2. Script
    full_text           = generate_script(topic, research_data)
    script, title, meta = parse_script(full_text)

    # 3. Audio — zero gaps, news anchor
    audio_file = generate_audio(script)

    # 4. Video clips
    search_terms = meta.get(
        "search_terms",
        "european bank building,euro cash money,property market chart,real estate germany,london financial district,swiss bank,inflation graph,stock market screen"
    )
    video_clips = get_pexels_videos(search_terms, target_count=40)

    # 5. Thumbnail
    create_thumbnail(meta.get("thumbnail","73 PERCENT BROKE"), title)

    # 6. Assemble video
    create_video(audio_file, video_clips, title)

    # 7. Metadata
    save_metadata(title, meta, topic, research_data)

    # Cleanup
    try: os.remove(audio_file)
    except: pass

    print(f"\n{'═'*55}")
    print(f"🎉 DONE!")
    print(f"📹 Title     : {meta.get('best_title', title)}")
    print(f"🖼️  Thumbnail : {meta.get('thumbnail','')}")
    print(f"📈 Trend     : {research_data.get('raw_query','Groq generated') if research_data else 'Groq generated'}")
    print(f"⏰ Upload    : 21:30 PKT every day")
    print(f"{'═'*55}\n")

main()
       
