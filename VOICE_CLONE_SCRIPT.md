# 🎤 Voice Cloning Script for Zivio AI

**Goal**: Record ~90 seconds of your own voice in a quiet room and clone it on ElevenLabs so your phone-call AI sounds genuinely human — with *your* accent, *your* warmth.

---

## 📋 How to record

1. **Quiet room**. No AC hum, no kids, no TV. Close windows.
2. **Phone 6 inches from mouth** — closer is better than farther.
3. **Use Voice Memos (iPhone)** or **Easy Voice Recorder (Android)**. Save as `.m4a` or `.mp3`.
4. **Read at a natural pace** — like you're greeting a real customer on the phone. Don't rush. Don't be flat.
5. **One take**. If you mess up a word, pause 2 seconds and continue — ElevenLabs will auto-trim silences.
6. **Record all three languages in the SAME file**, back to back, with a 2-second pause between sections.

**Total length target**: 90 seconds to 2 minutes. That's the sweet spot for ElevenLabs Instant Voice Clone.

---

## 📝 Read this exact script (word-for-word)

### Part 1 — English (~30 seconds)

> "Hey, thanks for calling Ceremony Indian Cuisine. This is Riya. What can I get started for you today?
>
> Our bestseller tonight is the Butter Chicken — it's creamy, smoky, and pairs amazing with our fresh garlic naan.
>
> Sure, let me add that to your order. Anything else? A mango lassi maybe — it really cools down the spice.
>
> Perfect, so that's one butter chicken, one garlic naan, and one mango lassi. Ready in about twenty minutes. See you soon!"

*(pause 2 seconds, then continue)*

### Part 2 — Hindi (~30 seconds)

> "नमस्ते जी! Ceremony Indian Cuisine में आपका स्वागत है। मैं रिया बात कर रही हूँ। क्या ऑर्डर करना चाहेंगे आज?
>
> आज का स्पेशल है शाही लैम्ब चॉप्स — बहुत स्वादिष्ट है, एक बार ज़रूर try करना चाहिए।
>
> ठीक है, एक बटर चिकन और दो गार्लिक नान जोड़ देती हूँ। कुछ और चाहिए — मैंगो लस्सी ले लेंगे?
>
> बढ़िया, बीस मिनट में तैयार हो जाएगा। मिलते हैं Ceremony में!"

*(pause 2 seconds, then continue)*

### Part 3 — Punjabi (~30 seconds)

> "ਸਤ ਸ੍ਰੀ ਅਕਾਲ ਜੀ! Ceremony Indian Cuisine ਵਿੱਚ ਤੁਹਾਡਾ ਸਵਾਗਤ ਹੈ। ਮੈਂ ਰਿਆ ਹਾਂ। ਕੀ ਚਾਹੀਦਾ ਹੈ ਅੱਜ?
>
> ਸਾਡਾ ਅੱਜ ਦਾ ਖਾਸ ਹੈ ਸ਼ਾਹੀ ਲੈਂਬ ਚੌਪਸ — ਬਹੁਤ ਸੁਆਦ ਹੁੰਦਾ ਹੈ, ਇੱਕ ਵਾਰੀ ਜ਼ਰੂਰ ਮੰਗਾਇਓ।
>
> ਠੀਕ ਏ, ਇੱਕ ਬਟਰ ਚਿਕਨ ਅਤੇ ਦੋ ਗਾਰਲਿਕ ਨਾਨ ਪਾ ਦਿੱਤੇ। ਲੱਸੀ ਵੀ ਲੈ ਲੈਨੀ — ਮਸਾਲਾ ਘੱਟ ਲੱਗੇਗਾ?
>
> ਠੀਕ ਏ, ਵੀਹ ਮਿੰਟ ਵਿੱਚ ਤਿਆਰ। ਜਲਦੀ ਮਿਲਦੇ ਆਂ!"

---

## ☁️ Upload & clone on ElevenLabs

1. Open **https://elevenlabs.io** → log in.
2. Left sidebar → **Voices** → **Add a New Voice** → **Instant Voice Clone**.
3. **Name it**: `Ceremony Indian – Riya`
4. **Upload your recording** (drag-drop the `.m4a` or `.mp3`).
5. **Labels**: `age: young`, `accent: Indian`, `gender: female`, `use_case: conversational`.
6. **Description** (paste this exactly):
   > Warm, friendly Indian-Canadian restaurant staff. Speaks English, Hindi and Punjabi fluently. Conversational pace. Uses natural fillers like "mmm", "sure", "one sec". Never robotic.
7. Click **Add Voice**. It takes ~60 seconds.
8. Click on your new voice → copy the **Voice ID** (looks like `21m00Tcm4TlvDq8ikWAM`).

## 🔌 Plug it into Zivio AI

1. Go to the Zivio AI demo app → **Admin Panel** (sidebar).
2. Scroll to **Voice Configuration (ElevenLabs)**.
3. Paste your Voice ID into all three fields: **English**, **Hindi**, **Punjabi**. (Multilingual models support all three from one clone.)
4. Click **Save**.
5. Open **Live Demo** screen and type anything — you should now hear *your* voice.
6. For phone calls: no extra step — the IVR automatically uses the same voice ID.

---

## 🎯 Pro tips for a premium clone

- **Record on the phone you'll take calls on** — mic timbre matches.
- **Smile while you read** — it literally changes your voice warmth (sounds silly, works).
- **If your first clone sounds flat**: re-record with 20% more energy and more pitch variation. ElevenLabs mirrors your prosody.
- **Punjabi sounding off?**: clone a second voice with ONLY the Punjabi section and paste that specifically into the Punjabi slot in Admin Panel.
- **Cost**: Instant Clone is free on ElevenLabs Starter; Professional Clone (fine-tuned, even closer) requires the $99 Creator plan but is worth it for production.

---

## 🧪 Quick A/B test before going live

After pasting your voice ID, open the Live Demo and try these exact messages:

- `"I want one butter chicken and two garlic naan please"`  → should sound like YOU
- `"नमस्ते, chicken biryani mangwana hai"` → Hindi reply in your voice
- `"ਸਤ ਸ੍ਰੀ ਅਕਾਲ, lamb chops ਚਾਹੀਦੇ ਨੇ"` → Punjabi reply in your voice

If all three sound unmistakably like you — you're done. 🎉
