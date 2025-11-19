from telegram.ext import Application, MessageHandler, filters
from telegram import Update
import logging

BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"
CHANNEL_ID = -1003258379804

logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context):
    if not update.message:
        return

    user_text = update.message.text

    send_text = f"📩 *Anonymous Confession:*\n\n{user_text}"

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=send_text,
        parse_mode="Markdown"
    )

    await update.message.reply_text(
        "Your confession has been posted anonymously ✔️"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
