# BOUNCE BACK

a 2 player arcade shooter for pygame-ce. me and my mate made it.

both players share one screen and shoot at a little core that bounces
around the middle. it gets smaller and faster as the 60 second match goes
on, and it flings itself away whenever it gets hit.

small target = more points. large 1, medium 3, small 5, tiny 10.

## the whole game is about bouncing

- **bank shots** - if your shot bounces off a wall before it hits the core
  it pays way more. every wall bounce raises the multiplier: one bounce = x2
  (BANK SHOT!), three bounces = x5 (TRIPLE BANK!)
- **BOUNCE BACK** - the title shot. if your bullet goes all the way off your
  own back wall and comes back out again, it pays x6. hardest shot in the
  game, feels amazing
- **hot bullets** - banked bullets heat up and drag a little trail, and the
  game shows their multiplier over them while they fly (X2, X6, X5...)
- **rebound** - hit the core right after it bounces off an arena wall for
  bonus points (REBOUND!)
- **trampolines** - two green bands in the middle of the arena launch the
  core with a speed kick. the core goes zoom
- **living walls** - the walls bulge out where bullets smack them, then
  spring back
- **WALLS ARE LIVE** - every bounce charges the walls up. when the meter
  fills they flash gold and the next banked shot pays one multiplier step
  higher. yes that means a x10 shot is possible. go get it

missed shots keep ricocheting around the arena, so a shot that looks lost
may still come back and save the day.

## modes

- **1P - VS THE CPU**: the cpu aims where the core is going, but its aim
  wanders and it gets worse the longer the match runs
- **2P - VS YOUR MATE**: two people, one keyboard, no friendships harmed
  (allegedly)

tied score at 0:00 = SUDDEN DEATH, first hit wins. no draws, ever.

## controls

| | P1 (blue) | P2 (orange) |
|---|---|---|
| move | W / S | up / down |
| shoot | SPACE | ENTER |

hold shoot to auto fire. ESC or P pauses (the game also pauses itself if
the window loses focus). pause menu: ESC resume, R restart, M menu.
results: ENTER = rematch, ESC or M = menu.

## sound

the music is actual songs now (in `assets/`): `menu.mp3` on the menu,
`seels.mp3` during the match (it keeps playing while paused, and speeds up
for the last 10 seconds) and `victory.mp3` on the results screen. if a song
file is missing, that screen falls back to a chiptune loop the game writes
itself. menu song is "Retro Platforming" by David Fesliyan - legend.

the sfx are all generated in code: square waves, noise bursts and boings.

## tech stuff

- everything draws to a 320x180 surface scaled up x4, so it looks chunky
  on purpose
- the pixel art, the font (a hand made 3x5 one) and the sfx are all
  generated in code. no image files
- the only dependency is pygame-ce

## run it

```
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## tuning

timings, sizes, cpu skill and all the scoring stuff live at the top of
settings.py. DONT TOUCH THE NUMBERS. (we will definitely touch the numbers)
