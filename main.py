import os
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai

# --- 1. SETUP AI ---
# I have inserted your key here.
GEMINI_API_KEY = "GEMINI_API_KEY"

# Configure the API
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        # We try to use the faster 'flash' model first
        model = genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        print(f"Error loading Flash model: {e}")
        # Fallback to Pro if Flash fails
        model = genai.GenerativeModel('gemini-pro')
else:
    print("CRITICAL ERROR: API Key is missing.")

# --- 2. SETUP FLASK ---
app = Flask(__name__)

# --- 3. HTML INTERFACE ---
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Chatbot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; height: 100vh; margin: 0; }
        .chat-container { width: 100%; max-width: 400px; background: white; display: flex; flex-direction: column; height: 100%; }
        .header { background: #007bff; color: white; padding: 15px; text-align: center; font-weight: bold; }
        .messages { flex: 1; padding: 10px; overflow-y: auto; display: flex; flex-direction: column; gap: 10px; }
        .message { padding: 8px 12px; border-radius: 15px; max-width: 80%; word-wrap: break-word; }
        .user { background: #007bff; color: white; align-self: flex-end; }
        .bot { background: #e0e0e0; color: black; align-self: flex-start; }
        .input-area { display: flex; padding: 10px; border-top: 1px solid #ddd; }
        input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 20px; outline: none; }
        button { margin-left: 10px; padding: 10px 15px; background: #007bff; color: white; border: none; border-radius: 20px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
<div class="chat-container">
    <div class="header">🤖 Pathu's AI</div>
    <div class="messages" id="chat-box">
        <div class="message bot">Hello! I am ready to chat.</div>
    </div>
    <div class="input-area">
        <input type="text" id="user-input" placeholder="Type..." onkeypress="handleEnter(event)">
        <button onclick="sendMessage()">Send</button>
    </div>
</div>
<script>
    async function sendMessage() {
        let input = document.getElementById("user-input");
        let chatBox = document.getElementById("chat-box");
        let text = input.value.trim();
        if (!text) return;

        // Add user message
        chatBox.innerHTML += `<div class="message user">${text}</div>`;
        input.value = "";
        
        // Add loading indicator
        let loadingId = "loading-" + Date.now();
        chatBox.innerHTML += `<div class="message bot" id="${loadingId}">...</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            let response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            
            let data = await response.json();
            
            // Replace loading with actual response
            document.getElementById(loadingId).innerText = data.reply;
        } catch (error) {
            document.getElementById(loadingId).innerText = "Error: Could not reach server.";
        }
        
        chatBox.scrollTop = chatBox.scrollHeight;
    }
    
    function handleEnter(event) { if (event.key === "Enter") sendMessage(); }
</script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_CODE)

@app.route('/chat', methods=['POST'])
def chat():
    # 1. Check for User Message
    user_data = request.json
    if not user_data or "message" not in user_data:
        return jsonify({"reply": "Error: No message received."})
    
    user_message = user_data["message"]

    # 2. Check for API Key
    if not GEMINI_API_KEY:
        return jsonify({"reply": "Error: API Key is missing in the code."})

    # 3. Try to Generate Content
    try:
        response = model.generate_content(user_message)
        
        # Check if response was blocked by safety filters
        if response.prompt_feedback and response.prompt_feedback.block_reason:
            return jsonify({"reply": "Error: Response blocked by safety filters."})
            
        return jsonify({"reply": response.text})
        
    except Exception as e:
        # This will print the EXACT error to your command prompt so you can debug
        print(f"------------ ERROR ------------")
        print(e)
        print(f"-------------------------------")
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == '__main__':
    # This block allows it to run on Render or Locally
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

