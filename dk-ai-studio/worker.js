/**
 * DK AI Studio — Telegram + OpenAI Cloudflare Worker
 * Required Worker secrets: BOT_TOKEN, TELEGRAM_WEBHOOK_SECRET, OPENAI_API_KEY
 * Optional variable: OWNER_ID (defaults to 872647685), AI_MODEL (defaults to gpt-4o-mini)
 */

const OWNER_ID_DEFAULT = "872647685";

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (request.method === "GET" && url.pathname === "/") {
      return new Response("DK AI Studio Worker is online.", {
        headers: { "content-type": "text/plain; charset=utf-8" }
      });
    }

    if (request.method !== "POST" || url.pathname !== "/telegram") {
      return new Response("Not found", { status: 404 });
    }

    if (!env.BOT_TOKEN || !env.TELEGRAM_WEBHOOK_SECRET || !env.OPENAI_API_KEY) {
      return new Response("Worker secrets are not configured.", { status: 500 });
    }

    const suppliedSecret = request.headers.get("X-Telegram-Bot-Api-Secret-Token");
    if (suppliedSecret !== env.TELEGRAM_WEBHOOK_SECRET) {
      return new Response("Unauthorized", { status: 401 });
    }

    let update;
    try {
      update = await request.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    const message = update.message;
    if (!message?.chat?.id || !message?.from?.id) {
      return new Response("OK");
    }

    const ownerId = String(env.OWNER_ID || OWNER_ID_DEFAULT);
    if (String(message.from.id) !== ownerId) {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "यह निजी DK AI Studio बॉट है। आपको इसका उपयोग करने की अनुमति नहीं है।");
      return new Response("OK");
    }

    const text = (message.text || message.caption || "").trim();
    if (!text) {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "अभी मैं टेक्स्ट मैसेज संभाल सकता हूँ। फोटो, वीडियो, वॉइस और म्यूजिक फीचर अगले इंटीग्रेशन में जोड़ेंगे।");
      return new Response("OK");
    }

    if (text === "/start") {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "नमस्ते! DK AI Studio तैयार है।\n\nमुझसे हिंदी या English में सवाल पूछें।\n/help — कमांड और जानकारी\n/id — Telegram ID");
      return new Response("OK");
    }

    if (text === "/help") {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "DK AI Studio Commands\n/start — बॉट शुरू करें\n/help — मदद\n/id — आपकी Telegram ID\n\nसीधे कोई भी सवाल लिखें और AI से जवाब पाएँ।");
      return new Response("OK");
    }

    if (text === "/id") {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "आपकी Telegram ID: " + message.from.id);
      return new Response("OK");
    }

    if (text === "/status") {
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "DK AI Studio online है। टेक्स्ट AI सक्रिय है।");
      return new Response("OK");
    }

    await sendTelegramAction(env.BOT_TOKEN, message.chat.id, "typing");

    try {
      const aiResponse = await fetch("https://api.openai.com/v1/responses", {
        method: "POST",
        headers: {
          "Authorization": "Bearer " + env.OPENAI_API_KEY,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: env.AI_MODEL || "gpt-4o-mini",
          instructions: "You are DK AI Studio, a helpful assistant for DkRapria. Reply naturally in the language used by the user. Be concise, accurate, and practical.",
          input: text,
          max_output_tokens: 900
        })
      });

      const data = await aiResponse.json();
      if (!aiResponse.ok) {
        console.error("OpenAI API error:", JSON.stringify(data));
        await sendTelegram(env.BOT_TOKEN, message.chat.id,
          "AI सेवा में अभी समस्या है। कृपया थोड़ी देर बाद दोबारा कोशिश करें।");
        return new Response("OK");
      }

      const answer = extractOutputText(data) || "माफ़ कीजिए, इस बार जवाब नहीं मिल पाया।";
      await sendTelegramLong(env.BOT_TOKEN, message.chat.id, answer);
    } catch (error) {
      console.error("DK AI Studio error:", String(error));
      await sendTelegram(env.BOT_TOKEN, message.chat.id,
        "कनेक्शन में समस्या आई है। कृपया दोबारा कोशिश करें।");
    }

    return new Response("OK");
  }
};

function extractOutputText(data) {
  if (typeof data.output_text === "string") return data.output_text.trim();
  const parts = [];
  for (const item of data.output || []) {
    for (const content of item.content || []) {
      if (content.type === "output_text" && content.text) parts.push(content.text);
    }
  }
  return parts.join("\n").trim();
}

async function sendTelegram(token, chatId, text) {
  return fetch("https://api.telegram.org/bot" + token + "/sendMessage", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, text })
  });
}

async function sendTelegramLong(token, chatId, text) {
  const chunks = [];
  for (let i = 0; i < text.length; i += 3800) chunks.push(text.slice(i, i + 3800));
  for (const chunk of chunks) await sendTelegram(token, chatId, chunk);
}

async function sendTelegramAction(token, chatId, action) {
  return fetch("https://api.telegram.org/bot" + token + "/sendChatAction", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ chat_id: chatId, action })
  });
}
