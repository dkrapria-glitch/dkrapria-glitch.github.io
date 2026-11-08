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
    "sab dekh raha", "sukh ko dhoondhan", "sukh dhoondhan", "balak bana de",
    "ri maa", "pooja", "puja", "jagran"
)
KNOWN_DEVOTIONAL_IDS = {"IBhqbDGe8a8", "pKo-YZtCPqo", "XtZwYw7i_4k"}


def is_devotional(title, video_id):
    normalized = title.casefold()
    return video_id in KNOWN_DEVOTIONAL_IDS or any(
        term in normalized for term in DEVOTIONAL_TERMS
    )


def get_published(entry):
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


def get_thumbnail(entry, video_id, previous):
    thumbnail = entry.get("thumbnail")
    if isinstance(thumbnail, list):
        thumbnail = next(
            (item.get("url") for item in reversed(thumbnail)
             if isinstance(item, dict) and item.get("url")),
            "",
        )
    return thumbnail or previous.get("thumbnail") or (
        f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
    )


def load_previous():
    if not OUT.exists():
        return {}
    try:
        data = json.loads(OUT.read_text(encoding="utf-8"))
        entries = data.get("songs", []) if isinstance(data, dict) else []
        return {
            item["videoId"]: item
            for item in entries
            if isinstance(item, dict) and item.get("videoId")
        }
    except (OSError, json.JSONDecodeError):
        return {}


def main():
    previous_by_id = load_previous()
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
    detail_options = {
        "skip_download": True,
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "socket_timeout": 12,
        "retries": 1,
        "extractor_retries": 1,
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        channel = ydl.extract_info(CHANNEL_URL, download=False)

    if not channel:
        raise RuntimeError("Could not read the DkRapria YouTube channel.")

    entries = channel.get("entries") or []
    songs = []
    seen_video_ids = set()

    with yt_dlp.YoutubeDL(detail_options) as detail_ydl:
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

            previous = previous_by_id.get(video_id, {})
            published = get_published(entry) or previous.get("published", "")
            if not published:
                try:
                    details = detail_ydl.extract_info(
                        f"https://www.youtube.com/watch?v={video_id}",
                        download=False,
                    )
                    if details:
                        published = get_published(details)
                except Exception as error:
                    print(f"Could not read upload date for {video_id}: {error}")

            # Preserve manually verified YouTube Music release playlists and
            # platform URLs; never replace them with guessed video-ID URLs.
            music_url = previous.get("url", "")
            if not isinstance(music_url, str) or not music_url.startswith(
                "https://music.youtube.com/"
            ):
                music_url = f"https://music.youtube.com/watch?v={video_id}"

            song = dict(previous)
            song.update({
                "title": title,
                "videoId": video_id,
                "url": music_url,
                "thumbnail": get_thumbnail(entry, video_id, previous),
                "published": published,
            })
            if isinstance(previous.get("platforms"), dict):
                song["platforms"] = dict(previous["platforms"])
            songs.append(song)

            if len(songs) >= MAX_SONGS:
                break

    if not songs:
        raise RuntimeError(
            "The channel was read, but no eligible songs were found. "
            "Keeping the previous website feed unchanged."
        )

    # Sorting is stable, so entries with no date retain the channel's newest-first order.
    songs.sort(key=lambda item: item.get("published") or "", reverse=True)
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
