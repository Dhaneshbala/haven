"""One 60 second match."""

import math
import random

import pygame

from settings import (
    HUD_H, MATCH_TIME, HURRY_AT, ARENA_L, ARENA_R, BANK_LADDER, BOSSES,
    BULGE_TIME,
    HITSTOP_MIN_MULT, HITSTOP_SCALE, HITSTOP_TIME,
    MSGS, MSG_TIMES, PLAY_TOP, PLAY_BOTTOM,
    P1_X, P2_X, P1_COLORS, P2_COLORS, TARGET_ZONE, VW, VH,
    RUBBER_DARK, RUBBER_MID, RUBBER_LIGHT, TRAMPOLINE_COMPRESS,
    TRAMPOLINE_YS, TRAMP_LIGHT, TRAMP_MID,
    TARGET_DARK, TARGET_LIGHT,
    UI_DARK, UI_MID, UI_LINE, WHITE, GRAY, GOLD, RED,
    WALL_CHARGE_BULLET, WALL_CHARGE_CORE, WALL_CHARGE_TRAMP,
    target_size, target_speed, tier_for_size,
)
from pixel_font import draw_text, text_width
from entities import (
    Bullet, Particle, Player, Ripple, ScorePop, Target, point_seg_dist,
)
from records import best_score, save_bank, save_score


