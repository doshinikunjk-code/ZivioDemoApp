"""ElevenLabs TTS endpoint with SHA-256 hash cache to avoid burning quota on repeats."""
import hashlib
import re
import time
from collections import OrderedDict

import httpx
from fastapi import APIRouter, HTTPException, Response

from core import EL_API_KEY, EL_DEFAULT_VOICE, db, logger
from models import TTSRequest

router = APIRouter()

# Hash-cache so repeat "Listen" clicks don't re-hit ElevenLabs.
# Key = sha256(clean_text + voice_id + model) → (timestamp, mp3_bytes)
_HASH_CACHE: "OrderedDict[str, tuple[float, bytes]]" = OrderedDict()
_HASH_CACHE_MAX = 300
_HASH_CACHE_TTL_S = 600

_EMOJI_RE = re.compile(r"[\U0001F300-\U0001FFFF]")
_VS_RE = re.compile(r"[\U0000FE00-\U0000FE0F]")
_ZWJ_RE = re.compile(r"[\U0000200D]")

# Pronunciation-preservation dictionary — when replying in Hindi/Punjabi, any
# Latin-script menu word that leaks through gets normalized to native script so
# ElevenLabs pronounces it with the cloned voice's natural Hindi/Punjabi rhythm
# (not a flat English-accented reading). Applied case-insensitively.
_HI_MAP = {
    "butter chicken": "बटर चिकन",
    "garlic naan": "गार्लिक नान",
    "butter naan": "बटर नान",
    "lamb chops": "लैम्ब चॉप्स",
    "mango lassi": "मैंगो लस्सी",
    "rose lassi": "रोज़ लस्सी",
    "chicken biryani": "चिकन बिरयानी",
    "goat biryani": "बकरे की बिरयानी",
    "veg biryani": "वेज बिरयानी",
    "chicken tikka masala": "चिकन टिक्का मसाला",
    "paneer tikka masala": "पनीर टिक्का मसाला",
    "karahi chicken": "कढ़ाई चिकन",
    "shahi paneer": "शाही पनीर",
    "palak paneer": "पालक पनीर",
    "dal makhani": "दाल मखनी",
    "chana bhatura": "छोले भटूरे",
    "gulab jamun": "गुलाब जामुन",
    "kulfi falooda": "कुल्फी फालूदा",
    "rasmalai": "रसमलाई",
    "tandoori chicken": "तंदूरी चिकन",
    "malai chicken tikka": "मलाई चिकन टिक्का",
    "ceremony indian cuisine": "सेरेमनी इंडियन कुज़ीन",
    "ceremony": "सेरेमनी",
    "desi road": "देसी रोड",
    "riya": "रिया",
    "biryani": "बिरयानी",
    "naan": "नान",
    "lassi": "लस्सी",
    "tikka": "टिक्का",
    "paneer": "पनीर",
    "chicken": "चिकन",
    "roti": "रोटी",
    "paratha": "पराठा",
}
_PA_MAP = {
    "butter chicken": "ਬਟਰ ਚਿਕਨ",
    "garlic naan": "ਗਾਰਲਿਕ ਨਾਨ",
    "butter naan": "ਬਟਰ ਨਾਨ",
    "lamb chops": "ਲੈਂਬ ਚੌਪਸ",
    "mango lassi": "ਮੈਂਗੋ ਲੱਸੀ",
    "rose lassi": "ਰੋਜ਼ ਲੱਸੀ",
    "chicken biryani": "ਚਿਕਨ ਬਿਰਯਾਨੀ",
    "goat biryani": "ਬੱਕਰੇ ਦੀ ਬਿਰਯਾਨੀ",
    "chicken tikka masala": "ਚਿਕਨ ਟਿੱਕਾ ਮਸਾਲਾ",
    "paneer tikka masala": "ਪਨੀਰ ਟਿੱਕਾ ਮਸਾਲਾ",
    "karahi chicken": "ਕੜਾਹੀ ਚਿਕਨ",
    "shahi paneer": "ਸ਼ਾਹੀ ਪਨੀਰ",
    "palak paneer": "ਪਾਲਕ ਪਨੀਰ",
    "dal makhani": "ਦਾਲ ਮੱਖਣੀ",
    "chana bhatura": "ਛੋਲੇ ਭਟੂਰੇ",
    "gulab jamun": "ਗੁਲਾਬ ਜਾਮੁਨ",
    "kulfi falooda": "ਕੁਲਫ਼ੀ ਫਲੂਦਾ",
    "rasmalai": "ਰਸਮਲਾਈ",
    "tandoori chicken": "ਤੰਦੂਰੀ ਚਿਕਨ",
    "malai chicken tikka": "ਮਲਾਈ ਚਿਕਨ ਟਿੱਕਾ",
    "ceremony indian cuisine": "ਸੇਰੇਮਨੀ ਇੰਡੀਅਨ ਕਿਊਜ਼ੀਨ",
    "ceremony": "ਸੇਰੇਮਨੀ",
    "desi road": "ਦੇਸੀ ਰੋਡ",
    "riya": "ਰੀਆ",
    "biryani": "ਬਿਰਯਾਨੀ",
    "naan": "ਨਾਨ",
    "lassi": "ਲੱਸੀ",
    "tikka": "ਟਿੱਕਾ",
    "paneer": "ਪਨੀਰ",
    "chicken": "ਚਿਕਨ",
    "roti": "ਰੋਟੀ",
    "paratha": "ਪਰਾਠਾ",
}
# Pre-compile length-sorted (longest-first) patterns so "chicken tikka masala"
# wins over "chicken".
_HI_PATTERNS = sorted(_HI_MAP.items(), key=lambda kv: -len(kv[0]))
_PA_PATTERNS = sorted(_PA_MAP.items(), key=lambda kv: -len(kv[0]))


