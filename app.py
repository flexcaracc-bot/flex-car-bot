import express from "express";
import fetch from "node-fetch";

const app = express();
app.use(express.json());

// Verification
app.get("/webhook", (req, res) => {
  if (req.query["hub.verify_token"] === process.env.VERIFY_TOKEN) {
    return res.send(req.query["hub.challenge"]);
  }
  res.sendStatus(403);
});

// Messages
app.post("/webhook", async (req, res) => {
  try {
    const msg = req.body.entry?.[0]?.changes?.[0]?.value?.messages?.[0];
    if (!msg || !msg.text) return res.sendStatus(200);

    const from = msg.from;
    const userText = msg.text.body;

    // Gemini Pro (v1beta)
    const gRes = await fetch(
      "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key=" +
        process.env.GEMINI_API_KEY,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          contents: [{
            parts: [{
              text:
`أنت مساعد بيع ذكي. جاوب باختصار شديد وبأسلوب طبيعي.
اطلب: المنتج، المدينة، نوع السيارة.
اقترح خدمة إضافية واحدة فقط.
اللغة حسب رسالة المستخدم.
النص: ${userText}`
            }]
          }]
        })
      }
    );

    const gData = await gRes.json();
    const reply =
      gData.candidates?.[0]?.content?.parts?.[0]?.text ||
      "مرحبا! شنو الخدمة اللي باغي؟ المدينة ونوع السيارة لو سمحت.";

    // Send WhatsApp reply
    await fetch(
      `https://graph.facebook.com/v19.0/${process.env.PHONE_NUMBER_ID}/messages`,
      {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${process.env.WHATSAPP_TOKEN}`,
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          messaging_product: "whatsapp",
          to: from,
          text: { body: reply }
        })
      }
    );

    res.sendStatus(200);
  } catch (e) {
    console.error(e);
    res.sendStatus(200);
  }
});

app.listen(3000);
