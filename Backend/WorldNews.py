"""
WorldNews.py  –  F.R.I.D.A.Y. World Intelligence Module
────────────────────────────────────────────────────────
Fetch strategy (tries in order until headlines arrive):
  1. gnews  – Google News Python wrapper (India-reliable)
  2. feedparser RSS chain  – BBC / NYT / NPR / Guardian
  3. Groq knowledge fallback  – model generates briefing
"""

import feedparser
import requests
import webbrowser
import os
import json
from gnews import GNews
from groq import Groq
from dotenv import dotenv_values
from datetime import datetime

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)

TOPIC_FEEDS = {
    "world": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
        "https://feeds.npr.org/1004/rss.xml",
        "https://www.theguardian.com/world/rss",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "india": [
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "http://feeds.bbci.co.uk/news/world/south_asia/rss.xml",
        "https://www.thehindu.com/news/national/feeder/default.rss",
        "https://feeds.feedburner.com/ndtvnews-top-stories",
    ],
    "tech": [
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theverge.com/rss/index.xml",
        "http://feeds.arstechnica.com/arstechnica/index",
        "https://feeds.feedburner.com/TechCrunch",
    ],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://www.theguardian.com/business/rss",
        "https://feeds.npr.org/1006/rss.xml",
    ],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

GEO_MAP = {
    "india": [20.59, 78.96, "India"], "new delhi": [28.61, 77.20, "New Delhi"],
    "mumbai": [19.07, 72.87, "Mumbai"], "china": [35.86, 104.19, "China"],
    "beijing": [39.90, 116.40, "Beijing"], "russia": [61.52, 105.31, "Russia"],
    "moscow": [55.75, 37.61, "Moscow"], "ukraine": [48.37, 31.16, "Ukraine"],
    "usa": [37.09, -95.71, "United States"], "united states": [37.09, -95.71, "United States"],
    "washington": [38.90, -77.03, "Washington DC"], "new york": [40.71, -74.00, "New York"],
    "london": [51.50, -0.12, "London"], "uk": [55.37, -3.43, "United Kingdom"],
    "europe": [54.52, 15.25, "Europe"], "france": [46.22, 2.21, "France"],
    "paris": [48.85, 2.35, "Paris"], "germany": [51.16, 10.45, "Germany"],
    "israel": [31.04, 34.85, "Israel"], "iran": [32.42, 53.68, "Iran"],
    "pakistan": [30.37, 69.34, "Pakistan"], "middle east": [29.31, 47.48, "Middle East"],
    "gaza": [31.35, 34.30, "Gaza"], "japan": [36.20, 138.25, "Japan"],
    "tokyo": [35.67, 139.65, "Tokyo"], "korea": [35.90, 127.76, "Korea"],
    "taiwan": [23.69, 120.96, "Taiwan"], "africa": [8.78, 34.50, "Africa"],
    "brazil": [-14.23, -51.92, "Brazil"], "australia": [-25.27, 133.77, "Australia"],
    "canada": [56.13, -106.34, "Canada"], "turkey": [38.96, 35.24, "Turkey"],
    "saudi": [23.88, 45.07, "Saudi Arabia"], "singapore": [1.35, 103.81, "Singapore"],
    "egypt": [26.82, 30.80, "Egypt"], "iraq": [33.22, 43.67, "Iraq"],
    "south africa": [-30.55, 22.93, "South Africa"],
}


def _layer1_gnews(topic: str, max_articles: int) -> list:
    try:
        gn = GNews(language="en", country="IN", max_results=max_articles)
        topic_map = {
            "india":    lambda: gn.get_news("India"),
            "tech":     lambda: gn.get_news("technology"),
            "business": lambda: gn.get_news("business finance"),
            "world":    lambda: gn.get_top_news(),
        }
        raw = topic_map.get(topic, topic_map["world"])()
        headlines = [
            item["title"].rsplit(" - ", 1)[0].strip()
            for item in raw if item.get("title")
        ]
        if headlines:
            print(f"[WorldNews] Layer 1 (gnews): {len(headlines)} headlines")
        return headlines
    except Exception as e:
        print(f"[WorldNews] Layer 1 failed: {e}")
        return []


