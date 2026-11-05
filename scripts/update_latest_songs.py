import json
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp

CHANNEL_URL = "https://www.youtube.com/@dkrapria/videos"
OUT = Path("latest-songs.json")
MAX_RESULTS = 40
MAX_SONGS = 8

# Keep devotional releases in the separate Bhakti Songs section.
DEVOTIONAL_TERMS = (
    "bhajan", "bhakti", "devotional", "mantra", "jaap", "jap", "chalisa",
    "aarti", "arti", "stotra", "kavach", "kirtan", "vrat", "katha",
    "shiv", "shiva", "mahakal", "mahadev", "bhole", "krishna", "radha",
    "hanuman", "bajrang", "mata", "devi", "durga", "santoshi", "ganesh",
    "ganesha", "shani", "surya", "vishnu", "laxmi", "lakshmi",
    "brihaspati", "ram ji", "ram naam", "sita", "geeta", "gita",
    "meditation", "relax music", "sukh dhund", "marzi rab", "rab ki",
    "sab dekh raha", "pooja", "puja", "jagran"
)
KNOWN_DEVOTIONAL_IDS = {"IBhqbDGe8a8", "pKo-YZtCPqo", "XtZwYw7i_4k"}


def is_devotional(title, video_id):
    normalized = title.casefold()
    return video_id in KNOWN_DEVOTIONAL_IDS or any(
        term in normalized for term in DEVOTIONAL_TERMS
    )


def main():
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
        raise RuntimeError("Could not read the DkRapria YouTube channel.")

    entries = channel.get("entries") or []
    songs = []
    seen_video_ids = set()
    for entry in entries:
        if not entry:
            continue
        title = (entry.get("title") or "").strip()
        video_id = (entry.get("id") or "").strip()
        if not title or not video_id or video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)
        if is_devotional(title, video_id):
            continue

        upload_date = entry.get("upload_date")
        if upload_date and len(upload_date) == 8:
            published = (
                f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                "T00:00:00Z"
            )
        else:
            timestamp = entry.get("timestamp")
            published = (
                datetime.fromtimestamp(timestamp, timezone.utc).isoformat()
                if timestamp else ""
            )

        thumbnail = entry.get("thumbnail") or (
            f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        )
        songs.append({
            "title": title,
            "videoId": video_id,
            "url": f"https://music.youtube.com/watch?v={video_id}",
            "thumbnail": thumbnail,
            "published": published,
        })

    if not songs:
        raise RuntimeError(
            "The channel was read, but no eligible songs were found. "
            "Keeping the previous website feed unchanged."
        )

    songs.sort(key=lambda item: item["published"], reverse=True)
    payload = {
        "source": "DkRapria official YouTube channel",
        "channelUrl": CHANNEL_URL,
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "songs": songs[:MAX_SONGS],
    }

    OUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Saved {len(payload['songs'])} latest non-devotional releases.")


if __name__ == "__main__":
    main()
