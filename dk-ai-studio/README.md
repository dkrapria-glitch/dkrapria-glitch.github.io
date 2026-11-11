# DK AI Studio — Telegram Worker

This folder contains an isolated Cloudflare Worker for the private DK AI Studio Telegram bot. It does not modify the website's root files.

## What works in this version

- Private Telegram bot access for owner ID `872647685` (configurable)
- Hindi and English AI text replies through the OpenAI Responses API
- `/start`, `/help`, `/id`, and `/status` commands
- Telegram webhook secret validation
- Long reply splitting for Telegram message limits

Image, video, voice cloning, speech generation, and music generation are **not enabled yet**. Those require separate provider integrations and credentials; this starter does not pretend those features are active.

## Cloudflare setup

Create a Worker and paste `worker.js` into its editor, or deploy this file with Wrangler.

Add these **Worker secrets** in Cloudflare → Worker → Settings → Variables and Secrets:

- `BOT_TOKEN` — token from BotFather
- `TELEGRAM_WEBHOOK_SECRET` — a private random string (letters and numbers; 32+ characters recommended)
- `OPENAI_API_KEY` — OpenAI API key

Optional plain-text variables:

- `OWNER_ID` — defaults to `872647685`
- `AI_MODEL` — defaults to `gpt-4o-mini`

After deployment, your Worker URL will look like:

`https://YOUR-WORKER.workers.dev`

Set the Telegram webhook from a trusted terminal (replace the placeholders):

```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
  -d "url=https://YOUR-WORKER.workers.dev/telegram" \
  -d "secret_token=<TELEGRAM_WEBHOOK_SECRET>"
```

Check webhook status:

```bash
curl "https://api.telegram.org/bot<BOT_TOKEN>/getWebhookInfo"
```

Test the Worker health URL by opening `https://YOUR-WORKER.workers.dev/`. It should show:

`DK AI Studio Worker is online.`

## Security

- Never put bot tokens or API keys in this repository.
- Add credentials only in Cloudflare Worker Secrets.
- Do not share screenshots that expose tokens.
