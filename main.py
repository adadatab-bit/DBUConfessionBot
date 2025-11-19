from telegram.ext import Application, MessageHandler, filters, CommandHandler
from telegram import Update
import logging

# --- BOT SETTINGS ---
BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"  # <-- keep your token here
CHANNEL_ID = -1003258379804
# ---------------------

logging.basicConfig(level=logging.INFO)

# --- /start command ---
async def start(update: Update, context):
    welcome_text = (
        "👋 Welcome to *DBU Vent Space*! \n\n"
        "This bot allows students to anonymously share their thoughts, rants, "
        "confessions, or anything on their mind.\n\n"
        "📌 How it works:\n"
        "1. Send any message to this bot.\n"
        "2. Your message will be posted anonymously to our channel.\n"
        "3. Forward a message from the channel to reply anonymously.\n\n"
        "Feel free to start by sending your first message!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- Handle normal messages ---
async def handle_message(update: Update, context):
    if not update.message:
        return

    user_text = update.message.text

    send_text = (
        "────────────────\n"
        "📩 *Anonymous Confession*\n\n"
        f"{user_text}\n"
        "────────────────"
    )

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=send_text,
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "Your confession has been posted anonymously ✔️"
    )

# --- Handle forwarded messages (reply feature) ---
async def handle_forwarded(update: Update, context):
    if update.message.forward_from_chat:
        forwarded_text = update.message.text
        send_text = (
            "────────────────\n"
            "🔁 *Anonymous Reply*\n\n"
            f"{forwarded_text}\n"
            "────────────────"
        )
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=send_text,
            parse_mode="Markdown"
        )
        await update.message.reply_text("Your anonymous reply has been posted ✔️")

# --- Main bot setup ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded))
    
    app.run_polling()

if __name__ == "__main__":
    main()
