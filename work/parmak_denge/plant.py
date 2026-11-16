"""Contact-triggered early landing for perturbations that arrive during a swing."""

import numpy as np
from blindbalance import Balance, setting, ease


class Reflex(Balance):
    def nominal(self, g):
        foot, weight = super().nominal(g)
        if hasattr(self, "offsets"):
            for s in range(2):
                order = (s - self.first) % 2
                phase = (np.asarray(g) - self.start) / self.period - order
                foot[:, s, 0] += self.offsets[s] * ease(
                    (phase - setting("LIFT", 0.25))
                    / (setting("LAND", 0.69) - setting("LIFT", 0.25))
                )
        return foot, weight

    def __init__(self, *args):
        self.pending = getattr(self, "offsets", np.zeros(2))
        super().__init__(*args)
        self.mode = None

    def update(self, t, m, d):
        if self.mode is None and abs(self.val) < setting("EARLY", 2):
            return super().update(t, m, d)
        if self.mode is None:
            self.age = 0.0
            self.quiet = 0.0
            self.pos0 = self.footlast.copy()
            self.vel0 = self.fv.copy()
            self.dest = self.pos0.copy()
            self.dest[:, 2] = self.base[:, 2]
            self.rpos = d.qpos[:3].copy()
            self.rvel = d.qvel[:3].copy()
            self.rheight = self.root0[2]
            self.duration = setting("PLANT", 0.26)
            self.swinging = int(np.argmax(self.pos0[:, 2] - self.base[:, 2]))
            self.air = np.max(self.pos0[:, 2] - self.base[:, 2]) > 0.002
            self.dest[:, 1] += self.vel0[:, 1] * self.duration * 0.28
            if self.air:
                s = self.swinging
                self.dest[s, 0] += np.clip(
                    setting("CATCH", 0.21) * d.qvel[0]
                    + setting("EARLYLEAD", 0.0006) * self.fdot,
                    -0.13,
                    0.13,
                )
            self.sign = np.sign(self.val)
            if self.air:
                s = self.swinging
                self.dest[s, 0] = self.pos0[s, 0] + self.sign * setting(
                    "AIRSHIFT", 0.085
                )
            self.holding = True
            self.t0 = t
            self.mode = 1
            self.prevfoot = self.footlast.copy()
            self.prevfv = self.fv.copy()
        dt = self.dt
        old = self.estimate
        self.estimate += (self.val - old) * dt / (setting("OBS", 0.035) + dt)
        self.fdot += dt / (0.045 + dt) * ((self.estimate - old) / dt - self.fdot)
        self.age += dt
        self.quiet = self.quiet + dt if abs(self.estimate) < 2.5 else 0.0
        if self.quiet > 0.68 and self.age > 0.95:
            self.offsets = self.sign * setting("RESTSTEP", 0.16) - (
                self.dest[:, 0] - self.pos0[:, 0]
            )
            self.restarted = True
            self.holding = False
            self.__init__(
                m,
                d,
                dt,
                self.dest.copy(),
                d.qpos[:3].copy(),
                self.com.copy(),
                self.period,
                self.stride,
                self.clear,
            )
            return super().update(t, m, d)
        T = self.duration
        u = np.clip(self.age / T, 0, 1)
        foot = (
            self.pos0
            + (self.dest - self.pos0) * ease(u)
            + self.vel0 * T * (u - 6 * u**3 + 8 * u**4 - 3 * u**5)
        )
        v = (foot - self.prevfoot) / dt
        acc = (v - self.prevfv) / dt
        self.prevfv = v.copy()
        self.prevfoot = foot.copy()
        self.footlast = foot
        self.fv = v
        f = self.estimate
        lead = np.clip(f + setting("LEAD", 0.16) * self.fdot, -150, 150)
        w = np.clip(0.5 + setting("BIAS", 0.42) * f / 110, 0.04, 0.96)
        if self.air:
            landed = ease((self.age - 0.65 * T) / (0.45 * T))
            w = landed * w + (1 - landed) * (1 - self.swinging)
        weights = np.array([1 - w, w])
        cop = weights @ self.dest[:, :2]
        cop[1] -= 0.05
        goal = np.r_[cop - self.com[:2], self.rheight]
        goal[0] -= setting("LEVER", 1.35) * lead / (self.mass * self.omega**2)
        goal[2] -= setting("DROP", 0.11) * (abs(lead) / 115) ** 1.6
        goal[1] -= setting("YOFF", 0) * (abs(lead) / 100)
        rate = setting("RATE", 10)
        dd = rate**2 * (goal - self.rpos) - 2 * rate * self.rvel
        self.rvel += dt * dd
        self.rpos += dt * self.rvel
        self.rolldot += dt * (
            setting("TGAIN", 0.003) * f * 25
            - setting("DAMP", 4) * self.rolldot
            - 25 * self.roll
        )
        self.roll += dt * self.rolldot
        return self.rpos, self.rvel, dd, foot, v, acc, weights, f, self.roll
