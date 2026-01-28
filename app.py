import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات من البيئة (Koyeb)
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/')
def home():
    return "السيرفر شغال ومرتبط بـ Koyeb!", 200

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    # 1. تحقق الـ Webhook الخاص بميتـا
    if request.method == 'GET':
        mode = request.args.get('hub.mode')
        token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        if mode == 'subscribe' and token == VERIFY_TOKEN:
            print("--- تم التحقق من الـ Webhook بنجاح!")
            return challenge, 200
        return 'خطأ في التوكن', 403

    # 2. استقبال البيانات من ميتـا
    data = request.get_json()
    print("--- [بيانات واردة من ميتـا]: " + json.dumps(data))

    try:
        val = data['entry'][0]['changes'][0]['value']
        if 'messages' in val:
            msg = val['messages'][0]
            sender = msg['from']
            text = msg['text']['body']
            
            # 3. طلب الرد من Gemini مع فحص الأخطاء
            ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": f"أنت مساعد في شركة Flex Car لتأجير السيارات، أجب باختصار: {text}"}]}]})
            ai_data = ai_res.json()

            # تصحيح عطل الـ 'candidates'
            if 'candidates' in ai_data and len(ai_data['candidates']) > 0:
                answer = ai_data['candidates'][0]['content']['parts'][0]['text']
            else:
                print(f"--- فشل Gemini في الرد: {json.dumps(ai_data)}")
                answer = "عذراً، نظام الذكاء الاصطناعي يواجه ضغطاً حالياً. يرجى المحاولة لاحقاً."

            # 4. إرسال الرد إلى واتساب
            wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
            headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
            payload = {
                "messaging_product": "whatsapp",
                "to": sender,
                "type": "text",
                "text": {"body": answer}
            }
            wa_res = requests.post(wa_url, json=payload, headers=headers)
            
            if wa_res.status_code == 200:
                print(f"--- تم إرسال الرد بنجاح إلى {sender}")
            else:
                print(f"--- خطأ في إرسال واتساب: {wa_res.text}")

    except Exception as e:
        print(f"--- عطل عام أثناء المعالجة: {str(e)}")

    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    # المنفذ 10000 هو الافتراضي في حسابك على Koyeb
    app.run(host='0.0.0.0', port=10000)
