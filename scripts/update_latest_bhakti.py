import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp

CHANNEL_URL = "https://www.youtube.com/channel/UCokS_ORFCf6Ql_LBAFF1Ohg/videos"
CHANNEL_NAME = "SunoDk"
OUT = Path("latest-bhakti.json")
MAX_RESULTS = 50
MAX_VIDEOS = 12

ENGLISH_DEVOTIONAL = re.compile(
    r"\b(?:bhakti|bhajan|devotional|spiritual|nirgun|mantra|jaap|jap|"
    r"chalisa|aarti|arti|stotra|kavach|kirtan|vrat|katha|shiv|shiva|"
    r"mahakal|mahadev|bholenath|bhole|krishna|radha|hanuman|bajrang|"
    r"mata|devi|durga|kali|santoshi|ganesh|ganesha|shani|surya|vishnu|"
    r"laxmi|lakshmi|brihaspati|ram|sita|geeta|gita|gayatri|meditation|"
    r"pooja|puja|jagran|satsang|hari|govind|gopal|shyam|radhe|om)\b",
    re.IGNORECASE,
)
ROMAN_PHRASES = re.compile(
    r"\b(?:sukh\s+ko\s+dhoondhan|sukh\s+dhoondhan|marzi\s+rab\s+ki|"
    r"rab\s+ki|sab\s+dekh\s+raha|balak\s+bana\s+de|ram\s+naam)\b",
    re.IGNORECASE,
)
HINDI_DEVOTIONAL_TERMS = (
    "भजन", "भक्ति", "मंत्र", "आरती", "शिव", "महादेव", "भोले", "कृष्ण",
    "राधा", "राम", "हनुमान", "माता", "देवी", "दुर्गा", "काली", "संतोषी",
    "शनिदेव", "सूर्य", "जाप", "जप", "ध्यान", "प्रभु", "भगवान", "ईश्वर",
    "हरि", "गोविंद", "गोपाल", "श्याम", "राधे", "विष्णु", "लक्ष्मी", "गायत्री",
    "स्तोत्र", "कवच", "कीर्तन", "व्रत", "कथा", "पूजा", "जगराता", "निर्गुण",
    "सत्संग", "मोको कहाँ ढूँढे", "सुख ढूंढन", "मर्जी रब की", "वो सब देख रहा",
    "मनने फेर ते बालक बना",
)
KNOWN_DEVOTIONAL_IDS = {"PDaqBlUkPJo"}

# Verified distributor releases linked to their exact SunoDk video cards.
# Keep only direct, title/artist-matched URLs; no search pages or guessed links.
MANUAL_RELEASES = {
    "pLJv-l_D_VQ": {
        "displayTitle": "राम जी राम जी, सबके बनाओ तुम बिगड़े काम जी",
        "artist": "DkRapria",
        "genre": "Hindi Devotional Bhajan",
        "language": "Hindi",
        "duration": "3:35",
        "releaseDate": "2026-11-11",
        "upc": "8909705839071",
        "platforms": {
            "youtube": "https://www.youtube.com/watch?v=pLJv-l_D_VQ",
            "youtubeMusic": "https://music.youtube.com/watch?v=959fRJPZph4",
            "songdew": "https://songdew.com/songs/ram-ji-ram-ji-sabke-banao-tum-bigde-kaam-ji-149355",
            "spotify": "https://open.spotify.com/album/6ZraErwI9fQFPusX4NRlgT",
            "amazonMusic": "https://music.amazon.com/albums/B0HQNMMHPP",
            "appleMusic": "https://music.apple.com/us/song/ram-ji-ram-ji-sabke-banao-tum-bigde-kaam-ji/6831526868",
            "deezer": "https://www.deezer.com/us/track/4395471691",
            "jiosaavn": "https://www.jiosaavn.com/song/ram-ji-ram-ji-sabke-banao-tum-bigde-kaam-ji/RSQlekNGRmo",
            "soundcloud": "https://soundcloud.com/dkrapria/ram-ji-ram-ji-sabke-banao-tum",
            "musicLink": "https://musiclink.one/album/dk-rapria/ram-ji-ram-ji-sabke-banao-tum-bigde-kaam-ji"
        }
    },
    "nh4bvuJ3JhE": {
        "displayTitle": "मैं मिट्टी का खिलौना प्रभु",
        "artist": "DkRapria",
        "genre": "Hindi Devotional Bhajan",
        "language": "Hindi",
        "duration": "5:52",
        "releaseDate": "2026-11-10",
        "upc": "8909705826637",
        "platforms": {
            "youtube": "https://www.youtube.com/watch?v=nh4bvuJ3JhE",
            "youtubeMusic": "https://music.youtube.com/watch?v=Cru3kLNUa-M",
            "appleMusic": "https://music.apple.com/us/song/main-mitti-ka-khilauna-prabhu/6831146774",
            "gaana": "https://gaana.com/song/main-mitti-ka-khilauna-prabhu",
            "soundcloud": "https://soundcloud.com/dkrapria/main-mitti-ka-khilauna-prabhu"
        }
    }
}


