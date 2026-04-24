import requests
import xml.etree.ElementTree as ET
import webbrowser
import os
import json
from groq import Groq
from dotenv import dotenv_values
from datetime import datetime

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
client = Groq(api_key=GroqAPIKey)

# Reliable RSS feeds with fallbacks per topic
TOPIC_FEEDS = {
    "world": [
        "http://feeds.bbci.co.uk/news/world/rss.xml",
        "https://feeds.skynews.com/feeds/rss/world.xml",
        "https://www.aljazeera.com/xml/rss/all.xml",
    ],
    "india": [
        "https://timesofindia.indiatimes.com/rssfeedstopstories.cms",
        "http://feeds.bbci.co.uk/news/world/south_asia/rss.xml",
        "https://www.thehindu.com/news/national/feeder/default.rss",
    ],
    "tech": [
        "https://feeds.feedburner.com/TechCrunch",
        "http://feeds.bbci.co.uk/news/technology/rss.xml",
        "https://www.theverge.com/rss/index.xml",
    ],
    "business": [
        "http://feeds.bbci.co.uk/news/business/rss.xml",
        "https://feeds.skynews.com/feeds/rss/business.xml",
    ],
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

# keyword → [lat, lng, city_label]
GEO_MAP = {
    "india":         [20.59,  78.96,   "India"],
    "new delhi":     [28.61,  77.20,   "New Delhi"],
    "mumbai":        [19.07,  72.87,   "Mumbai"],
    "china":         [35.86, 104.19,   "China"],
    "beijing":       [39.90, 116.40,   "Beijing"],
    "russia":        [61.52, 105.31,   "Russia"],
    "moscow":        [55.75,  37.61,   "Moscow"],
    "ukraine":       [48.37,  31.16,   "Ukraine"],
    "usa":           [37.09, -95.71,   "United States"],
    "united states": [37.09, -95.71,   "United States"],
    "washington":    [38.90, -77.03,   "Washington DC"],
    "new york":      [40.71, -74.00,   "New York"],
    "london":        [51.50,  -0.12,   "London"],
    "uk":            [55.37,  -3.43,   "United Kingdom"],
    "britain":       [55.37,  -3.43,   "Britain"],
    "europe":        [54.52,  15.25,   "Europe"],
    "france":        [46.22,   2.21,   "France"],
    "paris":         [48.85,   2.35,   "Paris"],
    "germany":       [51.16,  10.45,   "Germany"],
    "israel":        [31.04,  34.85,   "Israel"],
    "iran":          [32.42,  53.68,   "Iran"],
    "pakistan":      [30.37,  69.34,   "Pakistan"],
    "middle east":   [29.31,  47.48,   "Middle East"],
    "gaza":          [31.35,  34.30,   "Gaza"],
    "japan":         [36.20, 138.25,   "Japan"],
    "tokyo":         [35.67, 139.65,   "Tokyo"],
    "korea":         [35.90, 127.76,   "Korea"],
    "taiwan":        [23.69, 120.96,   "Taiwan"],
    "africa":        [ 8.78,  34.50,   "Africa"],
    "nigeria":       [ 9.08,   8.67,   "Nigeria"],
    "brazil":        [-14.23, -51.92,  "Brazil"],
    "australia":     [-25.27, 133.77,  "Australia"],
    "canada":        [56.13, -106.34,  "Canada"],
    "mexico":        [23.63, -102.55,  "Mexico"],
    "turkey":        [38.96,  35.24,   "Turkey"],
    "saudi":         [23.88,  45.07,   "Saudi Arabia"],
    "singapore":     [ 1.35, 103.81,   "Singapore"],
    "thailand":      [15.87, 100.99,   "Thailand"],
    "myanmar":       [19.16,  95.96,   "Myanmar"],
    "egypt":         [26.82,  30.80,   "Egypt"],
    "iraq":          [33.22,  43.67,   "Iraq"],
    "afghanistan":   [33.93,  67.70,   "Afghanistan"],
    "south africa":  [-30.55,  22.93,  "South Africa"],
}


def _fetch_rss(url: str, max_items: int = 10) -> list:
    """Fetch and parse an RSS feed. Returns list of headline strings."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)

        headlines = []
        # Handle both RSS 2.0 (<item>) and Atom (<entry>) feeds
        items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")

        for item in items[:max_items]:
            title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
            if title_el is not None and title_el.text:
                # Strip CDATA / publisher suffix
                title = title_el.text.strip()
                title = title.rsplit(" - ", 1)[0].strip()
                if title:
                    headlines.append(title)

        return headlines

    except Exception as e:
        print(f"[WorldNews] Feed failed ({url}): {e}")
        return []


def _get_headlines(topic: str, max_articles: int = 10) -> list:
    """Try each feed URL for a topic until we get headlines."""
    for url in TOPIC_FEEDS.get(topic, TOPIC_FEEDS["world"]):
        print(f"[WorldNews] Trying: {url}")
        headlines = _fetch_rss(url, max_articles)
        if headlines:
            print(f"[WorldNews] ✅ Got {len(headlines)} headlines from {url}")
            return headlines
    return []


def geocode_headline(headline: str):
    hl = headline.lower()
    for keyword, coords in GEO_MAP.items():
        if keyword in hl:
            return coords
    return None


def GetWorldNews(topic: str = "world", max_articles: int = 10) -> str:
    print(f"[WorldNews] Fetching '{topic}' news...")
    articles = _get_headlines(topic, max_articles)

    if not articles:
        return (
            "Boss, I'm having trouble reaching all news sources right now. "
            "Check your internet connection and try again."
        )

    # Open the visual world monitor in browser
    _open_world_monitor(articles, topic)

    # Generate spoken briefing via Groq
    headlines_text = "\n".join(f"• {a}" for a in articles)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are F.R.I.D.A.Y., Tony Stark's AI assistant. "
                        "Give a sharp, confident, 3-4 sentence spoken news briefing. "
                        "Start with something like 'Here's what's happening, Boss.' "
                        "No bullet points — this is spoken audio. Keep it punchy."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Today's top headlines:\n{headlines_text}\n\nBriefing please.",
                },
            ],
            max_tokens=300,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()

    except Exception as e:
        # Fallback: just read first 3 headlines
        return (
            f"Here's what's happening, Boss. "
            + " ".join(articles[:3])
        )


def _open_world_monitor(articles: list, topic: str = "world"):
    """Generate and open the Bloomberg-style FRIDAY World Monitor HTML."""

    # Geocode headlines → map markers
    markers = []
    seen_cities = set()
    for article in articles:
        geo = geocode_headline(article)
        if geo and geo[2] not in seen_cities:
            seen_cities.add(geo[2])
            markers.append({"lat": geo[0], "lng": geo[1], "city": geo[2], "headline": article})

    # Default fallback markers
    fallbacks = [
        {"lat": 40.71,  "lng": -74.00,  "city": "New York", "headline": "Global markets in focus"},
        {"lat": 51.50,  "lng":  -0.12,  "city": "London",   "headline": "European political updates"},
        {"lat": 35.67,  "lng": 139.65,  "city": "Tokyo",    "headline": "Asia-Pacific briefing"},
        {"lat": 20.59,  "lng":  78.96,  "city": "India",    "headline": "South Asia developments"},
        {"lat": 48.85,  "lng":   2.35,  "city": "Paris",    "headline": "Eurozone financial news"},
    ]
    for fb in fallbacks:
        if fb["city"] not in seen_cities and len(markers) < 8:
            markers.append(fb)

    topic_label = {
        "world": "WORLD", "tech": "TECHNOLOGY",
        "india": "INDIA", "business": "BUSINESS"
    }.get(topic, "WORLD")

    now = datetime.now()
    current_date = now.strftime("%B %d, %Y").upper()
    current_time = now.strftime("%H:%M:%S")
    n_articles = len(articles)

    markers_json  = json.dumps(markers)
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
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --red:#e63c3c;--red-dim:rgba(230,60,60,0.12);--orange:#ff7b00;
  --cyan:#00d4ff;--green:#00ff88;
  --bg:#06090d;--panel:#080c12;
  --border:rgba(230,60,60,0.2);--border-b:rgba(230,60,60,0.5);
  --text:#c5cdd8;--dim:#5a6472;
  --mono:'Share Tech Mono',monospace;--display:'Orbitron',sans-serif;
}}
body{{background:var(--bg);font-family:var(--mono);color:var(--text);overflow:hidden;height:100vh;width:100vw}}
body::before{{content:'';position:fixed;inset:0;background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,0.07) 2px,rgba(0,0,0,0.07) 4px);pointer-events:none;z-index:9999}}

/* TOP BAR */
#topbar{{position:fixed;top:0;left:0;right:0;height:52px;background:rgba(6,9,13,0.97);border-bottom:1px solid var(--border-b);display:flex;align-items:center;justify-content:space-between;padding:0 24px;z-index:1000}}
.brand{{display:flex;align-items:center;gap:14px}}
.brand-logo{{font-family:var(--display);font-size:13px;font-weight:900;letter-spacing:4px;color:var(--red);text-shadow:0 0 20px rgba(230,60,60,0.6)}}
.brand-sep{{width:1px;height:24px;background:var(--border-b)}}
.brand-sub{{font-size:10px;letter-spacing:3px;color:var(--dim)}}
.topbar-right{{display:flex;align-items:center;gap:20px}}
.live-badge{{display:flex;align-items:center;gap:6px;font-size:9px;letter-spacing:2px;color:var(--green)}}
.live-dot{{width:7px;height:7px;background:var(--green);border-radius:50%;box-shadow:0 0 8px var(--green);animation:livePulse 1.4s ease-in-out infinite}}
@keyframes livePulse{{0%,100%{{opacity:1;box-shadow:0 0 0 0 rgba(0,255,136,0.5)}}50%{{opacity:.7;box-shadow:0 0 0 8px rgba(0,255,136,0)}}}}
.topbar-date{{font-size:10px;color:var(--dim);letter-spacing:2px}}
#clock{{font-family:var(--display);font-size:14px;color:var(--cyan);letter-spacing:3px;text-shadow:0 0 12px rgba(0,212,255,0.5)}}

/* MAP */
#map{{position:fixed;top:52px;left:0;right:320px;bottom:64px;z-index:1}}
.leaflet-container{{background:#06090d!important}}
#map-grid{{position:fixed;top:52px;left:0;right:320px;bottom:64px;pointer-events:none;z-index:2;background:linear-gradient(rgba(230,60,60,0.025) 1px,transparent 1px),linear-gradient(90deg,rgba(230,60,60,0.025) 1px,transparent 1px);background-size:60px 60px}}
#map-grid::before,#map-grid::after{{content:'';position:absolute;width:20px;height:20px;border-color:var(--red);border-style:solid;opacity:.4}}
#map-grid::before{{top:8px;left:8px;border-width:2px 0 0 2px}}
#map-grid::after{{bottom:8px;right:8px;border-width:0 2px 2px 0}}

/* RIGHT PANEL */
#news-panel{{position:fixed;top:52px;right:0;width:320px;bottom:64px;background:var(--panel);border-left:1px solid var(--border);display:flex;flex-direction:column;z-index:100}}
.panel-header{{padding:12px 16px;border-bottom:1px solid var(--border);display:flex;align-items:center;gap:10px}}
.panel-title{{font-family:var(--display);font-size:9px;letter-spacing:3px;color:var(--red)}}
.panel-count{{margin-left:auto;font-size:9px;color:var(--dim);letter-spacing:1px}}
#news-feed{{flex:1;overflow-y:auto;padding:10px;scrollbar-width:thin;scrollbar-color:var(--border) transparent}}
#news-feed::-webkit-scrollbar{{width:3px}}
#news-feed::-webkit-scrollbar-thumb{{background:var(--border-b);border-radius:2px}}
.news-card{{background:var(--red-dim);border:1px solid var(--border);border-left:2px solid var(--red);border-radius:3px;padding:10px 12px;margin-bottom:8px;font-size:11px;line-height:1.55;color:var(--text);opacity:0;transform:translateX(12px);animation:cardIn 0.4s ease forwards;transition:all .2s}}
.news-card:hover{{background:rgba(230,60,60,0.15);border-left-color:var(--orange);color:#e2e8f0}}
.card-index{{font-size:9px;color:var(--red);letter-spacing:2px;margin-bottom:5px;font-family:var(--display)}}
@keyframes cardIn{{to{{opacity:1;transform:translateX(0)}}}}

/* CORNER SUMMARY */
#summary-box{{position:fixed;bottom:72px;left:12px;width:340px;background:rgba(6,9,13,0.92);border:1px solid var(--border-b);border-radius:4px;padding:12px 16px;z-index:500;backdrop-filter:blur(10px)}}
.summary-label{{font-family:var(--display);font-size:8px;letter-spacing:3px;color:var(--red);margin-bottom:8px}}
.summary-text{{font-size:10px;line-height:1.7;color:var(--text)}}

/* TICKER */
#ticker{{position:fixed;bottom:0;left:0;right:0;height:64px;background:rgba(6,9,13,0.97);border-top:1px solid var(--border-b);display:flex;align-items:center;overflow:hidden;z-index:1000}}
.ticker-label{{background:var(--red);color:#fff;padding:0 16px;height:100%;display:flex;align-items:center;font-family:var(--display);font-size:9px;font-weight:700;letter-spacing:2px;white-space:nowrap;flex-shrink:0}}
.ticker-div{{width:1px;height:100%;background:linear-gradient(180deg,transparent,var(--red),transparent);flex-shrink:0}}
#ticker-vp{{flex:1;overflow:hidden;height:100%;display:flex;align-items:center}}
#ticker-track{{display:flex;align-items:center;white-space:nowrap}}
.ticker-item{{font-size:12px;color:var(--text);padding:0 36px;letter-spacing:.3px}}
.ticker-sep{{color:var(--red);margin:0 4px;opacity:.7}}
@keyframes tickerScroll{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}

/* MARKERS */
.friday-marker{{width:14px;height:14px;background:var(--red);border-radius:50%;border:2px solid rgba(230,60,60,.3);animation:markerRing 2s ease-out infinite}}
@keyframes markerRing{{0%{{box-shadow:0 0 0 0 rgba(230,60,60,.7)}}70%{{box-shadow:0 0 0 14px rgba(230,60,60,0)}}100%{{box-shadow:0 0 0 0 rgba(230,60,60,0)}}}}
.leaflet-tooltip{{background:rgba(6,9,13,.95)!important;border:1px solid var(--border-b)!important;color:var(--text)!important;font-family:var(--mono)!important;font-size:11px!important;border-radius:3px!important;max-width:220px!important;padding:8px 12px!important;box-shadow:0 0 16px rgba(230,60,60,.25)!important;line-height:1.5!important}}
.leaflet-tooltip-top::before{{border-top-color:rgba(230,60,60,.5)!important}}
.tt-city{{color:var(--red);font-family:'Orbitron',sans-serif;font-size:10px;letter-spacing:1px;display:block;margin-bottom:4px}}
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
    <div class="live-badge"><div class="live-dot"></div>LIVE FEED</div>
    <div class="topbar-date">{current_date}</div>
    <div id="clock">{current_time}</div>
  </div>
</div>

<div id="map"></div>
<div id="map-grid"></div>

<div id="news-panel">
  <div class="panel-header">
    <div class="live-dot"></div>
    <div class="panel-title">BREAKING NEWS</div>
    <div class="panel-count" id="story-count">{n_articles} STORIES</div>
  </div>
  <div id="news-feed"></div>
</div>

<div id="summary-box">
  <div class="summary-label">▸ INTEL SUMMARY</div>
  <div class="summary-text" id="summary-text"></div>
</div>

<div id="ticker">
  <div class="ticker-label">FRIDAY INTEL</div>
  <div class="ticker-div"></div>
  <div id="ticker-vp"><div id="ticker-track"></div></div>
</div>

<script>
const ARTICLES = {articles_json};
const MARKERS  = {markers_json};

// Clock
function tick(){{const n=new Date(),p=v=>String(v).padStart(2,'0');document.getElementById('clock').textContent=`${{p(n.getHours())}}:${{p(n.getMinutes())}}:${{p(n.getSeconds())}}`;}}
setInterval(tick,1000);tick();

// Map
const map=L.map('map',{{zoomControl:false,attributionControl:false,center:[20,12],zoom:2.3,minZoom:1.5,maxZoom:6}});
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png',{{maxZoom:19}}).addTo(map);

// Markers
MARKERS.forEach((m,i)=>{{
  const icon=L.divIcon({{className:'',html:`<div class="friday-marker" style="animation-delay:${{i*0.35}}s"></div>`,iconSize:[14,14],iconAnchor:[7,7]}});
  L.marker([m.lat,m.lng],{{icon}}).addTo(map)
    .bindTooltip(`<span class="tt-city">${{m.city}}</span>${{m.headline}}`,{{direction:'top',permanent:false,offset:[0,-4]}});
}});

// News panel
const feed=document.getElementById('news-feed');
ARTICLES.forEach((a,i)=>{{
  const c=document.createElement('div');
  c.className='news-card';
  c.style.animationDelay=`${{i*0.08}}s`;
  c.innerHTML=`<div class="card-index">STORY ${{String(i+1).padStart(2,'0')}}</div>${{a}}`;
  feed.appendChild(c);
}});

// Typewriter summary
const lines=[
  "Scanning {n_articles} intelligence sources...",
  "Cross-referencing geopolitical data...",
  ARTICLES.slice(0,2).join(' · '),
];
let li=0,ci=0;
const el=document.getElementById('summary-text');
function type(){{
  if(li>=lines.length){{li=0;el.textContent='';}}
  if(ci<lines[li].length){{el.textContent+=lines[li][ci++];setTimeout(type,28);}}
  else{{setTimeout(()=>{{li++;ci=0;el.textContent='';type();}},2600);}}
}}
setTimeout(type,600);

// Ticker
const track=document.getElementById('ticker-track');
[...ARTICLES,...ARTICLES].forEach(a=>{{
  const s=document.createElement('span');s.className='ticker-item';
  s.innerHTML=`${{a}}<span class="ticker-sep">◆</span>`;
  track.appendChild(s);
}});
setTimeout(()=>{{const dur=track.scrollWidth/90;track.style.animation=`tickerScroll ${{dur}}s linear infinite`;}},200);

// Auto-scroll news panel
setTimeout(()=>{{let d=1;setInterval(()=>{{feed.scrollTop+=d*0.4;if(feed.scrollTop>=feed.scrollHeight-feed.clientHeight)d=-1;if(feed.scrollTop<=0)d=1;}},40);}},5000);
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
    print(f"[WorldNews] 🌍 Monitor opened → {out_path}")