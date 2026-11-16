"""Feedback walking with a momentum observer and an interruptible swing trajectory."""

import os, numpy as np, mujoco as mj
from scipy.ndimage import convolve1d


def setting(k, default):
    return float(os.environ.get(k, default))


def ease(x):
    u = np.clip(x, 0, 1)
    return u**3 * (10 + u * (-15 + 6 * u))


class Balance:
    def __init__(self, m, d, dt, feet, root, comoff, period, stride, clear):
        self.model = m
        self.dt = dt
        self.period = setting("PERIOD", 0.82)
        self.stride = stride
        self.clear = clear
        self.gait = 0.0
        self.start = (
            setting("RESUME", 0.65) if getattr(self, "restarted", False) else 1.3
        )
        self.base = feet.copy()
        self.root0 = root.copy()
        self.com = comoff
        self.mass = m.body_mass.sum()
        self.omega = np.sqrt(9.81 / (root[2] + comoff[2]))
        self.M = np.zeros((m.nv, m.nv))
        self.val = 0.0
        self.estimate = 0.0
        self.fdot = 0.0
        self.active = False
        self.endphase = np.inf
        self.settle = 0.0
        self.speed = 1.0
        self.correction = np.zeros(3)
        self.drift = 0.0
        self.vdrift = 0.0
        self.shift = [0.0, 0.0]
        self.side0 = [0.0, 0.0]
        self.next = [0.0, 0.0]
        self.swing = -1
        self.roll = 0.0
        self.rolldot = 0.0
        self.px = 0.0
        self.vx = 0.0
        self.pz = 0.0
        self.vz = 0.0
        self.clock = 0
        self.acc = np.zeros(3)
        self.footlast = feet.copy()
        self.fv = np.zeros((2, 3))
        self.fa = self.fv.copy()
        self.rootlast = root.copy()
        self.rootv = np.zeros(3)
        self.aim = root.copy()
        self.foot = feet.copy()
        self.h = np.arange(-1.8, 1.801, 0.04)
        self.kernel = np.exp(-self.omega * np.abs(self.h))
        self.kernel /= self.kernel.sum()
        self.first = int(feet[1, 1] > feet[0, 1] + 0.02)
        if (
            getattr(self, "restarted", False)
            and setting("RESTFIRST", 1)
            and np.max(abs(self.pending)) > 0.03
        ):
            self.first = int(np.argmax(abs(self.pending)))
        if getattr(self, "close_stance_first", False):
            self.first = int(np.argmax(abs(self.pending)))
            self.start = 0.80
        self.times = np.arange(0, 80, dt)
        self.table = self.nominal(self.times)
        f, ld = self.table
        self.zmp = np.sum(f[:, :, :2] * ld[:, :, None], axis=1)
        self.zmp[:, 1] -= 0.050
        kt = np.arange(-int(2 / dt), int(2 / dt) + 1) * dt
        kernel = np.exp(-self.omega * np.abs(kt))
        kernel /= kernel.sum()
        self.nom = np.tile(root, (len(self.times), 1))
        self.nom[:, :2] = (
            convolve1d(self.zmp, kernel, axis=0, mode="nearest") - self.com[:2]
        )
        self.nom[:, :2] = root[:2] + (self.nom[:, :2] - root[:2]) * ease(
            self.times[:, None] / 0.7
        )
        phase = np.maximum(0, (self.times - self.start) / self.period)
        self.nom[:, 2] += 0.010 * np.sin(np.pi * phase) ** 2
        self.nomv = np.gradient(self.nom, dt, axis=0)
        self.noma = np.gradient(self.nomv, dt, axis=0)
        self.rootlast = np.zeros(3)
        self.rootv = np.zeros(3)
        self.aim = np.zeros(3)

    def nominal(self, g):
        g = np.asarray(g)
        phase = (g - self.start) / self.period
        step = np.floor(phase).astype(int)
        a = phase - step
        idx = np.maximum(step, 0)
        up = setting("LIFT", 0.12)
        down = setting("LAND", 0.78)
        u = np.clip((a - up) / (down - up), 0, 1)
        est = ease(u)
        weight = ease((a - (up - 0.12)) / 0.13) * (1 - ease((a - (down - 0.01)) / 0.14))
        f = np.broadcast_to(self.base, (len(g), 2, 3)).copy()
        ld = np.full((len(g), 2), 0.5)
        for s in [0, 1]:
            order = (s - self.first) % 2
            count = np.maximum(0, (idx + 1 - order) // 2)
            first_len = (
                1 + (self.base[s, 1] - self.base[1 - s, 1]) / self.stride
                if order == 0
                else 2
            )
            prev = np.where(count > 0, 2 * (count - 1) + first_len, 0)
            mine = (idx % 2 == order) & (step >= 0)
            f[:, s, 1] -= self.stride * (
                prev + mine * (1 if False else np.where(idx == 0, first_len, 2)) * est
            )
            if os.environ.get("SQUARE"):
                f[:, s, 1] = self.base[s, 1] - 2 * self.stride * (count + mine * est)
            f[:, s, 2] += self.clear * mine * 64 * (u * (1 - u)) ** 3
            ld[:, s] += np.where(mine, -0.5, 0.5) * weight * (step >= 0)
        return f, ld

    def observe(self, m, d):
        # Floating-base linear momentum residual. Only the latest accelerations,
        # inertial terms and realized constraint reactions enter this estimate.
        mj.mj_fullM(m, self.M, d.qM)
        self.val = float(
            self.M[0] @ d.qacc
            + d.qfrc_bias[0]
            - d.qfrc_passive[0]
            - d.qfrc_constraint[0]
        )

    def update(self, t, m, d):
        dt = self.dt
        old = self.estimate
        self.estimate += (self.val - old) * dt / (setting("OBS", 0.035) + dt)
        self.fdot += dt / (0.045 + dt) * ((self.estimate - old) / dt - self.fdot)
        phase = (self.gait - self.start) / self.period
        idx = int(np.floor(phase))
        a = phase - idx
        if abs(self.estimate) > setting("DETECT", 7) and not self.active:
            self.active = True
            self.settle = 0.0
            # Stop at a reachable two-foot support pose after the current swing.
            self.endphase = (
                self.gait
                if idx < 0 or a < setting("LIFT", 0.12) or a > 0.91
                else self.start + (idx + 0.97) * self.period
            )
        if self.active:
            self.settle = self.settle + dt if abs(self.estimate) < 3 else 0.0
            if self.settle > setting("REST", 0.65):
                self.__init__(
                    m,
                    d,
                    dt,
                    self.footlast.copy(),
                    d.qpos[:3].copy(),
                    self.com.copy(),
                    self.period,
                    self.stride,
                    self.clear,
                )
                return self.update(t, m, d)
        self.gait = min(self.gait + dt, self.endphase)
        phase = (self.gait - self.start) / self.period
        idx = int(np.floor(phase))
        a = phase - idx
        # Correct the swing landing from the currently measured sideways motion.
        if idx >= 0 and idx != self.swing:
            self.swing = idx
            s = (idx + self.first) % 2
            self.side0[s] = self.shift[s]
            self.next[s] = self.drift
        if idx >= 0:
            s = (idx + self.first) % 2
            if self.active and a < 0.58:
                self.next[s] = np.clip(
                    setting("STEP", 0.28) * d.qvel[0]
                    + setting("FSTEP", 0.0012) * self.estimate,
                    -0.15,
                    0.15,
                )
            self.shift[s] = self.side0[s] + (self.next[s] - self.side0[s]) * ease(
                (a - 0.10) / 0.70
            )
        kk = min(len(self.times) - 1, round(self.gait / dt))
        foot = self.table[0][kk].copy()
        weight = self.table[1][kk].copy()
        foot[:, 0] += self.shift
        stance = 2 * min(weight)
        bias = np.clip(self.estimate / 110, -1, 1) * setting("BIAS", 0.42) * stance
        weight += [-bias, bias]
        if self.clock % 5 == 0:
            future = np.clip(self.gait + self.h, 0, self.endphase)
            indices = np.clip(np.rint(future / dt).astype(int), 0, len(self.times) - 1)
            fg = self.table[0][indices]
            ld = self.table[1][indices]
            z = self.zmp[indices].copy()
            z[:, 0] += (ld * np.asarray(self.shift)).sum(1)
            z += bias * (fg[:, 1, :2] - fg[:, 0, :2])
            neutral_indices = np.clip(
                np.rint(np.maximum(0, self.gait + self.h) / dt).astype(int),
                0,
                len(self.times) - 1,
            )
            aim = np.zeros(3)
            aim[:2] = self.kernel @ (z - self.zmp[neutral_indices])

            f = np.clip(self.estimate + setting("LEAD", 0.16) * self.fdot, -150, 150)
            aim[0] -= setting("LEVER", 1.43) * f / (self.mass * self.omega**2)
            aim[2] -= setting("DROP", 0.115) * (abs(f) / 115) ** 1.6

            rel = d.subtree_com[1] - d.qpos[:3] - self.com
            aim[:2] -= setting("COMGAIN", 0) * rel[:2] * min(1, abs(f) / 40)
            aim[1] -= setting("YOFF", 0) * (abs(f) / 100)
            self.aim = aim
        self.clock += 1
        # Critically damped task-space references prevent position jumps on detection.
        rate = setting("RATE", 12)
        acc = rate**2 * (self.aim - self.rootlast) - 2 * rate * self.rootv
        self.rootv += dt * acc
        self.rootlast += dt * self.rootv
        # Independent trunk compliance to a sensed lateral load, with spring return.
        self.rolldot += dt * (
            setting("TGAIN", 0.0013) * self.estimate * 5**2
            - setting("DAMP", 7) * self.rolldot
            - 25 * self.roll
        )
        self.roll += dt * self.rolldot
        v = (foot - self.footlast) / dt
        fa = (v - self.fv) / dt
        self.footlast = foot.copy()
        self.fv = v.copy()
        moving = float(self.gait < self.endphase - 1e-7)
        return (
            self.nom[kk] + self.rootlast,
            self.nomv[kk] * moving + self.rootv,
            self.noma[kk] * moving + acc,
            foot,
            v,
            fa,
            weight,
            self.estimate * setting("FF", 1),
            self.roll,
        )
