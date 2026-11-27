# HK Pet Volleyball

**Early review build.** Phase 0 is a side-view 1v1 arcade rally. The court looks across Victoria Harbour: The Peak on one side, ICC on the other. It is offline only: you pick a mascot and play a short set against the AI.

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
6. Set the Game view to a **landscape** aspect (16:9, or an iPhone landscape preset). Pick **Cha Cha**, **Miso**, or **Biscuit** by tapping the card, or press 1 / 2 / 3.
7. You serve first. Tap **SERVE** or press **F**, then rally until the set ends. **Rematch** keeps the same mascots. **Change mascot** returns to the picker.

The unused mascot stands on the left railing, so all three are on screen during a match. The picker also cycles their poses.

### Controls

On-screen buttons sit in the bottom corners so they stay off the score, the ball, and the net. In the Editor, click and hold them in the Game view. On an iPhone they are the thumb controls. Keyboard still works.

| Action | On screen | Keys |
| --- | --- | --- |
| Move left / right | Hold **◀** or **▶** (bottom left) | A / D or Left / Right |
| Jump | **JUMP** (bottom right) | W, Up, or Space |
| Hit / serve | **HIT** / **SERVE** (bottom right) | F, J, K, S, or Down |
| Pick a mascot | Tap the card | 1 / 2 / 3 |
| Leave the match | **Mascots** | Esc |
| Rematch / new mascot | **Rematch** / **Change mascot** | R / M |

On a phone, hold a move button with the left thumb and tap JUMP or HIT with the right thumb at the same time. In the Editor the mouse is one pointer, so hold ◀ or ▶ and use the keyboard for jump or hit when you want both at once, or click one button at a time.

### What the hit button does

The same button covers every touch. The pose and the ball decide the shot:

- **Bump** — low ball, or the first touch. Pops the ball up just in front of you and lets it hang, so the next pass is the same ball you are already under. The receive window is wide on purpose: press a little early or a little late and it still connects. You still have to be there and press hit. Missing the ball loses the point.
- **Set** — ball is up, you are on the ground, and it is not your last touch. Lifts a high pass toward the net.
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

Poses: idle, ready, run (two steps), jump, bump, and spike. Pose changes crossfade, and a jump stretches on the way up and squashes on landing, so the cats (and Biscuit) do not pop between still drawings.

## iPhone build

This is an iOS player setup only. **No IPA was built, and nothing was uploaded to TestFlight or App Store Connect.** This machine has no Unity Editor and no Xcode, so it cannot sign or produce a device build. Do not upload to TestFlight or App Store Connect from this project unless Barry or Legend has approved it and signing credentials are in place.

Player settings already in the project:

| Setting | Value |
| --- | --- |
| Bundle identifier | `com.barrysjh.hkpetvolleyball` |
| Minimum iOS | **15.0** (Unity 6000.3 supports iOS 15 and later) |
| Orientation | Landscape only (Landscape Left and Landscape Right). Portrait is off. |
| Target device | iPhone |
| Scripting backend | IL2CPP (required for iOS) |
| Apple Team ID | Not set. Do not invent one. |

Xcode **16 or later** matches what Unity 6000.3 documents for iOS.

### Build the Xcode project locally

1. In Unity Hub, install **6000.3.28f1** (or a later 6000.3 LTS) with the **iOS Build Support** module.
2. Open this project and wait for import and script compile to finish.
3. **File → Build Profiles**.
4. Select the **iOS** platform. If it is missing, install the iOS module from Hub and return here.
5. Click **Switch Platform** and wait for the reimport.
6. Confirm **Player Settings** (the button on that profile, or **Edit → Project Settings → Player**):
   - Company / product can stay as they are.
   - **Other Settings → Bundle Identifier** is `com.barrysjh.hkpetvolleyball`.
   - **Target minimum iOS version** is **15.0**.
   - **Resolution and Presentation**: default orientation is landscape autorotation, portrait disabled.
   - **Identification → Signing Team ID** stays empty in the repo. Set the team in Xcode, not by committing an Apple ID.
7. Click **Build**. Choose an empty output folder (for example `Builds/iOS`). Do not use **Build And Run** until signing is set up.
8. When the build finishes, open `Unity-iPhone.xcodeproj` from that folder in Xcode.
9. Select the **Unity-iPhone** target → **Signing & Capabilities**. Turn on **Automatically manage signing** and choose your Apple Developer team. That step needs your own Apple Developer account. This repo does not create one.
10. Destination: your iPhone, or **Any iOS Device** if you only want to archive later. **Product → Run** installs a development build on a phone you have registered.

A development install from Xcode is not a TestFlight build. Archiving and uploading to App Store Connect is a separate step and is **not** part of this PR.

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

No matchmaking, accounts, photo-to-pet pipeline, second sport, HealthKit, Mapbox, or IAP. No TestFlight or App Store Connect upload. This is not district-pet-brawl and does not link to it.

## Reference photos

The personal reference photos used to design the mascots are **not in this repository** and must not be added. Their filenames are listed in `.gitignore`:

- `cat1-orange-tabby.jpg`
- `cat2-orange-white.jpg`
- `dog1-from-ig.jpg`
- `dog2-from-ig.jpg`
- `dog3-from-ig.jpg`
