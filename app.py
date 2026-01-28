import os, requests, json
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب البيانات - تأكد أن الأسماء تطابق Render تماماً
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') # تم تصحيح الاسم هنا
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return 'Error', 403

    data = request.get_json()
    print("--- استلمت بيانات من ميتـا: " + json.dumps(data)) # طباعة البيانات كاملة للتحقق

    try:
        # التأكد من أن البيانات تحتوي على رسالة
        if data.get('entry') and data['entry'][0].get('changes') and data['entry'][0]['changes'][0]['value'].get('messages'):
            message = data['entry'][0]['changes'][0]['value']['messages'][0]
            if message.get('type') == 'text':
                text = message['text']['body']
                sender = message['from']
                
                print(f"--- جاري معالجة رسالة من {sender}: {text}")

                # استدعاء Gemini
                ai_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                ai_res = requests.post(ai_url, json={"contents": [{"parts": [{"text": f"أنت بائع في Flex Car. أجب باختصار: {text}"}]}]})
                
                if ai_res.status_code == 200:
                    answer = ai_res.json()['candidates'][0]['content']['parts'][0]['text']
                    print(f"--- رد Gemini: {answer}")

                    # إرسال للواتساب
                    wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
                    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
                    payload = {"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": answer}}
                    r = requests.post(wa_url, json=payload, headers=headers)
                    print(f"--- حالة إرسال واتساب: {r.status_code}, {r.text}")
                else:
                    print(f"--- خطأ في Gemini API: {ai_res.text}")
    except Exception as e:
        print(f"--- خطأ داخلي في الكود: {str(e)}")
        
    return jsonify({"status": "ok"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
