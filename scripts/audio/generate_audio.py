"""Generate synchronized Indonesian narration (edge-tts), procedural Foley SFX, dynamic Art Deco BGM,
exact timing_manifest.json (30 FPS), master_mix.wav, and pop-in bold ASS subtitles.

Usage:
    python scripts/audio/generate_audio.py
"""

from __future__ import annotations

import asyncio
import json
import math
import re
import subprocess
import sys
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
from scipy.signal import butter, filtfilt

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.storyboard import FPS, HEIGHT, STORYBOARD, WIDTH, SceneSpec  # noqa: E402

SR = 44100
VOICE_ID = "id-ID-ArdiNeural"
VOICE_RATE = "+8%"

HIGHLIGHT_KEYWORDS = {
    "BANGKRUT", "LAMBAT", "MENGAMUK", "PANIK", "ROKET", "TURBO", "MILIARAN",
    "NOL", "BESAR", "KOPI", "OTAK", "DISTRASKI", "DISTRASKI!", "DISTRAKSI",
    "MENIT", "CERMIN", "MURAH", "LUPA", "WAKTU", "RAMBUT", "CEPAT",
    "SEMBILAN", "PULUH", "PERSEN", "MERASAKANNYA",
}


# ==============================================================================
# AUDIO I/O & FFMPEG DECODE HELPERS
# ==============================================================================