def _fetch_feed(url: str, max_items: int) -> list:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code >= 400:
            return []
        if b"<!DOCTYPE" in resp.content[:300] or b"<html" in resp.content[:300]:
            return []
        feed = feedparser.parse(resp.content)
        headlines = []
        for entry in feed.entries[:max_items]:
            title = entry.get("title", "").strip().rsplit(" - ", 1)[0].strip()
            if title:
                headlines.append(title)
        return headlines
    except Exception as e:
        print(f"[WorldNews] Feed error ({url}): {e}")
        return []


def _layer2_rss(topic: str, max_articles: int) -> list:
    for url in TOPIC_FEEDS.get(topic, TOPIC_FEEDS["world"]):
        print(f"[WorldNews] Layer 2 trying: {url}")
        h = _fetch_feed(url, max_articles)
        if h:
            print(f"[WorldNews] Layer 2 (RSS): {len(h)} headlines")
            return h
    return []


def _layer3_groq(topic: str) -> list:
    print("[WorldNews] Layer 3: Groq knowledge fallback")
    label = {"india": "India", "tech": "technology", "business": "business"}.get(topic, "world")
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "You are a news headline generator. Generate exactly 8 concise, "
                    "realistic news headlines based on your knowledge of recent global events. "
                    "Return ONLY a JSON array of strings — no extra text, no markdown."
                )},
                {"role": "user", "content": f"Generate 8 current {label} news headlines."},
            ],
            max_tokens=400, temperature=0.4,
        )
        raw = resp.choices[0].message.content.strip().replace("```json","").replace("```","").strip()
        headlines = json.loads(raw)
        if isinstance(headlines, list):
            print(f"[WorldNews] Layer 3 (Groq): {len(headlines)} headlines")
            return [str(h) for h in headlines]
    except Exception as e:
        print(f"[WorldNews] Layer 3 failed: {e}")
    return []


def _get_headlines(topic: str, max_articles: int = 10) -> list:
    h = _layer1_gnews(topic, max_articles)
    if h: return h
    h = _layer2_rss(topic, max_articles)
    if h: return h
    return _layer3_groq(topic)


def geocode_headline(headline: str):
    hl = headline.lower()
    for keyword, coords in GEO_MAP.items():
        if keyword in hl:
            return coords
    return None


def GetWorldNews(topic: str = "world", max_articles: int = 10) -> str:
    print(f"\n[WorldNews] === Fetching '{topic}' news ===")
    articles = _get_headlines(topic, max_articles)

    if not articles:
        return "Boss, all three news layers failed. Check connection."

    _open_world_monitor(articles, topic)

    headlines_text = "\n".join(f"• {a}" for a in articles)
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    "You are F.R.I.D.A.Y., Tony Stark's AI assistant. "
                    "Give a sharp, confident 3-4 sentence spoken news briefing. "
                    "Start with 'Here's what's happening, Boss.' "
                    "No bullet points. Spoken audio. Punchy."
                )},
                {"role": "user", "content": f"Today's headlines:\n{headlines_text}\n\nBriefing please."},
            ],
            max_tokens=300, temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"[WorldNews] Groq briefing error: {e}")
        return "Here's what's happening, Boss. " + " | ".join(articles[:3])


