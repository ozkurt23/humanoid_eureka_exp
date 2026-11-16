"""Perturbation source used by the simulator, independent of the controller."""

import numpy as np, os


def loads(t):
    rng = np.random.default_rng(int(os.environ.get("SEED", "714")))
    center = np.array([6.65, 16.75, 27.75, 39.3, 47.15]) + rng.uniform(-0.65, 0.65, 5)
    signed = (
        np.array([60, 75, 85, 100, 115])
        * np.array([1, -1, 1, -1, 1])
        * float(os.environ.get("AMP", "1"))
    )
    signed *= rng.choice([-1, 1])
    durations = [1.0, 1.25, 1.5, 1.75, 2.0]
    if os.environ.get("RANDOM_EVENTS"):
        # The external disturbance generator never reads controller state.
        center = np.arange(5) * 10.3 + rng.uniform(3.0, 7.5, 5)
        signed = rng.uniform(60.0, 115.0, 5) * rng.choice([-1, 1], 5)
        durations = rng.uniform(1.0, 2.0, 5)
    rise = float(os.environ.get("RISE", ".55"))
    y = np.zeros_like(t)
    for a, b, c in zip(center, durations, signed):
        if os.environ.get("VARY_RISE"):
            rise = rng.uniform(0.85, 1.35)

        def ease(x):
            u = np.clip(x, 0, 1)
            return u * u * (3 - 2 * u)

        y += c * ease((t - a) / rise) * ease((a + b + 2 * rise - t) / rise)
    return y
