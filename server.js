const express = require('express');
const path    = require('path');
const https   = require('https');
const app     = express();

app.use(express.json({ limit: '10mb' }));
app.use(express.static(path.join(__dirname)));

// ── HELPER: HTTPS request ────────────────────────────────────────
function httpsPost(hostname, path, headers, body) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const options = {
      hostname, path, method: 'POST',
      headers: { ...headers, 'Content-Length': Buffer.byteLength(data) }
    };
    const req = https.request(options, (res) => {
      let chunks = [];
      res.on('data', c => chunks.push(c));
      res.on('end', () => resolve({ status: res.statusCode, body: Buffer.concat(chunks), headers: res.headers }));
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

function httpsPostStream(hostname, reqPath, headers, body, onChunk, onEnd) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(body);
    const options = {
      hostname, path: reqPath, method: 'POST',
      headers: { ...headers, 'Content-Length': Buffer.byteLength(data) }
    };
    const req = https.request(options, (res) => {
      res.on('data', chunk => onChunk(chunk));
      res.on('end', () => { onEnd(); resolve(); });
    });
    req.on('error', reject);
    req.write(data);
    req.end();
  });
}

// ── PROXY: Claude (non-streaming) ────────────────────────────────
app.post('/api/claude', async (req, res) => {
  try {
    const result = await httpsPost(
      'api.anthropic.com',
      '/v1/messages',
      {
        'Content-Type': 'application/json',
        'x-api-key': 'v5BCnln_o6mSoZilLS4ueGEHOM8dAa9e',
        'anthropic-version': '2023-06-01'
      },
      req.body
    );
    res.status(result.status).json(JSON.parse(result.body.toString()));
  } catch(e) {
    console.error('Claude error:', e.message);
    res.status(500).json({ error: e.message });
  }
});

// ── PROXY: Claude Streaming ───────────────────────────────────────
app.post('/api/claude/stream', async (req, res) => {
  try {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    res.setHeader('Access-Control-Allow-Origin', '*');

    await httpsPostStream(
      'api.anthropic.com',
      '/v1/messages',
      {
        'Content-Type': 'application/json',
        'x-api-key': 'v5BCnln_o6mSoZilLS4ueGEHOM8dAa9e',
        'anthropic-version': '2023-06-01'
      },
      { ...req.body, stream: true },
      (chunk) => res.write(chunk),
      () => res.end()
    );
  } catch(e) {
    console.error('Claude stream error:', e.message);
    res.status(500).end();
  }
});

// ── PROXY: ElevenLabs TTS ─────────────────────────────────────────
app.post('/api/tts', async (req, res) => {
  try {
    const { text, voice_id } = req.body;
    const vid = voice_id || 'EXAVITQu4vr4xnSDxMaL';

    const result = await httpsPost(
      'api.elevenlabs.io',
      `/v1/text-to-speech/${vid}`,
      {
        'Content-Type': 'application/json',
        'xi-api-key': 'sk_a24aa4e652d9cde8a45d3be07a2291ff268e213a737b9888',
        'Accept': 'audio/mpeg'
      },
      {
        text,
        model_id: 'eleven_multilingual_v2',
        voice_settings: { stability: 0.40, similarity_boost: 0.85, style: 0.35, use_speaker_boost: true }
      }
    );

    if (result.status !== 200) {
      console.error('EL error:', result.body.toString());
      return res.status(result.status).json({ error: result.body.toString() });
    }

    res.setHeader('Content-Type', 'audio/mpeg');
    res.send(result.body);
  } catch(e) {
    console.error('TTS error:', e.message);
    res.status(500).json({ error: e.message });
  }
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Zivio Demo live on port ${PORT}`);
});
