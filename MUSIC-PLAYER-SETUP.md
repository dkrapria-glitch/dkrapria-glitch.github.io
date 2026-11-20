# DkRapria Music Player

## Current implementation

- Public player page: `/music-player.html`
- Track data: `/music-player.json`
- Maximum visible tracks: 5
- One MP3 is currently configured: **Happy Birthday Haryana** by DkRapria (3:34).
- Current audio file: `/songs/happy-birthday-haryana/happy-birthday-haryana.mp3` (5,181,840 bytes in the repository).
- The player reads `music-player.json` at runtime. Keep each track's `audio` path in sync with the uploaded file.
- The complete catalogue remains available at `/songs.html`.

## Add or replace a track

1. Upload an MP3 you own or are licensed to distribute. The current track uses a song-specific folder under `/songs/`; keep the same pattern for additional files.
2. Add an optional cover image to the repository or use a verified artwork URL.
3. Add or update an object in the `tracks` array in `music-player.json`:

   ```json
   {
     "title": "Song title",
     "artist": "DkRapria",
     "audio": "/songs/song-folder/song-file.mp3",
     "cover": "/path/to/cover.webp",
     "duration": "3:34",
     "category": "Hindi"
   }
   ```

4. Keep no more than five objects in `tracks`. The page also enforces a five-track display limit.
5. Verify the MP3 path, duration, playback and mobile controls after deployment.

## Advertising

Audio pre-roll and AdSense are disabled. Audio pre-roll needs an approved audio/VAST provider and its tag/configuration. AdSense display ads need the publisher's approved client ID and ad slot IDs. AdSense display ads must not be represented as audio pre-roll. Never commit API tokens, passwords, or private ad credentials to this public repository.

## GitHub hosting note

This is a lightweight first version for a small five-track catalogue, not a high-volume streaming CDN. Keep audio files reasonably compressed and move them to dedicated object storage/CDN if traffic or bandwidth grows.
