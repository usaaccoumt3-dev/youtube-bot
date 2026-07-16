import os, time, requests, random, re
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
Image.ANTIALIAS = Image.LANCZOS
from moviepy.editor import *
from moviepy.video.fx import all as vfx
from pydub import AudioSegment
from pydub.effects import normalize
from gtts import gTTS

# ════════════════════════════════════════
# CONFIG
# ════════════════════════════════════════
GROQ_API_KEY     = os.environ.get("GROQ_API_KEY", "")
PEXELS_API_KEY   = os.environ.get("PEXELS_API_KEY", "")
NEWS_API_KEY     = os.environ.get("NEWS_API_KEY", "")

CHANNEL_NAME     = "Smart Money Tips"
TARGET_MARKETS   = "UK, Germany, France, Switzerland, Canada"
SCENE_DURATION   = 6
VIDEO_FPS        = 24
VIDEO_SIZE_LONG  = (1280, 720)
VIDEO_SIZE_SHORT = (1080, 1920) # Vertical for Shorts
USED_TOPICS_FILE = "used_topics.txt"

TREND_COUNTRIES = {
    "GB": "United Kingdom",
    "DE": "Germany",
    "FR": "France",
    "CH": "Switzerland",
    "CA": "Canada",
}

# Curiosity-driven seeds targeting viral/shocking finance news
FINANCE_SEEDS = [
    "financial scam", "bank fraud", "young millionaire", "company collapse",
    "investment disaster", "crypto crash", "stock market manipulation",
    "debt crisis europe", "economic shock", "wealth secrets",
    "tax evasion", "financial loophole", "retirement crisis",
    "real estate bubble", "cost of living crisis", "inflation impact",
    "interest rate hike", "pension fund failure", "currency devaluation",
    "financial freedom", "passive income europe", "budgeting mistakes",
    "savings account trick", "mortgage trap", "credit card debt escape",
    "financial independence retire early", "european financial news",
    "unexpected wealth", "hidden fees bank", "investment scam stories"
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
    "This 19-year-old made $1 million in one day: The untold story",
    "This bank scammed millions of people: How they got away with it",
    "A 20-year-old lost $50 million: The shocking truth behind his downfall",
    "Real stories of financial disasters: Lessons from Europe's biggest crashes",
    "Bank frauds exposed: The schemes that cost Europeans billions",
    "Young millionaires of Europe: Their secrets to early wealth",
    "Company crashes: The warning signs you missed in European markets",
    "The hidden truth about European debt: What your government isn't telling you",
    "Why your European pension is at risk: A looming crisis explained",
    "The secret investments of European elites: What they don't want you to know"
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
    "A 19-year-old made £{amount} in one day: The untold story",
    "This {country} bank scammed millions of people: How they got away with it",
    "A 20-year-old lost £{amount}: The shocking truth behind his downfall",
    "The {country} financial disaster that wiped out £{amount} in savings",
    "How {city} became the capital of bank fraud: A true story",
    "The young {country} millionaire who lost it all: A cautionary tale",
    "{company_name} collapse: The £{amount} scandal that shook {country}"
]

