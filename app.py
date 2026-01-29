# -*- coding: utf-8 -*-
import os
import requests
import json
from flask import Flask, request, jsonify

app = Flask(__name__)

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN")

@app.route("/")
def home():
    return "السيرفر شغال ✔", 200


@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # 1️⃣ Webhook Verification
    if request.method == "GET":
        if (
            request.args.get("hub.mode") == "subscribe"
            and request.args.get("hub.verify_token") == VERIFY_TOKEN
        ):
            return request.args.get("hub.challenge"), 200
        return "Forbidden", 403

    # 2️⃣ Incoming message
    data = request.get_json()
    print("INCOMING:", json.dumps(data, ensure_ascii=False))

    try:
        value = data["entry"][0]["changes"][0]["value"]

        if "messages" not in value:
            return jsonify({"status": "ignored"}), 200

        msg = value["messages"][0]
        sender = msg["from"]
        user_text = msg["text"]["body"]

        # 3️⃣ Gemini Pro request (v1beta)
        prompt = f"""
أنت مساعد بيع ذكي لشركة Flex Car.
جاوب بجملة أو جملتين فقط وبأسلوب طبيعي.
اطلب:
- المنتج
- المدينة
- نوع السيارة
واقترح خدمة إضافية واحدة فقط.
اللغة حسب كلام المستخدم.

رسالة المستخدم:
{user_text}
"""

        gemini_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            "gemini-1.5-flash:generateContent?key=" + GEMINI_API_KEY
        )

        gemini_res = requests.post(
            gemini_url,
            json={
                "contents": [
                    {
                        "parts": [{"text": prompt}]
                    }
                ]
            },
            timeout=20
        )

        gemini_data = gemini_res.json()

        if "candidates" in gemini_data:
            reply = gemini_data["candidates"][0]["content"]["parts"][0]["text"]
        else:
            reply = "مرحبا! شنو الخدمة اللي باغي؟ المدينة ونوع السيارة لو سمحت."

        # 4️⃣ Se