def _normalize_for_native_script(text: str, lang: str) -> str:
    """Swap Latin-script menu words to Devanagari/Gurmukhi when reply is in hi/pa."""
    if lang not in ("hi", "pa"):
        return text
    patterns = _HI_PATTERNS if lang == "hi" else _PA_PATTERNS
    # Only normalize if the text already contains Devanagari/Gurmukhi — that tells us
    # the reply IS in the target language and Latin words are leakage, not intentional.
    native_range = (0x0900, 0x097F) if lang == "hi" else (0x0A00, 0x0A7F)
    has_native = any(native_range[0] <= ord(c) <= native_range[1] for c in text)
    if not has_native:
        return text
    out = text
    for latin, native in patterns:
        # Case-insensitive word-boundary swap
        out = re.sub(r"\b" + re.escape(latin) + r"\b", native, out, flags=re.IGNORECASE)
    return out


def _clean_text(text: str) -> str:
    s = _EMOJI_RE.sub("", text or "")
    s = s.replace("—", ", ")
    s = re.sub(r"[•\n]", " ", s)
    s = _VS_RE.sub("", s)
    s = _ZWJ_RE.sub("", s)
    return re.sub(r"  +", " ", s).strip()


def _cache_get(key: str) -> bytes | None:
    entry = _HASH_CACHE.get(key)
    if not entry:
        return None
    ts, data = entry
    if time.time() - ts > _HASH_CACHE_TTL_S:
        _HASH_CACHE.pop(key, None)
        return None
    # LRU touch
    _HASH_CACHE.move_to_end(key)
    return data


def _cache_put(key: str, data: bytes) -> None:
    now = time.time()
    while _HASH_CACHE and next(iter(_HASH_CACHE.values()))[0] < now - _HASH_CACHE_TTL_S:
        _HASH_CACHE.popitem(last=False)
    while len(_HASH_CACHE) >= _HASH_CACHE_MAX:
        _HASH_CACHE.popitem(last=False)
    _HASH_CACHE[key] = (now, data)


@router.post("/tts")
async def tts_endpoint(req: TTSRequest):
    try:
        voice_id = req.voice_id or EL_DEFAULT_VOICE

        # Resolve per-language voice from restaurant config
        if req.restaurant_id and req.lang and req.lang != "auto":
            config = await db.restaurants.find_one({"id": req.restaurant_id}, {"_id": 0})
            if config:
                voice_map = config.get("voice_ids", {}) or {}
                if voice_map.get(req.lang):
                    voice_id = voice_map[req.lang]

        clean = _clean_text(req.text)
        clean = _normalize_for_native_script(clean, req.lang or "")
        if not clean:
            raise HTTPException(status_code=400, detail="Empty text")

        # Cache hit — skip ElevenLabs entirely
        model_id = "eleven_multilingual_v2"
        cache_key = hashlib.sha256(f"{clean}|{voice_id}|{model_id}".encode()).hexdigest()
        cached = _cache_get(cache_key)
        if cached:
            return Response(
                content=cached,
                media_type="audio/mpeg",
                headers={"X-Cache": "HIT"},
            )

        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
                json={
                    "text": clean,
                    "model_id": model_id,
                    "voice_settings": {
                        "stability": 0.38,
                        "similarity_boost": 0.88,
                        "style": 0.55,
                        "use_speaker_boost": True,
                    },
                },
                headers={
                    "xi-api-key": EL_API_KEY,
                    "Content-Type": "application/json",
                    "Accept": "audio/mpeg",
                },
            )
            if response.status_code != 200:
                logger.error(f"EL error: {response.status_code} {response.text[:300]}")
                raise HTTPException(status_code=500, detail="TTS failed")

            _cache_put(cache_key, response.content)
            return Response(
                content=response.content,
                media_type="audio/mpeg",
                headers={"X-Cache": "MISS"},
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