SHOCK_VARS = {
    'amount':  ['50,000','100,000','250,000','1 Million','500,000','5 Million','10 Million','50 Million'],
    'time':    ['6 Months','1 Year','18 Months','2 Years','3 Days','One Day','One Week'],
    'city':    ['London','Berlin','Zurich','Munich','Frankfurt','Paris','Amsterdam','Dublin','Geneva','Toronto','Vancouver'],
    'country': ['UK','German','Swiss','French','European','Canadian','Dutch','Irish'],
    'x':       ['3','4','5','10','20','50'],
    'pct':     ['73','68','81','76','89','92','65','70'],
    'salary':  ['£28,000','€35,000','£32,000','€40,000','£25,000','€30,000'],
    'n':       ['50','100','30','75','20','40'],
    'n2':      ['3','5','7','2','4'],
    'company_name': ['Wirecard','Credit Suisse','Lehman Brothers','Enron','Parmalat','Volkswagen']
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
        'scam','fraud','millionaire','collapse','disaster','crisis',
        'loophole','elite','secret','hidden','uncover','expose'
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
    seeds_sample = random.sample(FINANCE_SEEDS, min(10, len(FINANCE_SEEDS)))
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
            f"Transform this into ONE short, curiosity-driven YouTube finance title for UK, Germany, France, Switzerland, Canada audiences.\n"
            f"Focus on creating a curiosity gap, avoiding overly dramatic clickbait. Max 58 characters.\n"
            f"Example: '19-Year-Old Made $1M in a Day: How?'\n"
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
            f"Generate ONE short, curiosity-driven YouTube finance topic for UK, Germany, France, Switzerland, Canada 2025.\n"
            f"Focus on creating a curiosity gap, avoiding overly dramatic clickbait. Max 58 characters.\n"
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
    if not is_duplicate(candidate, used):
        save_used_topic(candidate)
        print(f"✅ Shock topic: {candidate[:90]}")
        return candidate, research_data

    print("❌ Failed to find a unique topic.")
    return "The European Financial Crisis Nobody Saw Coming", {}

# ════════════════════════════════════════
# SCRIPT GENERATION
# ════════════════════════════════════════
def generate_script_groq(topic, research_data=None):
    print(f"✍️ Generating script for: '{topic}'")
    trend_context = ""
    if research_data and research_data.get('raw_query'):
        c_names = [TREND_COUNTRIES.get(c,c) for c in research_data.get('countries',[])]
        trend_context = (
            f"\nNOTE: This topic is based on REAL trending search '{research_data['raw_query']}' "
            f"rising in {', '.join(c_names)}. Reference this naturally."
        )

    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    prompt  = f"""You are the most viral YouTube scriptwriter for high-income audiences in UK, Germany, France, Switzerland, Canada.

Write a HYPNOTIC financial video script about: "{topic}"{trend_context}

ABSOLUTE RULES:
1. NEVER write "Welcome to my channel" — banned
2. NEVER write "Today we will discuss" — banned
3. NEVER write robotic filler phrases — banned
4. First 5-10 seconds (first 2-3 sentences) MUST be a STRONG HOOK: a shocking statement or question that makes them stay till the end. Use a PATTERN INTERRUPT — devastating counter-intuitive fact with a specific number.
5. Every 90-100 words end the paragraph with ONE curiosity tease sentence
6. Use REAL European/Canadian statistics — specific percentages, years, country names, cities
7. Tone: analytical, authoritative, slightly conspiratorial — like revealing secrets
8. Total: 950-1050 words of pure spoken content — ZERO stage directions, ZERO brackets

STRUCTURE:

[STRONG HOOK / PATTERN INTERRUPT]
One devastating ironic fact. Specific number. Specific country. Stops scrolling instantly.

[DARK REVELATION — 120 words]
Brutal specificity. Named institutions. Named cities. Real mechanisms. End with one curiosity hook sentence.

[FIRST KEY INSIGHT — 150 words]
Deep dive with European/Canadian case study. Specific numbers. Real scenario. End with tease.

[SECOND KEY INSIGHT — 150 words]
Hidden mechanism nobody explains. How the system works against Europeans/Canadians. End with tease.

[THIRD KEY INSIGHT — 150 words]
Psychological dimension. Why people stay trapped. End with darkest tease.

[WEALTH PSYCHOLOGY — 100 words]
How wealthy people think differently about the exact same situation.

[SOLUTION — 120 words]
Three specific actionable steps. Name exact account types, strategies, platforms. Zero generic advice.

[POWER OUTRO — 60 words]
"If you are still watching, you already think differently from 95 percent of people. Most people will watch this and do nothing. You are not most people. Press like — it takes one second and helps more people find this truth. Subscribe — because tomorrow I am covering something that will make today look like a warm-up. I will see you there."

---
After the script write EXACTLY on new lines:

BEST_TITLE: [max 58 chars — Short, curiosity-driven, e.g., '19-Year-Old Made $1M in a Day: How?']
ALL_TITLES: [5 numbered options all using numbers, short, curiosity-driven]
TAGS: [30 comma-separated YouTube SEO tags including country-specific ones]
DESCRIPTION: [250 words: hook paragraph, What You Will Learn bullets, European/Canadian CTA]
THUMBNAIL: [2-3 ALL CAPS bold words, one clear focal point, high contrast, clean design, no special characters, must include a number if possible, e.g., '1M IN A DAY']
SEARCH_TERMS: [12 specific Pexels terms: european financial scam, bank fraud investigation, young entrepreneur success, company bankruptcy, investment failure, crypto market crash, stock market manipulation, debt crisis europe, economic shockwave, wealth management secrets, tax evasion europe, financial loophole explained]"""

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
def generate_audio(script, filename="audio.mp3"):
    print("🎙️ Generating news anchor voiceover (zero gaps)...")
    clean = re.sub(r'\[.*?\]', '', script).strip()
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    sentences = [s.strip() for s in sentences if s.strip()]
    print(f"  📝 {len(sentences)} sentences")

    chunk_size = 6
    chunks     = []
    for i in range(0, len(sentences), chunk_size):
        chunk = " ".join(sentences[i:i+chunk_size]).strip()
        if chunk:
            chunks.append(chunk)
    print(f"  🔊 {len(chunks)} chunks to process")

    temp_files = []
    segments = []
    for idx, chunk in enumerate(chunks):
        temp = f"chunk_{idx}.mp3"
        try:
            tts = gTTS(text=chunk, lang="en", tld="co.uk", slow=False)
            tts.save(temp)
            seg = AudioSegment.from_mp3(temp)
            seg = normalize(seg)
            new_rate = int(seg.frame_rate * 0.93)
            seg      = seg._spawn(seg.raw_data, overrides={"frame_rate": new_rate})
            seg      = seg.set_frame_rate(44100)
            seg      = seg.low_pass_filter(8000)
            # Reduced pause to 10ms to fix the silence issue
            pause = AudioSegment.silent(duration=10)
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

    print("  ⚠️ pydub merge failed — single gTTS fallback")
    tts = gTTS(text=clean, lang="en", tld="co.uk", slow=False)
    tts.save(filename)
    return filename

# ════════════════════════════════════════
# PEXELS VIDEO FETCH
# ════════════════════════════════════════
def download_video(url, filename):
    r = requests.get(url, timeout=90, stream=True)
    with open(filename, "wb") as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    return filename

def get_pexels_videos(search_terms_str, target_count=40, orientation="landscape"):
    print(f"🎬 Fetching {target_count} footage clips ({orientation})...")
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
        "financial scam investigation","bank fraud news","young entrepreneur success",
        "company collapse news","investment disaster footage","crypto market crash animation",
        "stock market manipulation news","debt crisis europe footage","economic shock europe",
        "wealth secrets europe","tax evasion europe","financial loophole footage"
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
                f"&per_page=5&orientation={orientation}&size=medium"
            )
            r = requests.get(url, headers=headers, timeout=20)
            if r.status_code != 200:
                continue
            for v in r.json().get("videos", []):
                for vf in v.get("video_files", []):
                    if vf.get("quality") in ["hd","sd"] and ((orientation == "landscape" and vf.get("width",0) >= 1280) or (orientation == "portrait" and vf.get("height",0) >= 1920)):
                        videos.append({"url": vf["link"], "term": term})
                        break
        except Exception as e:
            print(f"  ⚠️ Pexels [{term}]: {e}")

    random.shuffle(videos)
    print(f"✅ {len(videos)} clips found")
    return videos[:target_count]

