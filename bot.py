import os
import requests
import json
from flask import Flask, request, jsonify
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import asyncio

app = Flask(__name__)

# ---------- CONFIG ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable not set")

API_BASE_URL = os.environ.get("API_BASE_URL", "https://xgi-api.onrender.com")

# ---------- BOT HANDLERS ----------
application = Application.builder().token(BOT_TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I can fetch Free Fire player info.\n"
        "Commands:\n"
        "/info <uid> – show player profile\n"
        "/wishlist <uid> – show wishlist items"
    )

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = context.args[0]
    except IndexError:
        await update.message.reply_text("Usage: /info <uid>")
        return

    try:
        int(uid)
    except ValueError:
        await update.message.reply_text("❌ Invalid UID – must be numeric.")
        return

    url = f"{API_BASE_URL}/info?uid={uid}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        if len(text) > 4000:
            text = text[:4000] + "\n... (truncated)"
        await update.message.reply_text(f"📊 Player Info for `{uid}`:\n```json\n{text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

async def wishlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = context.args[0]
    except IndexError:
        await update.message.reply_text("Usage: /wishlist <uid>")
        return

    try:
        int(uid)
    except ValueError:
        await update.message.reply_text("❌ Invalid UID – must be numeric.")
        return

    url = f"{API_BASE_URL}/wishlist?uid={uid}"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        text = json.dumps(data, indent=2, ensure_ascii=False)
        if len(text) > 4000:
            text = text[:4000] + "\n... (truncated)"
        await update.message.reply_text(f"🎁 Wishlist for `{uid}`:\n```json\n{text}\n```", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("info", info))
application.add_handler(CommandHandler("wishlist", wishlist))


# ---------- WEBHOOK ----------
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        json_data = request.get_json(force=True)
        update = Update.de_json(json_data, application.bot)
        asyncio.run(application.process_update(update))
        return '', 200
    except Exception as e:
        print(f"Webhook error: {e}")
        return str(e), 500

@app.route('/setwebhook', methods=['GET'])
def set_webhook():
    if not BOT_TOKEN:
        return "Bot token missing", 500
    host = request.headers.get('X-Forwarded-Host', request.host)
    scheme = request.headers.get('X-Forwarded-Proto', 'https')
    webhook_url = f"{scheme}://{host}/webhook"
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        result = asyncio.run(bot.set_webhook(webhook_url))
        return jsonify({"success": True, "webhook_url": webhook_url, "result": result.to_dict()})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "🤖 Telegram Bot is running!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