def is_devotional(title: str, video_id: str) -> bool:
    if video_id in KNOWN_DEVOTIONAL_IDS:
        return True
    return bool(
        ENGLISH_DEVOTIONAL.search(title)
        or ROMAN_PHRASES.search(title)
        or any(term in title for term in HINDI_DEVOTIONAL_TERMS)
    )


def get_published(entry: dict) -> str:
    upload_date = entry.get("upload_date")
    if upload_date and len(str(upload_date)) == 8:
        date = str(upload_date)
        return f"{date[:4]}-{date[4:6]}-{date[6:8]}T00:00:00Z"
    timestamp = entry.get("timestamp")
    if timestamp:
        try:
            return datetime.fromtimestamp(float(timestamp), timezone.utc).isoformat()
        except (TypeError, ValueError, OverflowError):
            pass
    return ""


def get_thumbnail(entry: dict, video_id: str) -> str:
    thumbnail = entry.get("thumbnail")
    if isinstance(thumbnail, list):
        thumbnail = next(
            (item.get("url") for item in reversed(thumbnail)
             if isinstance(item, dict) and item.get("url")),
            "",
        )
    return thumbnail or f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def main() -> None:
    options = {
        "extract_flat": "in_playlist",
        "playlistend": MAX_RESULTS,
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 30,
        "retries": 3,
        "extractor_retries": 3,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        channel = ydl.extract_info(CHANNEL_URL, download=False)

    if not channel:
        raise RuntimeError("Could not read the public SunoDk YouTube channel.")

    entries = channel.get("entries") or []
    if not entries:
        raise RuntimeError("SunoDk channel returned no video entries; keeping the previous feed.")

    videos = []
    seen_ids = set()
    for entry in entries:
        if not entry:
            continue
        title = html.unescape((entry.get("title") or "").strip())
        video_id = (entry.get("id") or "").strip()
        if not title or not video_id or video_id in seen_ids:
            continue
        seen_ids.add(video_id)
        if not is_devotional(title, video_id):
            continue
        videos.append({
            "videoId": video_id,
            "title": title,
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "thumbnail": get_thumbnail(entry, video_id),
            "published": get_published(entry),
        })

    # Flat playlist entries often omit upload dates and durations. Enrich the
    # newest eligible devotional uploads so the website can sort and label them.
    detail_options = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 12,
        "retries": 1,
        "extractor_retries": 1,
    }
    with yt_dlp.YoutubeDL(detail_options) as detail_ydl:
        for video in videos[:20]:
            try:
                details = detail_ydl.extract_info(video["url"], download=False)
                if not details:
                    continue
                video["published"] = get_published(details) or video["published"]
                if details.get("duration"):
                    total_seconds = int(float(details["duration"]))
                    video["duration"] = (
                        f"{total_seconds // 60}:{total_seconds % 60:02d}"
                    )
                if details.get("thumbnail"):
                    video["thumbnail"] = get_thumbnail(details, video["videoId"])
            except Exception as error:
                print(f"Could not enrich {video['videoId']}: {error}")

    # Attach verified distributor metadata after upload enrichment so release
    # dates and distributor durations remain authoritative.
    for video in videos:
        manual = MANUAL_RELEASES.get(video["videoId"])
        if manual:
            video.update(manual)

    videos.sort(
        key=lambda item: item.get("releaseDate") or item.get("published") or "",
        reverse=True,
    )
    videos = videos[:MAX_VIDEOS]

    if not videos and OUT.exists():
        try:
            previous = json.loads(OUT.read_text(encoding="utf-8"))
            videos = previous.get("videos", []) if isinstance(previous, dict) else []
        except (OSError, json.JSONDecodeError):
            videos = []
        print("No new matching devotional uploads; retaining the previous video cards.")

    payload = {
        "channel": CHANNEL_NAME,
        "channelId": "UCokS_ORFCf6Ql_LBAFF1Ohg",
        "channelUrl": "https://www.youtube.com/@sunodk",
        "updated": datetime.now(timezone.utc).isoformat(),
        "videos": videos,
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Saved {len(videos)} SunoDk devotional video cards.")


if __name__ == "__main__":
    main()