# ════════════════════════════════════════
# THUMBNAIL
# ════════════════════════════════════════
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

def draw_text_shadow(draw, pos, text, font, color, shadow=(0,0,0), offset=7):
    x, y = pos
    for o in [offset, offset-2, offset-4]:
        if o > 0:
            draw.text((x+o, y+o), text, font=font, fill=shadow)
    r,g,b  = color
    glow   = (max(0,r-90), max(0,g-90), max(0,b-90))
    draw.text((x+1, y+2), text, font=font, fill=glow)
    draw.text((x, y),     text, font=font, fill=color)

def create_thumbnail(thumbnail_text, title, filename="thumbnail.jpg", video_type="long"):
    print(f"🖼️ Creating professional thumbnail for {video_type} video...")
    W, H = (1280, 720) if video_type == "long" else (1080, 1920)
    img  = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)

    for y in range(H):
        ratio = y / H
        r = int(10 + ratio * 20)
        g = int(8  + ratio * 12)
        b = int(8  + ratio * 15)
        draw.line([(0,y),(W,y)], fill=(r,g,b))

    cx, cy = int(W*0.40), int(H*0.40)
    for radius in range(min(W,H)//2, 0, -5):
        alpha = int(20 * (1 - radius/(min(W,H)//2)))
        rv = min(255, 38+alpha*2)
        gv = min(255, 22+alpha)
        bv = min(255, 8+alpha)
        draw.ellipse([cx-radius,cy-radius,cx+radius,cy+radius], fill=(rv,gv,bv))

    bar_width = 18 if video_type == "long" else 30
    for x in range(bar_width):
        gval = max(0, int(220 - x*7))
        rval = min(255, gval+35)
        draw.rectangle([x,0,x,H], fill=(rval, gval, 0))

    clean = thumbnail_text.upper().replace("*","").replace("[","").replace("]","").replace('"',"").strip()
    words = clean.split()[:3]
    if not words: words = ["FINANCE"]
    lines = [words[0], " ".join(words[1:])] if len(words) > 1 else [words[0]]

    font_mega = load_font(180 if video_type == "short" else 118)
    font_xl   = load_font(120 if video_type == "short" else 90)
    font_md   = load_font(50 if video_type == "short" else 38)
    font_sm   = load_font(35 if video_type == "short" else 28)

    LEFT = 30 if video_type == "long" else 50
    y_pos = 55 if video_type == "long" else 150
    if video_type == "short":
        y_pos = (H - (300 if len(lines) > 1 else 180)) // 2

    if lines[0]:
        draw_text_shadow(draw, (LEFT, y_pos), lines[0], font_mega, color=(255,215,0), shadow=(0,0,0), offset=9)
        y_pos += (180 if video_type == "short" else 128)
    if len(lines) > 1 and lines[1]:
        draw_text_shadow(draw, (LEFT, y_pos), lines[1], font_xl, color=(255,255,255), shadow=(0,0,0), offset=7)

    sy = H - (75 if video_type == "long" else 120)
    draw.text((LEFT+6, sy+16), CHANNEL_NAME.upper(), font=font_md, fill=(255,235,200))
    img.save(filename, quality=97)
    return filename

# ════════════════════════════════════════
# VIDEO ASSEMBLY
# ════════════════════════════════════════
def create_video(audio_file, video_clips, title, output="final_video.mp4", video_type="long"):
    print(f"🎞️ Assembling {video_type} video...")
    audio     = AudioFileClip(audio_file)
    total_dur = audio.duration
    if video_type == "short" and total_dur > 59:
        total_dur = 59
        audio = audio.subclip(0, total_dur)
    
    video_size = VIDEO_SIZE_SHORT if video_type == "short" else VIDEO_SIZE_LONG
    target_scenes = max(int(total_dur / 2), 10) if video_type == "short" else max(int(total_dur / SCENE_DURATION), 30)
    scene_dur = total_dur / target_scenes

    raw_clips = []
    downloaded = []
    for i, vc in enumerate(video_clips[:target_scenes]):
        fname = f"raw_{video_type}_{i}.mp4"
        try:
            download_video(vc["url"], fname)
            clip = VideoFileClip(fname).resize(height=video_size[1])
            # Center crop
            w, h = clip.size
            target_w = video_size[0]
            if w > target_w:
                clip = clip.crop(x_center=w/2, width=target_w)
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
                start = random.uniform(0, max_start) if max_start > 0 else 0
                c = src.subclip(start, start + scene_dur) if src.duration >= scene_dur else src.fx(vfx.loop, duration=scene_dur)
                c = c.set_duration(scene_dur)
                if idx > 0: c = c.crossfadein(0.2)
                compiled.append(c)
            except:
                compiled.append(ColorClip(size=video_size, color=[10,6,6], duration=scene_dur))
    else:
        compiled = [ColorClip(size=video_size, color=[10,6,6], duration=total_dur)]

    video = concatenate_videoclips(compiled, method="compose")
    video = video.set_duration(total_dur).set_audio(audio)
    video.write_videofile(output, fps=VIDEO_FPS, codec="libx264", audio_codec="aac", bitrate="3000k", logger=None)

    for c,_ in raw_clips:
        try: c.close()
        except: pass
    for f in downloaded:
        try: os.remove(f)
        except: pass
    return output

# ════════════════════════════════════════
# METADATA
# ════════════════════════════════════════
def save_metadata(title, meta, topic, video_type="long"):
    content = f"# {video_type.upper()} METADATA\nTITLE: {meta.get('best_title', title)}\nTOPIC: {topic}\nTAGS: {meta.get('tags', '')}\nDESC: {meta.get('description', '')}\n"
    with open(f"{video_type}_metadata.txt", "w", encoding="utf-8") as f:
        f.write(content)

# ════════════════════════════════════════
# MAIN
# ════════════════════════════════════════
def main():
    topic, research_data = get_topic()
    full_script = generate_script_groq(topic, research_data)
    script, title, meta = parse_script(full_script)

    # Long Video
    audio_long = generate_audio(script, filename="long_audio.mp3")
    clips_long = get_pexels_videos(meta["search_terms"], orientation="landscape")
    create_video(audio_long, clips_long, title, output="final_video.mp4", video_type="long")
    create_thumbnail(meta["thumbnail"], title, filename="thumbnail.jpg", video_type="long")
    save_metadata(title, meta, topic, video_type="long")

    # Short Video
    short_script = " ".join(script.split()[:250])
    audio_short = generate_audio(short_script, filename="short_audio.mp3")
    clips_short = get_pexels_videos(meta["search_terms"], target_count=20, orientation="portrait")
    create_video(audio_short, clips_short, title, output="short_video.mp4", video_type="short")
    create_thumbnail(meta["thumbnail"], title, filename="short_thumbnail.jpg", video_type="short")
    save_metadata(title, meta, topic, video_type="short")

if __name__ == "__main__":
    main()
