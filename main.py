import os
from flask import Flask, render_template_string, request, jsonify
from google import genai

# --- 1. SETUP AI ---
# This safely pulls the key from Render's environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

client = None
if GEMINI_API_KEY:
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        print("AI Client initialized successfully.")
    except Exception as e:
        print(f"Error setting up client: {e}")
else:
    print("CRITICAL ERROR: API Key is missing.")

# --- 2. SETUP FLASK ---
app = Flask(__name__)

# --- 3. HTML INTERFACE (Mobile Optimized UI) ---
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Pathu's AI</title>
    <style>
        /* Mobile Reset & Base Setup */
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; 
            background-color: #e5ddd5; /* WhatsApp Web style background */
            display: flex; 
            justify-content: center; 
            height: 100dvh; /* Dynamic viewport handles mobile browser bars */
        }
        
        /* Main Container */
        .chat-container { 
            width: 100%; 
            max-width: 480px; 
            background: #ffffff; 
            display: flex; 
            flex-direction: column; 
            height: 100dvh;
            box-shadow: 0 0 20px rgba(0,0,0,0.05);
        }

        /* Header */
        .header { 
            background: #007aff; /* iOS Blue */
            color: white; 
            padding: 16px 20px; 
            text-align: center; 
            font-size: 1.1rem;
            font-weight: 600; 
            box-shadow: 0 1px 4px rgba(0,0,0,0.1);
            z-index: 10;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        /* Message Area */
        .messages { 
            flex: 1; 
            padding: 20px 15px; 
            overflow-y: auto; 
            display: flex; 
            flex-direction: column; 
            gap: 15px; 
            background-color: #f3f4f6;
            scroll-behavior: smooth;
        }
        /* Hide Scrollbar for cleaner look */
        .messages::-webkit-scrollbar { display: none; }
        .messages { -ms-overflow-style: none; scrollbar-width: none; }

        /* Bubbles */
        .message { 
            padding: 12px 16px; 
            max-width: 80%; 
            word-wrap: break-word; 
            font-size: 0.95rem;
            line-height: 1.4;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
            animation: fadeIn 0.3s ease-in-out;
        }
        .user { 
            background: #007aff; 
            color: white; 
            align-self: flex-end; 
            border-radius: 18px 18px 4px 18px; /* Native chat tail */
        }
        .bot { 
            background: #e9ecef; 
            color: #212529; 
            align-self: flex-start; 
            border-radius: 18px 18px 18px 4px; /* Native chat tail */
        }

        /* Formatting inside bot messages (Bold, lists, etc) */
        .bot b { color: #000; font-weight: 600; }
        .bot br { display: block; margin-bottom: 6px; content: ""; }

        /* Input Area */
        .input-area { 
            display: flex; 
            padding: 12px 15px; 
            /* Safe area prevents iPhone home bar overlap */
            padding-bottom: max(12px, env(safe-area-inset-bottom)); 
            background: #f8f9fa; 
            border-top: 1px solid #dee2e6;
            align-items: center;
            gap: 10px;
        }
        
        /* Font size must be 16px to stop iOS Safari from auto-zooming! */
        input { 
            flex: 1; 
            padding: 12px 18px; 
            border: 1px solid #ccc; 
            border-radius: 24px; 
            outline: none; 
            font-size: 16px; 
            background: white;
            transition: border-color 0.2s;
        }
        input:focus { border-color: #007aff; }

        button { 
            background: #007aff; 
            color: white; 
            border: none; 
            border-radius: 50%; 
            width: 44px; 
            height: 44px; 
            display: flex;
            justify-content: center;
            align-items: center;
            cursor: pointer; 
            transition: transform 0.1s, background 0.2s;
        }
        button:active { transform: scale(0.92); background: #0056b3; }
        
        /* Send Icon SVG */
        .send-icon { width: 20px; height: 20px; fill: white; margin-left: -2px; }

        /* Animations */
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
        
        /* Bouncing Loading Dots */
        .typing-indicator { display: flex; gap: 4px; padding: 4px 0; align-items: center; justify-content: center; height: 18px;}
        .dot { width: 6px; height: 6px; background-color: #888; border-radius: 50%; animation: bounce 1.4s infinite ease-in-out both; }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        @keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
    </style>
</head>
<body>
<div class="chat-container">
    <div class="header">
        🤖 Pathu's AI
    </div>
    <div class="messages" id="chat-box">
        <div class="message bot">Hello! I am ready to chat.</div>
    </div>
    <div class="input-area">
        <input type="text" id="user-input" placeholder="Message..." onkeypress="handleEnter(event)">
        <button onclick="sendMessage()" aria-label="Send">
            <svg class="send-icon" viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
    </div>
</div>
<script>
    // Simple markdown parser to handle Gemini's bold text and line breaks
    function formatBotText(text) {
        let formattedText = text.replace(/\\*\\*(.*?)\\*\\*/g, '<b>$1</b>'); // Handle **bold**
        formattedText = formattedText.replace(/\\*/g, ''); // Remove stray asterisks
        formattedText = formattedText.replace(/\\n/g, '<br>'); // Handle new lines
        return formattedText;
    }

    async function sendMessage() {
        let input = document.getElementById("user-input");
        let chatBox = document.getElementById("chat-box");
        let text = input.value.trim();
        if (!text) return;

        // User Message
        chatBox.innerHTML += `<div class="message user">${text}</div>`;
        input.value = "";
        
        // Animated Typing Indicator
        let loadingId = "loading-" + Date.now();
        chatBox.innerHTML += `
            <div class="message bot" id="${loadingId}">
                <div class="typing-indicator">
                    <div class="dot"></div><div class="dot"></div><div class="dot"></div>
                </div>
            </div>`;
        chatBox.scrollTop = chatBox.scrollHeight;

        try {
            let response = await fetch("/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text })
            });
            
            let data = await response.json();
            
            // Format and update response
            document.getElementById(loadingId).innerHTML = formatBotText(data.reply);
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
    user_data = request.json
    if not user_data or "message" not in user_data:
        return jsonify({"reply": "Error: No message received."})
    
    user_message = user_data["message"]

    if not client:
        return jsonify({"reply": "Error: API Client is not initialized."})

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_message
        )
        return jsonify({"reply": response.text})
        
    except Exception as e:
        print(f"------------ ERROR ------------")
        print(e)
        print(f"-------------------------------")
        return jsonify({"reply": f"Error: {str(e)}"})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)




