# DkRapria Music Player

## Current implementation
- Public player page: `/music-player.html`
- Track data: `/music-player.json`
- Maximum visible tracks: 5
- Audio files are not included yet; the playlist is intentionally empty until the owner supplies the selected MP3 files and confirms the five tracks.
- Full catalogue links to `/songs.html`.

## Add a track
1. Upload an audio file you own or are licensed to distribute into `/music/` (MP3 recommended for the first version).
2. Add an optional cover image into `/music/covers/`.
3. Add an object to the `tracks` array in `music-player.json`:
   ```json
   {
     "title": "Song title",
     "artist": "DkRapria",
     "audio": "/music/song-file.mp3",
     "cover": "/music/covers/song-cover.webp"
   }
   ```
4. Keep no more than five objects in `tracks`. The page also enforces a five-track display limit.

## Advertising
Audio pre-roll and AdSense are disabled in the initial build. Audio pre-roll needs an approved audio/VAST provider and its tag/configuration. AdSense display ads need the publisher's approved client ID and ad slot IDs. AdSense display ads must not be represented as audio pre-roll. Never commit API tokens, passwords, or private ad credentials to this public repository.

## GitHub hosting note
This is a lightweight first version for a small five-track catalogue, not a high-volume streaming CDN. Keep audio files reasonably compressed and move them to dedicated object storage/CDN if traffic or bandwidth grows.
