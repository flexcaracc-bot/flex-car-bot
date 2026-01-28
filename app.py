import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# استدعاء المفاتيح من إعدادات Render للأمان
ACCESS_TOKEN = os.environ.get('ACCESS_TOKEN')
PHONE_NUMBER_ID = os.environ.get('PHONE_NUMBER_ID')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
VERIFY_TOKEN = os.environ.get('VERIFY_TOKEN')

@app.route('/webhook', methods=['GET'])
def verify():
    # التحقق من الرابط بواسطة Meta
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Verification failed'

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        # استلام الرسالة ورقم الزبون
        msg_body = data['entry'][0]['changes'][0]['value']['messages'][0]['text']['body']
        sender_id = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        
        # إرسال الرسالة لـ Gemini والحصول على رد
        ai_answer = call_gemini(msg_body)
        
        # إرسال الرد للواتساب
        send_whatsapp(sender_id, ai_answer)
        return jsonify({"status": "ok"}), 200
    except:
        return jsonify({"status": "error"}), 500

def call_gemini(query):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    # --- تدريب البوت (هذا هو بديل Train AI المدفوع) ---
    system_instruction = (
        "أنت موظف مبيعات ذكي ومؤدب في شركة 'Flex Car' لتأجير السيارات بالمغرب. "
        "قائمة السيارات المتوفرة: "
        "1. داسيا لوغان: 300 درهم/يوم. "
        "2. رينو كليو 5: 350 درهم/يوم. "
        "3. هيونداي توسان: 700 درهم/يوم. "
        "خدماتنا: توصيل للمطار مجاناً، تأمين شامل. "
        "أجب الزبائن بلهجة مغربية بيضاء مهذبة وقصيرة."
    )
    payload = {"contents": [{"parts": [{"text": f"{system_instruction}\nالزبون يسأل: {query}"}]}]}
    res = requests.post(url, json=payload)
    return res.json()['candidates'][0]['content']['parts'][0]['text']

def send_whatsapp(to, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}", "Content-Type": "application/json"}
    payload = {"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}}
    requests.post(url, json=payload, headers=headers)
