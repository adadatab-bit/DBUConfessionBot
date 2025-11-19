from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import logging

# --- BOT SETTINGS ---
BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"
CHANNEL_ID = -1003258379804
BOT_USERNAME = "dbu_ventspace_bot"
# ---------------------

logging.basicConfig(level=logging.INFO)

# Store confessions and comments
confession_counter = 1000  # Starting number for confessions
confessions = {}           # key: number, value: text
confession_comments = {}   # key: number, value: list of comments

# --- /start command ---
async def start(update: Update, context):
    welcome_text = (
        "👋 Welcome to *DBU Vent Space*!\n\n"
        "A safe, anonymous space for students to vent, confess, or share anything.\n\n"
        "🔒 Your privacy is fully protected.\n\n"
        "📬 How it works:\n"
        "• Send me a confession → I post it anonymously in the channel.\n"
        "• Click 'Comments' in the channel → opens this bot.\n"
        "• Send the confession number here → view/add comments.\n\n"
        "be sure to have fun!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- Handle new confession ---
async def handle_message(update: Update, context):
    global confession_counter
    user_text = update.message.text.strip()

    # Check if user sent a confession number (for comments)
    if user_text.isdigit() and int(user_text) in confessions:
        confession_id = int(user_text)
        confession_text = confessions[confession_id]

        keyboard = [
            [
                InlineKeyboardButton("📖 Read Comments", callback_data=f"read_{confession_id}"),
                InlineKeyboardButton("✏️ Add Comment", callback_data=f"add_{confession_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"📩 *Confession #{confession_id}:*\n\n{confession_text}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
        return

    # Otherwise, treat as a new confession
    confession_counter += 1
    confession_id = confession_counter

    confessions[confession_id] = user_text
    confession_comments[confession_id] = []

    # Post to channel
    send_text = (
        f"#{confession_id}\n"
        "📩 *Anonymous Confession*\n\n"
        f"{user_text}"
    )
    keyboard = [
        [InlineKeyboardButton("💬 Comments", url=f"https://t.me/{BOT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=send_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    await update.message.reply_text(f"✅ Your confession has been posted anonymously as #{confession_id}!")

# --- Handle inline button clicks (Read/Add Comment) ---
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data.startswith("read_"):
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
            text="✏️ Please type your comment. It will be added anonymously."
        )

# --- Handle user comment input ---
async def handle_comment_input(update: Update, context):
    confession_id = context.user_data.get("awaiting_comment")
    if confession_id:
        comment_text = update.message.text
        confession_comments[confession_id].append(comment_text)
        await update.message.reply_text("✅ Your anonymous comment has been added!")
        context.user_data["awaiting_comment"] = None

# --- Main bot setup ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))

    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment_input))

    app.run_polling()

if __name__ == "__main__":
    main()
