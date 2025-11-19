import json
import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
import logging
from fastapi import FastAPI, Request
import uvicorn

# ---------- BOT SETTINGS ----------
BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"
CHANNEL_ID = -1003258379804
BOT_USERNAME = "dbu_ventspace_bot"
DATA_FILE = "confessions.json"
PAD_WIDTH = 4  # zero-padding for 0001, 0002, etc.
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"  # Telegram webhook endpoint
PORT = int(os.environ.get("PORT", 8000))  # Render will provide PORT env
# -----------------------------------

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- Helpers ----------
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"counter": 0, "confessions": {}}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def next_id(data):
    data["counter"] = data.get("counter", 0) + 1
    return str(data["counter"]).zfill(PAD_WIDTH)

# ---------- Bot Handlers ----------
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if args:
        requested = args[0]
        if requested.isdigit():
            requested = str(requested).zfill(PAD_WIDTH)
        data = load_data()
        conf = data["confessions"].get(requested)
        if conf:
            keyboard = [
                [
                    InlineKeyboardButton("📖 Read Comments", callback_data=f"read_{requested}"),
                    InlineKeyboardButton("✏️ Add Comment", callback_data=f"add_{requested}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            text = f"📩 *Confession #{requested}:*\n\n{conf['text']}"
            await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)
            return
        else:
            await update.message.reply_text("❌ Sorry, this confession ID does not exist.")
            return

    # Normal home page
    welcome_text = (
        "👋 Welcome to *DBU Vent Space*!\n\n"
        "A safe, anonymous space for students to vent, confess, or share.\n\n"
        "🔒 Your privacy is protected — your identity will not be revealed.\n\n"
        "📬 How it works:\n"
        "1. Send me a confession — I'll post it anonymously in the channel with a number (e.g., #0001).\n"
        "2. Tap *Comments* under any channel post → opens this bot with the confession.\n"
        "3. Or open the bot and send the confession number (e.g., 0001) to view/add comments.\n\n"
        "Use /myconfession to see your last posted confession number."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id
    data = load_data()

    # User sends confession ID to view post
    if text.isdigit():
        key = str(text).zfill(PAD_WIDTH)
        conf = data["confessions"].get(key)
        if conf:
            keyboard = [
                [
                    InlineKeyboardButton("📖 Read Comments", callback_data=f"read_{key}"),
                    InlineKeyboardButton("✏️ Add Comment", callback_data=f"add_{key}"),
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                f"📩 *Confession #{key}:*\n\n{conf['text']}",
                parse_mode="Markdown",
                reply_markup=reply_markup,
            )
            return
        else:
            await update.message.reply_text("❌ This confession ID does not exist.")
            return

    # Handle awaiting comment
    awaiting = context.user_data.get("awaiting_comment")
    if awaiting:
        conf_id = awaiting
        comment_text = text
        data["confessions"][conf_id]["comments"].append(comment_text)
        save_data(data)
        await update.message.reply_text("✅ Your anonymous comment has been added!")
        context.user_data["awaiting_comment"] = None
        return

    # Treat as new confession
    conf_id = next_id(data)
    data["confessions"][conf_id] = {"text": text, "channel_message_id": None, "comments": []}

    post_text = f"#{conf_id}\n📩 *Anonymous Confession*\n\n{text}"
    url = f"https://t.me/{BOT_USERNAME}?start={conf_id}"
    keyboard = [[InlineKeyboardButton("💬 Comments", url=url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    msg = await context.bot.send_message(chat_id=CHANNEL_ID, text=post_text, parse_mode="Markdown", reply_markup=reply_markup)
    data["confessions"][conf_id]["channel_message_id"] = msg.message_id
    save_data(data)

    context.user_data["last_confession"] = conf_id
    await update.message.reply_text(f"✅ Your confession was posted anonymously as #{conf_id}!")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    payload = query.data
    data = load_data()

    if payload.startswith("read_"):
        conf_id = payload.split("_", 1)[1]
        conf = data["confessions"].get(conf_id)
        if not conf:
            await context.bot.send_message(chat_id=user_id, text="No such confession.")
            return
        comments = conf.get("comments", [])
        if comments:
            text = "💬 *Comments:*\n\n" + "\n\n".join(f"{i}. {c}" for i, c in enumerate(comments, 1))
        else:
            text = "No comments yet."
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")
        return

    if payload.startswith("add_"):
        conf_id = payload.split("_", 1)[1]
        if conf_id not in data["confessions"]:
            await context.bot.send_message(chat_id=user_id, text="No such confession.")
            return
        context.user_data["awaiting_comment"] = conf_id
        await context.bot.send_message(chat_id=user_id, text="✏️ Please type your comment. It will be added anonymously.")
        return

async def myconfession(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conf_id = context.user_data.get("last_confession")
    if not conf_id:
        await update.message.reply_text("You haven't posted a confession yet.")
        return
    await update.message.reply_text(f"Your last confession ID is #{conf_id}.")

# ---------- FastAPI Webhook Server ----------
app = FastAPI()
bot_app = Application.builder().token(BOT_TOKEN).build()
bot_app.add_handler(CommandHandler("start", start_command))
bot_app.add_handler(CommandHandler("myconfession", myconfession))
bot_app.add_handler(CallbackQueryHandler(callback_handler))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, bot_app.bot)
    await bot_app.update_queue.put(update)
    return {"ok": True}

# ---------- Main ----------
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    # Set webhook on startup
    import requests
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
    webhook_url = f"https://dbu-ventspace-bot.onrender.com{WEBHOOK_PATH}"
    r = requests.get(url, params={"url": webhook_url})
    print("Set webhook response:", r.text)
    uvicorn.run(app, host="0.0.0.0", port=PORT)
