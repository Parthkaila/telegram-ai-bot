import os
import google.generativeai as genai
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
from google.generativeai.types import HarmCategory, HarmBlockThreshold # NEW IMPORTS
from keep_alive import keep_alive

# --- 1. SECURELY LOAD KEYS ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Keys not found! Check Render Environment Variables.")

# --- 2. CONFIGURE AI ---
genai.configure(api_key=GEMINI_API_KEY)

# --- 3. SAFETY SETTINGS (Prevent "I'm sorry" errors) ---
# This tells Google: "Don't block my messages unless they are VERY bad."
safety_settings = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
}

# Load Model
try:
    print("Attempting to load gemini-2.5-flash...")
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception:
    try:
        print("Switching to gemini-2.0-flash...")
        model = genai.GenerativeModel('gemini-2.0-flash')
    except Exception:
        model = genai.GenerativeModel('gemini-pro')

# --- 4. BOT FUNCTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("I am online 24/7 with Safety Filters reduced.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text
    chat_id = update.effective_chat.id
    
    await context.bot.send_chat_action(chat_id=chat_id, action='typing')

    try:
        # We pass the safety_settings here to stop blocking answers
        response = model.generate_content(user_text, safety_settings=safety_settings)
        
        # Check if the response was blocked safely
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            await update.message.reply_text(f"Blocked by Google Safety: {response.prompt_feedback.block_reason}")
            return

        ai_reply = response.text

        # Split long messages
        if len(ai_reply) > 4000:
            for x in range(0, len(ai_reply), 4000):
                await update.message.reply_text(ai_reply[x:x+4000])
        else:
            await update.message.reply_text(ai_reply)
            
    except Exception as e:
        print(f"Error: {e}")
        # DEBUG MODE: This sends the ACTUAL error to Telegram so you can see it.
        # Once your bot is perfect, you can change this back to "I'm sorry..."
        await update.message.reply_text(f"System Error: {e}")

def main():
    keep_alive()
    trequest = HTTPXRequest(connection_pool_size=8, connect_timeout=20.0, read_timeout=20.0)
    app = Application.builder().token(TELEGRAM_TOKEN).request(trequest).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
