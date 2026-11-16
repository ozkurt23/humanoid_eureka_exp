"""Evaluate reachable steps in independent copies of the current simulated state."""

import os
import multiprocessing as mp
import numpy as np

# (catch side, delay, swing time, distance, pressure offset)
options = [
    (-1, -1, 0.31, 0.18, 1.22),
    (0, 0.025, 0.20, 0.25, 1.08),
    (0, 0.10, 0.25, 0.20, 1.18),
    (0, 0.24, 0.27, 0.18, 1.20),
    (0, 0.42, 0.29, 0.15, 1.25),
    (1, 0.025, 0.21, 0.17, 1.10),
    (1, 0.12, 0.25, 0.15, 1.15),
    (1, 0.26, 0.28, 0.15, 1.22),
    (1, 0.42, 0.30, 0.12, 1.22),
    (-1, -1, 0.20, 0.08, 1.22),
    (-1, -1, 0.38, 0.09, 1.25),
    (-1, -1, 0.21, 0.30, 1.04),
]
options.extend(
    [
        (0, 0.045, 0.23, 0.24, 0.88),
        (1, 0.05, 0.23, 0.17, 0.92),
        (0, 0.19, 0.28, 0.22, 1.0),
        (1, 0.24, 0.28, 0.19, 1.04),
    ]
)
options.extend(
    [
        (0, 0.035, 0.32, 0.32, 1.28),
        (1, 0.09, 0.19, 0.12, 1.28),
        (0, 0.04, 0.24, 0.31, 0.98),
        (1, 0.12, 0.32, 0.20, 1.36),
    ]
)
options.extend([(-1, -1, 0.28, 0.15, 1.15)] * 7)
options.extend(
    [
        (0, 0.025, 0.17, 0.29, 1.36),
        (1, 0.04, 0.18, 0.13, 1.33),
        (0, 0.13, 0.20, 0.24, 1.43),
        (1, 0.18, 0.22, 0.10, 1.42),
        (0, 0.07, 0.32, 0.32, 0.83),
        (1, 0.05, 0.30, 0.19, 0.85),
    ]
)
# Closing the stance can require landing the outside foot inward when the
# capture point is still travelling towards the other supporting foot.
options.extend(
    [
        (0, 0.03, 0.24, -0.13, 1.18),
        (0, 0.1, 0.30, -0.20, 1.25),
        (0, 0.22, 0.25, -0.15, 1.32),
        (0, 0.04, 0.28, -0.23, 1.05),
        (1, 0.02, 0.21, 0.26, 1.25),
        (1, 0.16, 0.26, 0.29, 1.12),
        (0, 0.025, 0.26, 0.025, 1.10),
        (1, 0.34, 0.30, 0.25, 1.26),
    ]
)
base_options = len(options)
rng = np.random.default_rng(23)
backup = [
    (
        rng.uniform(0.20, 0.50),
        rng.uniform(0.78, 1.58),
        rng.uniform(0.15, 0.36),
        rng.uniform(0.08, 0.15),
        rng.uniform(0.08, 0.25),
        rng.uniform(0.22, 0.39),
        rng.uniform(0.04, 0.14),
        rng.uniform(0.0005, 0.0021),
    )
    for _ in range(48)
]
options.extend([(-1, -1, 0.28, 0.15, 1.15)] * len(backup))


def option(i):
    j = (i - 20) % 4
    if i >= 20:
        os.environ.update(
            RESTSTEP=".16",
            AIRSHIFT=str([0.045, 0.095, 0.15, 0.12][j]),
            LEVER="1.25",
            BIAS=".47",
            TGAIN=".0014",
            PLANT=".24",
            FIRST=str([0.35, 0.23, 0.25, 0.30][j]),
            LEADLEN=str([0.35, 0.25, 0.29, 0.32][j]),
            TRAIL=str([0.25, 0.18, 0.2, 0.22][j]),
            DELTA=str([0.35, 0.25, 0.29, 0.32][j]),
            LAG=str([0.68, 0.73, 0.56, 0.63][j]),
            SIDE_T=str([0.34, 0.38, 0.30, 0.36][j]),
            SQUAT=".14",
            YGAPTIME=".3",
            YJOIN=".90",
            VELFB="0",
        )
    os.environ.update(
        N2=str(int(12 <= i < 16)),
        MEDONLY="0",
        FOLLOW=".88",
        GAP=".55",
        LOAD=".94",
        FFR="0.85",
    )
    os.environ.update(
        {
            k: str(v)
            for k, v in zip(
                ("CHOOSEFOOT", "STARTAT", "SW", "WIDTH", "ALPHA"), options[i]
            )
        }
    )

    if i == 20:
        os.environ.update(
            DELTA=".35",
            FIRST=".35",
            LEADLEN=".35",
            TRAIL=".25",
            SIDE_T=".34",
            PLANT=".25",
            SQUAT=".15",
            LAG=".68",
            YJOIN="1",
            YGAPTIME=".3",
        )
    if i >= base_options:
        b, l, t, h, prep, dur, dist, roll = backup[i - base_options]
        os.environ.update(
            BIAS=str(b),
            LEVER=str(l),
            PLANT=str(t),
            DROP=str(h),
            PREPARE=str(prep),
            CATCHTIME=str(dur),
            CATCHLEN=str(dist),
            TGAIN=str(roll),
            AIRSHIFT=str(dist),
            RESTSTEP=".15",
        )


