#!/usr/bin/env python3
"""Build the static puzzle data for Spectrum.

Reads puzzles/src/categories.json and puzzles/src/puzzles.json plus a word-vector file, and writes
for every puzzle:
  puzzles/<id>/puzzle.json   category, answer and its positions, spectrum end words
  puzzles/<id>/w/<hex>.json  256 shards: every vocabulary word -> [pos on each spectrum (x100), category fit (0..100)]
and puzzles/index.json, the day-by-day schedule.

A word's position on a spectrum comes from a ridge regression fitted to that spectrum's anchor words
(plus its end words and synonyms at -1 / +1), which places words far better than a plain
"high minus low" direction. Leave-one-out error is printed per spectrum so anchors can be improved.

Usage:  .venv/bin/python build.py [--vectors data/glove-wiki-gigaword-100.gz] [--vocab 200000] [--days 120]
"""
import argparse, datetime, gzip, json, os, re, shutil
import numpy as np

SHARDS = 256
SRC = os.path.join('puzzles', 'src')


def fnv1a(s):
    """Same hash as the browser uses to find a word's shard."""
    h = 0x811c9dc5
    for b in s.encode('utf8'):
        h = ((h ^ b) * 0x01000193) & 0xffffffff
    return h


def load_vectors(path, limit):
    words, rows = [], []
    opener = gzip.open if path.endswith('.gz') else open
    with opener(path, 'rt', encoding='utf8') as f:
        first = f.readline().split()
        if len(first) != 2:            # plain GloVe text has no "count dim" header line
            f.seek(0)
        for line in f:
            w, rest = line.split(' ', 1)
            if not re.fullmatch(r'[a-z]+', w):
                continue
            words.append(w)
            rows.append(np.array(rest.split(), dtype=np.float32))
            if len(words) == limit:
                break
    X = np.vstack(rows)
    X /= np.linalg.norm(X, axis=1, keepdims=True)
    return words, X


def ridge(A, y, lam):
    """Ridge regression with an (almost) unregularised bias term."""
    A1 = np.hstack([A, np.ones((len(A), 1))])
    reg = lam * np.eye(A1.shape[1])
    reg[-1, -1] = 1e-6
    return np.linalg.solve(A1.T @ A1 + reg, A1.T @ y)


def predict(w, A):
    return np.hstack([A, np.ones((len(A), 1))]) @ w


def model(A, y, lam, tau, alpha):
    """A scorer blending two estimates of a word's position from the anchors (A, y):
    - a ridge-regression direction through the embedding (global, can extrapolate), and
    - a similarity-weighted average of the anchors' positions (local: a word lands near the
      anchors it most resembles, and can never leave the anchors' range).
    alpha is the weight of the local estimate; tau is the softmax temperature over cosine similarity."""
    w = ridge(A, y, lam)
    a, b = np.polyfit(predict(w, A), y, 1)

    def score(Xq):
        lin = a * predict(w, Xq) + b
        S = Xq @ A.T
        K = np.exp((S - S.max(axis=1, keepdims=True)) / tau)
        local = (K @ y) / K.sum(axis=1)
        return np.clip(alpha * local + (1 - alpha) * lin, -1, 1)
    return score