def _open_world_monitor(articles: list, topic: str = "world"):
    markers = []
    seen_cities = set()
    for article in articles:
        geo = geocode_headline(article)
        if geo and geo[2] not in seen_cities:
            seen_cities.add(geo[2])
            markers.append({"lat": geo[0], "lng": geo[1], "city": geo[2], "headline": article})

    for fb in [
        {"lat": 40.71, "lng": -74.00, "city": "New York",  "headline": "Global markets in focus"},
        {"lat": 51.50, "lng":  -0.12, "city": "London",    "headline": "European political updates"},
        {"lat": 35.67, "lng": 139.65, "city": "Tokyo",     "headline": "Asia-Pacific briefing"},
        {"lat": 20.59, "lng":  78.96, "city": "India",     "headline": "South Asia developments"},
        {"lat": 48.85, "lng":   2.35, "city": "Paris",     "headline": "Eurozone financial news"},
    ]:
        if fb["city"] not in seen_cities and len(markers) < 8:
            markers.append(fb)

    # Verified Live Video IDs (Latest as of April 2026)
    # Format: (VideoID, Label)
    VIDEO_MAP = {
        "world": [
            ("iipR5yUp36o", "ABC NEWS LIVE"),
            ("YDvsBbKfLPA", "SKY NEWS LIVE")
        ],
        "india": [
            ("Ygi3z94x2t8", "INDIA TODAY LIVE"),
            ("4dtlhcvb-YU", "NDTV 24x7 LIVE")
        ],
        "tech": [
            ("iEpJwprxDdk", "BLOOMBERG TECH"),
            ("YDvsBbKfLPA", "SKY NEWS LIVE")
        ],
        "business": [
            ("iEpJwprxDdk", "BLOOMBERG LIVE"),
            ("YDvsBbKfLPA", "SKY NEWS LIVE")
        ]
    }
    
    selected_feeds = VIDEO_MAP.get(topic, VIDEO_MAP["world"])
    v1_id, v1_label = selected_feeds[0]
    v2_id, v2_label = selected_feeds[1]

    topic_label = {"world":"WORLD","tech":"TECHNOLOGY","india":"INDIA","business":"BUSINESS"}.get(topic,"WORLD")
    now = datetime.now()
    current_date = now.strftime("%B %d, %Y").upper()
    current_time = now.strftime("%H:%M:%S")
    n_articles = len(articles)
    markers_json = json.dumps(markers)
    articles_json = json.dumps(articles)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>F.R.I.D.A.Y. — {topic_label} MONITOR</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet">
<style>
/* CSS Reset and Variables (Blue Theme) */
*,*::before,*::after {{ margin:0; padding:0; box-sizing:border-box; }}
:root {{
    --blue: #00a8ff;
    --blue-dim: rgba(0,168,255,0.12);
    --cyan: #00d4ff;
    --green: #00ff88;
    --alert: #ff3366;
    --bg: #06090d;
    --panel: #080c12;
    --panel-header: rgba(0,168,255,0.08);
    --border: rgba(0,168,255,0.25);
    --border-b: rgba(0,168,255,0.5);
    --text: #c5cdd8;
    --dim: #5a6472;
    --mono: 'Share Tech Mono', monospace;
    --display: 'Orbitron', sans-serif;
}}

body {{ background:var(--bg); font-family:var(--mono); color:var(--text); overflow:hidden; height:100vh; width:100vw; }}
/* CRT Scanline Overlay */
body::before {{ content:''; position:fixed; inset:0; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.07) 2px,rgba(0,0,0,0.07) 4px); pointer-events:none; z-index:9999; }}

/* Custom Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-track {{ background: var(--bg); }}
::-webkit-scrollbar-thumb {{ background: var(--border-b); border-radius: 3px; }}
::-webkit-scrollbar-thumb:hover {{ background: var(--blue); }}

/* Topbar Styles */
#topbar {{ position:fixed; top:0; left:0; right:0; height:52px; background:rgba(6,9,13,0.97); border-bottom:1px solid var(--border-b); display:flex; align-items:center; justify-content:space-between; padding:0 24px; z-index:1000; box-shadow: 0 4px 20px rgba(0,168,255,0.1); }}
.brand {{ display:flex; align-items:center; gap:14px; }}
.brand-logo {{ font-family:var(--display); font-size:14px; font-weight:900; letter-spacing:4px; color:var(--blue); text-shadow:0 0 15px rgba(0,168,255,0.6); }}
.brand-sep {{ width:1px; height:24px; background:var(--border-b); }}
.brand-sub {{ font-size:11px; letter-spacing:3px; color:var(--dim); font-weight:bold; }}

.topbar-right {{ display:flex; align-items:center; gap:20px; }}
.live-badge {{ display:flex; align-items:center; gap:6px; font-size:10px; letter-spacing:2px; color:var(--green); }}
.live-dot {{ width:8px; height:8px; background:var(--green); border-radius:50%; box-shadow:0 0 10px var(--green); animation:livePulse 1.4s ease-in-out infinite; }}
@keyframes livePulse {{ 0%,100% {{opacity:1;}} 50% {{opacity:.4;}} }}

