# HK Pet Volleyball

**Early review build.** Phase 0 is a side-view 1v1 arcade rally on a Hong Kong harbour rooftop. It is offline only: you pick a mascot and play a short set against the AI.

This project was assembled without a Unity Editor on the build machine. **Play Mode was not run.** The first time you press Play, you are the playtest.

## Editor

- **Unity 6000.3.28f1 LTS** (changeset `8f082d2fe476`)
- A later **6000.3 LTS** patch is fine. Let Hub upgrade the project if it asks.
- Built-in render pipeline. No URP package, no extra registry downloads required to press Play.

## Open and play

1. Install **6000.3.28f1** (or a later 6000.3 LTS) in Unity Hub.
2. Hub → **Add** → **Add project from disk** → this folder (`hk-pet-volleyball`).
3. Open the project and wait until the import / script compile spinner finishes.
4. The editor should land on `Assets/Scenes/Phase0_Court.unity`. If it does not, double-click that scene.
5. The Scene view is only a camera until you play. The court, mascots, and HUD are built in Play Mode. Click the **Game** view once (so the keyboard goes to the game), then press **Play**.
6. Pick **Cha Cha**, **Miso**, or **Biscuit** (click or press 1 / 2 / 3).
7. You serve first. Press **F** to serve, then rally until the set ends. **Rematch** keeps the same mascots. **Change mascot** returns to the picker.

The unused mascot stands on the left railing, so all three are on screen during a match. The picker also cycles their poses.

### Controls

| Action | Keys |
| --- | --- |
| Move | A / D or Left / Right |
| Jump | W, Up, or Space |
| Hit / serve | F, J, K, S, or Down |
| Leave the match | Esc, or the Mascots button |
| Rematch / new mascot | R / M on the set-end card |

### What the hit button does

The same button covers every touch. The pose and the ball decide the shot:

- **Bump** — low ball, or the first touch. Pops the ball up on your side.
- **Set** — ball is up, you are on the ground, and it is not your last touch. Places a high ball near the net.
- **Spike** — you are in the air and the ball is high. Drives it onto the other court. Closer to the sweet spot is faster and deeper.
- **Block** — jump at the net against a smash.
- **Last touch** that is not a spike or block sends a safe arc over the net.

You get **three touches**. A block does not use one up. The serve has to cross before you can touch it again. The floor on your side, a ball that flies long, or a fourth touch is a point for the other side. A ball that dies on your side of the net after clipping it is a net point.

A small marker shows where a falling ball will land. Contact pops **OK / GOOD / PERFECT**.

### Set

First to **7**, **win by 2**, **cap 10** (10–9 ends it). You serve first, then the serve alternates.

### Mascots

Hand-drawn sticker sprites, not the reference photos.

- **Cha Cha** — compact ginger tabby, amber eyes, white chest blaze. Balanced.
- **Miso** — orange tabby cap and back, white muzzle, chest, and paws, green-gold eyes. Slightly higher jump.
- **Biscuit** — long low red-and-white Pembroke, large erect ears, white forehead blaze, white chest and paws, white rump patch. Faster, lower reach. No harness and no clothing.

Poses in each file: idle, ready, bump, spike.

## What a human playtest still needs to judge

Please play at least one full set with each mascot and note:

- Whether the serve is easy to return, and whether bump → set → spike is obvious without reading this file.
- Whether spikes clear the net often enough, and whether a good spike actually beats the AI.
- Whether the AI returns lobs often enough to rally, and whether it is too sticky or too sleepy.
- Whether Biscuit’s lower reach feels like a corgi or just like a handicap.
- Timing window: early / late hits should miss or come off weak; on-time hits should feel fair. The hit buffer is short on purpose.
- Anything that reads as the wrong animal, or a marking that does not match the pets you know.

Tuning lives in `Assets/Scripts/MatchSim.cs` (`Tune`, `Mascots`, and the shot solvers). Presentation and input live in `Assets/Scripts/Phase0Game.cs`.

## Project layout

- `Assets/Scenes/Phase0_Court.unity` — the only scene. One bootstrap object builds the court at runtime.
- `Assets/Resources/Athletes/` — sticker poses.
- `Assets/Resources/Court/` — rooftop backdrop, net, ball.
- `ArtSource/make_sprites.py` — the generator for that original art. It does not read photographs.

If a sprite fails to import, the match still runs with flat placeholders and a console warning. That means the texture importer did not keep the sprite type; select the PNGs, set Texture Type to **Sprite (2D and UI)**, and press Play again.

## Not in this build

No matchmaking, accounts, photo-to-pet pipeline, second sport, HealthKit, Mapbox, IAP, or store upload. This is not district-pet-brawl and does not link to it.

## Reference photos

The personal reference photos used to design the mascots are **not in this repository** and must not be added. Their filenames are listed in `.gitignore`:

- `cat1-orange-tabby.jpg`
- `cat2-orange-white.jpg`
- `dog1-from-ig.jpg`
- `dog2-from-ig.jpg`
- `dog3-from-ig.jpg`
