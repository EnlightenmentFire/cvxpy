# Pickaxe Pete Goes Crypto Mining — delivery notes

**Files**
- `final_vertical.mp4`: 1080×1920, 30 fps, H.264 + AAC stereo, 1:53 (113.2 s), 13.6 MB
- `final_horizontal.mp4`: 1920×1080, same specs, 14.1 MB
- `voice_tests/scene4_test_{kokoro,chatterbox,dia}.mp3`: the 15-second Scene 4 engine comparison
- `src/`: everything that generates the film (art, music, SFX, voices, mix, render) plus the QA report

## Voice engine: Chatterbox (Resemble AI, MIT)
I tested all three engines on Scene 4.

| Engine | Result |
|---|---|
| **Dia 1.6B** | Rejected. It dropped Pete's line from the two-speaker take, cut Riggy off mid-line ("I get new…"), and picked a random high voice for him. On this CPU-only machine it was also ~14× slower than real time. |
| **Kokoro** | Clean and fast, but the flattest delivery (narrowest pitch range). Sounds like narration. |
| **Chatterbox** ✅ | Most actor-like. Exaggeration was set high for Pete (0.72; 0.95 on shouts) and Riggy (0.9), and low for Zoe (0.3). |

Chatterbox clones a voice from a short reference clip. To avoid using any real person's voice, I made the three reference voices with Kokoro: Pete is pitched down with extra low end, Zoe is dry, Riggy is big and compressed.

For each line I generated three takes. Whisper transcribed every take; garbled takes were rejected, and the liveliest accurate one was kept. For Pete and Riggy that means the widest pitch range; for Zoe, the take closest to deadpan.

Post-processing per character:
- **Pete:** warm low end and tanh saturation for gravel. Shouts are +3 dB, since he's a bit hard of hearing.
- **Zoe:** dry and close.
- **Riggy:** +7% pitch, light bitcrush, flanger, compression and a three-tap echo for the robot announcer sound.

## Length: 113 s, over the 75–100 s target
The script is fixed at about 330 words, and Chatterbox reads it at a natural comic pace. The first assembly was 130 s. To tighten it I:
- capped dead air inside lines at 0.2 s, keeping the scripted "…" beats at up to 0.42 s;
- sped delivery up 7–10% with pitch preserved;
- set gaps between lines to 0.2–0.3 s;
- trimmed scene intros and tails.

Going below about 110 s would mean rushing the jokes or cutting lines.

## What I changed or added
- **Script:** meaning is unchanged. Only TTS punctuation was tuned (e.g. "A WHOLE COUNTRY?!"). Subtitles show the script text exactly, with Riggy in ALL CAPS. Pete's "(beat) …Well. Good to know…" is two clips with a 0.5 s beat between them.
- **Stage banners:** each scene opens with a game-style card ("STAGE 3: THE NOTEBOOK").
- **Fact cards:** "TIP" cards state the five facts in plain words:
  - everyone has the same copy;
  - mining = guessing;
  - the winner writes the page and gets new coins;
  - more miners make the game harder, so a page still takes about 10 min;
  - guessing burns lots of electricity and makes heat.
- **Extra gags:**
  - "GOLD: 0" HUD and circling vultures in 1849;
  - a tumbleweed rolls through the warehouse during the silent beat before "…Where's the dirt?";
  - a rooftop crowd whose copies all flash in sync, and one cheater flagged "DOESN'T MATCH!";
  - a saloon tab whose tally marks get secretly erased ("NOT HONEST");
  - Pete's hat flies off on "A WHOLE COUNTRY?";
  - Biscuit gets a personal rain cloud, faints, and ends the film asleep in the hot tub.
- **Riggy:** drawn at 2× scale in the vertical cut so he reads as a giant rack.
- **Layout:** in the vertical cut, subtitles sit at y = 1220–1600 px, clear of the top 200 px and the bottom 300 px.

## Music and SFX
All of it is synthesized in code (`src/synth.py`); no samples are used.
- **Music:** an original western chiptune for Scenes 1 and 8, and an original 16-bit adventure loop for Scenes 2–7, with a hotter variation in Scene 5.
- **Ducking:** music drops 12 dB under the voices, and cuts to silence before "…Where's the dirt?" and "…Well."
- **SFX:** warp, coin jingles, accelerating "WRONG" buzzer storm, jackpot fanfare, dragon roars, meter whir, mule hee-haw, splash and a game-over jingle.

## QA results
- I rendered the low-res preview first, reviewed it frame by frame on contact sheets in both orientations, and fixed overlaps and timing before the final render.
- Whisper transcribed every line from the final mp4's own audio (music and SFX included): **33 of 33 lines pass**. See `src/final_qa.txt`. One line ("I'd build") blurred after the speed-up, so it now plays at natural speed.
- Loudness is −16.2 LUFS integrated with a true peak of −3.7 dBTP, so there is no clipping. Both files are well under 100 MB.
- There are no real coin names, companies, people, prices or advice. All art, sound and characters are original.