.topbar-date {{ font-size:11px; color:var(--dim); letter-spacing:2px; }}
#clock {{ font-family:var(--display); font-size:15px; color:var(--cyan); letter-spacing:3px; text-shadow:0 0 12px rgba(0,212,255,0.5); width: 90px; text-align: right; }}

/* Main Layout */
#main-container {{ position:fixed; top:52px; left:0; right:0; bottom:64px; display:flex; }}

/* Map Pane */
#left-pane {{ width:45%; position:relative; border-right:1px solid var(--border-b); background:#06090d; overflow: hidden; }}
#map {{ width:100%; height:100%; z-index:1; }}
.leaflet-container {{ background:#06090d !important; }}
#map-grid {{ position:absolute; inset:0; pointer-events:none; z-index:2; background:linear-gradient(rgba(0,168,255,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(0,168,255,0.03) 1px,transparent 1px); background-size:50px 50px; }}

#scanner-line {{
    position: absolute; top: 0; left: 0; width: 100%; height: 2px;
    background: var(--alert);
    box-shadow: 0 0 15px var(--alert);
    z-index: 3; pointer-events: none;
    animation: scanMap 4s linear infinite;
}}
@keyframes scanMap {{ 0% {{ top:0; opacity:0; }} 10% {{ opacity:1; }} 90% {{ opacity:1; }} 100% {{ top:100%; opacity:0; }} }}

#summary-box {{ position:absolute; bottom:15px; left:15px; width:calc(100% - 30px); background:rgba(6,9,13,0.85); border:1px solid var(--border-b); border-radius:4px; padding:12px 16px; z-index:500; backdrop-filter:blur(8px); }}
.summary-label {{ font-family:var(--display); font-size:9px; letter-spacing:3px; color:var(--blue); margin-bottom:6px; display:flex; justify-content:space-between;}}
.summary-text {{ font-size:11px; line-height:1.6; color:var(--text); min-height: 36px; }}

/* Right Pane */
#right-pane {{ width:55%; display:flex; flex-direction:column; padding:12px; gap:12px; background:linear-gradient(135deg, #080c12 0%, #06090d 100%); overflow-y:auto; }}
.dash-row {{ display:flex; gap:12px; width:100%; }}

/* Panels */
.panel {{ background:var(--panel); border:1px solid var(--border); border-radius:4px; display:flex; flex-direction:column; overflow:hidden; position:relative; }}
.panel-header {{ background:var(--panel-header); padding:8px 12px; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:8px; font-family:var(--display); font-size:10px; letter-spacing:2px; color:var(--text); }}
.panel-header i {{ color:var(--blue); font-style:normal; }}

