from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq
from json import load, dump
import datetime
from dotenv import load_dotenv
import os
from googlesearch import search

load_dotenv()

app = Flask(__name__)
CORS(app)

Username = os.getenv("Username", "User")
Assistantname = os.getenv("Assistantname", "Assistant")
GroqAPIKey = os.getenv("GroqAPIKey")

if not GroqAPIKey:
    raise Exception("GroqAPIKey missing in .env")

client = Groq(api_key=GroqAPIKey)

System = f"""Hello, I am {Username}, You are a very accurate and advanced AI chatbot named {Assistantname} which has real-time up-to-date information from the internet.
*** Provide Answers In a Professional Way, make sure to add full stops, commas, question marks, and use proper grammar.***
*** Just answer the question from the provided data in a professional way. ***"""

# Load or init chat history
CHATLOG_PATH = r"Data\ChatLog.json"
try:
    with open(CHATLOG_PATH, "r") as f:
        messages = load(f)
except:
    with open(CHATLOG_PATH, "w") as f:
        dump([], f)
    messages = []

def GoogleSearch(query):
    results = list(search(query, advanced=True, num_results=5))
    answer = ""
    for i in results:
        answer += f"Title: {i.title}\nDescription: {i.description}\n\n"
    answer += "[end]"
    return answer

def AnswerModifier(answer):
    lines = answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def Information():
    now = datetime.datetime.now()
    return (f"Use This Real-Time Information if needed:\n"
            f"Day: {now.strftime('%A')}\n"
            f"Date: {now.strftime('%d')}\n"
            f"Month: {now.strftime('%B')}\n"
            f"Year: {now.strftime('%Y')}\n"
            f"Time: {now.strftime('%H')} hours:{now.strftime('%M')} minutes:{now.strftime('%S')} seconds.\n")

def RealtimeSearchEngine(prompt):
    global messages

    with open(CHATLOG_PATH, "r") as f:
        messages = load(f)

    # Append current user query to messages
    messages.append({"role": "user", "content": prompt})

    # Get Google search context (you may want to append as system or assistant message)
    search_context = GoogleSearch(prompt)

    # Build system + context + messages for prompt
    full_messages = [
        {"role": "system", "content": System},
        {"role": "system", "content": Information()},
        {"role": "system", "content": search_context},
    ] + messages

    # Call Groq chat completion (stream=False for simplicity here)
    completion = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=full_messages,
        max_tokens=2048,
        temperature=0.7,
        top_p=1,
        stream=False
    )

    answer = completion.choices[0].message.content.strip()

    messages.append({"role": "assistant", "content": answer})

    with open(CHATLOG_PATH, "w") as f:
        dump(messages, f, indent=4)

    return AnswerModifier(answer)

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({'answer': 'Please provide a prompt.'}), 400

        answer = RealtimeSearchEngine(prompt)
        return jsonify({'answer': answer})
    except Exception as e:
        print("Error in /api/chat:", e)
        return jsonify({'answer': 'Internal server error occurred.'}), 500

@app.route('/')
def index():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
