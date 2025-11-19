from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import logging

# --- BOT SETTINGS ---
BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"
CHANNEL_ID = -1003258379804
# ---------------------

logging.basicConfig(level=logging.INFO)

# Temporary storage for comments: key = channel message_id, value = list of comments
confession_comments = {}

# --- /start command ---
async def start(update: Update, context):
    welcome_text = (
        "👋 Welcome to *DBU Vent Space*!\n\n"
        "A safe, anonymous space for students to vent, confess, or share anything on their mind.\n\n"
        "🔒 Your privacy is fully protected — your identity will never be revealed.\n\n"
        "📬 How it works:\n"
        "• Send me a message → I post it anonymously in the channel.\n"
        "• Click 'Comments' under a post to read or add anonymous comments privately.\n\n"
        "Please be respectful. No hate speech or private info sharing."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- Handle new confession ---
async def handle_message(update: Update, context):
    user_text = update.message.text

    # Inline button for channel post
    keyboard = [[InlineKeyboardButton("💬 Comments", callback_data="comments")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    send_text = (
        "────────────────\n"
        "📩 *Anonymous Confession*\n\n"
        f"{user_text}\n"
        "────────────────"
    )

    # Send confession to the channel only
    msg = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=send_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Initialize comments list
    confession_comments[msg.message_id] = []

    await update.message.reply_text("Your confession has been posted anonymously ✔️")

# --- Handle inline button clicks ---
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id  # send all interactions privately

    if query.data == "comments":
        # Open bot privately with confession text + buttons
        confession_text = query.message.text
        keyboard = [
            [
                InlineKeyboardButton("📖 Read Comments", callback_data=f"read_{query.message.message_id}"),
                InlineKeyboardButton("✏️ Add Comment", callback_data=f"add_{query.message.message_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 *Confession:*\n\n{confession_text}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

    elif query.data.startswith("read_"):
        confession_id = int(query.data.split("_")[1])
        comments = confession_comments.get(confession_id, [])
        if comments:
            text = "💬 *Comments:*\n\n" + "\n\n".join(comments)
        else:
            text = "No comments yet."
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="Markdown")

    elif query.data.startswith("add_"):
        confession_id = int(query.data.split("_")[1])
        context.user_data["awaiting_comment"] = confession_id
        await context.bot.send_message(
            chat_id=user_id,
            text="Please type your comment. It will be added anonymously."
        )

# --- Handle user comment input ---
async def handle_comment_input(update: Update, context):
    confession_id = context.user_data.get("awaiting_comment")
    if confession_id:
        comment_text = update.message.text
        confession_comments[confession_id].append(comment_text)

        await update.message.reply_text("Your anonymous comment has been added ✔️")
        context.user_data["awaiting_comment"] = None

# --- Main bot setup ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command
    app.add_handler(CommandHandler("start", start))

    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment_input))

    app.run_polling()

if __name__ == "__main__":
    main()
