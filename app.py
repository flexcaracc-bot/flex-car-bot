import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات من Render
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/')
def home():
    return "السيرفر شغال!", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # خطوة التحقق الأولية لميتـا
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("--- تم التحقق من الـ Webhook بنجاح!")
            return challenge, 200
        return 'خطأ في التوكن', 403

    # استقبال الرسائل
    data = request.get_json()
    print("--- [وصلت إشارة من ميتـا]: " + json.dumps(data)) # هذا السطر سيحسم الشك

    try:
        # استخراج الرسالة
        val = data['entry'][0]['changes'][0]['value']
        if 'messages' in val:
            msg = val['messages'][0]
            sender = msg['from']
            text = msg['text']['body']
            
            # استدعاء Gemini
            ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": f"أجب باختصار: {text}"}]}]})
            answer = ai_res.json()['candidates'][0]['content']['parts'][0]['text']

            # الرد
            wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": answer}}
            requests.post(wa_url, json=payload, headers=headers)
            print(f"--- تم إرسال الرد إلى {sender}")

    except Exception as e:
        print(f"--- عطل أثناء المعالجة: {str(e)}")

    return jsonify({"status": "ok"}), 200