def _write_wav(path: Path, stereo: np.ndarray, sr: int = SR) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = np.nan_to_num(stereo, nan=0.0, posinf=0.0, neginf=0.0)
    clipped = np.clip(clean, -0.98, 0.98)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(2)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def _decode_mp3_to_stereo(mp3_path: Path, sr: int = SR) -> np.ndarray:
    """Decode any audio file via FFmpeg into float32 stereo numpy array."""
    cmd = [
        "ffmpeg", "-y", "-i", str(mp3_path),
        "-f", "s16le", "-acodec", "pcm_s16le", "-ac", "2", "-ar", str(sr),
        "pipe:1",
    ]
    proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    raw = np.frombuffer(proc.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    if raw.size == 0:
        return np.zeros((int(sr * 1.0), 2), dtype=np.float32)
    return raw.reshape(-1, 2)


def _bp_filter(sig: np.ndarray, lo_hz: float, hi_hz: float, sr: int = SR) -> np.ndarray:
    nyq = sr * 0.5
    lo = max(20.0, min(lo_hz, nyq - 200.0)) / nyq
    hi = max(lo + 0.01, min(hi_hz, nyq - 100.0)) / nyq
    b, a = butter(2, [lo, hi], btype="band")
    return filtfilt(b, a, sig).astype(np.float32)


def _lp_filter(sig: np.ndarray, cutoff_hz: float, sr: int = SR) -> np.ndarray:
    nyq = sr * 0.5
    wn = max(0.002, min(cutoff_hz / nyq, 0.98))
    b, a = butter(2, wn, btype="low")
    return filtfilt(b, a, sig).astype(np.float32)


# ==============================================================================
# 1. VOICEOVER NARRATION (EDGE-TTS WITH WORD BOUNDARY TIMING)
# ==============================================================================

async def _tts_single(text: str, out_mp3: Path) -> List[Tuple[str, float, float]]:
    """Synthesize Indonesian TTS and capture exact word start/end timings in seconds."""
    import edge_tts  # type: ignore

    communicate = edge_tts.Communicate(text, voice=VOICE_ID, rate=VOICE_RATE, boundary="WordBoundary")
    words: List[Tuple[str, float, float]] = []
    audio_chunks = bytearray()

    async for chunk in communicate.stream():
        ctype = chunk.get("type")
        if ctype == "audio":
            audio_chunks.extend(chunk["data"])
        elif ctype == "WordBoundary":
            w_text = str(chunk.get("text", "")).strip()
            offset_s = float(chunk.get("offset", 0)) / 1e7
            dur_s = float(chunk.get("duration", 0)) / 1e7
            if w_text:
                words.append((w_text, offset_s, offset_s + max(dur_s, 0.08)))

    out_mp3.parent.mkdir(parents=True, exist_ok=True)
    out_mp3.write_bytes(bytes(audio_chunks))
    return words


def _fallback_word_timings(text: str, duration_s: float) -> List[Tuple[str, float, float]]:
    tokens = [t for t in re.split(r"\s+", text.strip()) if t]
    if not tokens:
        return []
    weights = [max(2, len(re.sub(r"[^A-Za-z0-9]", "", t))) for t in tokens]
    total_w = sum(weights) or 1
    out: List[Tuple[str, float, float]] = []
    cur = 0.04
    usable = max(0.3, duration_s - 0.12)
    for tok, w in zip(tokens, weights):
        seg = usable * (w / total_w)
        out.append((tok, cur, cur + seg))
        cur += seg
    return out


def synthesize_all_narration(audio_dir: Path) -> List[dict]:
    """Generate voiceover clips for all 10 scenes and return real measured timings."""
    results: List[dict] = []

    async def _run_all():
        for sc in STORYBOARD:
            mp3_path = audio_dir / f"vo_{sc.slug}.mp3"
            words: List[Tuple[str, float, float]] = []
            try:
                words = await _tts_single(sc.narration, mp3_path)
                pcm = _decode_mp3_to_stereo(mp3_path)
                vo_dur = len(pcm) / SR
                tts_ok = True
            except Exception as exc:
                print(f"[Audio WARN] edge-tts unavailable for S{sc.scene_id:02d} ({exc}); using timed narration bed.")
                vo_dur = max(3.6, sc.default_duration_s - 0.65)
                pcm = np.zeros((int(vo_dur * SR), 2), dtype=np.float32)
                tts_ok = False

            if not words:
                words = _fallback_word_timings(sc.narration, vo_dur)

            # Pad neatly for visual breathing room & comedic timing (keeps total near ~58–62s!)
            lead_s = 0.24
            tail_s = 0.42 if sc.scene_id in (3, 7, 8, 9, 10) else 0.30
            scene_dur = max(sc.default_duration_s * 0.82, lead_s + vo_dur + tail_s)
            num_frames = int(round(scene_dur * FPS))
            exact_dur = num_frames / FPS

            results.append(
                {
                    "scene": sc,
                    "pcm": pcm,
                    "vo_dur": vo_dur,
                    "lead_s": lead_s,
                    "duration_s": exact_dur,
                    "num_frames": num_frames,
                    "words": [(w, s + lead_s, e + lead_s) for (w, s, e) in words],
                    "tts_ok": tts_ok,
                }
            )

    asyncio.run(_run_all())
    return results


# ==============================================================================
# 2. PROCEDURAL DIEGETIC FOLEY SFX LIBRARY (ZERO EXTERNAL FILES!)
# ==============================================================================

def _make_sfx(sfx_type: str, seed: int = 7) -> np.ndarray:
    rng = np.random.default_rng(seed)

    if sfx_type == "whoosh":
        n = int(0.42 * SR)
        t = np.linspace(0, 0.42, n, dtype=np.float32)
        env = np.maximum(0.0, np.sin(np.pi * (t / 0.42))) ** 1.4
        noise = rng.normal(0, 1.0, n).astype(np.float32)
        sig = _bp_filter(noise, 260, 1850) * env * 0.55
        # Subtle pitched air sweep
        freq = 160.0 + 480.0 * np.sin(np.pi * t / 0.42)
        phase = np.cumsum(2 * np.pi * freq / SR)
        sig += np.sin(phase) * env * 0.14
        return np.stack([sig * 0.95, sig * 1.05], axis=1)

    if sfx_type == "click_burst":
        n = int(1.05 * SR)
        out = np.zeros(n, dtype=np.float32)
        for idx, onset in enumerate((0.0, 0.16, 0.31, 0.44, 0.56, 0.67)):
            i0 = int(onset * SR)
            m = int(0.055 * SR)
            t = np.linspace(0, 0.055, m, dtype=np.float32)
            env = np.exp(-t * 95.0)
            click = (
                np.sin(2 * np.pi * (1750 + idx * 90) * t) * 0.5
                + np.sin(2 * np.pi * 4100 * t) * 0.3
                + rng.normal(0, 0.35, m)
            ) * env * 0.72
            end = min(n, i0 + m)
            out[i0:end] += click[: end - i0]
        return np.stack([out, out], axis=1)

    if sfx_type == "tick_slow":
        # Heavy echoing lobby clock TICK... TOCK with elastic wood+brass body
        n = int(0.95 * SR)
        out = np.zeros(n, dtype=np.float32)
        for onset, f0 in ((0.0, 720.0), (0.50, 560.0)):
            i0 = int(onset * SR)
            m = int(0.22 * SR)
            t = np.linspace(0, 0.22, m, dtype=np.float32)
            env = np.exp(-t * 28.0)
            tone = (np.sin(2 * np.pi * f0 * t) * 0.55 + np.sin(2 * np.pi * f0 * 2.42 * t) * 0.32) * env
            thump = np.sin(2 * np.pi * 155.0 * t) * np.exp(-t * 42.0) * 0.45
            end = min(n, i0 + m)
            out[i0:end] += (tone + thump)[: end - i0] * 0.68
        return np.stack([out, out], axis=1)

    if sfx_type == "tick_fast":
        # Accelerating clockwork whirr cascade (time flying 2x faster!)
        n = int(2.2 * SR)
        out = np.zeros(n, dtype=np.float32)
        t_cur = 0.0
        step = 0.16
        k = 0
        while t_cur < 2.05:
            i0 = int(t_cur * SR)
            m = int(0.06 * SR)
            t = np.linspace(0, 0.06, m, dtype=np.float32)
            f = 950.0 + k * 45.0
            tick = (np.sin(2 * np.pi * f * t) * 0.5 + np.sin(2 * np.pi * f * 2.1 * t) * 0.25) * np.exp(-t * 75.0) * 0.55
            end = min(n, i0 + m)
            out[i0:end] += tick[: end - i0]
            t_cur += step
            step = max(0.055, step * 0.90)
            k += 1
        return np.stack([out, out], axis=1)

    if sfx_type == "rocket_rev":
        n = int(1.45 * SR)
        t = np.linspace(0, 1.45, n, dtype=np.float32)
        env = np.maximum(0.0, np.sin(np.pi * (t / 1.45))) ** 0.8
        freq = 58.0 + 135.0 * (t / 1.45) ** 1.3
        phase = np.cumsum(2 * np.pi * freq / SR)
        rumble = np.tanh(np.sin(phase) * 2.2 + np.sin(phase * 2.02) * 0.9) * 0.36
        hiss = _bp_filter(rng.normal(0, 1.0, n).astype(np.float32), 450, 3200) * 0.42
        sig = (rumble + hiss) * env
        return np.stack([sig, sig], axis=1)

    if sfx_type == "thud":
        n = int(0.38 * SR)
        t = np.linspace(0, 0.38, n, dtype=np.float32)
        freq = 145.0 * np.exp(-t * 14.0) + 36.0
        phase = np.cumsum(2 * np.pi * freq / SR)
        sig = np.sin(phase) * np.exp(-t * 11.5) * 0.85
        return np.stack([sig, sig], axis=1)

    if sfx_type == "sip":
        n = int(0.45 * SR)
        t = np.linspace(0, 0.45, n, dtype=np.float32)
        env = np.maximum(0.0, np.sin(np.pi * t / 0.45)) ** 1.2
        noise = _bp_filter(rng.normal(0, 1.0, n).astype(np.float32), 1400, 4200) * 0.35
        chirp = np.sin(np.cumsum(2 * np.pi * (420 + 680 * t / 0.45) / SR)) * 0.20
        sig = (noise + chirp) * env * 0.72
        return np.stack([sig, sig], axis=1)

    if sfx_type == "chime_aha":
        n = int(1.25 * SR)
        out = np.zeros(n, dtype=np.float32)
        notes = [(0.00, 523.25), (0.07, 659.25), (0.14, 783.99), (0.21, 1174.66)]
        for onset, f in notes:
            i0 = int(onset * SR)
            m = n - i0
            t = np.linspace(0, m / SR, m, dtype=np.float32)
            bell = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t)) * np.exp(-t * 3.8)
            out[i0:] += bell * 0.24
        return np.stack([out, out], axis=1)

    if sfx_type == "mirror_drop":
        n = int(0.85 * SR)
        t = np.linspace(0, 0.85, n, dtype=np.float32)
        # Quick swoosh-down + crisp solid mount thump + metallic ring!
        thump = np.zeros(n, dtype=np.float32)
        i_hit = int(0.18 * SR)
        th = np.linspace(0, 0.4, int(0.4 * SR), dtype=np.float32)
        hit = np.sin(np.cumsum(2 * np.pi * (160 * np.exp(-th * 16) + 42) / SR)) * np.exp(-th * 12) * 0.78
        ring = np.sin(2 * np.pi * 880.0 * th) * np.exp(-th * 6.5) * 0.22
        thump[i_hit : i_hit + len(th)] = hit + ring
        return np.stack([thump, thump], axis=1)

    if sfx_type == "boing":
        n = int(0.55 * SR)
        t = np.linspace(0, 0.55, n, dtype=np.float32)
        freq = 210.0 + 185.0 * (1.0 - np.exp(-t * 9.0)) + 52.0 * np.sin(2 * np.pi * 16.0 * t) * np.exp(-t * 3.5)
        phase = np.cumsum(2 * np.pi * freq / SR)
        sig = np.sin(phase) * np.exp(-t * 4.5) * 0.60
        return np.stack([sig, sig], axis=1)

    if sfx_type == "sparkle":
        n = int(1.10 * SR)
        out_l = np.zeros(n, dtype=np.float32)
        out_r = np.zeros(n, dtype=np.float32)
        freqs = [1318.5, 1661.2, 1975.5, 2637.0, 3322.4]
        for idx, f in enumerate(freqs):
            i0 = int(idx * 0.065 * SR)
            m = n - i0
            t = np.linspace(0, m / SR, m, dtype=np.float32)
            twinkle = np.sin(2 * np.pi * f * t) * np.exp(-t * 5.2) * 0.22
            pan = 0.35 + 0.3 * (idx % 2)
            out_l[i0:] += twinkle * (1.0 - pan)
            out_r[i0:] += twinkle * pan
        return np.stack([out_l, out_r], axis=1)

    if sfx_type == "ding":
        # Authentic gleaming Art Deco brass elevator bell DING!!
        n = int(1.75 * SR)
        t = np.linspace(0, 1.75, n, dtype=np.float32)
        sig = (
            0.55 * np.sin(2 * np.pi * 1046.5 * t) * np.exp(-t * 2.2)
            + 0.30 * np.sin(2 * np.pi * 2098.0 * t) * np.exp(-t * 3.6)
            + 0.16 * np.sin(2 * np.pi * 3156.0 * t) * np.exp(-t * 5.5)
            + 0.08 * np.sin(2 * np.pi * 4215.0 * t) * np.exp(-t * 8.0)
        )
        # Crisp hammer attack
        sig *= 1.0 - np.exp(-t * 420.0)
        return np.stack([sig * 0.78, sig * 0.78], axis=1)

    if sfx_type == "door_slide":
        n = int(1.05 * SR)
        t = np.linspace(0, 1.05, n, dtype=np.float32)
        env = np.maximum(0.0, np.sin(np.pi * t / 1.05)) ** 0.75
        noise = _bp_filter(rng.normal(0, 1.0, n).astype(np.float32), 280, 1150) * 0.35
        hum = np.sin(2 * np.pi * 195.0 * t) * 0.12
        sig = (noise + hum) * env
        return np.stack([sig, sig], axis=1)

    # jazz_fin — Warm lush Art Deco Maj9 finale chord sting!
    n = int(1.85 * SR)
    t = np.linspace(0, 1.85, n, dtype=np.float32)
    chord = [261.63, 329.63, 392.00, 493.88, 587.33]  # Cmaj9
    sig = np.zeros(n, dtype=np.float32)
    for f in chord:
        sig += (np.sin(2 * np.pi * f * t) + 0.22 * np.sin(2 * np.pi * f * 2 * t)) * np.exp(-t * 1.45)
    sig *= (1.0 - np.exp(-t * 40.0)) * 0.16
    return np.stack([sig, sig], axis=1)


