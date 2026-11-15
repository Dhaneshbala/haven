"""Menu, pause and results screens."""

import math

import pygame

from settings import (
    VH, VW, BOSSES, UI_DARK, UI_MID, UI_LINE, WHITE, GRAY, GOLD, GREEN, RED,
    P1_COLORS, P2_COLORS,
)
from pixel_font import draw_text, text_width


class Button:
    """Clickable pixel button."""

    def __init__(self, cx, cy, w, h, label, accent, scale=2, action=None):
        self.rect = pygame.Rect(int(cx - w / 2), int(cy - h / 2), int(w), int(h))
        self.label = label
        self.accent = accent
        self.scale = scale
        self.action = action

    def contains(self, point):
        """Use the same forgiving hit area for hover and click."""
        return self.rect.inflate(6, 4).collidepoint(point)

    def draw(self, surf, mouse):
        # A little extra hit area keeps the controls pleasant at high-DPI
        # display scales, while the visible border remains pixel precise.
        hovered = self.contains(mouse)
        pygame.draw.rect(surf, (8, 10, 22), self.rect.move(2, 2))
        pygame.draw.rect(surf, (46, 54, 100) if hovered else UI_MID, self.rect)
        pygame.draw.rect(surf, self.accent, self.rect, 1)
        pygame.draw.rect(surf, UI_DARK, self.rect.inflate(-4, -4), 1)
        color = WHITE if hovered else self.accent
        y = self.rect.centery - (5 * self.scale) // 2
        draw_text(surf, self.label, (self.rect.centerx, y), color, self.scale, "center")


class MuteButton(Button):
    """Speaker icon that silences music and sound effects.

    One instance is shared by every screen: it sits in the scoreboard gap
    during a match and in the open sky on the menus, so the audio can be
    cut at any moment without digging through a menu.
    """

    def __init__(self, x, y):
        self.rect = pygame.Rect(int(x), int(y), 14, 9)
        self.label = ""
        self.accent = WHITE
        self.scale = 1
        self.action = "mute"

    def draw(self, surf, mouse, muted=False):
        hovered = self.contains(mouse)
        if hovered:
            pygame.draw.rect(surf, (46, 54, 100), self.rect.inflate(3, 2))
        x, y = self.rect.x + 1, self.rect.y
        color = GRAY if muted else WHITE
        surf.fill(color, (x, y + 3, 2, 3))                     # speaker body
        pygame.draw.polygon(surf, color,                       # horn
                            [(x + 2, y + 1), (x + 2, y + 7), (x + 6, y + 4)])
        if muted:                                              # cross = off
            pygame.draw.line(surf, RED, (x + 8, y + 1), (x + 12, y + 7))
            pygame.draw.line(surf, RED, (x + 8, y + 7), (x + 12, y + 1))
        else:                                                  # waves = on
            pygame.draw.line(surf, color, (x + 8, y + 2), (x + 8, y + 6))
            pygame.draw.line(surf, color, (x + 11, y + 1), (x + 11, y + 7))


