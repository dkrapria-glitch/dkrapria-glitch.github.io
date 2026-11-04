import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

CHANNEL_ID = "UCbdxiWPCAgIkncfXCj6u1qQ"
FEED_URL = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = "latest-songs.json"

# Known devotional terms and existing devotional catalogue IDs are excluded.
DEVOTIONAL_TERMS = (
    "bhajan", "bhakti", "mantra", "chalisa", "aarti", "arti", "vrat",
    "katha", "shiv", "shiva", "mahakal", "krishna", "radha", "hanuman",
    "mata", "devi", "durga", "ram ji", "sita", "geeta", "meditation",
    "relax music", "sukh dhund", "marzi rab", "rab ki", "sab dekh raha"
)
KNOWN_DEVOTIONAL_IDS = {
    "IBhqbDGe8a8", "pKo-YZtCPqo", "XtZwYw7i_4k"
}

def main():
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "DkRapriaSiteBot/1.0"})
    with urllib.request.urlopen(req, timeout=30) as response:
        xml_data = response.read()
    root = ET.fromstring(xml_data)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    songs = []
    for entry in root.findall("a:entry", ns):
        title = (entry.findtext("a:title", default="", namespaces=ns)).strip()
        video_id = (entry.findtext("yt:videoId", default="", namespaces=ns)).strip()
        published = (entry.findtext("a:published", default="", namespaces=ns)).strip()
        if not title or not video_id or video_id in KNOWN_DEVOTIONAL_IDS:
            continue
        normalized = title.casefold()
        if any(term in normalized for term in DEVOTIONAL_TERMS):
            continue
        songs.append({
            "title": title,
            "videoId": video_id,
            "url": f"https://music.youtube.com/watch?v={video_id}",
            "thumbnail": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
            "published": published
        })
    songs.sort(key=lambda x: x["published"], reverse=True)
    payload = {
        "source": "DkRapria YouTube Music Topic channel",
        "channelId": CHANNEL_ID,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "songs": songs[:8]
    }
    with open(OUT, "w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)
    print(f"Saved {len(payload['songs'])} non-devotional songs from Topic feed")

if __name__ == "__main__":
    main()
