# Spectrum

Two daily word games on one page, live at https://henri-cmd.github.io/spectrum/ (the Darts tab is https://henri-cmd.github.io/spectrum/#darts).

**Spectrum** is a daily word game. Each day has a category and a hidden answer. Four spectrums (like *tiny ↔ huge*) are revealed one at a time; each guess is marked on its spectrum by where it sits compared with the answer. After four guesses comes a final guess with all four showing. Any word the game knows (200,000 of them) can be guessed.

**Darts** is the comparison game, built on the same data. The two least alike of the day's spectrums become the axes of a dartboard with a grid over it (`build.py` picks the pair with the lowest correlation over the category's words). Each of four rounds sets a new target, seeded by the date so everyone gets the same ones: the first three each land in a different quarter of the board, and the last is always the bull at the very centre. A thrown word lands where it sits on both spectrums and scores the ring it lands in: 50 for the bull, then 25, 10 and 5. At the end, the category's hand-picked words (seeds and anchors) that would have scored most on each target are revealed. "New targets" gives unseeded practice rounds on the same board.

## Files

- `index.html` — both games and the tab switcher. No build step; serve the folder over http.
- `game.js` — Spectrum. `darts.js` — Darts. Each loads the day's puzzle on its own and they share nothing but the data files.
- `puzzles/src/categories.json` — each weekday's category, the seed words that define what fits it, and its bank of spectrums with anchor words.
- `puzzles/src/puzzles.json` — the puzzles: an answer and four spectrums from the category's bank.
- `build.py` — generates `puzzles/<id>/…` and `puzzles/index.json` (the day-by-day schedule).
- `designs.html` — the seven chart designs that were compared when choosing the wheel and star views.

## Running locally

```bash
python3 -m http.server 8000
```

then open http://localhost:8000.

## Rebuilding puzzle data

Needs Python 3 with numpy, and a word-vector file in GloVe/word2vec text format (gzipped is fine). The live data was built with `glove-wiki-gigaword-300.gz` (394 MB, from the gensim-data releases on GitHub), which places words noticeably better than the 100-dimension file.

```bash
python3 -m venv .venv && .venv/bin/pip install numpy
.venv/bin/python build.py --vectors data/glove-wiki-gigaword-300.gz
```

The build prints, for every spectrum, its leave-one-out error over the anchors (lower is better; 0.2 is good, 0.5 is rough) and the words that land at each end. Improve a spectrum by adding anchors: common words from the category with a hand-placed position from −1 to 1.

## Adding a puzzle

Add an entry to `puzzles/src/puzzles.json` (answer must be a single word the vectors know), optionally add spectrums or anchors to `categories.json`, and run the build. Each weekday's category uses its puzzles in order, one per week; the schedule is generated for 120 days from the launch date (`--launch`, `--days`).

## Scoring

Spectrum: `scoreGame()` at the top of `game.js` is the one place the rule lives: the closest guess's mean gap from the answer across the revealed spectrums, mapped to 0–100. Only the exact answer scores 100.

Darts: `RINGS` and `scoreDart()` at the top of `darts.js`, with the number of rounds, the target band and the grid spacing as constants beside them. `puzzle.json` carries the board axes (`board`) and the curated words with positions (`common`).