# menu
def draw_menu(surf, assets, t, demo_target, buttons, mouse):
    surf.blit(assets["background"], (0, 0))
    for i, (x, y, _c) in enumerate(assets["stars"]):
        if (int(t * 3.0) + i) % 9 == 0:
            surf.fill((196, 206, 240), (x, y, 1, 1))
    demo_target.draw(surf, t, 0, 0)
    for pid, x in (("p1", 26), ("p2", 294)):
        player = assets["players"][pid]
        blink_on = int(t * 3.0) % 2 == 0
        frames = player["frames"] if blink_on else player["frames_off"]
        frame = frames[int(t * 6.0) % 2]
        ax, _ay = player["anchor"]
        bob = 1 if int(t * 2.0) % 2 else 0
        surf.blit(frame, (x - ax, VH - frame.get_height() - 1 - bob))

    ty = 30 - (1 if int(t * 2.0) % 2 else 0)      # chunky 1px title bounce
    x0 = VW // 2 - text_width("BOUNCE BACK", 4) // 2
    w1 = text_width("BOUNCE ", 4)
    draw_text(surf, "BOUNCE BACK", (x0 + 2, ty + 2), (6, 7, 16), 4)
    draw_text(surf, "BOUNCE", (x0, ty), P1_COLORS["light"], 4)
    draw_text(surf, "BACK", (x0 + w1, ty), P2_COLORS["light"], 4)
    draw_text(surf, "PIXEL ARCADE - SOLO OR TWO PLAYER SHOWDOWN", (VW // 2, 51), GRAY, 1, "center")

    panel = pygame.Rect(30, 58, 260, 52)
    pygame.draw.rect(surf, UI_DARK, panel)
    pygame.draw.rect(surf, UI_LINE, panel, 1)
    draw_text(surf, "PLAYER 1", (44, 63), P1_COLORS["light"], 1)
    draw_text(surf, "W/S - MOVE", (44, 73), WHITE, 1)
    draw_text(surf, "SPACE - SHOOT", (44, 83), WHITE, 1)
    draw_text(surf, "PLAYER 2", (170, 63), P2_COLORS["light"], 1)
    draw_text(surf, "UP/DOWN - MOVE", (170, 73), WHITE, 1)
    draw_text(surf, "ENTER - SHOOT", (170, 83), WHITE, 1)
    draw_text(surf, "SMALLER TARGET = MORE POINTS", (VW // 2, 97), GOLD, 1, "center")

    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "CLICK OR PRESS 1 / 2", (VW // 2, 158), GRAY, 1, "center")
    draw_text(surf, "N MUTE - ESC QUITS", (VW // 2, 168), GRAY, 1, "center")


# character select
def draw_select(surf, assets, t, mode, fighters, buttons, mouse):
    surf.blit(assets["background"], (0, 0))
    for i, (x, y, _c) in enumerate(assets["stars"]):
        if (int(t * 3.0) + i) % 9 == 0:
            surf.fill((196, 206, 240), (x, y, 1, 1))

    draw_text(surf, "CHOOSE YOUR FIGHTER", (VW // 2 + 2, 14), (6, 7, 16),
              2, "center")
    draw_text(surf, "CHOOSE YOUR FIGHTER", (VW // 2, 12), WHITE, 2, "center")
    mode_label = "1P - VS CPU" if mode == "solo" else "2P - VERSUS"
    draw_text(surf, mode_label, (VW // 2, 26), GOLD, 1, "center")

    if mode == "solo":
        slots = ((84, "YOU", P1_COLORS, fighters[0], "right"),
                 (236, "CPU", P2_COLORS, fighters[1], "left"))
    else:
        slots = ((84, "PLAYER 1", P1_COLORS, fighters[0], "right"),
                 (236, "PLAYER 2", P2_COLORS, fighters[1], "left"))
    for cx, label, scheme, fighter_name, face in slots:
        card = pygame.Rect(cx - 66, 34, 132, 100)
        pygame.draw.rect(surf, (8, 10, 22), card.move(2, 2))
        pygame.draw.rect(surf, UI_DARK, card)
        pygame.draw.rect(surf, scheme["light"], card, 1)
        draw_text(surf, label, (card.x + 6, card.y + 5), scheme["light"], 1)
        fighter = assets["fighters"][fighter_name][face]
        blink_on = int(t * 3.0) % 2 == 0
        frames = fighter["frames"] if blink_on else fighter["frames_off"]
        frame = frames[int(t * 6.0) % 2]
        ax, _ay = fighter["anchor"]
        bob = 1 if int(t * 2.0) % 2 else 0
        surf.blit(frame, (cx - ax, 94 - frame.get_height() - bob))
        draw_text(surf, fighter_name.upper(), (cx, 97), WHITE, 1, "center")

    active = {f"p1_{fighters[0]}"}
    if mode != "solo":
        active.add(f"p2_{fighters[1]}")
    for button in buttons:
        button.draw(surf, mouse)
        if button.action in active and int(t * 4.0) % 2 == 0:
            draw_text(surf, "V", (button.rect.centerx, button.rect.y - 7),
                      button.accent, 1, "center")

    hint = ("CLICK A FIGHTER, THEN FIGHT!" if mode == "solo"
            else "EACH PLAYER PICKS - THEN FIGHT!")
    draw_text(surf, hint, (VW // 2, 164), GRAY, 1, "center")


# pause
def draw_pause(surf, match, t, buttons, mouse):
    match.draw(surf, t)
    dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
    dim.fill((8, 9, 18, 178))
    surf.blit(dim, (0, 0))
    panel = pygame.Rect(84, 46, 152, 92)
    pygame.draw.rect(surf, (10, 12, 26), panel.move(2, 2))
    pygame.draw.rect(surf, UI_DARK, panel)
    pygame.draw.rect(surf, UI_LINE, panel, 2)
    draw_text(surf, "PAUSED", (VW // 2, 54), WHITE, 3, "center")
    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "CLICK A BUTTON", (VW // 2, 144), GRAY, 1, "center")


# results
def draw_results(surf, match, t, buttons, mouse, confetti, message):
    match.draw(surf, t)
    dim = pygame.Surface((VW, VH), pygame.SRCALPHA)
    dim.fill((8, 9, 18, 172))
    surf.blit(dim, (0, 0))
    for bit in confetti:
        pygame.draw.rect(surf, bit["c"], (int(bit["x"]), int(bit["y"]), 1, 1))

    if match.mode == "solo":
        name = match.boss_name or "CPU"
        if match.winner == 1:
            if match.boss_index >= len(BOSSES) - 1:
                title, color = "GAUNTLET CLEAR!", GOLD   # ladder finished
            else:
                title, color = "YOU WIN!", P1_COLORS["light"]
        elif match.winner == 2:
            title, color = f"{name} WINS!", P2_COLORS["light"]
        else:
            title, color = "DRAW MATCH!", GOLD
        left_label, right_label = "YOU", name
    else:
        if match.winner == 1:
            title, color = "PLAYER 1 WINS!", P1_COLORS["light"]
        elif match.winner == 2:
            title, color = "PLAYER 2 WINS!", P2_COLORS["light"]
        else:
            title, color = "DRAW MATCH!", GOLD
        left_label, right_label = "P1", "P2"
    draw_text(surf, title, (VW // 2 + 2, 42), (6, 7, 16), 3, "center")
    draw_text(surf, title, (VW // 2, 40), color, 3, "center")

    draw_text(surf, f"{left_label} {match.p1.score:02d}", (150, 68), P1_COLORS["light"], 2, "right")
    draw_text(surf, "-", (160, 68), WHITE, 2, "center")
    draw_text(surf, f"{match.p2.score:02d} {right_label}", (170, 68), P2_COLORS["light"], 2, "left")

    draw_text(surf, message, (VW // 2, 92), GOLD, 1, "center")
    if match.new_best:
        draw_text(surf, "NEW BEST!!", (VW // 2, 100), GOLD, 1, "center")
    elif match.best > 0:
        draw_text(surf, f"BEST {match.best}", (VW // 2, 100), GRAY, 1, "center")
    if match.longest_bank >= 1:
        color = GOLD if match.new_bank_record else GRAY
        draw_text(surf, f"LONGEST BANK {match.longest_bank}",
                  (VW // 2, 107), color, 1, "center")
    for button in buttons:
        button.draw(surf, mouse)
    draw_text(surf, "CLICK PLAY AGAIN OR MENU", (VW // 2, 154), GRAY, 1, "center")
