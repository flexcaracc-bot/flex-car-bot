import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات من Environment Variables
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return 'Wrong token', 403

    data = request.get_json()
    # حماية الكود: التأكد من وجود رسالة نصية
    try:
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [{}])[0]
        
        if 'text' in messages:
            msg_body = messages['text']['body']
            sender_id = messages['from']
            
            # استدعاء Gemini
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            prompt = f"أنت بائع في Flex Car. أجب الزبون: {msg_body}"
            ai_res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]})
            answer = ai_res.json()['candidates'][0]['content']['parts'][0]['text']

            # إرسال الرد للواتساب
            send_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product": "whatsapp", "to": sender_id, "type": "text", "text": {"body": answer}}
            requests.post(send_url, json=payload, headers=headers)
            
    except Exception as e:
        print(f"Error: {e}") # سيظهر الخطأ في Logs لتعرفه
        
    return jsonify({"status": "ok"}), 200
