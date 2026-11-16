"""A low catch step with pressure transfer for short reachable landings."""

import numpy as np
from plant import Reflex
from blindbalance import setting, ease


class ShortStep(Reflex):
    def update(self, t, m, d):
        fresh = self.mode is None and abs(self.val) >= setting("EARLY", 2)
        if fresh:
            self.lowstep = max(self.footlast[:, 2] - self.base[:, 2]) < 0.003
            xi = d.subtree_com[1, 0] + d.qvel[0] / self.omega
            self.free_side = int(xi < self.footlast[:, 0].mean())
        p, v, a, f, fv, fa, w, estimate, roll = super().update(t, m, d)
        if self.mode is None or not self.lowstep:
            return p, v, a, f, fv, fa, w, estimate, roll
        age = self.age
        side = self.free_side
        prep = setting("PREPARE", 0.16)
        duration = setting("CATCHTIME", 0.27)
        u = np.clip((age - prep) / duration, 0, 1)
        de = (30 * u * u * (1 - u) ** 2) / duration
        dde = 60 * u * (1 - u) * (1 - 2 * u) / duration**2
        g = 64 * (u * (1 - u)) ** 3
        gd = 192 * u * u * (1 - u) ** 2 * (1 - 2 * u) / duration
        gdd = 384 * u * (1 - u) * (1 - 5 * u + 5 * u * u) / duration**2
        dx = self.sign * setting("CATCHLEN", 0.075)
        f = f.copy()
        fv = fv.copy()
        fa = fa.copy()
        f[side, 0] += dx * ease(u)
        fv[side, 0] += dx * de
        fa[side, 0] += dx * dde
        f[side, 2] += 0.022 * g
        fv[side, 2] += 0.022 * gd
        fa[side, 2] += 0.022 * gdd
        unloading = ease(age / prep) * (
            1 - ease((age - prep - duration + 0.018) / 0.14)
        )
        w = w.copy()
        w[1 - side] += unloading * w[side]
        w[side] *= 1 - unloading
        self.footlast = f.copy()
        # Preserve the completed landing when the parent starts its next gait.
        if age > prep + duration and not getattr(self, "committed", False):
            self.dest[side, 0] += dx
            self.prevfoot[side, 0] += dx
            self.lowstep = False
            self.committed = True
        return p, v, a, f, fv, fa, w, estimate, roll
