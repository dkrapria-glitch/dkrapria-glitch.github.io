import json
from datetime import datetime, timezone
from pathlib import Path

import yt_dlp

CHANNEL_URL = "https://www.youtube.com/@dkrapria/videos"
SECONDARY_CHANNEL_URL = "https://www.youtube.com/channel/UCokS_ORFCf6Ql_LBAFF1Ohg/videos"
SECONDARY_CHANNEL_CREDIT = "DkRapria Originals"
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

# Verified distributor release not consistently surfaced in either channel feed.
# Keep it in Latest Songs and preserve only the direct URLs confirmed for this recording.
MANUAL_RELEASES = {
    "ivQeQKEF6qs": {
        "title": "Aurat Hone Ka Dard Part 2 Main Begunah Thi",
        "displayTitle": "औरत होने का दर्द 💔 | Part 2 – मैं बेगुनाह थी",
        "url": "https://music.youtube.com/watch?v=ivQeQKEF6qs",
        "thumbnail": "https://i.ytimg.com/vi/ivQeQKEF6qs/hqdefault.jpg",
        "published": "2026-11-05T00:00:00Z",
        "releaseDate": "2026-11-06",
        "duration": "5:19",
        "genre": "Hindi Sad Song",
        "language": "Hindi",
        "artist": "DkRapria",
        "platforms": {
            "youtubeMusic": "https://music.youtube.com/watch?v=ivQeQKEF6qs",
            "youtube": "https://www.youtube.com/watch?v=ivQeQKEF6qs",
            "appleMusic": "https://music.apple.com/in/album/aurat-hone-ka-dard-part-2-main-begunah-thi/6830467425?i=6830467426",
            "soundcloud": "https://soundcloud.com/dkrapria/aurat-hone-ka-dard-part-2-main",
            "deezer": "https://www.deezer.com/us/track/4389723821",
            "pandora": "https://www.pandora.com/artist/dk-rapria/aurat-hone-ka-dard-part-2-main-begunah-thi/aurat-hone-ka-dard-part-2-main-begunah-thi/TRgcn926ZhrJXnw",
            "gaana": "https://gaana.com/song/aurat-hone-ka-dard-part-2-main-begunah-thi"
        }
    }
}


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
        secondary_channel = None
        try:
            secondary_channel = ydl.extract_info(
                SECONDARY_CHANNEL_URL, download=False
            )
        except Exception as error:
            print(f"Could not read SunoDk channel: {error}")

    if not channel:
        raise RuntimeError("Could not read the DkRapria YouTube channel.")

    # Include only non-devotional SunoDk uploads whose title explicitly credits
    # DkRapria. This keeps unrelated channel videos out of the artist feed.
    entries = [
        (entry, "DkRapria", False)
        for entry in (channel.get("entries") or [])
        if entry
    ]
    if secondary_channel:
        entries.extend(
            (entry, "SunoDk", True)
            for entry in (secondary_channel.get("entries") or [])
            if entry
        )

    candidates = []
    seen_video_ids = set()
    for entry, source_channel, is_secondary in entries:
        title = (entry.get("title") or "").strip()
        video_id = (entry.get("id") or "").strip()
        if not title or not video_id or video_id in seen_video_ids:
            continue
        seen_video_ids.add(video_id)

        if is_secondary and "dkrapria originals" not in title.casefold():
            continue
        if is_devotional(title, video_id):
            continue

        previous = previous_by_id.get(video_id, {})
        published = get_published(entry) or previous.get("published", "")
        candidates.append({
            "entry": entry,
            "source_channel": source_channel,
            "video_id": video_id,
            "title": title,
            "previous": previous,
            "published": published,
        })

    # Flat playlist entries sometimes omit upload_date. Enrich the newest
    # eligible candidates from each channel before sorting the combined feed.
    per_channel_counts = {}
    with yt_dlp.YoutubeDL(detail_options) as detail_ydl:
        for candidate in candidates:
            source_channel = candidate["source_channel"]
            per_channel_counts[source_channel] = (
                per_channel_counts.get(source_channel, 0) + 1
            )
            if candidate["published"] or per_channel_counts[source_channel] > MAX_SONGS:
                continue
            try:
                details = detail_ydl.extract_info(
                    f"https://www.youtube.com/watch?v={candidate['video_id']}",
                    download=False,
                )
                if details:
                    candidate["published"] = get_published(details)
            except Exception as error:
                print(
                    f"Could not read upload date for "
                    f"{candidate['video_id']}: {error}"
                )

    candidates.sort(
        key=lambda item: (
            item["previous"].get("releaseDate")
            or item["published"]
            or ""
        ),
        reverse=True,
    )
    songs = []

    for candidate in candidates[:MAX_SONGS]:
        entry = candidate["entry"]
        source_channel = candidate["source_channel"]
        video_id = candidate["video_id"]
        title = candidate["title"]
        previous = candidate["previous"]
        published = candidate["published"]

        # A channel video ID is a direct YouTube URL, not proof of a
        # matching YouTube Music track. Preserve only manually verified
        # YouTube Music watch URLs; never synthesize them from video IDs.
        platforms = (
            dict(previous.get("platforms", {}))
            if isinstance(previous.get("platforms"), dict)
            else {}
        )
        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
        platforms["youtube"] = youtube_url

        music_url = platforms.get("youtubeMusic")
        if not isinstance(music_url, str) or not music_url.startswith(
            "https://music.youtube.com/watch?v="
        ):
            music_url = ""

        primary_url = music_url or platforms["youtube"]
        song = dict(previous)
        song.update({
            "title": title,
            "videoId": video_id,
            "url": primary_url,
            "thumbnail": get_thumbnail(entry, video_id, previous),
            "published": published,
        })

        duration = entry.get("duration")
        if duration and not song.get("duration"):
            try:
                total_seconds = int(float(duration))
                song["duration"] = (
                    f"{total_seconds // 60}:{total_seconds % 60:02d}"
                )
            except (TypeError, ValueError, OverflowError):
                pass

        if source_channel == "SunoDk":
            song["artist"] = SECONDARY_CHANNEL_CREDIT
            song["sourceChannel"] = "SunoDk"
            song.setdefault("genre", "Hindi Original Song")
            song.setdefault("language", "Hindi")
        else:
            song.pop("artist", None)
            song.pop("sourceChannel", None)

        song["platforms"] = platforms
        songs.append(song)

    # If the secondary channel is temporarily unavailable, retain previously
    # verified SunoDk uploads rather than silently dropping them from the feed.
    present_ids = {song.get("videoId") for song in songs}
    for video_id, previous in previous_by_id.items():
        if previous.get("sourceChannel") == "SunoDk" and video_id not in present_ids:
            songs.append(previous)
            present_ids.add(video_id)

    # Retain verified distributor releases even when their Topic/channel upload
    # is not returned by the two channel feeds. Manual metadata overrides stale data.
    for video_id, metadata in MANUAL_RELEASES.items():
        manual_song = dict(previous_by_id.get(video_id, {}))
        manual_song.update(metadata)
        manual_song["videoId"] = video_id
        manual_song["platforms"] = dict(metadata["platforms"])
        manual_song["url"] = (
            manual_song["platforms"].get("youtubeMusic")
            or manual_song["platforms"].get("youtube")
            or ""
        )
        songs = [song for song in songs if song.get("videoId") != video_id]
        songs.append(manual_song)

    if not songs:
        raise RuntimeError(
            "The channel was read, but no eligible songs were found. "
            "Keeping the previous website feed unchanged."
        )

    # Prefer verified distributor release dates; fall back to the YouTube upload date.
    songs.sort(key=lambda item: item.get("releaseDate") or item.get("published") or "", reverse=True)
    payload = {
        "source": "DkRapria official YouTube channel + SunoDk uploads credited to DkRapria Originals + verified distributor releases",
        "channelUrl": CHANNEL_URL,
        "sourceChannels": [CHANNEL_URL, SECONDARY_CHANNEL_URL],
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
