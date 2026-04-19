// Voice Activity Detection utility.
// Opens a mic stream with aggressive noise-suppression / echo-cancellation,
// calibrates the ambient noise floor for the first ~400ms, then emits
// level / speech-start / speech-end events so background chatter never
// registers as direct speech.

const CALIBRATION_MS = 400;
const SPEECH_MULT = 3.0;    // must be >= noiseFloor * SPEECH_MULT to count as speech
const MIN_SPEECH_RMS = 0.025;   // hard floor — below this, always background
const SPEECH_HANG_MS = 180;     // speech must sustain this long to flip on
const SILENCE_HANG_MS = 550;    // silence must sustain this long to flip off

export async function startVAD({ onLevel, onCalibrated, onSpeechStart, onSpeechEnd }) {
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
        channelCount: 1,
      },
    });
  } catch (err) {
    throw err;
  }

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  const ctx = new AudioCtx();
  if (ctx.state === 'suspended') { try { await ctx.resume(); } catch {} }
  const source = ctx.createMediaStreamSource(stream);
  const analyser = ctx.createAnalyser();
  analyser.fftSize = 1024;
  analyser.smoothingTimeConstant = 0.2;
  source.connect(analyser);

  const buf = new Uint8Array(analyser.fftSize);
  const state = {
    stopped: false,
    noiseFloor: 0.01,
    speechThreshold: MIN_SPEECH_RMS,
    peak: 0,
    speaking: false,
    speechStartedAt: 0,
    silenceStartedAt: 0,
    calibrated: false,
    calibSamples: [],
    calibStart: performance.now(),
  };

  const computeRMS = () => {
    analyser.getByteTimeDomainData(buf);
    let sum = 0;
    for (let i = 0; i < buf.length; i++) {
      const v = (buf[i] - 128) / 128;
      sum += v * v;
    }
    return Math.sqrt(sum / buf.length);
  };

  const loop = () => {
    if (state.stopped) return;
    const rms = computeRMS();
    const now = performance.now();

    if (!state.calibrated) {
      state.calibSamples.push(rms);
      if (now - state.calibStart >= CALIBRATION_MS) {
        const sorted = [...state.calibSamples].sort((a, b) => a - b);
        // Use 70th percentile of calibration window as noise floor (robust vs spikes)
        const idx = Math.min(sorted.length - 1, Math.floor(sorted.length * 0.7));
        state.noiseFloor = Math.max(sorted[idx] || 0.01, 0.008);
        state.speechThreshold = Math.max(state.noiseFloor * SPEECH_MULT, MIN_SPEECH_RMS);
        state.calibrated = true;
        onCalibrated?.({ noiseFloor: state.noiseFloor, threshold: state.speechThreshold });
      }
      requestAnimationFrame(loop);
      return;
    }

    // Post-calibration: emit level + detect speech transitions
    onLevel?.({ rms, threshold: state.speechThreshold, noiseFloor: state.noiseFloor });
    if (rms > state.peak) state.peak = rms;

    const isLoud = rms >= state.speechThreshold;

    if (isLoud) {
      if (!state.speaking) {
        if (!state.speechStartedAt) state.speechStartedAt = now;
        if (now - state.speechStartedAt >= SPEECH_HANG_MS) {
          state.speaking = true;
          state.silenceStartedAt = 0;
          onSpeechStart?.({ rms, threshold: state.speechThreshold });
        }
      } else {
        state.silenceStartedAt = 0;
      }
    } else {
      state.speechStartedAt = 0;
      if (state.speaking) {
        if (!state.silenceStartedAt) state.silenceStartedAt = now;
        if (now - state.silenceStartedAt >= SILENCE_HANG_MS) {
          state.speaking = false;
          state.silenceStartedAt = 0;
          onSpeechEnd?.({ peak: state.peak });
        }
      }
    }
    requestAnimationFrame(loop);
  };
  requestAnimationFrame(loop);

  return {
    getPeak: () => state.peak,
    getNoiseFloor: () => state.noiseFloor,
    getThreshold: () => state.speechThreshold,
    isSpeaking: () => state.speaking,
    stop: () => {
      state.stopped = true;
      try { stream.getTracks().forEach(t => t.stop()); } catch {}
      try { ctx.close(); } catch {}
    },
  };
}
