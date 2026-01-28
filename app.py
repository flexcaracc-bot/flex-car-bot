import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Error', 403

    data = request.get_json()
    try:
        val = data['entry'][0]['changes'][0]['value']
        if 'messages' in val:
            msg = val['messages'][0]
            sender = msg['from']
            text = msg['text']['body']
            
            # 1. طلب الرد من Gemini (الرابط المحدث)
            ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": text}]}]})
            ai_data = ai_res.json()
            
            if 'candidates' in ai_data:
                answer = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                answer = "أهلاً! أنا شغال، كيف أساعدك؟"

            # 2. إرسال الرد لواتساب
            wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": answer}}
            requests.post(wa_url, json=payload, headers=headers)
            
    except Exception as e:
        print(f"--- خطأ: {str(e)}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
