"""生成原创的轻音乐、环境音与交互音效（无第三方音频素材）。

输出到 src/qiqi_town/assets/audio，22050 Hz / 16-bit / mono WAV。
"""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "src" / "qiqi_town" / "assets" / "audio"
SR = 22050
random.seed(20261029)


def envelope(t: float, attack: float, release: float, duration: float) -> float:
    if t < attack:
        return t / max(attack, 1e-6)
    if t > duration - release:
        return max(0.0, (duration - t) / max(release, 1e-6))
    return 1.0


def write_wav(name: str, samples: list[float], gain: float = 0.8) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    peak = max(1e-9, max(abs(s) for s in samples))
    scale = (32767 * gain) / peak
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SR)
        frames = bytearray()
        for sample in samples:
            frames += struct.pack("<h", int(max(-32768, min(32767, sample * scale))))
        wav.writeframes(frames)
    print(f"wrote {path.name}: {len(samples) / SR:.1f}s, {path.stat().st_size // 1024} KiB")


def note_freq(name: str, octave: int) -> float:
    semitones = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}[name]
    midi = 12 * (octave + 1) + semitones
    return 440.0 * (2.0 ** ((midi - 69) / 12.0))


def add_tone(
    buf: list[float],
    start: float,
    duration: float,
    freq: float,
    amp: float,
    *,
    harmonics: tuple[float, ...] = (1.0, 0.3, 0.12),
    vibrato: float = 0.0,
) -> None:
    begin = int(start * SR)
    count = int(duration * SR)
    for i in range(count):
        t = i / SR
        if begin + i >= len(buf):
            break
        env = envelope(t, 0.02, min(0.6, duration * 0.4), duration)
        phase = 2 * math.pi * freq * t + vibrato * math.sin(2 * math.pi * 4.5 * t)
        sample = sum(h * math.sin(phase * (h_index + 1)) for h_index, h in enumerate(harmonics))
        buf[begin + i] += sample * amp * env


def add_noise(buf: list[float], start: float, duration: float, amp: float, lowpass: float = 0.05) -> None:
    begin = int(start * SR)
    count = int(duration * SR)
    value = 0.0
    for i in range(count):
        if begin + i >= len(buf):
            break
        t = i / SR
        value += (random.random() * 2 - 1 - value) * lowpass
        env = envelope(t, 0.03, duration * 0.5, duration)
        buf[begin + i] += value * amp * env


def make_music(name: str, duration: float, chords: list[list[str]], melody: list[tuple[float, str, int]], *, tempo_pad: float = 0.55) -> list[float]:
    buf = [0.0] * int(duration * SR)
    section = duration / len(chords)
    for index, chord in enumerate(chords):
        start = index * section
        for note in chord:
            add_tone(buf, start, section + 0.8, note_freq(note, 3), 0.10, harmonics=(1.0, 0.25, 0.08), vibrato=0.02)
            add_tone(buf, start, section + 0.6, note_freq(note, 4), 0.035, harmonics=(1.0, 0.12))
    for start, note, octave in melody:
        add_tone(buf, start, 1.4, note_freq(note, octave), 0.10, harmonics=(1.0, 0.35, 0.1), vibrato=0.08)
    # 很轻的底噪，避免过于电子。
    add_noise(buf, 0, duration, 0.012, lowpass=0.008)
    # 循环首尾淡入淡出。
    fade = int(0.5 * SR)
    for i in range(fade):
        buf[i] *= i / fade
        buf[-1 - i] *= i / fade
    return buf


def make_ambience(name: str, duration: float, *, birds: bool) -> list[float]:
    buf = [0.0] * int(duration * SR)
    add_noise(buf, 0, duration, 0.06, lowpass=0.004)
    if birds:
        for _ in range(16):
            start = random.uniform(0.5, duration - 1.0)
            base = random.uniform(1900, 3200)
            for k in range(3):
                add_tone(buf, start + k * 0.11, 0.08, base * random.uniform(0.9, 1.15), 0.045, harmonics=(1.0, 0.1))
    fade = int(0.5 * SR)
    for i in range(fade):
        buf[i] *= i / fade
        buf[-1 - i] *= i / fade
    return buf


def make_sfx(name: str, duration: float, generator) -> None:
    buf = [0.0] * int(duration * SR)
    generator(buf)
    write_wav(name, buf, 0.85)