# ==============================================================================
# 3. DYNAMIC ART DECO JAZZ-LOUNGE BGM (SHIFTS WITH STORY MOOD!)
# ==============================================================================

def _synthesize_bgm(total_s: float, scene_ranges: List[Tuple[float, float, str]]) -> np.ndarray:
    """Synthesize a crisp, charming 118 BPM Art Deco lounge-jazz BGM evolving with the 3 lighting moods."""
    n = int(math.ceil(total_s * SR))
    bgm = np.zeros((n, 2), dtype=np.float32)
    rng = np.random.default_rng(2026)

    bpm = 118.0
    beat_s = 60.0 / bpm
    total_beats = int(total_s / beat_s) + 1

    # Walking upright-bass note tables (Hz) per mood!
    bass_morning = [130.81, 146.83, 164.81, 196.00, 174.61, 164.81, 146.83, 123.47]  # C major Art Deco bounce
    bass_stress = [110.00, 116.54, 130.81, 123.47, 110.00, 103.83, 116.54, 130.81]   # Tense A-minor chromatic creep
    bass_golden = [130.81, 164.81, 196.00, 220.00, 174.61, 196.00, 220.00, 196.00]   # Warm Cmaj7/Fmaj7 glide

    chords_morning = [
        [261.63, 329.63, 392.00, 493.88],
        [293.66, 349.23, 440.00, 523.25],
    ]
    chords_stress = [
        [220.00, 261.63, 329.63, 392.00],
        [233.08, 293.66, 349.23, 415.30],
    ]
    chords_golden = [
        [261.63, 329.63, 392.00, 493.88, 587.33],
        [349.23, 440.00, 523.25, 659.25],
    ]

    def _mood_at(sec: float) -> str:
        for s0, s1, m in scene_ranges:
            if s0 <= sec < s1:
                return m
        return "golden_mirror"

    for b in range(total_beats):
        t0 = b * beat_s
        i0 = int(t0 * SR)
        if i0 >= n:
            break
        mood = _mood_at(t0)

        # 1. Warm Plucked Walking Bass on every beat!
        b_list = bass_morning if mood == "morning_busy" else (bass_stress if mood == "midday_stress" else bass_golden)
        f_bass = b_list[b % len(b_list)]
        dur_b = min(beat_s * 0.85, (n - i0) / SR)
        mb = int(dur_b * SR)
        if mb > 10:
            tb = np.linspace(0, dur_b, mb, dtype=np.float32)
            bass = (np.sin(2 * np.pi * f_bass * tb) + 0.35 * np.sin(2 * np.pi * f_bass * 2 * tb)) * np.exp(-tb * 4.2)
            bass *= 1.0 - np.exp(-tb * 90.0)
            bgm[i0 : i0 + mb, 0] += bass * 0.24
            bgm[i0 : i0 + mb, 1] += bass * 0.24

        # 2. Warm Rhodes / Electric Piano Art Deco Comping Chords on beats 0 & 2 (off-beat swing feel!)
        if b % 2 == 0:
            c_bank = chords_morning if mood == "morning_busy" else (chords_stress if mood == "midday_stress" else chords_golden)
            chord = c_bank[(b // 4) % len(c_bank)]
            dur_c = min(beat_s * (1.8 if mood == "golden_mirror" else 1.2), (n - i0) / SR)
            mc = int(dur_c * SR)
            if mc > 10:
                tc = np.linspace(0, dur_c, mc, dtype=np.float32)
                pad = np.zeros(mc, dtype=np.float32)
                for f in chord:
                    pad += (np.sin(2 * np.pi * f * tc) + 0.14 * np.sin(2 * np.pi * f * 2 * tc)) * np.exp(-tc * (1.6 if mood == "golden_mirror" else 2.8))
                pad *= (1.0 - np.exp(-tc * 45.0)) * (0.065 if mood == "golden_mirror" else 0.048)
                bgm[i0 : i0 + mc, 0] += pad * 0.92
                bgm[i0 : i0 + mc, 1] += pad * 1.08

        # 3. Light Brushed Jazz Hi-Hat / Rim Swing Pulse
        hh_len = min(int(0.055 * SR), n - i0)
        if hh_len > 12:
            th = np.linspace(0, hh_len / SR, hh_len, dtype=np.float32)
            hh = _bp_filter(rng.normal(0, 1.0, hh_len).astype(np.float32), 4500, 11000) * np.exp(-th * 55.0)
            amp = 0.075 if b % 2 == 1 else 0.045
            bgm[i0 : i0 + hh_len, 0] += hh * amp
            bgm[i0 : i0 + hh_len, 1] += hh * amp

    # Soft warm lowpass glue & fade out cleanly on final 1.2s
    bgm[:, 0] = _lp_filter(bgm[:, 0], 8500.0)
    bgm[:, 1] = _lp_filter(bgm[:, 1], 8500.0)
    fade_n = min(int(1.2 * SR), n)
    bgm[-fade_n:] *= np.linspace(1.0, 0.0, fade_n, dtype=np.float32)[:, None]
    return bgm


# ==============================================================================
# 4. BOLD POP-IN WORD-BY-WORD ASS SUBTITLES (1-3 WORDS, SAFE ZONE 9:16)
# ==============================================================================

def _ass_time(sec: float) -> str:
    sec = max(0.0, sec)
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    cs = int(round((sec - math.floor(sec)) * 100.0))
    if cs >= 100:
        s += 1
        cs -= 100
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def _build_ass_subtitles(all_word_events: List[Tuple[str, float, float]], out_ass: Path) -> None:
    """Group words into crisp 1-3 word pop-in chunks in the 9:16 lower-middle safe area."""
    header = f"""[Script Info]
Title: Cermin Murah yang Mempercepat Lift
ScriptType: v4.00+
PlayResX: {WIDTH}
PlayResY: {HEIGHT}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: ViralCap,DejaVu Sans,84,&H00FFFFFF,&H0000D7FF,&H00120E16,&H80000000,-1,0,0,0,100,100,1.5,0,1,8,4,2,70,70,395,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    chunks: List[Tuple[str, float, float]] = []
    buf: List[Tuple[str, float, float]] = []

    def _flush() -> None:
        if not buf:
            return
        raw_words = [w for (w, _, _) in buf]
        formatted_words = []
        for w in raw_words:
            clean = re.sub(r"[^A-Za-z0-9]", "", w).upper()
            up = w.upper()
            if clean in HIGHLIGHT_KEYWORDS:
                # Vibrant Art Deco Gold highlight on key punchline words!
                formatted_words.append(f"{{\\c&H0048D1FF&}}{up}{{\\c&H00FFFFFF&}}")
            else:
                formatted_words.append(up)
        text = " ".join(formatted_words)
        chunks.append((text, buf[0][1], buf[-1][2]))
        buf.clear()

    for w, t0, t1 in all_word_events:
        # Flush on natural pause or max 2–3 short words (<= 17 chars)
        if buf:
            cur_len = sum(len(x[0]) + 1 for x in buf) + len(w)
            gap = t0 - buf[-1][2]
            if len(buf) >= 3 or cur_len > 18 or gap > 0.35:
                _flush()
        buf.append((w, t0, t1))
        if any(w.endswith(p) for p in ("!", "?", ".", "—")):
            _flush()
    _flush()

    lines = [header]
    for idx, (txt, t0, t1) in enumerate(chunks):
        # Prevent tiny flicker gaps between adjacent chunks inside same sentence
        if idx + 1 < len(chunks) and chunks[idx + 1][1] - t1 < 0.14:
            t1 = chunks[idx + 1][1]
        t1 = max(t1, t0 + 0.24)
        # Crisp elastic pop-in scale animation!
        pop = r"{\fscx86\fscy86\t(0,85,\fscx106\fscy106)\t(85,150,\fscx100\fscy100)}"
        lines.append(f"Dialogue: 0,{_ass_time(t0)},{_ass_time(t1)},ViralCap,,0,0,0,,{pop}{txt}\n")

    out_ass.parent.mkdir(parents=True, exist_ok=True)
    out_ass.write_text("".join(lines), encoding="utf-8")


# ==============================================================================
# MAIN PIPELINE ENTRYPOINT
# ==============================================================================

def main() -> None:
    audio_dir = REPO_ROOT / "output" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    print("[Audio 1/4] Synthesizing Indonesian voiceover narration (edge-tts)...")
    scene_vo = synthesize_all_narration(audio_dir)

    # Compute exact cumulative timeline locked cleanly to 30 FPS frames
    cursor_frame = 0
    timeline_entries = []
    scene_ranges = []
    for item in scene_vo:
        sc: SceneSpec = item["scene"]
        f_start = cursor_frame + 1
        f_end = cursor_frame + item["num_frames"]
        t_start = cursor_frame / FPS
        t_end = f_end / FPS
        cursor_frame = f_end

        scene_ranges.append((t_start, t_end, sc.mood))
        timeline_entries.append(
            {
                "scene_id": sc.scene_id,
                "slug": sc.slug,
                "title": sc.title,
                "mood": sc.mood,
                "mirrors_on": sc.mirrors_on,
                "rocket_on": sc.rocket_on,
                "narration": sc.narration,
                "start_s": round(t_start, 4),
                "end_s": round(t_end, 4),
                "duration_s": round(item["duration_s"], 4),
                "frame_start": f_start,
                "frame_end": f_end,
                "num_frames": item["num_frames"],
                "tts_ok": item["tts_ok"],
            }
        )

    total_frames = cursor_frame
    total_s = total_frames / FPS
    print(f"            Total locked timeline: {total_s:.2f}s ({total_frames} frames @ {FPS} FPS)")

    print("[Audio 2/4] Synthesizing dynamic Art Deco lounge-jazz BGM & synced Foley SFX...")
    total_samples = int(math.ceil(total_s * SR))
    vo_bus = np.zeros((total_samples, 2), dtype=np.float32)
    sfx_bus = np.zeros((total_samples, 2), dtype=np.float32)
    all_words: List[Tuple[str, float, float]] = []

    sfx_cache: Dict[str, np.ndarray] = {}
    for entry, item in zip(timeline_entries, scene_vo):
        sc = item["scene"]
        t0 = entry["start_s"]
        dur = entry["duration_s"]

        # Place narration clip on VO bus
        vo_i0 = int((t0 + item["lead_s"]) * SR)
        pcm = item["pcm"]
        end_i = min(total_samples, vo_i0 + len(pcm))
        if end_i > vo_i0:
            vo_bus[vo_i0:end_i] += pcm[: end_i - vo_i0] * 1.15

        # Collect absolute word timings for subtitles
        for w, ws, we in item["words"]:
            all_words.append((w, t0 + ws, t0 + we))

        # Place synced Foley SFX cues on SFX bus
        for cue_idx, cue in enumerate(sc.sfx_cues):
            if cue.sfx_type not in sfx_cache:
                sfx_cache[cue.sfx_type] = _make_sfx(cue.sfx_type, seed=sc.scene_id * 13 + cue_idx)
            clip = sfx_cache[cue.sfx_type]
            si0 = int((t0 + cue.offset_ratio * dur) * SR)
            send = min(total_samples, si0 + len(clip))
            if send > si0:
                sfx_bus[si0:send] += clip[: send - si0] * cue.volume * 0.65

    bgm_bus = _synthesize_bgm(total_s, scene_ranges)
    if len(bgm_bus) > total_samples:
        bgm_bus = bgm_bus[:total_samples]
    elif len(bgm_bus) < total_samples:
        pad = np.zeros((total_samples - len(bgm_bus), 2), dtype=np.float32)
        bgm_bus = np.vstack([bgm_bus, pad])

    # Smooth sidechain ducking on BGM whenever voiceover is speaking!
    vo_env = np.abs(vo_bus).mean(axis=1)
    # Smooth envelope with ~120ms moving average
    win = int(0.12 * SR)
    kernel = np.ones(win, dtype=np.float32) / win
    smooth_env = np.convolve(vo_env, kernel, mode="same")
    duck_gain = np.where(smooth_env > 0.015, 0.34, 0.72).astype(np.float32)
    duck_gain = np.convolve(duck_gain, kernel, mode="same")

    master = np.nan_to_num(vo_bus + sfx_bus + bgm_bus * duck_gain[:, None], nan=0.0, posinf=0.0, neginf=0.0)
    # Gentle soft-clip mastering limiter
    peak = float(np.max(np.abs(master))) or 1.0
    if peak > 0.92:
        master = master * (0.92 / peak)

    print("[Audio 3/4] Writing master_mix.wav & timing_manifest.json...")
    mix_path = audio_dir / "master_mix.wav"
    _write_wav(mix_path, master, SR)

    manifest = {
        "fps": FPS,
        "width": WIDTH,
        "height": HEIGHT,
        "total_frames": total_frames,
        "total_duration_s": round(total_s, 4),
        "master_audio": str(mix_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        "subtitles_ass": "output/audio/subtitles.ass",
        "scenes": timeline_entries,
    }
    manifest_path = audio_dir / "timing_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print("[Audio 4/4] Generating viral bold pop-in ASS subtitles...")
    ass_path = audio_dir / "subtitles.ass"
    _build_ass_subtitles(all_words, ass_path)
    print(f"            Saved {mix_path} ({mix_path.stat().st_size // 1024} KB) & {ass_path}")


if __name__ == "__main__":
    main()
