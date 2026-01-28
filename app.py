import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/')
def home():
    return "السيرفر شغال ومرتبط بـ Koyeb!", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            return challenge, 200
        return 'خطأ في التوكن', 403

    data = request.get_json()
    print("--- [بيانات واردة]: " + json.dumps(data))

    try:
        val = data['entry'][0]['changes'][0]['value']
        if 'messages' in val:
            msg = val['messages'][0]
            sender = msg['from']
            text = msg['text']['body']
            
            # تحديث الرابط إلى النسخة المستقرة v1
            ai_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": f"أنت مساعد في شركة Flex Car، أجب باختصار: {text}"}]}]})
            ai_data = ai_res.json()

            if 'candidates' in ai_data:
                answer = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"--- فشل Gemini: {json.dumps(ai_data)}")
                answer = "عذراً، أنا أتعلم حالياً. كيف أخدمك؟"

            wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": answer}}
            wa_res = requests.post(wa_url, json=payload, headers=headers)
            print(f"--- نتيجة الإرسال: {wa_res.text}")

    except Exception as e:
        print(f"--- خطأ: {str(e)}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