def _lerp_color(a, b, t):
    """Blend two rgb colors: t=0 returns a, t=1 returns b."""
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Match:
    def __init__(self, assets, sfx, mode="versus", boss=0,
                 fighters=("girl", "boy")):
        self.assets = assets
        self.sfx = sfx
        self.mode = mode  # "solo" or "versus"
        self.fighters = tuple(fighters)  # (p1, p2) art picks
        self.boss_index = boss if mode == "solo" else 0
        self.boss_name = (BOSSES[self.boss_index]["name"]
                          if mode == "solo" else "")
        self.zone = pygame.Rect(TARGET_ZONE)
        mid_y = (PLAY_TOP + PLAY_BOTTOM) / 2
        self.p1 = Player("p1", P1_X, mid_y, assets, sfx,
                         fighter=self.fighters[0])
        self.p2 = Player("p2", P2_X, mid_y, assets, sfx,
                         is_cpu=(mode == "solo"),
                         cpu=BOSSES[self.boss_index] if mode == "solo"
                         else None, fighter=self.fighters[1])
        self.target = Target(self.zone, target_size, target_speed, sfx,
                             assets["targets"], self._core_bounce)
        self.bullets = []
        self.particles = []
        self.pops = []
        self.ripples = []
        self.wall_charge = 0.0      # bounce meter; full = WALLS ARE LIVE!
        self.walls_live = False
        self.bulges = []            # (side, y, age) living-wall bulges
        self.hitstop = 0.0          # slow-mo timer while a jackpot lands
        self.longest_bank = 0       # biggest single-bullet bank chain
        self.best = best_score(mode)    # score to beat this match
        self.best_popped = False
        self.new_best = False       # record flags, filled in at _finish
        self.new_bank_record = False
        self.timer = MATCH_TIME
        self.elapsed = 0.0
        self.msg_idx = 0
        self.hurry = False
        self.ticks = set()
        self.banner_text = ""
        self.banner_color = WHITE
        self.banner_t = 0.0
        self.shake = 0.0
        self.over = False
        self.sudden_death = False  # tie at 0:00 -> first score wins
        self.sd_won = False
        self.winner = 0  # 1 = player 1, 2 = player 2, 0 = draw
        if mode == "solo":
            self._announce_boss()

    def _announce_boss(self):
        """Open each fight of the ladder with who you are up against."""
        if self.boss_index == 0:
            self.show_banner(f"BOSS 1/{len(BOSSES)} - {self.boss_name}",
                             P2_COLORS["light"], 2.6)
        else:
            previous = BOSSES[self.boss_index - 1]["name"]
            self.show_banner(f"{previous} DEFEATED! - {self.boss_name}",
                             GOLD, 2.6)

    # helpers
    def spawn_bullet(self, player):
        mx, my = player.muzzle()
        self.bullets.append(Bullet(player.pid, mx, my, player.face))
        self.sfx.play("shoot")

    def show_banner(self, text, color, duration=2.4):
        self.banner_text = text
        self.banner_color = color
        self.banner_t = duration

    def explosion(self, x, y, colors):
        for _ in range(14):
            angle = random.uniform(0.0, math.tau)
            speed = random.uniform(22.0, 78.0)
            self.particles.append(Particle(
                x, y, math.cos(angle) * speed, math.sin(angle) * speed,
                random.uniform(0.3, 0.75),
                (random.choice(colors), UI_LINE), random.choice((1, 1, 2))))

    def wall_puff(self, x, y, color):
        for _ in range(5):
            self.particles.append(Particle(
                x, y, random.uniform(-34, 34), random.uniform(-34, 34),
                random.uniform(0.15, 0.35), (color, UI_MID), 1))

    def _core_bounce(self, kind):
        """Target calls this on every zone wall and trampoline bounce."""
        self._charge_walls(WALL_CHARGE_CORE if kind == "zone"
                           else WALL_CHARGE_TRAMP)

    def _charge_walls(self, amount):
        """Feed the wall meter; when it fills, the next bank shot pays extra."""
        if self.walls_live:
            return
        self.wall_charge = min(1.0, self.wall_charge + amount)
        if self.wall_charge >= 1.0:
            self.walls_live = True
            self.show_banner("WALLS ARE LIVE!", GOLD)
            self.sfx.play("start")

    # update
    def update(self, dt, held):
        if self.over:
            return
        if self.hitstop > 0.0:          # slow-mo while the jackpot lands
            self.hitstop = max(0.0, self.hitstop - dt)
            dt *= HITSTOP_SCALE
        self.elapsed += dt
        self.timer = max(0.0, self.timer - dt)

        while self.msg_idx < len(MSG_TIMES) and self.elapsed >= MSG_TIMES[self.msg_idx]:
            self.show_banner(MSGS[self.msg_idx], GOLD)
            self.msg_idx += 1
        if not self.hurry and self.timer <= HURRY_AT:
            self.hurry = True
            self.show_banner("HURRY!", RED, 2.0)
        whole = int(math.ceil(self.timer))
        if 1 <= whole <= 5 and whole not in self.ticks and self.timer > 0.0:
            self.ticks.add(whole)
            self.sfx.play("tick")

        self.p1.update(dt, held, self)
        if self.mode == "solo":
            self.p2.update_cpu(dt, self)
        else:
            self.p2.update(dt, held, self)

        for bullet in self.bullets:
            event = bullet.update(dt)
            if event == "wall":
                colors = P1_COLORS if bullet.owner == "p1" else P2_COLORS
                self.wall_puff(bullet.x, bullet.y, colors["light"])
                self.ripples.append(
                    Ripple(bullet.x, bullet.y, (colors["light"], colors["shade"])))
                self.sfx.play("boing")
                side = "L" if bullet.x < VW / 2 else "R"
                self.bulges.append((side, bullet.y, 0.0))
                self._charge_walls(WALL_CHARGE_BULLET)
            elif event == "fizzle":
                self.wall_puff(bullet.x, bullet.y, GRAY)
        self._collisions()
        self.bullets = [b for b in self.bullets if b.alive]

        self.target.update(dt, self.elapsed)
        self.particles = [p for p in self.particles if p.update(dt)]
        self.pops = [p for p in self.pops if p.update(dt)]
        self.ripples = [r for r in self.ripples if r.update(dt)]
        self.bulges = [(side, y, age + dt) for side, y, age in self.bulges
                       if age < BULGE_TIME]
        self.banner_t = max(0.0, self.banner_t - dt)
        self.shake = max(0.0, self.shake - dt * 9.0)

        if self.timer <= 0.0001 and not self.sudden_death:
            if self.p1.score == self.p2.score:
                # tied, so keep playing until someone scores
                self.sudden_death = True
                self.show_banner("SUDDEN DEATH - FIRST SCORE WINS!", RED, 3.0)
                self.sfx.play("start")
            else:
                self._finish()

    def _collisions(self):
        target = self.target
        reach = target.radius() + 1.5
        for bullet in self.bullets:
            if not bullet.alive:
                continue
            if point_seg_dist(target.x, target.y, bullet.px, bullet.py,
                              bullet.x, bullet.y) <= reach:
                base_points, _label, _color = target.hit(bullet.x)
                points = self._hit_points(bullet, base_points)
                scorer = self.p1 if bullet.owner == "p1" else self.p2
                scorer.score += points
                if (not self.best_popped and self.best > 0
                        and scorer.score > self.best):
                    self.best_popped = True
                    self.show_banner("NEW BEST!!", GOLD, 2.0)
                    self.pops.append(ScorePop(bullet.x, bullet.y - 34,
                                              "NEW BEST!!", GOLD))
                self.pops.append(ScorePop(bullet.x, bullet.y - 6, f"+{points}",
                                          scorer.colors["light"]))
                self.explosion(bullet.x, bullet.y,
                               (WHITE, scorer.colors["body"], scorer.colors["light"]))
                self.ripples.append(Ripple(bullet.x, bullet.y,
                                           (TARGET_LIGHT, TARGET_DARK), 0.34))
                self.shake = 2.2
                self.sfx.play("hit")
                self.sfx.play("boing_low")
                bullet.alive = False
                if self.sudden_death:
                    self._finish()
                    break

    def _hit_points(self, bullet, base_points):
        """Bank ladder x back-wall return bonus, plus a flat rebound bonus."""
        bounces = min(bullet.bounces, len(BANK_LADDER) - 1)
        if self.walls_live and bounces >= 1:
            mult = bullet.multiplier(1)   # one ladder step up
            points = base_points * mult
            self.walls_live = False
            self.wall_charge = 0.0
            self.pops.append(ScorePop(bullet.x, bullet.y - 27, "WALLS LIVE!",
                                      GOLD))
        else:
            mult = bullet.multiplier()
            points = base_points * mult
        if bounces >= 1:
            labels = {1: "BANK SHOT!", 2: "BOUNCE BACK!", 3: "TRIPLE BANK!"}
            self.pops.append(ScorePop(bullet.x, bullet.y - 13, labels[bounces],
                                      GOLD))
            self.longest_bank = max(self.longest_bank, bullet.bounces)
            if bounces >= 2:
                self.sfx.play("start")       # little flourish on the jackpots
        if self.target.rebound > 0.0:
            points += base_points            # core just bounced off a zone wall
            self.pops.append(ScorePop(bullet.x, bullet.y - 20, "REBOUND!",
                                      TARGET_LIGHT))
        if mult >= HITSTOP_MIN_MULT:
            self.hitstop = HITSTOP_TIME      # jackpots stop time for a beat
        return points

    def _finish(self):
        self.over = True
        self.sd_won = self.sudden_death
        self.banner_t = 0.0
        if self.p1.score > self.p2.score:
            self.winner = 1
        elif self.p2.score > self.p1.score:
            self.winner = 2
        else:
            self.winner = 0
        score = (self.p1.score if self.mode == "solo"
                 else max(self.p1.score, self.p2.score))
        self.new_best = save_score(self.mode, score)
        self.new_bank_record = save_bank(self.longest_bank)
        self.sfx.play("win")

    # draw
    def draw(self, surf, t):
        sdx = sdy = 0
        if self.shake > 0.0:
            sdx = int(round(random.uniform(-1, 1) * self.shake))
            sdy = int(round(random.uniform(-1, 1) * self.shake))
        surf.blit(self.assets["background"], (0, 0))
        for i, (x, y, _c) in enumerate(self.assets["stars"]):
            if (int(t * 3.0) + i) % 9 == 0:
                surf.fill((196, 206, 240), (x, y, 1, 1))
        self._draw_zone(surf, sdx)
        self._draw_trampolines(surf, sdx, sdy)
        self.target.draw(surf, t, sdx, sdy)
        for bullet in self.bullets:
            bullet.draw(surf, self.assets["bullets"][bullet.owner], sdx, sdy,
                        self.walls_live)
        self.p1.draw(surf, t, sdx, sdy)
        self.p2.draw(surf, t, sdx, sdy)
        for particle in self.particles:
            particle.draw(surf, sdx, sdy)
        for pop in self.pops:
            pop.draw(surf, sdx, sdy)
        self._draw_walls(surf, t)
        for ripple in self.ripples:
            ripple.draw(surf, sdx, sdy)
        self._draw_banner(surf)
        self._draw_hud(surf, t)
        surf.blit(self.assets["scanlines"], (0, 0))
        if self.hitstop > 0.0:          # white flash while the jackpot lands
            alpha = int(150 * (self.hitstop / HITSTOP_TIME))
            flash = pygame.Surface((VW, VH), pygame.SRCALPHA)
            flash.fill((255, 255, 255, alpha))
            surf.blit(flash, (0, 0))

    def _draw_zone(self, surf, dx):
        zone = self.zone
        for y in range(zone.top, zone.bottom, 4):
            surf.fill((52, 60, 104), (zone.left + dx, y, 1, 2))
            surf.fill((52, 60, 104), (zone.right - 1 + dx, y, 1, 2))

    def _draw_walls(self, surf, t):
        # rubber walls, stitching, corner pads. they glow gold as the wall
        # meter charges up, and pulse when WALLS ARE LIVE
        if self.walls_live:
            charge = 1.0 if int(t * 8) % 2 == 0 else 0.7    # live = pulsing
        else:
            charge = self.wall_charge
        wall = _lerp_color(RUBBER_MID, GOLD, charge * 0.85)
        stitch = _lerp_color(RUBBER_LIGHT, WHITE, charge * 0.7)
        pygame.draw.rect(surf, wall, (0, HUD_H, VW, 2))
        pygame.draw.rect(surf, RUBBER_DARK, (0, HUD_H + 2, VW, 1))
        pygame.draw.rect(surf, wall, (0, PLAY_BOTTOM + 1, VW, 2))
        pygame.draw.rect(surf, wall, (0, HUD_H, 2, 153))
        pygame.draw.rect(surf, wall, (VW - 2, HUD_H, 2, 153))
        for y in range(HUD_H + 3, PLAY_BOTTOM + 1, 5):     # stitching
            surf.fill(stitch, (1, y, 1, 1))
            surf.fill(stitch, (VW - 2, y, 1, 1))
        for x in range(4, VW - 4, 5):
            surf.fill(stitch, (x, HUD_H + 1, 1, 1))
            surf.fill(stitch, (x, PLAY_BOTTOM + 1, 1, 1))
        self._draw_bulges(surf)
        self._bumper_pad(surf, 2, HUD_H + 2)
        self._bumper_pad(surf, VW - 6, HUD_H + 2)
        self._bumper_pad(surf, 2, PLAY_BOTTOM - 2)
        self._bumper_pad(surf, VW - 6, PLAY_BOTTOM - 2)

    def _draw_bulges(self, surf):
        # living walls: rubber bumps where bullets smack in, springing back
        for side, y, age in self.bulges:
            amp = math.sin(min(1.0, age / BULGE_TIME) * math.pi)
            depth = max(1, int(round(amp * 5.0)))
            if side == "L":
                rect = (ARENA_L, int(y) - 2, depth, 5)
                tip = (ARENA_L + depth - 1, int(y), 1, 1)
            else:
                rect = (ARENA_R - depth, int(y) - 2, depth, 5)
                tip = (ARENA_R - depth, int(y), 1, 1)
            pygame.draw.rect(surf, RUBBER_LIGHT, rect)
            surf.fill(WHITE, tip)

    def _draw_trampolines(self, surf, dx=0, dy=0):
        # springy bands across the target zone; they squash when the core
        # launches off them
        zone = self.zone
        for i, band_y in enumerate(TRAMPOLINE_YS):
            y = int(band_y) + dy
            comp = min(1.0, self.target.compress[i] / TRAMPOLINE_COMPRESS)
            thick = 1 if comp > 0.35 else 2
            color = _lerp_color(TRAMP_MID, WHITE, comp)
            pygame.draw.rect(surf, color, (zone.left + dx, y, zone.width,
                                           thick))
            for x in range(zone.left + 3, zone.right - 3, 6):   # coil ticks
                surf.fill(TRAMP_LIGHT, (x + dx, y + thick, 1, 1))

    def _bumper_pad(self, surf, x, y):
        pygame.draw.rect(surf, RUBBER_DARK, (x, y, 4, 4))
        pygame.draw.rect(surf, RUBBER_LIGHT, (x, y, 4, 4), 1)
        pygame.draw.rect(surf, GOLD, (x + 1, y + 1, 2, 2))

    def _draw_banner(self, surf):
        if self.banner_t <= 0.0:
            return
        if self.banner_t < 0.5 and int(self.banner_t * 14) % 2 == 0:
            return
        width = text_width(self.banner_text, 1) + 8
        x = VW // 2 - width // 2
        pygame.draw.rect(surf, UI_DARK, (x, 30, width, 11))
        pygame.draw.rect(surf, UI_LINE, (x, 30, width, 11), 1)
        draw_text(surf, self.banner_text, (VW // 2, 32), self.banner_color, 1, "center")

    def _draw_hud(self, surf, t):
        pygame.draw.rect(surf, UI_DARK, (0, 0, VW, HUD_H))
        pygame.draw.rect(surf, UI_MID, (0, HUD_H - 1, VW, 1))
        draw_text(surf, "P1", (6, 4), P1_COLORS["body"], 1)
        draw_text(surf, f"{self.p1.score:02d}", (6, 11), P1_COLORS["light"], 2)
        p2_label = "CPU" if self.mode == "solo" else "P2"
        draw_text(surf, p2_label, (VW - 6, 4), P2_COLORS["shade"], 1, "right")
        if self.mode == "solo":            # which boss this fight is
            draw_text(surf, f"BOSS {self.boss_index + 1}/{len(BOSSES)} "
                            f"{self.boss_name}", (46, 4),
                      P2_COLORS["light"], 1)
        draw_text(surf, f"{self.p2.score:02d}", (VW - 6, 11), P2_COLORS["light"], 2, "right")
        self.p1.draw_ammo(surf, 16, 4)
        self.p2.draw_ammo(surf, VW - 19, 4, right=True)
        if self.p1.score > self.p2.score:          # who has the most points
            draw_text(surf, ">", (24, 13), P1_COLORS["light"], 1)
        elif self.p2.score > self.p1.score:
            draw_text(surf, "<", (VW - 24, 13), P2_COLORS["light"], 1, "right")
        if self.sudden_death:
            if int(t * 4) % 2 == 0:
                draw_text(surf, "SD", (VW // 2, 3), RED, 2, "center")
            draw_text(surf, "FIRST SCORE WINS", (VW // 2, 16), GOLD, 1, "center")
        else:
            seconds = int(math.ceil(self.timer))
            minutes, secs = divmod(seconds, 60)
            color = RED if (self.timer <= HURRY_AT and int(t * 4) % 2 == 0) else WHITE
            draw_text(surf, f"{minutes}:{secs:02d}", (VW // 2, 3), color, 2, "center")
            points, name, tier_color = tier_for_size(target_size(self.elapsed))
            draw_text(surf, f"TARGET {name} +{points}", (VW // 2, 16), tier_color, 1, "center")
