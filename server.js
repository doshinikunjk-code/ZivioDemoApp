const express = require('express');
const path    = require('path');
const https   = require('https');
const app     = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname)));

// ── HELPER: HTTPS POST returning full body ────────────────────────
function httpsPost(hostname, urlPath, headers, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const req  = https.request({
      hostname, path: urlPath, method: 'POST',
      headers: { ...headers, 'Content-Length': Buffer.byteLength(data) }
    }, (res) => {
      const chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end',  () => resolve({ status: res.statusCode, body: Buffer.concat(chunks) }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// ── PROXY: Claude non-streaming (for call demo) ───────────────────
app.post('/api/claude', async (req, res) => {
  try {
    const r = await httpsPost(
      'api.anthropic.com', '/v1/messages',
      { 'Content-Type':'application/json', 'x-api-key':'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', 'anthropic-version':'2023-06-01' },
      req.body
    );
    console.log('Claude status:', r.status);
    res.status(r.status).type('json').send(r.body);
  } catch(e) {
    console.error('Claude error:', e.message);
    res.status(500).json({ error: e.message });
  }
});

// ── PROXY: Claude streaming (WhatsApp chat) ───────────────────────
app.post('/api/claude/stream', async (req, res) => {
  res.setHeader('Content-Type',  'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection',    'keep-alive');

  const data = JSON.stringify({ ...req.body, stream: true });
  const reqH = {
    'Content-Type': 'application/json',
    'x-api-key': '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',
    'anthropic-version': '2023-06-01',
    'Content-Length': Buffer.byteLength(data)
  };

  const apiReq = https.request({
    hostname: 'api.anthropic.com', path: '/v1/messages', method: 'POST', headers: reqH
  }, (apiRes) => {
    console.log('Claude stream status:', apiRes.statusCode);
    apiRes.on('data', chunk => res.write(chunk));
    apiRes.on('end',  () => res.end());
  });

  apiReq.on('error', (e) => {
    console.error('Claude stream error:', e.message);
    res.end();
  });

  apiReq.write(data);
  apiReq.end();
});

// ── PROXY: ElevenLabs TTS ─────────────────────────────────────────
app.post('/api/tts', async (req, res) => {
  try {
    const { text, voice_id } = req.body;
    const vid  = voice_id || 'ack0QsRaQyDLnVyMQTSd';
    const r = await httpsPost(
      'api.elevenlabs.io',
      `/v1/text-to-speech/${vid}`,
      {
        'Content-Type': 'application/json',
        'xi-api-key': 'sk_a2902f9f7e15502b886f81801697acdcf10e29ee485835bf',
        'Accept': 'audio/mpeg'
      },
      { text, model_id: 'eleven_multilingual_v2',
        voice_settings: { stability:0.40, similarity_boost:0.85, style:0.35, use_speaker_boost:true } }
    );
    console.log('EL status:', r.status);
    if (r.status !== 200) return res.status(r.status).json({ error: r.body.toString() });
    res.setHeader('Content-Type', 'audio/mpeg');
    res.send(r.body);
  } catch(e) {
    console.error('TTS error:', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('*', (_, res) => res.sendFile(path.join(__dirname, 'index.html')));

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => console.log(`Zivio Demo live on port ${PORT}`));