def main() -> None:
    town = make_music(
        "town_day.wav",
        48.0,
        [["C", "E", "G", "B"], ["F", "A", "C", "E"], ["A", "C", "E", "G"], ["G", "B", "D", "F"]],
        [
            (0.5, "E", 5), (1.2, "G", 5), (2.0, "A", 5), (3.0, "G", 5),
            (4.5, "D", 5), (5.4, "E", 5), (6.4, "G", 5), (7.2, "A", 5),
            (9.0, "C", 5), (10.0, "A", 4), (11.0, "G", 4), (12.0, "E", 5),
            (13.5, "D", 5), (14.4, "E", 5), (15.4, "G", 5), (16.4, "A", 5),
            (18.0, "E", 5), (19.0, "G", 5), (20.0, "A", 5), (21.0, "C", 6),
            (22.5, "A", 5), (23.4, "G", 5), (24.2, "E", 5), (25.0, "D", 5),
            (27.0, "C", 5), (28.0, "D", 5), (29.0, "E", 5), (30.0, "G", 5),
            (31.5, "A", 5), (32.4, "G", 5), (33.4, "E", 5), (34.4, "D", 5),
            (36.0, "C", 5), (37.0, "E", 5), (38.0, "G", 5), (39.0, "A", 5),
            (40.5, "C", 6), (41.4, "A", 5), (42.4, "G", 5), (43.4, "E", 5),
            (45.0, "D", 5), (46.0, "E", 5),
        ],
    )
    write_wav("town_day.wav", town, 0.72)

    interior = make_music(
        "interior.wav",
        36.0,
        [["C", "E", "G"], ["A", "C", "E"], ["F", "A", "C"], ["G", "B", "D"]],
        [
            (0.5, "E", 5), (2.0, "G", 5), (3.5, "A", 5), (5.0, "G", 5),
            (7.0, "E", 5), (8.5, "D", 5), (10.0, "C", 5), (12.0, "D", 5),
            (14.0, "E", 5), (16.0, "G", 5), (18.0, "A", 5), (20.0, "G", 5),
            (22.0, "E", 5), (24.0, "D", 5), (26.0, "C", 5), (28.0, "A", 4),
            (30.0, "C", 5), (32.0, "E", 5), (34.0, "D", 5),
        ],
    )
    write_wav("interior.wav", interior, 0.58)

    dusk = make_music(
        "dusk.wav",
        36.0,
        [["F", "A", "C"], ["G", "B", "D"], ["A", "C", "E"], ["C", "E", "G"]],
        [
            (0.5, "A", 4), (2.0, "C", 5), (4.0, "E", 5), (6.0, "D", 5),
            (8.0, "C", 5), (10.0, "A", 4), (12.0, "G", 4), (14.0, "A", 4),
            (16.0, "C", 5), (18.0, "D", 5), (20.0, "E", 5), (22.0, "G", 5),
            (24.0, "E", 5), (26.0, "D", 5), (28.0, "C", 5), (30.0, "A", 4),
            (32.0, "G", 4), (34.0, "A", 4),
        ],
    )
    write_wav("dusk.wav", dusk, 0.60)

    write_wav("ambience_town.wav", make_ambience("ambience_town.wav", 30.0, birds=True), 0.35)
    write_wav("ambience_interior.wav", make_ambience("ambience_interior.wav", 30.0, birds=False), 0.22)

    make_sfx("click.wav", 0.10, lambda b: add_tone(b, 0.0, 0.09, 880, 0.4, harmonics=(1.0, 0.2)))
    make_sfx("choose.wav", 0.5, lambda b: (add_tone(b, 0.0, 0.35, 660, 0.25), add_tone(b, 0.12, 0.35, 880, 0.22)))
    make_sfx("save.wav", 1.0, lambda b: [add_tone(b, i * 0.13, 0.5, f, 0.22) for i, f in enumerate((523, 659, 784, 1046))])
    make_sfx("success.wav", 1.2, lambda b: [add_tone(b, i * 0.11, 0.7, f, 0.24) for i, f in enumerate((523, 659, 784, 1046, 1318))])
    make_sfx("page.wav", 0.25, lambda b: add_noise(b, 0.0, 0.22, 0.5, lowpass=0.2))
    make_sfx("door.wav", 0.55, lambda b: add_noise(b, 0.0, 0.5, 0.35, lowpass=0.03))
    make_sfx("step.wav", 0.12, lambda b: add_tone(b, 0.0, 0.1, 130, 0.35, harmonics=(1.0, 0.4)))
    make_sfx("duck.wav", 0.35, lambda b: [add_tone(b, i * 0.1, 0.12, 380 + (i % 2) * 60, 0.3) for i in range(3)])
    make_sfx("swing.wav", 0.5, lambda b: add_noise(b, 0.0, 0.45, 0.35, lowpass=0.03))
    make_sfx("lantern.wav", 1.4, lambda b: (add_tone(b, 0.0, 1.1, 784, 0.22), add_tone(b, 0.02, 1.0, 1175, 0.12)))
    make_sfx("error.wav", 0.35, lambda b: add_tone(b, 0.0, 0.3, 220, 0.25, harmonics=(1.0, 0.2)))


if __name__ == "__main__":
    main()
