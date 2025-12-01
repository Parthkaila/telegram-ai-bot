import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import google.generativeai as genai
from keep_alive import keep_alive  # Import the fake web server

# --- 1. GET KEYS FROM ENVIRONMENT (SECURE) ---
# We do NOT paste keys here. We set them in the Cloud Dashboard later.
TELEGRAM_TOKEN = os.environ.get("8294266435:AAElxkl1zD4Sr7q1qwTG6JCZUYnAZCq0ha8")
GEMINI_API_KEY = os.environ.get("AIzaSyA8siylIYyMACLcci0ydQi3Rmrxbd52IXk")

# --- 2. CONFIGURE AI ---
genai.configure(api_key=GEMINI_API_KEY)

try:
    # Use 1.5-flash for best free tier stability
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    print("Error loading model. Defaulting to pro.")
    model = genai.GenerativeModel('gemini-pro')

# --- 3. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am online 24/7.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        response = model.generate_content(user_text)
        ai_reply = response.text

        if len(ai_reply) > 4000:
            for x in range(0, len(ai_reply), 4000):
                await update.message.reply_text(ai_reply[x:x+4000])
        else:
            await update.message.reply_text(ai_reply)
            
    except Exception as e:
        print(f"AI Error: {e}")
        await update.message.reply_text("I encountered an error processing that request.")

def main():
    # 1. Start the fake web server so the cloud doesn't shut us down
    keep_alive()

    # 2. Start the Bot
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=20.0, read_timeout=20.0)
    
    # Check if token exists
    if not TELEGRAM_TOKEN:
        print("Error: TELEGRAM_TOKEN not found in environment variables!")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).request(trequest).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()