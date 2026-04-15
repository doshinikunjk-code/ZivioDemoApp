const express = require('express');
const path    = require('path');
const axios   = require('axios');
const app     = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname)));

const CLAUDE_KEY = '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';
const EL_KEY     = 'sk_a2902f9f7e15502b886f81801697acdcf10e29ee485835bf';
const EL_VOICE   = 'mActWQg9kibLro6Z2ouY';

// ── Claude ────────────────────────────────────────────────────────
app.post('/api/claude', async (req, res) => {
  try {
    const r = await axios.post('https://api.anthropic.com/v1/messages', req.body, {
      headers: {
        'x-api-key': CLAUDE_KEY,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    console.log('Claude OK:', r.status);
    res.json(r.data);
  } catch(e) {
    console.error('Claude error:', e.response?.status, e.response?.data || e.message);
    res.status(500).json({ error: e.message });
  }
});

// ── ElevenLabs TTS ────────────────────────────────────────────────
app.post('/api/tts', async (req, res) => {
  try {
    const { text, voice_id, lang } = req.body;
    const r = await axios.post(
      `https://api.elevenlabs.io/v1/text-to-speech/${voice_id || EL_VOICE}`,
      {
        // Prepend invisible Hindi primer to force Indian accent on all text
        text: req.body.lang === 'hi' ? text : 'जी। ' + text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: { stability: 0.30, similarity_boost: 0.92, style: 0.45, use_speaker_boost: true }
      },
      {
        headers: { 'xi-api-key': EL_KEY, 'Content-Type': 'application/json', 'Accept': 'audio/mpeg' },
        responseType: 'arraybuffer',
        timeout: 30000
      }
    );
    console.log('EL OK:', r.status);
    res.setHeader('Content-Type', 'audio/mpeg');
    res.send(Buffer.from(r.data));
  } catch(e) {
    console.error('EL error:', e.response?.status, e.response?.data?.toString()?.substring(0,200) || e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('*', (_, res) => res.sendFile(path.join(__dirname, 'index.html')));

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => console.log(`Zivio Demo live on port ${PORT}`));