def fit_spectrum(spec, index, X):
    """Chooses the model settings with the lowest leave-one-out error over the anchors.
    Returns (scorer, loo_error, missing words, settings)."""
    samples = {}
    for w in [spec['low']] + spec.get('lowSyn', []):
        samples[w] = -1.0
    for w in [spec['high']] + spec.get('highSyn', []):
        samples[w] = 1.0
    samples.update(spec.get('anchors', {}))
    known = [w for w in samples if w in index]
    missing = [w for w in samples if w not in index]
    A = X[[index[w] for w in known]]
    y = np.array([samples[w] for w in known])

    best = None
    # The local estimate always gets at least half the weight: the linear one alone can look fine
    # on the anchors yet fling unrelated words to the ends of the scale.
    for lam in (0.1, 0.3, 1.0, 3.0):
        for tau in (0.04, 0.07, 0.1):
            for alpha in (0.5, 0.75, 1.0):
                errs = []
                for i in range(len(known)):
                    m = np.ones(len(known), bool)
                    m[i] = False
                    p = model(A[m], y[m], lam, tau, alpha)(A[i:i + 1])[0]
                    errs.append(abs(p - y[i]))
                err = float(np.mean(errs))
                if best is None or err < best[0]:
                    best = (err, (lam, tau, alpha))
    err, settings = best
    return model(A, y, *settings), err, missing, settings


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--vectors', default='data/glove-wiki-gigaword-100.gz')
    ap.add_argument('--vocab', type=int, default=200000)
    ap.add_argument('--days', type=int, default=120)
    ap.add_argument('--launch', default='2026-10-11')
    args = ap.parse_args()

    cats = json.load(open(os.path.join(SRC, 'categories.json')))['categories']
    puzzles = json.load(open(os.path.join(SRC, 'puzzles.json')))['puzzles']

    print(f'loading {args.vocab} words from {args.vectors} ...')
    words, X = load_vectors(args.vectors, args.vocab)
    index = {w: i for i, w in enumerate(words)}
    X1 = np.hstack([X, np.ones((len(X), 1))])
    print(f'{len(words)} words, {X.shape[1]} dims')

    # Category fit: how close a word is to the nearest seed word (0..100). No seeds = everything fits.
    fits = {}
    for cid, cat in cats.items():
        seeds = [index[s] for s in cat['seeds'] if s in index]
        fits[cid] = np.full(len(words), 100, dtype=np.int16) if not seeds else \
            np.clip(np.rint((X @ X[seeds].T).max(axis=1) * 100), 0, 100).astype(np.int16)

    # Fit every spectrum in every category once, then reuse across puzzles.
    axes = {}
    for cid, cat in cats.items():
        # Diagnostics look only at common words that fit the category, i.e. words players will guess.
        relevant = np.where(fits[cid][:30000] >= (50 if cat['seeds'] else 0))[0]
        for key, spec in cat['spectrums'].items():
            low, high = key.split('|')
            spec = {**spec, 'low': low, 'high': high}
            scorer, err, missing, settings = fit_spectrum(spec, index, X)
            pos = scorer(X)
            axes[(cid, key)] = pos
            top = relevant[np.argsort(pos[relevant])]
            print(f'  {cid:7} {key:22} loo err {err:.2f}  {str(settings):18}'
                  f'  {low}: {", ".join(words[i] for i in top[:5])}  |  {high}: {", ".join(words[i] for i in top[-5:][::-1])}'
                  + (f'  MISSING {missing}' if missing else ''))

    for p in puzzles:
        cid = p['category']
        cat = cats[cid]
        out = os.path.join('puzzles', p['id'])
        shutil.rmtree(out, ignore_errors=True)
        os.makedirs(os.path.join(out, 'w'))
        cols = np.stack([axes[(cid, k)] for k in p['spectrums']], axis=1)
        q = np.rint(cols * 100).astype(np.int16)
        if p['answer'] not in index:
            raise SystemExit(f'answer "{p["answer"]}" is not in the vocabulary')
        ans = index[p['answer']]
        fit = fits[cid]
        # For Darts: the board's two axes are the least correlated pair of the puzzle's spectrums
        # (measured over the words that fit the category), and `common` is the category's hand-picked
        # words (its seeds and every spectrum's anchors) with their positions, used to place reachable
        # targets and to reveal, at the end, which words would have hit each target. Fit-based lists
        # were tried and gave generic words ("food", "job"); the curated ones are real category items.
        # The Spectrum answer is left out of it.
        fitting = np.where(fit >= 50)[0]
        corr = np.corrcoef(cols[fitting].T) if len(fitting) > 2 else np.eye(4)
        board = min(((i, j) for i in range(4) for j in range(i + 1, 4)), key=lambda ij: abs(corr[ij]))
        curated = set(cat['seeds'])
        for spec in cat['spectrums'].values():
            curated |= set(spec.get('anchors', {}))
        common = {w: [int(v) for v in q[index[w]]] for w in sorted(curated) if w in index and w != p['answer']}
        json.dump({
            'id': p['id'], 'category': cat['name'], 'answer': p['answer'],
            'answerPos': [int(v) for v in q[ans]],
            'spectrums': [dict(zip(('low', 'high'), k.split('|'))) for k in p['spectrums']],
            'board': list(board), 'common': common,
        }, open(os.path.join(out, 'puzzle.json'), 'w'))
        print(f'  board {p["spectrums"][board[0]]} x {p["spectrums"][board[1]]} (r={corr[board]:+.2f}), {len(common)} common words')
        shards = [{} for _ in range(SHARDS)]
        for i, w in enumerate(words):
            shards[fnv1a(w) % SHARDS][w] = [int(v) for v in q[i]] + [int(fit[i])]
        for n, shard in enumerate(shards):
            json.dump(shard, open(os.path.join(out, 'w', f'{n:02x}.json'), 'w'), separators=(',', ':'))
        print(f'wrote {out}: answer {p["answer"]} at {q[ans].tolist()}')

    # Arena (the Darts console game): rounds change category but the two axes stay fixed, so the axes
    # are the general spectrums of the 'random' bank. One shard set carries every word's position on
    # all six of them plus its fit for each seeded category; arena.json carries the spectrum and
    # category names, the least correlated axis pairs, and each category's curated words with their
    # positions (for reachable targets, the reverse round's word and the end-of-game reveal).
    gkeys = list(cats['random']['spectrums'].keys())
    gcols = np.stack([axes[('random', k)] for k in gkeys], axis=1)
    gq = np.rint(gcols * 100).astype(np.int16)
    gcorr = np.corrcoef(gcols[:50000].T)
    pairs = sorted(((i, j) for i in range(len(gkeys)) for j in range(i + 1, len(gkeys))), key=lambda ij: abs(gcorr[ij]))
    pairs = [list(ij) for ij in pairs if abs(gcorr[ij]) <= 0.3] or [list(pairs[0])]
    # The arena's categories are the specific ones in arena-categories.json: each is its seed words.
    acats = json.load(open(os.path.join(SRC, 'arena-categories.json')))['categories']
    afits, curated, thresholds, missing_seeds = {}, {}, {}, {}
    for cat in acats:
        seeds = [w for w in cat['seeds'] if w in index]
        missing_seeds[cat['id']] = [w for w in cat['seeds'] if w not in index]
        S = X[[index[w] for w in seeds]]
        sims = X @ S.T
        afits[cat['id']] = np.clip(np.rint(sims.max(axis=1) * 100), 0, 100).astype(np.int16)
        curated[cat['id']] = {w: [int(v) for v in gq[index[w]]] for w in seeds}
        # A word counts as the category if its fit clears a threshold calibrated on the seeds themselves,
        # leave-one-out: each seed's closeness to the nearest OTHER seed (a seed against itself is 100).
        # 80% of the 10th percentile of those, at least 20.
        ss = S @ S.T
        np.fill_diagonal(ss, -1)
        loo = ss.max(axis=1) * 100
        thresholds[cat['id']] = int(max(20, round(0.8 * np.percentile(loo, 10))))
    out = os.path.join('puzzles', 'arena')
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(os.path.join(out, 'w'))
    json.dump({
        'spectrums': [dict(zip(('low', 'high'), k.split('|'))) for k in gkeys],
        'categories': [{'id': cat['id'], 'name': cat['name'], 'threshold': thresholds[cat['id']]} for cat in acats],
        'pairs': pairs, 'curated': curated, 'launch': args.launch,
    }, open(os.path.join(out, 'arena.json'), 'w'))
    for cid, miss in missing_seeds.items():
        if miss:
            print(f'  arena category {cid}: seeds not in the vocabulary: {miss}')
    shards = [{} for _ in range(SHARDS)]
    catfits = [afits[cat['id']] for cat in acats]
    catids = [cat['id'] for cat in acats]
    for i, w in enumerate(words):
        shards[fnv1a(w) % SHARDS][w] = [int(v) for v in gq[i]] + [int(f[i]) for f in catfits]
    for n, shard in enumerate(shards):
        json.dump(shard, open(os.path.join(out, 'w', f'{n:02x}.json'), 'w'), separators=(',', ':'))
    print(f'arena: axes {gkeys}; pairs {[(gkeys[i], gkeys[j], round(float(gcorr[i, j]), 2)) for i, j in pairs]}; '
          f'{len(catids)} categories, thresholds {thresholds}')

    # Schedule: each weekday has a category; that category's puzzles are used in turn, one per week.
    by_cat = {}
    for p in puzzles:
        by_cat.setdefault(p['category'], []).append(p['id'])
    weekday_cat = {cat['weekday']: cid for cid, cat in cats.items()}
    launch = datetime.date.fromisoformat(args.launch)
    days = {}
    for n in range(args.days):
        d = launch + datetime.timedelta(days=n)
        cid = weekday_cat[(d.weekday() + 1) % 7]   # Python: Monday = 0; we use Sunday = 0 like JS
        ids = by_cat[cid]
        days[d.isoformat()] = ids[(n // 7) % len(ids)]
    json.dump({'launch': args.launch, 'days': days}, open(os.path.join('puzzles', 'index.json'), 'w'), indent=1)
    print(f'schedule: {args.days} days from {args.launch}')


if __name__ == '__main__':
    main()
