# Pitch deck rewrite kit

Cursor and this chat cannot preview `.pptx` files. This folder is the workaround.

## What the photographed lecture said

Open [`lecture.html`](./lecture.html) in a browser. That page reconstructs the APSUP / SEE Pakistan 2026 Entrepreneurial Bootcamp session: three jobs of a deck, six investor questions, the chain of conviction, and the scorecard.

## How to alter a pitch deck here

1. Paste real company facts into `COMPANY` at the top of `generate_pitch_deck.py`.
2. Regenerate:

```bash
python3 talks/2026-see-pakistan-pitch-deck/generate_pitch_deck.py
```

3. Review the result in [`pitch-preview.html`](./pitch-preview.html) (works in this environment).
4. Download `YOUR-PITCH-DECK.pptx` for PowerPoint / Google Slides.

If you have an existing deck, do **not** try to attach the `.pptx` in chat. Paste slide-by-slide text, or drop photos of each slide, or add the file to this folder in the repo. The rewrite follows the bootcamp chain: one breath → problem → solution/why now → market math → traction → model/GTM → competition → team → ask.
