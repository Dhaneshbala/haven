"""Sprites are drawn in code once at startup.

The two archers are the supplied pixel art, scaled down to the arena
and given the same two-frame walk the gunners used.
"""

import math
import os
import random

import pygame

from settings import (
    VH, VW, NAVY, WHITE, P1_COLORS, P2_COLORS,
    TARGET_BODY, TARGET_LIGHT, TARGET_DARK, TARGET_CORE,
)


def _sheet(rows, palette):
    """Turn rows of chars into a transparent surface."""
    width = len(rows[0])
    surf = pygame.Surface((width, len(rows)), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return surf


_ARCHER_DIR = os.path.dirname(os.path.abspath(__file__))

# The four bullseyes in target_reference.png.  These crops deliberately avoid
# the large green/orange character in the supplied reference.
_TARGET_CROPS = (
    (185, 19, 180, 180),   # upper-left target
    (500, 75, 245, 245),   # upper-right target
    (670, 380, 150, 150),  # middle-right target
    (690, 600, 220, 220),  # lower-right target
)

_FLASH_SMALL = (".X.", "XXX", ".X.")
_FLASH_BIG = (".lWl.", "lWWWl", ".lWl.")

def _load_reference_sprite(filename):
    """Crop a supplied sprite and drop any white reference backdrop."""
    path = os.path.join(_ARCHER_DIR, "assets", filename)
    image = pygame.image.load(path).convert_alpha()
    width, height = image.get_size()
    for y in range(height):
        for x in range(width):
            color = image.get_at((x, y))
            if color.a < 20 or (color.r > 240 and color.g > 240 and color.b > 240):
                image.set_at((x, y), (0, 0, 0, 0))
    min_x, min_y, max_x, max_y = width, height, 0, 0
    for y in range(height):
        for x in range(width):
            if image.get_at((x, y)).a > 10:
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
    return image.subsurface((min_x, min_y, max_x - min_x + 1, max_y - min_y + 1)).copy()


def _fit_archer(source):
    """Integer downsample so the archer stays crisp on the 320x180 screen."""
    width, height = source.get_size()
    out = pygame.Surface((width // 2, height // 2), pygame.SRCALPHA)
    for y in range(height // 2):
        for x in range(width // 2):
            samples = []
            for dy in range(2):
                for dx in range(2):
                    color = source.get_at((x * 2 + dx, y * 2 + dy))
                    if color.a > 20:
                        samples.append(color)
            if not samples:
                continue
            bow = [color for color in samples if color.r > 200 and color.g < 100]
            pick = bow[0] if bow else samples[0]
            out.set_at((x, y), (pick.r, pick.g, pick.b, 255))
    return out


def _fit_arrow(source):
    """Use the same 2x pixel scale as the archers without softening it."""
    width, height = source.get_size()
    return pygame.transform.scale(source, (width // 2, height // 2))


def _charged_arrow(source, amount):
    """Brighten a bounced arrow, preserving its supplied silhouette."""
    out = source.copy()
    for y in range(out.get_height()):
        for x in range(out.get_width()):
            color = out.get_at((x, y))
            if color.a < 20:
                continue
            out.set_at((x, y), (
                min(255, color.r + amount),
                min(255, color.g + amount),
                min(255, color.b + amount),
                color.a,
            ))
    return out


def _clear_edge_background(image):
    """Remove only the white backdrop connected to the crop's outer edge.

    The targets have a white scoring ring, so a simple "remove all white"
    pass would destroy part of the supplied artwork.
    """
    out = image.copy()
    width, height = out.get_size()
    pending = []
    for x in range(width):
        pending.extend(((x, 0), (x, height - 1)))
    for y in range(1, height - 1):
        pending.extend(((0, y), (width - 1, y)))
    seen = set()
    while pending:
        x, y = pending.pop()
        if (x, y) in seen or not (0 <= x < width and 0 <= y < height):
            continue
        seen.add((x, y))
        color = out.get_at((x, y))
        if color.a < 20 or not (color.r > 240 and color.g > 240 and color.b > 240):
            continue
        out.set_at((x, y), (0, 0, 0, 0))
        pending.extend(((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)))
    return out


def _load_target_references():
    """Extract the supplied bullseyes while keeping their white inner rings."""
    path = os.path.join(_ARCHER_DIR, "assets", "target_reference.png")
    sheet = pygame.image.load(path).convert_alpha()
    return [
        _clear_edge_background(sheet.subsurface(crop).copy())
        for crop in _TARGET_CROPS
    ]


def _is_bow(color):
    return color.a > 20 and color.r > 200 and color.g < 100 and color.b < 140


def _stride(surf, leg_rows=6):
    """Second walk frame: boots step apart, the same stride the gunners had."""
    width, height = surf.get_size()
    out = surf.copy()
    top = height - leg_rows
    center = width / 2.0
    for y in range(top, height):
        placed = {}
        for x in range(width):
            color = surf.get_at((x, y))
            if color.a < 20:
                continue
            if x < center:
                nx = max(0, x - 1)
            elif x > center:
                nx = min(width - 1, x + 1)
            else:
                nx = x
            placed[nx] = color
        for x in range(width):
            out.set_at((x, y), placed.get(x, (0, 0, 0, 0)))
    return out


def _blink(surf):
    """Idle frame closes the eye highlights, like the old antenna blink."""
    out = surf.copy()
    limit = int(surf.get_height() * 0.32)
    for y in range(limit):
        for x in range(surf.get_width()):
            color = surf.get_at((x, y))
            if (color.a > 20 and color.r > 240 and 180 < color.g < 235
                    and color.b > 170):
                out.set_at((x, y), (168, 106, 61, 255))
    return out


def _anchor_and_muzzle(surf):
    """Body center is where the player stands; the bow tip is where shots leave."""
    width, height = surf.get_size()
    body_x = []
    bow = []
    for y in range(height):
        for x in range(width):
            color = surf.get_at((x, y))
            if color.a < 20:
                continue
            if _is_bow(color):
                bow.append((x, y))
            else:
                body_x.append(x)
    ax = int(round(sum(body_x) / len(body_x))) if body_x else width // 2
    ay = int(round(height * 0.42))
    if bow:
        mx = int(round(sum(x for x, _y in bow) / len(bow)))
        my = int(round(sum(y for _x, y in bow) / len(bow)))
    else:
        mx, my = ax, ay
    return (ax, ay), (mx, my)


def _build_players():
    players = {}
    sources = (("p1", "girl_archer.png", P1_COLORS, False),
               ("p2", "boy_archer.png", P2_COLORS, True))
    for pid, filename, scheme, face_left in sources:
        fitted = _fit_archer(_load_reference_sprite(filename))
        if face_left:                    # player 2 shoots toward the arena
            fitted = pygame.transform.flip(fitted, True, False)
        stand = fitted
        step = _stride(fitted)
        frames = [stand, step]
        frames_off = [_blink(stand), _blink(step)]
        anchor, muzzle = _anchor_and_muzzle(stand)
        flash_small = _sheet(_FLASH_SMALL, {"X": (255, 255, 228)})
        flash_big = _sheet(_FLASH_BIG, {"W": (255, 255, 235), "l": scheme["light"]})
        players[pid] = {
            "frames": frames, "frames_off": frames_off, "colors": scheme,
            "flash_small": flash_small, "flash_big": flash_big,
            "anchor": anchor, "muzzle": muzzle,
        }
    return players


def _build_bullets():
    """Supplied arrows plus brighter bounced variants for the bank tiers."""
    bullets = {}
    arrow = _fit_arrow(_load_reference_sprite("arrow.png"))
    for pid, scheme in (("p1", P1_COLORS), ("p2", P2_COLORS)):
        normal = arrow if pid == "p1" else pygame.transform.flip(arrow, True, False)
        hot = _charged_arrow(normal, 38)
        super_hot = _charged_arrow(normal, 78)
        # Two identical frames keep the established projectile animation API;
        # flight and bounce motion remain controlled by Bullet.
        bullets[pid] = {
            "frames": (normal, normal),
            "hot": (hot, hot),
            "super": (super_hot, super_hot),
            "anchor": (normal.get_width() // 2, normal.get_height() // 2),
            "ramp": (scheme["shade"], scheme["body"], scheme["light"]),
        }
    return bullets


# The supplied bullseyes are scaled to every size the match can reach.
# As the timer advances, the target both shrinks and progresses through the
# matching reference-target stages.
def _build_targets():
    targets = {}
    references = _load_target_references()
    for diameter in range(4, 19):
        frames, whites = [], []
        size = diameter + 4
        progress = (18 - diameter) / 14.0
        reference = references[min(3, int(progress * len(references)))]
        for frame_idx in range(4):
            surf = pygame.transform.scale(reference, (size, size))
            white = pygame.Surface((size, size), pygame.SRCALPHA)
            for py in range(size):
                for px in range(size):
                    if surf.get_at((px, py)).a > 20:
                        white.set_at((px, py), (252, 252, 255))
            frames.append(surf)
            whites.append(white)
        targets[diameter] = {"frames": frames, "white": whites}
    return targets


# background: night skyline + stars
def _build_background():
    rng = random.Random(7)
    surf = pygame.Surface((VW, VH))
    surf.fill(NAVY)
    stars = []
    for _ in range(46):
        x = rng.randrange(4, VW - 4)
        y = rng.randrange(4, 110)
        color = rng.choice(((58, 68, 108), (94, 106, 148), (148, 158, 198)))
        stars.append((x, y, color))
        surf.fill(color, (x, y, 1, 1))
    floor_y = 174
    # far skyline
    x = 0
    while x < VW:
        w = rng.randrange(8, 22)
        h = rng.randrange(8, 26)
        pygame.draw.rect(surf, (18, 20, 44), (x, floor_y - h, w, h))
        for _ in range(rng.randrange(1, 4)):
            wx = x + rng.randrange(1, max(2, w - 2))
            wy = floor_y - h + rng.randrange(2, max(3, h - 2))
            if 0 <= wx < VW and floor_y - h + 2 <= wy < floor_y - 1:
                surf.set_at((wx, wy), (70, 90, 140) if rng.random() < 0.7 else (172, 128, 76))
        x += w + rng.randrange(1, 4)
    # near skyline with antenna beacons
    x = 0
    while x < VW:
        w = rng.randrange(10, 26)
        h = rng.randrange(14, 34)
        pygame.draw.rect(surf, (24, 27, 56), (x, floor_y - h, w, h))
        if rng.random() < 0.55:
            surf.set_at((x + w // 2, floor_y - h - 1), (255, 200, 80))
        x += w + rng.randrange(2, 6)
    # floor strip
    pygame.draw.rect(surf, (30, 34, 66), (0, floor_y, VW, VH - floor_y))
    for gx in range(0, VW, 8):
        surf.fill((46, 52, 92), (gx, floor_y + 2, 2, 1))
    return surf, stars


def _build_scanlines():
    surf = pygame.Surface((VW, VH), pygame.SRCALPHA)
    for y in range(1, VH, 2):
        surf.fill((0, 0, 0, 28), (0, y, VW, 1))
    return surf


def build_assets():
    background, stars = _build_background()
    return {
        "players": _build_players(),
        "bullets": _build_bullets(),
        "targets": _build_targets(),
        "background": background,
        "stars": stars,
        "scanlines": _build_scanlines(),
    }
