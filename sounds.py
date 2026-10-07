"""sounds.py - tiny synthesised sound effects (no sound files needed).

If the computer has no audio device the game simply runs silently.
"""
import array
import math
import random
import pygame

RATE = 22050


def _tone(freq, ms, volume=0.4, wave="sine", end_freq=None):
    """Make `ms` milliseconds of sound, fading out. A sweep goes freq -> end_freq."""
    count = int(RATE * ms / 1000)
    end_freq = freq if end_freq is None else end_freq
    data = array.array("h")
    phase = 0.0
    for i in range(count):
        f = freq + (end_freq - freq) * i / count
        phase += 2 * math.pi * f / RATE
        if wave == "square":
            value = 1.0 if math.sin(phase) > 0 else -1.0
        elif wave == "noise":
            value = random.uniform(-1, 1)
        else:
            value = math.sin(phase)
        envelope = min(1.0, i / 120) * (1 - i / count)
        data.append(int(32767 * volume * value * envelope))
    return data


class Sounds:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            pygame.mixer.init(frequency=RATE, size=-16, channels=1, buffer=512, allowedchanges=0)
        except pygame.error:
            return                      # no audio device: stay silent
        win = _tone(523, 110, 0.35, "square") + _tone(659, 110, 0.35, "square") + \
            _tone(784, 110, 0.35, "square") + _tone(1047, 380, 0.35, "square")
        lose = _tone(420, 700, 0.35, "square", 60)
        for i, x in enumerate(_tone(300, 700, 0.35, "noise")):
            lose[i] = int(lose[i] * 0.7 + x * 0.5)
        recipes = {
            "step": (_tone(300, 45, 0.10), 0.5),
            "bump": (_tone(110, 90, 0.5), 0.6),
            "select": (_tone(700, 55, 0.3, "square"), 0.4),
            "confirm": (_tone(500, 70, 0.3, "square") + _tone(900, 110, 0.3, "square"), 0.5),
            "beep": (_tone(660, 140, 0.4), 0.7),
            "go": (_tone(1320, 320, 0.4, "square"), 0.6),
            "win": (win, 0.7),
            "lose": (lose, 0.8),
            "tick": (_tone(1500, 40, 0.3, "square"), 0.5),
        }
        for name, (samples, volume) in recipes.items():
            sound = pygame.mixer.Sound(buffer=samples.tobytes())
            sound.set_volume(volume)
            self.sounds[name] = sound
        self.enabled = True

    def play(self, name):
        if self.enabled:
            self.sounds[name].play()
