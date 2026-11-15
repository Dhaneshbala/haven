
import random

import pygame

from settings import (
    BOSSES, FPS, GOLD, GREEN, GRAY, KEY_ACTIONS, P1_COLORS, P2_COLORS,
    RESULT_MSGS, SCALE, VH, VW, WIN_H, WIN_W,
)
from pixel_art import build_assets
from sfx import Sfx
from music import Music
from entities import Target
from match import Match
from screens import (Button, MuteButton, draw_menu, draw_pause, draw_results,
                     draw_select)


class Game:
    

    def __init__(self):
        pygame.init()
        self.window = pygame.display.set_mode((WIN_W, WIN_H))
        pygame.display.set_caption("BOUNCE BACK - Pixel Arcade")
        self.virtual = pygame.Surface((VW, VH))
        self.assets = build_assets()
        self.sfx = Sfx()
        self.music = Music()
        self.clock = pygame.time.Clock()
        self.state = "menu"
        self.mode = "versus"
        self.fighters = ["girl", "boy"]   # p1 / p2 art picks
        self.match = None
        self.held = set()
        self.t = 0.0
        self.running = True
        self.result_msg = ""
        self.confetti = []
        self.muted = False
        self.boss = 0                # which boss of the solo ladder
        self.solo_won = False        # ladder cleared, on the results screen
        # sits in the scoreboard gap during a match, in the sky on menus
        self.mute_btn = MuteButton(194, 3)
        self.menu_target = Target(pygame.Rect(8, 4, 304, 18),
                                  lambda e: 10.0, lambda e: 26.0,
                                  self.sfx, self.assets["targets"])
        self.buttons = self._build_buttons()

    
    def _build_buttons(self):
        menu = [
            Button(160, 122, 128, 18, "1P - VS CPU", GREEN, 2, "solo"),
            Button(160, 144, 128, 18, "2P - VERSUS", GOLD, 2, "versus"),
        ]
        pause = [
            Button(160, 82, 116, 16, "RESUME", GREEN, 2, "resume"),
            Button(160, 102, 116, 16, "RESTART", GOLD, 2, "restart"),
            Button(160, 122, 116, 16, "MAIN MENU", GRAY, 2, "menu"),
        ]
        results = [
            Button(160, 114, 124, 16, "PLAY AGAIN", GOLD, 2, "restart"),
            Button(160, 136, 124, 16, "MAIN MENU", GRAY, 2, "menu"),
        ]
        # keys must match the state names, or clicks fall through
        # "select" is rebuilt whenever a mode is picked
        return {"menu": menu, "select": [], "paused": pause,
                "results": results}

    
    def _select_buttons(self):
        """Fighter picks for the current mode, plus FIGHT! and BACK."""
        buttons = [
            Button(51, 122, 60, 16, "GIRL", P1_COLORS["light"], 2, "p1_girl"),
            Button(117, 122, 60, 16, "BOY", P1_COLORS["light"], 2, "p1_boy"),
        ]
        if self.mode != "solo":
            buttons += [
                Button(203, 122, 60, 16, "GIRL", P2_COLORS["light"], 2,
                       "p2_girl"),
                Button(269, 122, 60, 16, "BOY", P2_COLORS["light"], 2,
                       "p2_boy"),
            ]
        buttons += [
            Button(210, 148, 96, 18, "FIGHT!", GOLD, 2, "sel_fight"),
            Button(86, 148, 72, 18, "BACK", GRAY, 2, "sel_back"),
        ]
        return buttons

    def _open_select(self, mode):
        """A mode was picked: show the fighter select screen for it."""
        self.mode = mode
        self.fighters = ["girl", "boy"]      # fresh picks each visit
        self.boss = 0                        # every visit opens a fresh ladder
        self.state = "select"
        self.buttons["select"] = self._select_buttons()

    def _pick(self, slot, pick):
        self.fighters[slot] = pick
        if self.mode == "solo":
            # the CPU always takes the other fighter
            self.fighters[1] = "boy" if pick == "girl" else "girl"

    def _choose(self, slot, pick):
        """Keyboard pick on the select screen: blip, then move the marker."""
        self.sfx.play("select")
        self._pick(slot, pick)

    def start_match(self, mode=None, boss=None):
        """Start a match.

        A run opened from the menu always starts on boss 1; a mid-match
        restart keeps the boss you are on, and a cleared ladder starts over.
        """
        if mode is not None:
            self.mode = mode
            if boss is None and mode == "solo":
                boss = 0                     # new run opens on boss 1
        if self.mode != "solo":
            self.boss = 0
        elif boss is not None:
            self.boss = boss
        elif self.solo_won:
            self.boss = 0                     # ladder cleared: run it again
        # otherwise keep self.boss, so a restart retries that fight
        self.match = Match(self.assets, self.sfx, self.mode, self.boss,
                           fighters=tuple(self.fighters))
        self.solo_won = False                 # only meaningful on results
        self.state = "playing"
        self.sfx.play("start")

    def _button_action(self, action):
        if action in ("solo", "versus"):
            self._open_select(action)
        elif action in ("p1_girl", "p1_boy", "p2_girl", "p2_boy"):
            slot = 0 if action[1] == "1" else 1
            self._pick(slot, "girl" if action.endswith("girl") else "boy")
        elif action == "sel_fight":
            self.start_match()
        elif action == "sel_back":
            self.state = "menu"
        elif action == "restart":
            self.start_match()
        elif action == "resume":
            self.state = "playing"
        elif action == "menu":
            self.state = "menu"

    def _after_match(self):
        """A ladder win rolls straight into the next boss, back to back."""
        if (self.match.mode == "solo" and self.match.winner == 1
                and self.boss < len(BOSSES) - 1):
            self.start_match("solo", self.boss + 1)
        else:
            self._enter_results()

    def _enter_results(self):
        self.state = "results"
        # a solo win only gets here by beating the last boss of the ladder
        self.solo_won = self.match.mode == "solo" and self.match.winner == 1
        if self.solo_won:
            self.result_msg = "ALL BOSSES DEFEATED!"
        elif self.match.sd_won:
            self.result_msg = "SETTLED IN SUDDEN DEATH!"
        else:
            self.result_msg = random.choice(RESULT_MSGS)
        palette = (
            self.assets["players"]["p1"]["colors"]["light"],
            self.assets["players"]["p2"]["colors"]["light"],
            (240, 244, 255), (255, 202, 84),
        )
        self.confetti = [
            {"x": random.uniform(0, VW), "y": random.uniform(-50, -2),
             "vy": random.uniform(18, 46), "vx": random.uniform(-7, 7),
             "c": random.choice(palette)}
            for _ in range(46)
        ]

    
    def _sync_music(self):
        if self.state in ("menu", "select"):
            self.music.play("menu")
        elif self.state in ("playing", "paused"):
            
            self.music.play("hurry" if self.match.hurry else "game")
        else:
            self.music.play("results")

    def _virtual_point(self, point):
        """Map pointer input to the 320x180 canvas at any window scale."""
        width, height = self.window.get_size()
        x, y = point
        return (
            max(0, min(VW - 1, int(x * VW / max(1, width)))),
            max(0, min(VH - 1, int(y * VH / max(1, height)))),
        )

    
    def toggle_mute(self):
        """One switch for the soundtrack and every sound effect."""
        self.muted = not self.muted
        self.sfx.set_muted(self.muted)
        self.music.set_muted(self.muted)
        if not self.muted:
            self.sfx.play("select")        # confirmation blip on the way back

    def handle_event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return

        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            action = KEY_ACTIONS.get(event.key)
            if action:
                if event.type == pygame.KEYDOWN:
                    self.held.add(action)
                else:
                    self.held.discard(action)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._virtual_point(event.pos)
            if self.mute_btn.contains((mx, my)):
                self.toggle_mute()
                return
            for button in self.buttons.get(self.state, ()):
                if button.contains((mx, my)):
                    self.sfx.play("select")
                    self._button_action(button.action)
                    return

        if event.type == pygame.KEYDOWN:
            self._keydown(event.key)

        focus_lost = getattr(pygame, "WINDOWFOCUSLOST", None)
        if focus_lost is not None and event.type == focus_lost:
            self.held.clear()
            if self.state == "playing":
                self.state = "paused"

    def _keydown(self, key):
        if key == pygame.K_n:              # mute anywhere, mid-match included
            self.toggle_mute()
            return
        if self.state == "menu":
            if key == pygame.K_1:
                self._open_select("solo")
            elif key in (pygame.K_2, pygame.K_RETURN, pygame.K_SPACE):
                self._open_select("versus")
            elif key == pygame.K_ESCAPE:
                self.running = False
        elif self.state == "select":
            if key == pygame.K_ESCAPE:
                self.state = "menu"
                self.sfx.play("select")
            elif key == pygame.K_1:
                self._choose(0, "girl")
            elif key == pygame.K_2:
                self._choose(0, "boy")
            elif key == pygame.K_LEFT and self.mode != "solo":
                self._choose(1, "girl")
            elif key == pygame.K_RIGHT and self.mode != "solo":
                self._choose(1, "boy")
            elif key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.start_match()
        elif self.state == "playing":
            if key in (pygame.K_ESCAPE, pygame.K_p):
                self.state = "paused"
                self.sfx.play("select")
        elif self.state == "paused":
            if key == pygame.K_ESCAPE:
                self.state = "playing"
            elif key == pygame.K_r:
                self.start_match()
            elif key == pygame.K_m:
                self.state = "menu"
        elif self.state == "results":
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_match()
            elif key in (pygame.K_ESCAPE, pygame.K_m):
                self.state = "menu"

    
    def update(self, dt):
        self.t += dt
        if self.state == "menu":
            self.menu_target.update(dt, 0.0)
        elif self.state == "playing":
            self.match.update(dt, lambda key: key in self.held)
            if self.match.over:
                self._after_match()
        elif self.state == "results":
            for bit in self.confetti:
                bit["x"] += bit["vx"] * dt
                bit["y"] += bit["vy"] * dt
                if bit["y"] > VH:
                    bit["y"] = -2
                    bit["x"] = random.uniform(0, VW)
        self._sync_music()

    
    def draw(self):
        surf = self.virtual
        mouse = self._virtual_point(pygame.mouse.get_pos())
        if self.state == "menu":
            draw_menu(surf, self.assets, self.t, self.menu_target,
                      self.buttons["menu"], mouse)
        elif self.state == "select":
            draw_select(surf, self.assets, self.t, self.mode, self.fighters,
                        self.buttons["select"], mouse)
        elif self.state == "playing":
            self.match.draw(surf, self.t)
        elif self.state == "paused":
            draw_pause(surf, self.match, self.t, self.buttons["paused"], mouse)
        elif self.state == "results":
            draw_results(surf, self.match, self.t, self.buttons["results"],
                         mouse, self.confetti, self.result_msg)
        self.mute_btn.draw(surf, mouse, self.muted)   # on every screen
        pygame.transform.scale(surf, (WIN_W, WIN_H), self.window)
        pygame.display.flip()

    
    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                self.handle_event(event)
            self.update(dt)
            self.draw()
        pygame.quit()


def main():
    Game().run()


if __name__ == "__main__":
    main()
