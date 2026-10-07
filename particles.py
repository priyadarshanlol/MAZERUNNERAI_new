"""particles.py - glow lights and the particle system (dust, sparks, confetti)."""
import math
import random
import pygame

# ---------------------------------------------------------------- glow ----
_glow_cache = {}


def _get_glow(radius, color):
    """A black square with a soft coloured light in the middle (cached)."""
    key = (radius, color)
    surf = _glow_cache.get(key)
    if surf is None:
        surf = pygame.Surface((radius * 2, radius * 2))
        step = 2 if radius > 20 else 1
        for r in range(radius, 0, -step):
            k = (1 - r / radius) ** 2
            shade = (int(color[0] * k), int(color[1] * k), int(color[2] * k))
            pygame.draw.circle(surf, shade, (radius, radius), r)
        _glow_cache[key] = surf
    return surf


def draw_glow(target, center, radius, color, strength=1.0):
    """Add a soft light to `target` (additive blending = it looks like light)."""
    radius = max(2, int(radius) // 2 * 2)
    strength = round(max(0.0, min(1.0, strength)) * 8) / 8
    if strength <= 0:
        return
    shade = (int(color[0] * strength), int(color[1] * strength), int(color[2] * strength))
    glow = _get_glow(radius, shade)
    target.blit(glow, (center[0] - radius, center[1] - radius),
                special_flags=pygame.BLEND_RGB_ADD)


# ------------------------------------------------------------ particles ----
class Particle:
    __slots__ = ("x", "y", "vx", "vy", "life", "max_life", "size",
                 "color", "gravity", "kind", "spin")

    def __init__(self, x, y, vx, vy, life, size, color, gravity, kind):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.life = self.max_life = life
        self.size, self.color, self.gravity, self.kind = size, color, gravity, kind
        self.spin = random.uniform(0, 6.28)


class ParticleSystem:
    MAX_PARTICLES = 700

    def __init__(self):
        self.items = []

    def clear(self):
        self.items.clear()

    def add(self, x, y, vx, vy, life, size, color, gravity=0.0, kind="spark"):
        if len(self.items) >= self.MAX_PARTICLES:
            del self.items[:20]
        self.items.append(Particle(x, y, vx, vy, life, size, color, gravity, kind))

    # ---- ready-made effects ----
    def dust(self, x, y, n=4, color=(120, 150, 190)):
        for _ in range(n):
            a = random.uniform(0, 6.28)
            s = random.uniform(10, 45)
            self.add(x, y, math.cos(a) * s, math.sin(a) * s - 10, random.uniform(0.25, 0.5),
                     random.uniform(2, 4), color, kind="dust")

    def burst(self, x, y, color, n=50, speed=300):
        for _ in range(n):
            a = random.uniform(0, 6.28)
            s = random.uniform(speed * 0.2, speed)
            self.add(x, y, math.cos(a) * s, math.sin(a) * s, random.uniform(0.5, 1.2),
                     random.uniform(3, 6), color, gravity=120)

    def confetti(self, x, y, n=60, spread=300):
        palette = [(255, 60, 120), (0, 240, 255), (255, 220, 70), (120, 255, 150), (200, 120, 255)]
        for _ in range(n):
            self.add(x + random.uniform(-spread, spread), y, random.uniform(-90, 90),
                     random.uniform(-260, -40), random.uniform(1.8, 3.2), random.uniform(6, 11),
                     random.choice(palette), gravity=260, kind="confetti")

    def swirl(self, x, y, color):
        a = random.uniform(0, 6.28)
        r = random.uniform(24, 36)
        self.add(x + math.cos(a) * r, y + math.sin(a) * r,
                 -math.cos(a) * 60 - math.sin(a) * 90, -math.sin(a) * 60 + math.cos(a) * 90,
                 0.5, 3, color)

    # ---- per frame ----
    def update(self, dt):
        alive = []
        for p in self.items:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.spin += dt * 12
            if p.kind == "dust":
                p.vx *= 0.92
                p.vy *= 0.92
            alive.append(p)
        self.items = alive

    def draw(self, surf):
        for p in self.items:
            k = p.life / p.max_life
            if p.kind == "confetti":
                w = max(1, int(abs(math.cos(p.spin)) * p.size))
                pygame.draw.rect(surf, p.color, (int(p.x), int(p.y), w, int(p.size * 0.6) + 1))
            elif p.kind == "dust":
                shade = (int(p.color[0] * k), int(p.color[1] * k), int(p.color[2] * k))
                pygame.draw.circle(surf, shade, (int(p.x), int(p.y)), max(1, int(p.size * k)))
            else:
                draw_glow(surf, (p.x, p.y), p.size * k * 3 + 4, p.color, k)
                pygame.draw.circle(surf, (255, 255, 255), (int(p.x), int(p.y)), max(1, int(p.size * k * 0.5)))