def forecast(history, dt, hold=1.5):
    # Fit the observed beginning of the shove. Cap extrapolation at the first
    # stationary point and physically bounded amplitude, then hold it for planning.
    sign = np.sign(history[-1])
    y = sign * history
    nz = np.flatnonzero(y > 0.002)
    y = y[nz[0] :]
    x = np.arange(len(y)) * dt
    future = x[-1] + np.arange(round(6.8 / dt)) * dt
    if len(y) > 8:
        coeff = np.polyfit(x, y, 3)
        extrema = np.roots(np.polyder(coeff))
        ends = [
            r.real for r in extrema if abs(r.imag) < 1.0e-5 and x[-1] < r.real < 1.8
        ]
        if ends:
            top = min(ends)
            up = np.clip(np.polyval(coeff, np.minimum(future, top)), 0, 135)
            # Duration is unknown. Check a representative release and subsequent walk.
            down = np.clip((future - top - hold) / max(top, 0.45), 0, 1)
            return sign * up * (1 - down * down * (3 - 2 * down))
    u = np.clip(future / 1.15, 0, 1)
    return sign * 95 * u * u * (3 - 2 * u)


def choose(trial, history, dt, span):
    short = forecast(history, dt, 1.0)
    long = forecast(history, dt, 2.0)

    def evaluate(jobs):
        return evaluate_parallel(trial, jobs)

    # First evaluate the continuous-load policy on its original horizon.
    sustained = forecast(history, dt, 10.0)[: round(3.3 / dt)]
    nominal = evaluate([(i, i, sustained) for i in range(20)])
    original = min(nominal, key=nominal.get)
    candidates = [original]
    mid = forecast(history, dt, 1.5)
    waveforms = (short, mid, long)
    check = evaluate([(k, original, p) for k, p in enumerate(waveforms)])
    if max(check.values()) < 12 and span < 0.66:
        print("catch", original, "N", round(long[np.argmax(abs(long))]), flush=True)
        return original
    # If this pose is not recoverable, consider early planting, the original
    # lateral stepping controller, a different swing, and stronger ankle support.
    candidates += sorted(nominal, key=nominal.get)[:5] + list(range(20, base_options))
    if span > 0.66:
        candidates += list(range(20))
    candidates = sorted(set(candidates))
    scores = evaluate(
        [((i, k), i, p) for i in candidates for k, p in enumerate(waveforms)]
    )
    idx = min(
        candidates, key=lambda i: max(scores[i, k] for k in range(len(waveforms)))
    )
    if max(scores[idx, k] for k in range(3)) > 15:
        extra = list(range(base_options, len(options)))
        screen = evaluate([(i, i, long[: round(1.7 / dt)]) for i in extra])
        top = sorted(extra, key=screen.get)[:10]
        scores.update(
            evaluate([((i, k), i, p) for i in top for k, p in enumerate(waveforms)])
        )
        idx = min(
            [idx] + top,
            key=lambda i: (
                sum(scores[i, k] >= 40 for k in range(3)),
                max(scores[i, k] for k in range(3)),
            ),
        )
    print(
        "catch",
        idx,
        "N",
        round(long[np.argmax(abs(long))]),
        "worst",
        round(max(scores[idx, k] for k in range(3)), 2),
        flush=True,
    )
    return idx


def evaluate_parallel(trial, jobs):
    ctx = mp.get_context("fork")

    def run(i, profile, pipe):
        try:
            pipe.send(float(trial(i, profile)))
        except Exception as exc:
            pipe.send(str(exc))
        finally:
            pipe.close()

    scores = {}
    batch = int(os.environ.get("FANOUT", 2))
    for start in range(0, len(jobs), batch):
        children = []
        for key, i, profile in jobs[start : start + batch]:
            rx, tx = ctx.Pipe(False)
            proc = ctx.Process(target=run, args=(i, profile, tx))
            proc.start()
            tx.close()
            children.append((key, proc, rx))
        for key, proc, rx in children:
            value = rx.recv()
            rx.close()
            proc.join()
            if isinstance(value, str):
                raise RuntimeError(value)
            scores[key] = value
    return scores
