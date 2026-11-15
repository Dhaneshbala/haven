# Haven Sydney Project

## BOUNCE BACK

**BOUNCE BACK** is a two-player retro arcade shooter made with pygame-ce.
You share an arena, chase one bouncing energy core, and have 60 seconds to
score as many points as possible.

## How it works

The energy core is always moving. It ricochets around the arena, becoming
smaller and faster as the match goes on. Every time someone hits it, it gets
knocked back with a satisfying bounce.

The smaller the core, the more it is worth:

| Target size | Points |
| ----------- | ------ |
| Large       | 1      |
| Medium      | 3      |
| Small       | 5      |
| Tiny        | 10     |

Shots can earn bonus points too. Every wall bounce a bullet banks off raises
its multiplier: one bounce pays double (BANK SHOT!), three bounces pay x5
(TRIPLE BANK!). The jackpot is the title shot - a bullet that ricochets all
the way off your own back wall and heads back out pays x6 (BOUNCE BACK!).
Each wall bounce also refunds a little bullet lifetime, so banked shots can
fly much farther than straight ones, and they visibly heat up with a trail
as their multiplier grows. A hit landed just after the core bounces off an
arena wall earns an extra REBOUND! bonus worth its base points. While a
banked shot is in flight, its current multiplier is shown over the bullet.

The arena adds bounce hazards of its own. Two springy bands inside the
core's zone act as trampolines: when the core touches one it is launched
back with a speed boost, and the band visibly compresses. The walls are
living rubber too - they bulge outward wherever a bullet strikes, then
spring back into shape. Every bounce (bullet, core, or trampoline) also
charges a hidden wall meter; when it fills, the walls flash gold (WALLS
ARE LIVE!) and the next banked shot pays one multiplier step higher, so
a x6 BOUNCE BACK! becomes x10.

Big hits get a moment to land: any shot worth x5 or more (a TRIPLE BANK,
the x6 BOUNCE BACK, or a x10 walls-live jackpot) freezes the match for a
quarter second with a white flash, then time speeds back up.

Every archer starts with a full quiver of 10 arrows. Shoot them all and
the quiver goes dry: firing stops for a 3 second reload, then refills
automatically. The scoreboard shows what is left as pips next to each
score (a filling bar while the reload runs), and a blinking RELOAD pops
up over the archer's head, so you always know how close you are to
empty. The CPU opponent lives by the same rule.

The game also keeps records in a small `best.json` next to the game: the
best single-player score per mode (in versus, the better of the two
players counts) and the longest single-bullet bank chain ever. Cross
your best mid-match and the game shouts NEW BEST!!; the results screen
always shows the score to beat and the longest bank of the match, in
gold when either one just set a new record.

## Winning

When the timer reaches zero, the player with the highest score wins. A `>` or
`<` marker in the HUD shows who is currently ahead.

If the score is tied at the end of the match, the game goes into **SUDDEN
DEATH**. The timer stops, the arena keeps moving, and the next point wins.
That way, every match has a winner.

## Game modes

- **1P – VS CPU** — Play as the blue-clad archer against a green-clad computer
  opponent. The CPU predicts where the core is going, but its aim gets less
  reliable as the match gets more intense.
- **2P – VERSUS** — Two players compete on the same keyboard.

Choose a mode from the main menu by clicking a button or pressing `1` or `2`,
then pick your fighter on the select screen: **GIRL** or **BOY**. In 1P mode
the CPU always takes the other fighter; in 2P each player picks their own
(mirror matches are allowed - team colors tell the two archers apart).
Click **FIGHT!** or press `ENTER` to start, **BACK** or `ESC` to return to
the menu. On that screen `1` / `2` picks for player 1, and `LEFT` / `RIGHT`
picks for player 2.

## Controls

| Action | Player 1 (blue, left) | Player 2 (green, right) |
| ------ | --------------------- | ------------------------ |
| Move   | W / S                 | UP / DOWN                |
| Shoot  | SPACE (hold to fire)  | ENTER (hold to fire)     |

- Ammo — 10 arrows per quiver. Empty it and you get a 3 second reload
  before the quiver refills.

- `ESC` / `P` — Pause the match. The game also pauses when the window loses
  focus.
- `N` — Mute or unmute everything (music and sound effects) from any
  screen. The speaker icon in the scoreboard does the same thing when
  clicked: waves mean sound is on, a red cross means it is off.
- Pause menu — Choose **RESUME**, **RESTART**, or **MAIN MENU** with
  `ESC` / `R` / `M`, or click an option.
- Results screen — Choose **PLAY AGAIN** or **MAIN MENU** with `ENTER` /
  `ESC`, or click an option.

## Screens and sound

The game flows from the main menu through fighter select to a 60-second
match and then to a results screen. You will see the mode select, instructions, live scoreboard, timer,
target difficulty, winner announcement, final scores, confetti, and proper
draw handling. There is also a pause overlay, all inside one shared arena.

The soundtrack uses mp3 tracks in `assets/` — `menu.mp3` on the menu,
`seels.mp3` during the match, and `victory.mp3` on the results screen —
and the match song keeps playing while the game is paused. If a track
file is missing, that screen falls back to a procedural chiptune loop
generated in code, so there is always music. Sound effects are
synthesized square/noise blips, plus cartoon-spring "boing" waves that
fire every time a bullet ricochets or the target gets knocked back.

A speaker icon sits in the scoreboard during a match and in the same
spot on every other screen, so the audio can be cut at a moment's
notice — `N` does the same job from the keyboard. Muting stops the
music where it stands and remembers the track, so unmuting picks the
right loop back up instead of restarting the menu tune mid-match.

The arena itself is rubber: stitched bumper walls with gold spring pads in the
corners, and every impact — bullet ricochet or target hit — sends an expanding
ripple ring through the wall.

## Tech notes

- The whole game renders to a 320×180 virtual screen scaled ×4 with
  nearest-neighbour blitting — sprites, text and effects are genuinely
  pixelated, not just smooth graphics with pixel-style text.
- The supplied archer and arrow pixel sprites are loaded at startup and
  downscaled with nearest-neighbour pixels; the remaining art and text use
  code-drawn pixel graphics. Music and sound effects are synthesized in code.
- Frame-rate independent movement (delta time with a safety clamp) and swept
  circle-vs-segment collisions so fast bullets never tunnel through the target.

## Run it

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## Tuning

The main gameplay settings are collected at the top of `settings.py`. This is
where you can change the match length, core size and speed curve, bullet speed,
ricochet rules, cooldowns, quiver size and reload (`MAG_SIZE`,
`RELOAD_TIME`), scoring tiers, CPU skill (`CPU_*`), and the
encouragement messages.

Music tempo, patterns, and volume settings live in `music.py`.
