import os
from flask import Flask, render_template_string, request, jsonify
import google.generativeai as genai

# --- 1. SETUP AI ---
# Get the key from the cloud secrets (or paste it directly if testing locally)
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
    except:
        model = genai.GenerativeModel('gemini-pro')
else:
    print("ERROR: GEMINI_API_KEY is missing!")

# --- 2. SETUP FLASK WEBSITE ---
app = Flask(__name__)

# This is the HTML Code for your website (The Look & Feel)
HTML_CODE = """
<!DOCTYPE html>
<html>
<head>
    <title>My AI Chatbot</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: sans-serif; background-color: #f4f4f9; display: flex; justify-content: center; height: 100vh; margin: 0; }
        .chat-container { width: 400px; background: white; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); overflow: hidden; display: flex; flex-direction: column; }
        .header { background: #007bff; color: white; padding: 15px; text-align: center; font-weight: bold; }
        .messages { flex: 1; padding: 10px; overflow-y: auto; height: 400px; display: flex; flex-direction: column; gap: 10px; }
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
    <div class="header">🤖 Gemini AI Chat</div>
    <div class="messages" id="chat-box">
        <div class="message bot">Hello! I am your AI assistant. Ask me anything!</div>
    </div>
    <div class="input-area">
        <input type="text" id="user-input" placeholder="Type a message..." onkeypress="handleEnter(event)">
        <button onclick="sendMessage()">Send</button>
    </div>
</div>

<script>
    async function sendMessage() {
        let input = document.getElementById("user-input");
        let chatBox = document.getElementById("chat-box");
        let text = input.value.trim();
        
        if (!text) return;

        // 1. Show User Message
        chatBox.innerHTML += `<div class="message user">${text}</div>`;
        input.value = "";
        chatBox.scrollTop = chatBox.scrollHeight;

        // 2. Show "Thinking..."
        let loadingId = "loading-" + Date.now();
        chatBox.innerHTML += `<div class="message bot" id="${loadingId}">Thinking...</div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        // 3. Send to Python Backend
        let response = await fetch("/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: text })
        });

        let data = await response.json();
        
        // 4. Update Chat with AI Response
        document.getElementById(loadingId).innerText = data.reply;
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function handleEnter(event) {
        if (event.key === "Enter") sendMessage();
    }
</script>

</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_CODE)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get("message")
    
    if not GEMINI_API_KEY:
        return jsonify({"reply": "Error: API Key is missing on server."})

    try:
        response = model.generate_content(user_message)
        return jsonify({"reply": response.text})
    except Exception as e:
        return jsonify({"reply": "I am having trouble connecting to the brain right now."})

# Run the website
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