/* Videos */
.video-section {{ flex:1.2; display:flex; gap:12px; min-height: 280px; }}
.video-main {{ flex:2; }}
.video-sub {{ flex:1; }}
.iframe-container {{ width:100%; height:100%; flex:1; background:#000; position:relative; overflow:hidden; }}
.iframe-container iframe {{ width:100%; height:100%; border:none; }}

/* Watch on YouTube Button */
.yt-overlay {{ position:absolute; bottom:10px; right:10px; z-index:20; }}
.yt-btn {{ background:rgba(255,0,0,0.8); color:#fff; font-size:9px; padding:4px 10px; border-radius:2px; text-decoration:none; display:flex; align-items:center; gap:5px; font-family:var(--display); transition: 0.2s; }}
.yt-btn:hover {{ background:rgb(255,0,0); transform:scale(1.05); }}

/* Lower Section */
.lower-section {{ flex:1; display:flex; gap:12px; min-height: 250px;}}
#news-panel {{ flex:1.5; }}
#news-feed {{ flex:1; overflow-y:auto; padding:10px; scrollbar-width:thin; }}
.news-card {{ background:var(--blue-dim); border:1px solid var(--border); border-left:2px solid var(--blue); border-radius:2px; padding:10px; margin-bottom:8px; font-size:11px; position:relative; }}
.news-card:hover {{ background:rgba(0,168,255,0.2); }}
.card-meta {{ display:flex; justify-content:space-between; font-size:8px; color:var(--blue); letter-spacing:1px; margin-bottom:4px; font-family:var(--display); }}
.card-actions {{ position:absolute; top:10px; right:10px; display:flex; gap:5px; opacity:0; transition:0.2s; }}
.news-card:hover .card-actions {{ opacity:1; }}
.action-btn {{ color:var(--cyan); text-decoration:none; font-size:14px; font-weight:bold; }}

#intel-panel {{ flex:1; }}
.stat-box {{ padding:12px; border-bottom:1px solid var(--border-b); }}
.stat-label {{ font-size:9px; color:var(--dim); letter-spacing:1px; margin-bottom:6px; display:flex; justify-content:space-between; }}
.stat-bar-bg {{ width:100%; height:6px; background:rgba(255,255,255,0.05); border-radius:3px; overflow:hidden; }}
.stat-bar-fill {{ height:100%; background:var(--blue); transition: 0.8s; }}
.fill-alert {{ background:var(--alert); }}

/* Ticker */
#ticker {{ position:fixed; bottom:0; left:0; right:0; height:64px; background:rgba(6,9,13,0.98); border-top:1px solid var(--border-b); display:flex; align-items:center; overflow:hidden; }}
.ticker-label {{ background:var(--blue); color:#000; padding:0 20px; height:100%; display:flex; align-items:center; font-family:var(--display); font-size:10px; font-weight:900; letter-spacing:2px; }}
#ticker-track {{ display:flex; align-items:center; white-space:nowrap; animation: tickerScroll 60s linear infinite; }}
.ticker-item {{ font-size:12px; color:var(--text); padding:0 36px; }}
@keyframes tickerScroll {{ from {{transform:translateX(0);}} to {{transform:translateX(-50%);}} }}

/* Markers */
.friday-marker {{ width:12px; height:12px; background:var(--cyan); border-radius:50%; border:2px solid rgba(0,212,255,.5); animation:markerRing 2s infinite; }}
@keyframes markerRing {{ 0% {{box-shadow:0 0 0 0 rgba(0,212,255,.8);}} 70% {{box-shadow:0 0 0 15px rgba(0,212,255,0);}} 100% {{box-shadow:0 0 0 0 rgba(0,212,255,0);}} }}
</style>
</head>
<body>
<div id="topbar">
  <div class="brand">
      <div class="brand-logo">F.R.I.D.A.Y.</div>
      <div class="brand-sep"></div>
      <div class="brand-sub">{topic_label} INTELLIGENCE MONITOR</div> 
  </div>
  <div class="topbar-right">
    <div class="live-badge"><div class="live-dot"></div>NETWORK ONLINE</div>
    <div class="topbar-date">{current_date}</div>
    <div id="clock">{current_time}</div>
  </div>
</div>

<div id="main-container">
    <div id="left-pane">
        <div id="map"></div>
        <div id="map-grid"></div>
        <div id="scanner-line"></div>
        <div id="summary-box">
            <div class="summary-label"><span><i>&#9656;</i> INTEL SUMMARY</span></div>
            <div class="summary-text" id="summary-text"></div>
        </div>
    </div>

    <div id="right-pane">
        <div class="dash-row video-section">
            <div class="panel video-main">
                <div class="panel-header"><i>&#9673;</i> {v1_label}</div>
                <div class="iframe-container">
                    <iframe src="https://www.youtube.com/embed/{v1_id}?autoplay=1&mute=1&controls=0" allowfullscreen></iframe>
                    <div class="yt-overlay">
                        <a href="https://www.youtube.com/watch?v={v1_id}" target="_blank" class="yt-btn">▶ WATCH ON YOUTUBE</a>
                    </div>
                </div>
            </div>
            <div class="panel video-sub">
                <div class="panel-header"><i>&#9673;</i> {v2_label}</div>
                <div class="iframe-container">
                    <iframe src="https://www.youtube.com/embed/{v2_id}?autoplay=1&mute=1&controls=0" allowfullscreen></iframe>
                    <div class="yt-overlay">
                        <a href="https://www.youtube.com/watch?v={v2_id}" target="_blank" class="yt-btn">▶ WATCH ON YOUTUBE</a>
                    </div>
                </div>
            </div>
        </div>

        <div class="dash-row lower-section">
            <div class="panel" id="news-panel">
                <div class="panel-header"><i>&#9776;</i> BREAKING NEWS</div>
                <div id="news-feed"></div>
            </div>
            <div class="panel" id="intel-panel">
                <div class="panel-header"><i>&#9888;</i> THREAT INTEL</div>
                <div style="flex:1; display:flex; flex-direction:column; justify-content:space-around;">
                    <div class="stat-box">
                        <div class="stat-label"><span>GLOBAL INSTABILITY</span> <span id="v1">84%</span></div>
                        <div class="stat-bar-bg"><div class="stat-bar-fill fill-alert" id="b1" style="width: 84%;"></div></div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label"><span>CYBER THREAT</span> <span id="v2">62%</span></div>
                        <div class="stat-bar-bg"><div class="stat-bar-fill" id="b2" style="width: 62%;"></div></div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-label"><span>MARKET VOLATILITY</span> <span id="v3">45%</span></div>
                        <div class="stat-bar-bg"><div class="stat-bar-fill" id="b3" style="width: 45%;"></div></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="ticker">
  <div class="ticker-label">FRIDAY NEWS</div>
  <div id="ticker-vp"><div id="ticker-track"></div></div>
</div>

<script>
const ARTICLES = {articles_json};
const MARKERS = {markers_json};

function tick() {{
    const n = new Date(), p = v => String(v).padStart(2,'0');
    document.getElementById('clock').textContent = `${{p(n.getHours())}}:${{p(n.getMinutes())}}:${{p(n.getSeconds())}}`;
}}
setInterval(tick, 1000); tick();

const map = L.map('map', {{zoomControl:false, attributionControl:false, center:[20, 0], zoom:2.1}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);

MARKERS.forEach((m, i) => {{
  const icon = L.divIcon({{ className: '', html: `<div class="friday-marker" style="animation-delay:${{i * 0.3}}s"></div>`, iconSize: [12,12] }});
  L.marker([m.lat, m.lng], {{icon}}).addTo(map).bindTooltip(`<span class="tt-city">${{m.city}}</span>${{m.headline}}`);
}});

function renderNews() {{
    const feed = document.getElementById('news-feed');
    ARTICLES.forEach((a, i) => {{
      const c = document.createElement('div');
      c.className = 'news-card';
      c.innerHTML = `
        <div class="card-meta"><span>STORY ${{i+1}}</span><span>LIVE</span></div>
        ${{a}}
        <div class="card-actions">
            <a href="https://www.youtube.com/results?search_query=${{encodeURIComponent(a)}}" target="_blank" class="action-btn" title="Search Video">▶ SEARCH VIDEO</a>
        </div>
      `;
      feed.appendChild(c);
    }});
}}
renderNews();

const lines = ["Scanning sources...", "Metrics established.", "Briefing: " + ARTICLES.slice(0,2).join(' · ')];
let li=0, ci=0; const el=document.getElementById('summary-text');
function type() {{
    if(li >= lines.length) {{ li=0; el.textContent=''; }}
    if(ci < lines[li].length) {{ el.textContent += lines[li][ci++]; setTimeout(type, 30); }}
    else {{ setTimeout(() => {{ li++; ci=0; el.textContent=''; type(); }}, 4000); }}
}}
type();

const track = document.getElementById('ticker-track');
[...ARTICLES, ...ARTICLES].forEach(a => {{
    const s = document.createElement('span'); s.className = 'ticker-item';
    s.innerHTML = `${{a.toUpperCase()}} <span style="color:var(--blue)">///</span>`;
    track.appendChild(s);
}});

setInterval(() => {{
    [1,2,3].forEach(i => {{
        const b = document.getElementById('b'+i), v = document.getElementById('v'+i);
        let val = parseInt(v.textContent) + (Math.random() > 0.5 ? 1 : -1);
        val = Math.max(10, Math.min(95, val));
        v.textContent = val + '%'; b.style.width = val + '%';
    }});
}}, 3000);
</script>
</body>
</html>"""

    out_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "Frontend", "WorldMonitor.html"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    webbrowser.open(f"file:///{os.path.abspath(out_path).replace(os.sep, '/')}")
    print(f"[WorldNews] Monitor opened: {out_path}")