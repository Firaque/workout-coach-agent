import math
import wave
import struct
import random

sample_rate = 44100
bpm = 85
beat_duration = 60.0 / bpm  # ~0.7058 sec per beat
bar_duration = beat_duration * 4  # ~2.8235 sec per bar
total_seconds = 36  # ~12.75 bars

num_samples = int(sample_rate * total_seconds)
audio = [0.0] * num_samples

def midi_to_freq(note):
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

# Upbeat Lo-fi Chords (Cmaj7, Am7, Fmaj7, G7)
chords = [
    [60, 64, 67, 71],  # Cmaj7 (C4, E4, G4, B4)
    [57, 60, 64, 67],  # Am7   (A3, C4, E4, G4)
    [53, 57, 60, 64],  # Fmaj7 (F3, A3, C4, E4)
    [55, 59, 62, 65],  # G7    (G3, B3, D4, F4)
]

# Generate Piano/Rhodes Chords
for bar in range(int(total_seconds / bar_duration) + 1):
    chord = chords[bar % len(chords)]
    bar_start_sample = int(bar * bar_duration * sample_rate)
    
    # Play chord on beat 1 and beat 2.5
    stabs = [0, int(beat_duration * 2.5 * sample_rate)]
    for stab in stabs:
        stab_start = bar_start_sample + stab
        duration = int(beat_duration * 2.2 * sample_rate)
        
        for note in chord:
            freq = midi_to_freq(note)
            for i in range(duration):
                idx = stab_start + i
                if idx >= num_samples:
                    break
                t = i / sample_rate
                # Warm sine wave + soft 2nd & 3rd harmonics (Rhodes synth feel)
                envelope = math.exp(-i / (sample_rate * 0.8)) * (1.0 - math.exp(-i / (sample_rate * 0.01)))
                val = (
                    0.5 * math.sin(2 * math.pi * freq * t) +
                    0.25 * math.sin(2 * math.pi * freq * 2 * t) +
                    0.12 * math.sin(2 * math.pi * freq * 3 * t)
                ) * envelope * 0.15
                audio[idx] += val

# Generate Bassline
bass_notes = [48, 45, 41, 43] # C2, A1, F1, G1
for bar in range(int(total_seconds / bar_duration) + 1):
    note = bass_notes[bar % len(bass_notes)]
    freq = midi_to_freq(note)
    bar_start_sample = int(bar * bar_duration * sample_rate)
    
    # Bass on beat 1 and 3
    for beat in [0, 2]:
        start = bar_start_sample + int(beat * beat_duration * sample_rate)
        duration = int(beat_duration * 1.8 * sample_rate)
        for i in range(duration):
            idx = start + i
            if idx >= num_samples:
                break
            t = i / sample_rate
            envelope = math.exp(-i / (sample_rate * 0.9))
            # Deep warm sub bass
            val = (0.7 * math.sin(2 * math.pi * freq * t) + 0.3 * math.sin(2 * math.pi * freq * 2 * t)) * envelope * 0.25
            audio[idx] += val

# Generate Drums (Kick, Snare/Clap, Hihats)
for i in range(num_samples):
    t = i / sample_rate
    current_beat = (t % bar_duration) / beat_duration
    
    # Kick on beat 0 and beat 2.5
    beat_in_bar = (i / (beat_duration * sample_rate)) % 4
    
    # Simple Kick sound generator
    if abs(beat_in_bar - 0) < 0.05 or abs(beat_in_bar - 2.5) < 0.05:
        kick_t = (beat_in_bar % 0.5) * beat_duration
        if kick_t < 0.15:
            f_kick = 120.0 * math.exp(-kick_t * 30.0)
            env_kick = math.exp(-kick_t * 20.0)
            audio[i] += math.sin(2 * math.pi * f_kick * kick_t) * env_kick * 0.4

    # Snare on beat 1 and beat 3
    if abs(beat_in_bar - 1) < 0.05 or abs(beat_in_bar - 3) < 0.05:
        snare_t = (beat_in_bar % 1) * beat_duration
        if snare_t < 0.18:
            noise = (random.random() * 2.0 - 1.0)
            env_snare = math.exp(-snare_t * 18.0)
            audio[i] += noise * env_snare * 0.18

    # Hi-hat on 8th notes
    eighth_beat = (beat_in_bar * 2) % 1
    if eighth_beat < 0.1:
        hh_t = eighth_beat * (beat_duration / 2.0)
        noise = (random.random() * 2.0 - 1.0)
        env_hh = math.exp(-hh_t * 60.0)
        audio[i] += noise * env_hh * 0.06

    # Subtle vinyl crackle background
    if random.random() < 0.003:
        audio[i] += (random.random() * 2.0 - 1.0) * 0.03

# Normalize audio and write to WAV
max_val = max(abs(x) for x in audio)
scale = 0.8 / max_val if max_val > 0 else 1.0

with wave.open("lofi_bg_music.wav", "w") as wf:
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)
    frames = bytearray()
    for x in audio:
        sample = int(x * scale * 32767.0)
        sample = max(-32768, min(32767, sample))
        frames.extend(struct.pack("<h", sample))
    wf.writeframes(frames)

print("Saved lofi_bg_music.wav successfully!")
