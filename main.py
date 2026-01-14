import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler, CallbackQueryHandler, ContextTypes

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, name TEXT, age INTEGER, bio TEXT, photo_id TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS likes 
                      (liker_id INTEGER, liked_id INTEGER, PRIMARY KEY(liker_id, liked_id))''')
    conn.commit()
    conn.close()

# --- States ---
NAME, AGE, BIO, PHOTO = range(4)

# Registration Start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to TgTinder! 🔥\nWhat is your Name?")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['name'] = update.message.text
    await update.message.reply_text(f"Nice! And your Age?")
    return AGE

async def get_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['age'] = update.message.text
    await update.message.reply_text("Share a short Bio about yourself:")
    return BIO

async def get_bio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['bio'] = update.message.text
    await update.message.reply_text("Finally, send me your profile Photo!")
    return PHOTO

async def get_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo_id = update.message.photo[-1].file_id
    user_id = update.effective_user.id
    
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)",
                   (user_id, context.user_data['name'], context.user_data['age'], context.user_data['bio'], photo_id))
    conn.commit()
    conn.close()

    await update.message.reply_text("Profile saved! Use /discovery to find people.")
    return ConversationHandler.END

# Discovery Logic
async def discovery(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('dating_bot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id != ? ORDER BY RANDOM() LIMIT 1", (update.effective_user.id,))
    target = cursor.fetchone()
    conn.close()

    if target:
        uid, name, age, bio, photo = target
        keyboard = [[InlineKeyboardButton("❤️ Like", callback_data=f"like_{uid}"),
                     InlineKeyboardButton("❌ Skip", callback_data="skip")]]
        await update.message.reply_photo(photo=photo, caption=f"{name}, {age}\n{bio}", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("No more profiles yet!")

# Main Function
def main():
    init_db()
    # Yahan apna Token daalein (Ya use karein environment variable)
    TOKEN = "YOUR_TELEGRAM_BOT_TOKEN" 
    app = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_age)],
            BIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_bio)],
            PHOTO: [MessageHandler(filters.PHOTO, get_photo)],
        },
        fallbacks=[]
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler('discovery', discovery))
    app.run_polling()

if __name__ == '__main__':
    main()
  
