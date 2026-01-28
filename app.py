import os, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        return request.args.get("hub.challenge") if request.args.get("hub.verify_token") == os.environ.get('VERIFY_TOKEN') else ('Error', 403)

    data = request.get_json()
    print(f"--- رسالة جديدة وصلت: {data}") # سطر للتشخيص

    try:
        # استخراج الرسالة فقط إذا كانت نصية
        msg_obj = data['entry'][0]['changes'][0]['value']['messages'][0]
        if 'text' in msg_obj:
            text = msg_obj['text']['body']
            sender = msg_obj['from']
            
            # سؤال Gemini
            ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
            ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": f"أنت مساعد Flex Car. أجب باختصار: {text}"}]}]})
            answer = ai_res.json()['candidates'][0]['content']['parts'][0]['text']
            
            # الرد للواتساب
            wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": answer}}
            requests.post(wa_url, json=payload, headers=headers)
            print("--- تم إرسال الرد بنجاح!")
    except Exception as e:
        print(f"--- حدث خطأ: {e}")
        
    return jsonify({"status": "ok"}), 200
