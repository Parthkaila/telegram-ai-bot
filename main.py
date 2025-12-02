import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from keep_alive import keep_alive  # Imports the web server from File 2

# --- 1. SECURELY LOAD KEYS ---
# We use the VARIABLE NAMES here. Render injects the actual keys safely.
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# Safety Check: If keys are missing, stop immediately
if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("CRITICAL ERROR: Keys not found! Go to Render Dashboard -> Environment and add 'TELEGRAM_TOKEN' and 'GEMINI_API_KEY'.")

# --- 2. CONFIGURE AI ---
genai.configure(api_key=GEMINI_API_KEY)

# UPDATED: We use 2.5 Flash because your list confirmed you have access to it.
try:
    print("Attempting to load gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as first_error:
    try:
        # Fallback to 2.0 Flash if 2.5 isn't ready
        print(f"2.5 Flash failed ({first_error}). Trying gemini-2.0-flash...")
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception as second_error:
        # Final fallback to standard Pro
        print(f"2.0 Flash failed ({second_error}). Defaulting to gemini-pro.")
        model = genai.GenerativeModel('gemini-pro')

# --- 3. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am online 24/7 using Gemini 2.5 Flash.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    # Show "typing..." status so user knows bot is thinking
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    try:
        # Generate response from Google AI
        response = model.generate_content(user_text)
        ai_reply = response.text

        # --- HANDLE LONG MESSAGES ---
        # Telegram has a 4096 character limit. We split long replies.
        if len(ai_reply) > 4000:
            for x in range(0, len(ai_reply), 4000):
                await update.message.reply_text(ai_reply[x:x+4000])
        else:
            await update.message.reply_text(ai_reply)
            
    except Exception as e:
        print(f"Error: {e}")
        # If the content was blocked (Safety), tell the user
        if "blocked" in str(e).lower():
            await update.message.reply_text("I cannot answer that due to safety guidelines.")
        else:
            await update.message.reply_text("I'm sorry, I'm having trouble processing that right now.")

def main():
    # 1. Start the Background Web Server (Required for Render)
    keep_alive()

    # 2. Configure Telegram Connection
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=20.0, read_timeout=20.0)
    
    # 3. Build the App
    app = Application.builder().token(TELEGRAM_TOKEN).request(trequest).build()

    # 4. Add Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 5. Run
    print("Bot is running... Press Ctrl+C to stop.")
    app.run_polling()

if __name__ == "__main__":
    main()
