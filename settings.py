"""Shared constants and tuning knobs for BOUNCE BACK.

Everything draws to a 320x180 surface that main.py scales up x4.
"""

import pygame

# screen
VW, VH = 320, 180
SCALE = 4
WIN_W, WIN_H = VW * SCALE, VH * SCALE
FPS = 60

# match
MATCH_TIME = 60.0
HURRY_AT = 10.0              # when the HURRY banner shows

# arena
HUD_H = 23                   # scoreboard strip
TOP_WALL_Y = HUD_H
PLAY_TOP = HUD_H + 3
PLAY_BOTTOM = 173
BOTTOM_WALL_Y = 174
ARENA_L = 2                  # side walls are 2px thick
ARENA_R = 317

P1_X = 26
P2_X = 294

# where the target bounces around (left, top, w, h)
TARGET_ZONE = (96, 34, 128, 130)

# players
PLAYER_SPEED = 85.0

SHOT_COOLDOWN = 0.33
MAG_SIZE = 10                # arrows in a quiver
RELOAD_TIME = 3.0            # seconds an empty quiver takes to refill
BULLET_SPEED = 150.0
BULLET_LIFETIME = 3.2        # straight shots fizzle after this long
BOUNCE_LIFE_BONUS = 1.5      # every wall bounce refunds this much lifetime
BULLET_MAX_BOUNCES = 3       # a 4th wall bounce kills the bullet
BULLET_CAP = 32

# bank shots: wall bounces raise the multiplier (BANK_LADDER), and a bullet
# that touched its shooter's back wall doubles it again. The jackpot is the
# title shot: x3 ladder * x2 return = x6, the BOUNCE BACK!
BANK_LADDER = (1, 2, 3, 5)   # points multiplier for 0/1/2/3 wall bounces
RETURN_MULT = 2              # back-wall round trip bonus

# slow-mo jackpots: any hit worth HITSTOP_MIN_MULT or more freezes the match
# for a beat - the world runs at HITSTOP_SCALE speed while the flash fades
HITSTOP_MIN_MULT = 5
HITSTOP_TIME = 0.25
HITSTOP_SCALE = 0.25

# rebound: hitting the core right after it bounced off a zone wall pays the
# hit's base points again, on top of everything else
REBOUND_WINDOW = 0.3

# trampoline bands inside the target zone: the core bounces off them with a
# speed kick; bullets fly straight over them
TRAMPOLINE_YS = (58, 140)
TRAMPOLINE_COMPRESS = 0.3    # seconds a band stays squashed after a launch
TRAMP_MID = (58, 130, 92)
TRAMP_LIGHT = (150, 232, 180)

# walls charge up: every bounce feeds the meter. When it fills, the walls
# flash gold (WALLS ARE LIVE!) and the next banked shot pays one ladder step
# higher, then the meter drains and starts refilling
WALL_CHARGE_BULLET = 0.08
WALL_CHARGE_CORE = 0.05
WALL_CHARGE_TRAMP = 0.12

# living walls: rubber bulges where bullets smack the side walls
BULGE_TIME = 0.35

# target
TARGET_SIZE_START = 16.0     # diameter
TARGET_SIZE_END = 6.0
TARGET_SPEED_START = 40.0
TARGET_SPEED_END = 110.0

# size >= threshold -> points/label/color, biggest first
TIER_TABLE = (
    (13.5, 1, "LARGE", (240, 244, 255)),
    (10.0, 3, "MEDIUM", (255, 202, 84)),
    (7.0, 5, "SMALL", (255, 150, 90)),
    (0.0, 10, "TINY", (244, 84, 96)),
)

POP_LIFE = 0.9
RIPPLE_TTL = 0.28

# cpu opponent (1P mode)
CPU_LEAD = 0.65              # how much it leads the target
CPU_AIM_ERROR = 8.0          # aim wobble in px
CPU_FIRE_WINDOW = 2.4        # fires when its guess is this close
CPU_LAPSE = 0.3              # chance of a bad wander
CPU_COOLDOWN = 0.55          # shoots slower than a human

# mid-match banners
MSG_TIMES = (15.0, 30.0, 45.0)
MSGS = ("KEEP FIRING!", "STAY SHARP!", "BOUNCE BACK!")
RESULT_MSGS = (
    "GREAT MATCH - EVERY SHOT COUNTS!",
    "NOTHING BEATS A REMATCH!",
    "PERSISTENCE WINS MATCHES!",
    "BOUNCE BACK AND GO AGAIN!",
)

# palette
NAVY = (13, 15, 34)
UI_DARK = (18, 21, 44)
UI_MID = (30, 35, 68)
UI_LINE = (58, 66, 118)
WHITE = (240, 244, 255)
GRAY = (110, 118, 152)
GOLD = (255, 202, 84)
RED = (244, 84, 96)
GREEN = (124, 220, 144)

P1_COLORS = {
    "outline": (16, 26, 58), "body": (49, 146, 224), "light": (158, 208, 255),
    "shade": (29, 95, 168), "visor": (10, 16, 38), "eye": (235, 245, 255),
    "metal": (122, 74, 40),
}
P2_COLORS = {
    "outline": (16, 36, 22), "body": (35, 145, 79), "light": (150, 220, 160),
    "shade": (20, 94, 54), "visor": (20, 28, 24), "eye": (240, 244, 255),
    "metal": (122, 74, 40),
}

TARGET_BODY = (236, 76, 118)
TARGET_LIGHT = (255, 176, 208)
TARGET_DARK = (98, 26, 54)
TARGET_CORE = (255, 242, 250)

# rubber walls
RUBBER_DARK = (40, 46, 84)
RUBBER_MID = (66, 74, 126)
RUBBER_LIGHT = (108, 120, 176)

# input
CONTROLS = {
    "p1": ("p1_up", "p1_down", "p1_shoot"),
    "p2": ("p2_up", "p2_down", "p2_shoot"),
}
KEY_ACTIONS = {
    pygame.K_w: "p1_up", pygame.K_s: "p1_down", pygame.K_SPACE: "p1_shoot",
    pygame.K_UP: "p2_up", pygame.K_DOWN: "p2_down",
    pygame.K_RETURN: "p2_shoot", pygame.K_KP_ENTER: "p2_shoot",
}


def tier_for_size(size):
    """(points, label, color) for a target diameter."""
    for threshold, pts, name, color in TIER_TABLE:
        if size >= threshold:
            return pts, name, color
    return TIER_TABLE[-1][1], TIER_TABLE[-1][2], TIER_TABLE[-1][3]


def target_size(elapsed):
    """Target diameter over the match."""
    t = min(1.0, max(0.0, elapsed / MATCH_TIME))
    return TARGET_SIZE_START + (TARGET_SIZE_END - TARGET_SIZE_START) * t


def target_speed(elapsed):
    """Target speed over the match."""
    t = min(1.0, max(0.0, elapsed / MATCH_TIME))
    return TARGET_SPEED_START + (TARGET_SPEED_END - TARGET_SPEED_START) * t
