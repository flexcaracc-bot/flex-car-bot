# -*- coding: utf-8 -*-
import os
import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

# جلب المتغيرات من إعدادات Koyeb
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

@app.route("/")
def home():
    return "السيرفر شغال ✔", 200

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    # 1️⃣ التحقق من Webhook (لصالح ميتـا)
    if request.method == "GET":
        if (
            request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == VERIFY_TOKEN
        ):
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403

    # 2️⃣ استقبال الرسالة القادمة
    data = request.get_json()
    print("INCOMING:", json.dumps(data, ensure_ascii=False))

    try:
        # التأكد من وجود رسالة في البيانات المرسلة
        if "entry" in data and "changes" in data["entry"][0]:
            value = data["entry"][0]["changes"][0]["value"]
            
            if "messages" in value:
                msg = value["messages"][0]
                sender = msg["from"]
                user_text = msg.get("text", {}).get("body", "")

                if user_text:
                    # 3️⃣ طلب الرد من Gemini (v1beta)
                    prompt = f"أنت مساعد بيع لشركة Flex Car. اجب باختصار: {user_text}"
                    
                    gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
                    
                    gemini_res = requests.post(
                        gemini_url,
                        json={"contents": [{"parts": [{"text": prompt}]}]},
                        timeout=20
                    )
                    
                    gemini_data = gemini_res.json()
                    
                    if "candidates" in gemini_data:
                        reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
                    else:
                        reply = "مرحباً! كيف يمكنني مساعدتك اليوم؟"

                    # 4️⃣ إرسال الرد إلى واتساب
                    wa_url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
                    headers = {
                        "Authorization": f"Bearer {ACCESS_TOKEN}",
                        "Content-Type": "application/json"
                    }
                    payload = {
                        "messaging_product": "whatsapp",
                        "to": sender,
                        "type": "text",
                        "text": {"body": reply}
                    }
                    
                    wa_res = requests.post(wa_url, headers=headers, json=payload)
                    print("WA STATUS:", wa_res.status_code)

    except Exception as e:
        print("ERROR:", str(e))

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    # استخدام المنفذ 10000 كما هو مطلوب في Koyeb
    app.run(host="0.0.0.0", port=10000)
