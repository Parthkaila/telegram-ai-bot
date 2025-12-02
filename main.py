from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import google.generativeai as genai
import os

# --- 1. PASTE YOUR KEYS HERE ---
TELEGRAM_TOKEN = os.environ.get("8294266435:AAElxkl1zD4Sr7q1qwTG6JCZUYnAZCq0ha8")
GEMINI_API_KEY = os.environ.get("AIzaSyAc9IE3eQTXJ8fgzveizLoG5ptjSj3xFXk")

# --- 2. CONFIGURE AI (Using the Standard Free Model) ---
genai.configure(api_key=GEMINI_API_KEY)

# We are FORCING 'gemini-1.5-flash' because it has a generous free tier.
# If this gives an error, you must update your library (see below).
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
# or the alias:
# model = genai.GenerativeModel('gemini-flash-latest')

except Exception as e:
    print("Error loading model. Defaulting to legacy model.")
    model = genai.GenerativeModel('gemini-pro')

# --- 3. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am ready. I am using the standard Flash model.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    
    # Show "typing..." status
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')

    try:
        # Send text to Google AI
        response = model.generate_content(user_text)
        ai_reply = response.text

        # --- FIX FOR LONG MESSAGES ---
        # Telegram limit is 4096 chars. We split the message if it's too big.
        if len(ai_reply) > 4000:
            # Split the text into chunks of 4000 characters
            for x in range(0, len(ai_reply), 4000):
                await update.message.reply_text(ai_reply[x:x+4000])
        else:
            # If it's short enough, just send it
            await update.message.reply_text(ai_reply)
            
    except Exception as e:
        print(f"AI Error: {e}")
        # If the specific error is 'Message is too long', we catch it here just in case
        if "Message is too long" in str(e):
             await update.message.reply_text("The answer was too long for Telegram to handle!")
        else:
             await update.message.reply_text("Sorry, I encountered an error.")

def main():
    # Connection settings
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=20.0, read_timeout=20.0)

    app = Application.builder().token(TELEGRAM_TOKEN).request(trequest).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running with 'gemini-1.5-flash'...")
    print("Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()


