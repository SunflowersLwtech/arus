# Arus — Banjir Drill · 3-minute Demo Storyboard

Use the WAV files in this directory as voice-over. Each segment lists the
exact screen action + which narration file plays during it.

Generated: 2026-04-22 via Gemini 2.5 Flash TTS (voice=Kore, EN).

## Timeline

| Time | Screen action | Narration file | ~Duration |
|---|---|---|---|
| 0:00 – 0:20 | Kelantan / Shah Alam 2021 flood B-roll (stock footage — Reuters, ReliefWeb, or Malaysiakini). Overlay text: *"40,000 displaced · 54 deaths · 16-hour rooftop wait"*. | `01_hook.wav` | 20 s |
| 0:20 – 0:30 | Product title card: **Arus — Banjir Drill** · "Three modes, one simulation". | `02_title.wav` | 10 s |
| 0:30 – 1:00 | Screen-record the PLAY mode: live URL → tap Start drill → first card appears. Hover the 3 options to show delta chips. | `03_play.wav` | 30 s |
| 1:00 – 1:30 | Continue PLAY: pick "Send BOMBA immediately", Bravo drone flies, gauges animate, NADMA Radio updates. Show 2 more cards quickly. | `04_play_b.wav` | 30 s |
| 1:30 – 2:00 | Play Again → select **Coach** → Start. Wait for first card + CoT streams on right panel. Point cursor at the yellow "🤖 AI suggests" badge and the ghost drone on the map. | `05_coach.wav` | 30 s |
| 2:00 – 2:15 | Let game end (force trust collapse). Scroll the debrief down to the "Alignment with AI expert" section. Highlight the "If you'd followed AI every time: grade C" counterfactual card. | `06_coach_b.wav` | 15 s |
| 2:15 – 2:45 | Click "🤖 Watch the AI tackle this scenario" button. AUTO mode loads. Show the 5-stage progress bar lighting up. Wait for the bottom-centered BM/EN agency handoff toast to pop. | `07_auto.wav` | 30 s |
| 2:45 – 3:00 | **Antigravity B-roll** — open the repo in Antigravity, scroll through `backend/agents/coach.py` + `backend/game/cards.yaml`. End on the close frame: "Citizens First · arus-1030181742799.asia-southeast1.run.app". | `08_close.wav` | 15 s |

## Recording tips

- 1080p, 30fps, use Ghostty/Chrome fullscreen.
- Record each mode in a separate take; cut to the shortest usable segment.
- Browser DevTools audio/network panels should be CLOSED during capture.
- For the Antigravity B-roll, focus on these three files (in order):
  `backend/agents/coach.py:1-60` (2-stage agent),
  `backend/game/cards.yaml:1-40` (scenario spine),
  `backend/services/tool_server.py:1-30` (MCP tools).

## Audio mixing

- Voiceover files are 24 kHz mono WAV.
- Apply a gentle low-pass at 8 kHz + slight compression to sit over screen-capture audio.
- Drop BG music 10–12 dB under voice. Mission-thriller instrumental; no licensed tracks.

## Upload

YouTube unlisted. Title: `Arus — Banjir Drill: Play NADMA for 7 minutes`.
