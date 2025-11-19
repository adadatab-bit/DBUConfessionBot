from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, MessageHandler, filters, CommandHandler, CallbackQueryHandler
import logging

# --- BOT SETTINGS ---
BOT_TOKEN = "8284563442:AAHdtUvMaVAQr62vijuM6XUS7YDKW-88gEc"
CHANNEL_ID = -1003258379804
BOT_USERNAME = "DBU_Vent_Space_Bot"  # Replace with your bot username
# ---------------------

logging.basicConfig(level=logging.INFO)

# Temporary storage for comments: key = confession_id, value = list of comments
confession_comments = {}
# Map user submissions to confession_id for reference
confession_ids = {}

# --- /start command ---
async def start(update: Update, context):
    welcome_text = (
        "👋 Welcome to *DBU Vent Space*!\n\n"
        "A safe, anonymous space for students to vent, confess, or share anything on their mind.\n\n"
        "🔒 Your privacy is fully protected — your identity will never be revealed.\n\n"
        "📬 How it works:\n"
        "• Send me a message → I post it anonymously in the channel.\n"
        "• Click 'Comments' under a post in the channel → opens this bot to read/add comments.\n\n"
        "Have fun."
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# --- Handle new confession ---
async def handle_message(update: Update, context):
    user_text = update.message.text

    # Post confession to channel with URL button opening the bot
    keyboard = [
        [InlineKeyboardButton("💬 Comments", url=f"https://t.me/{BOT_USERNAME}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    send_text = (
        "────────────────\n"
        "📩 *Anonymous Confession*\n\n"
        f"{user_text}\n"
        "────────────────"
    )

    # Send confession to channel
    msg = await context.bot.send_message(
        chat_id=CHANNEL_ID,
        text=send_text,
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

    # Store confession_id for comments
    confession_id = msg.message_id
    confession_comments[confession_id] = []
    confession_ids[update.message.from_user.id] = confession_id

    await update.message.reply_text("✅ Your confession has been posted anonymously!")

# --- Handle inline button clicks in bot (Read/Add Comments) ---
async def button_click(update: Update, context):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    # Check if user is adding or reading comments
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

# --- Command to show last confession with buttons (for demonstration) ---
async def show_last_confession(update: Update, context):
    user_id = update.message.from_user.id
    # Get the last confession posted by this user
    confession_id = confession_ids.get(user_id)
    if not confession_id:
        await update.message.reply_text("You haven't posted any confessions yet.")
        return

    # Build buttons
    keyboard = [
        [
            InlineKeyboardButton("📖 Read Comments", callback_data=f"read_{confession_id}"),
            InlineKeyboardButton("✏️ Add Comment", callback_data=f"add_{confession_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=user_id,
        text=f"📩 *Confession:*\n\nCheck your confession below.",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# --- Main bot setup ---
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Command
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("myconfession", show_last_confession))

    # Handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_comment_input))

    app.run_polling()

if __name__ == "__main__":
    main()
