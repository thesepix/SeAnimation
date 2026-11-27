"""Zentrale Konfiguration.

MVP: hartkodierte Defaults (N3). Step 2: Auslagerung in eine Config-Datei.
"""

from pathlib import Path

# Ordner mit den Animations-Clips (Bilder/Videos). Wird im MVP manuell gesetzt.
MEDIA_DIR = Path(__file__).resolve().parent.parent / "media"

# Audio: MVP = Standard-/erstes verfügbares Windows-Audiogerät (WASAPI-Loopback).
# None = System-Default; später in der UI wählbar.
AUDIO_DEVICE = None
AUDIO_SAMPLERATE = 48000
AUDIO_BLOCKSIZE = 512

# Rendering (N1)
TARGET_FPS = 60
MAX_AUDIO_LATENCY_MS = 100

# Beat-Sync-Modell (Abschnitt 3.3 in ANFORDERUNGEN.md)
FRAME_STEP_BEATS = 1          # Video-Frame-Step: 1 Frame pro N Beats
FRAMES_PER_BEAT = FRAME_STEP_BEATS
DEFAULT_CLIP_LOOP_BEATS = 4   # Standard-Looplänge eines Clips in Beats
BEAT_DECAY_TAU = 0.25         # Zeitkonstante der Beat-Envelope in Sekunden

# GUI/Renderer (Abschnitt 3.5)
PREVIEW_SIZE = (960, 540)
OUTPUT_SIZE = (1280, 720)
