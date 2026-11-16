from blindbalance import Balance, setting, ease
import numpy as np
import mujoco as mj


class Catch(Balance):
    def __init__(self, *args):
        if not hasattr(self, "pending"):
            self.pending = np.zeros(2)
            self.restwidth = args[3][1, 0] - args[3][0, 0]
        super().__init__(*args)
        self.holding = False

    def nominal(self, g):
        f, w = super().nominal(g)
        phase = (np.asarray(g) - self.start) / self.period
        for ss in range(2):
            order = (ss - self.first) % 2
            f[:, ss, 0] += self.pending[ss] * ease(
                (phase - order - setting("LIFT", 0.25))
                / (setting("LAND", 0.69) - setting("LIFT", 0.25))
            )
        if getattr(self, "close_stance_first", False):
            # The narrowing foot is already forward: use its first swing for
            # lateral recovery and resume forward travel with the other foot.
            f[:, self.first, 1] += (
                2
                * self.stride
                * ease(
                    (phase - setting("LIFT", 0.25))
                    / (setting("LAND", 0.69) - setting("LIFT", 0.25))
                )
            )
        return f, w

    def update(self, t, m, d):
        dt = self.dt
        if not self.holding and abs(self.val) < setting("EARLY", 2):
            return super().update(t, m, d)
        if not self.holding:
            self.pressure_offset = 0.0
            self.perror = 0.0
            self.holding = True
            self.t0 = t
            self.quiet = 0
            self.sign = np.sign(self.val)
            self.s = int(self.sign > 0)
            self.o = 1 - self.s
            self.initfoot = self.footlast.copy()
            self.initvel = self.fv.copy()
            self.both = self.initfoot.copy()
            self.both[:, 1] += self.initvel[:, 1] * 0.045
            self.both[:, 2] = self.base[:, 2]
            self.rpc = d.qpos[:3].copy()
            self.vpc = d.qvel[:3].copy()
            self.ow = self.table[1][round(self.gait / dt)].copy()
            self.air = (
                int(np.argmax(self.initfoot[:, 2] - self.base[:, 2]))
                if np.max(self.initfoot[:, 2] - self.base[:, 2]) > 0.011
                else None
            )
            self.plant = setting("PLANTOS", 0.17)
            self.begin = self.plant + setting("PRE", 0.18)
            self.end = self.begin + setting("SW", 0.28)
            self.offset = setting("WIDTH", 0.22)
            self.after = self.end + 0.18
            self.grid = np.arange(-2, 8, dt)
            # Choose the first supporting leg and transfer time from measured capture point.
            cp = self.rpc[:2] + self.com[:2] + self.vpc[:2] / self.omega
            # A rising lateral force shifts the future capture point during transfer.
            # Project the measured slope over a bounded horizon to choose the catch foot.
            cp[0] += (
                np.clip(self.val + setting("CAPTIME", 0) * self.fdot, -90, 90)
                * setting("CAPGAIN", 0)
                / (self.mass * self.omega**2)
            )
            best = None
            tg = np.arange(0, 2.8, 0.015)
            ww = np.exp(-self.omega * tg)
            ww /= ww.sum()
            requested = self.offset
            room = self.initfoot[1, 0] - self.initfoot[0, 0] - setting("MINGAP", 0.17)
            signed_fraction = (cp[0] - self.initfoot[int(self.sign < 0), 0]) / (
                self.initfoot[int(self.sign > 0), 0]
                - self.initfoot[int(self.sign < 0), 0]
            )
            high_outward = self.sign * self.vpc[0] > setting("FASTVELOCITY", 100)
            self.fast = bool(
                setting("FASTOUT", 0)
                and self.air is None
                and 0.25 < signed_fraction
                and (signed_fraction < setting("FRACTION", 0.79) or high_outward)
            )
            for forward in (int(self.sign > 0), int(self.sign < 0)):
                if (
                    setting("CHOOSEFOOT", -1) >= 0
                    and self.air is None
                    and forward != int(self.sign > 0) ^ int(setting("CHOOSEFOOT", -1))
                ):
                    continue
                if self.fast and forward != int(self.sign > 0):
                    continue
                if self.air is not None and forward != self.air:
                    continue
                self.offset = (
                    requested
                    if forward == int(self.sign > 0)
                    else np.clip(room, 0, requested)
                )
                if (
                    forward != int(self.sign > 0)
                    and self.offset < 0.065
                    and self.air is None
                    and setting("CHOOSEFOOT", -1) < 0
                ):
                    continue
                for prep in (0.03, 0.13, 0.25, 0.43, 0.68, 0.88):
                    if prep > setting("MAXPRE", 0.32):
                        continue
                    self.s = forward
                    self.o = 1 - forward
                    self.begin = self.plant + prep
                    self.end = self.begin + setting("SW", 0.28)
                    self.after = self.end + setting("GAP", 0.26)
                    if self.fast:
                        self.begin = setting("STARTFAST", 0.055)
                        self.end = self.begin + setting("FASTOUT", 0.17)
                        self.offset = setting("FASTLEN", 0.23)
                        if high_outward:
                            self.begin = setting("VSTART", 0.025)
                            self.end = self.begin + setting("VDUR", 0.13)
                            self.offset = setting("VLEN", 0.26)
                    if self.air is not None:
                        self.begin = 0
                        self.end = setting("SW", 0.28)
                        self.after = self.end + setting("GAP", 0.85)
                    if setting("N2", 0) == 0 or (
                        setting("MEDONLY", 1) and self.s == int(self.sign > 0)
                    ):
                        self.after = 100
                    if setting("STARTAT", -1) >= 0 and self.air is None:
                        self.begin = setting("STARTAT", 0.16)
                        self.end = self.begin + setting("SW", 0.28)
                    ft, ws = self.plan(tg)
                    zz = (ft[:, :, :2] * ws[:, :, None]).sum(axis=1)
                    zz[:, 1] -= 0.05
                    err = cp - ww @ zz
                    score = np.linalg.norm(err / np.array([0.044, 0.065])) + 0.06 * prep
                    if (
                        setting("AIRFIRST", 1)
                        and self.initfoot[self.s, 2] - self.base[self.s, 2] > 0.012
                    ):
                        score -= 0.9
                    if best is None or score < best[0]:
                        best = (
                            score,
                            self.s,
                            self.begin,
                            self.end,
                            self.after,
                            err,
                            self.offset,
                        )
            _, self.s, self.begin, self.end, self.after, err, self.offset = best
            self.o = 1 - self.s
            pass
            self.cpbias = np.clip(err * 1.50, [-0.055, -0.075], [0.055, 0.075])
            self.tabf, self.tabw = self.plan(self.grid)
            z = (self.tabf[:, :, :2] * self.tabw[:, :, None]).sum(1)
            z[:, 1] -= 0.05
            z += self.cpbias * np.exp(-np.maximum(0, self.grid) / 0.7)[:, None]
            from scipy.ndimage import convolve1d

            kt = np.arange(-int(1.8 / dt), int(1.8 / dt) + 1) * dt
            mask = np.exp(-self.omega * abs(kt))
            mask /= mask.sum()
            self.baseref = convolve1d(z, mask, axis=0, mode="nearest") - self.com[:2]
            self.basevel = np.gradient(self.baseref, dt, axis=0)
            self.baseacc = np.gradient(self.basevel, dt, axis=0)
            self.neutral = self.rpc[:2] - self.baseref[round(2 / dt)]
            self.velerr = self.vpc[:2] - self.basevel[round(2 / dt)]
            self.extra = np.zeros(3)
            self.exv = np.zeros(3)
        age = t - self.t0
        k = min(len(self.grid) - 1, round((2 + age) / dt))
        trigger = setting("LOADSTEP", 999)
        if (
            self.after > 99
            and self.s != int(self.sign > 0)
            and age > self.end + 0.06
            and abs(self.estimate) > trigger
        ):
            self.after = age + setting("TRANSFER", 0.65)
            nf, nw = self.plan(self.grid)
            xy = (
                nf[:, :, :2] * nw[:, :, None]
                - self.tabf[:, :, :2] * self.tabw[:, :, None]
            ).sum(axis=1)
            from scipy.ndimage import convolve1d

            grid = np.arange(-int(1.8 / dt), int(1.8 / dt) + 1) * dt
            kg = np.exp(-self.omega * abs(grid))
            kg /= kg.sum()
            dr = convolve1d(xy, kg, axis=0, mode="nearest")
            # Start from the currently realized reference before transferring load to the newly placed foot.
            dr *= ease((self.grid - age) / setting("REPLAN", 0.4))[:, None]
            self.tabf, self.tabw = nf, nw
            self.baseref += dr
            self.basevel += np.gradient(dr, dt, axis=0)
            self.baseacc += np.gradient(np.gradient(dr, dt, axis=0), dt, axis=0)
        f = self.tabf[k]
        w = self.tabw[k].copy()
        old = self.estimate
        self.estimate += (self.val - old) * dt / (0.035 + dt)
        self.fdot += dt / (0.04 + dt) * ((self.estimate - old) / dt - self.fdot)
        force = self.estimate
        self.quiet = self.quiet + dt if abs(force) < 2 else 0
        if self.quiet > 0.7 and age > 1:
            self.restarted = True
            self.pending = np.zeros(2)
            self.pending[self.o] = np.clip(
                f[self.s, 0]
                + (self.restwidth if self.o else -self.restwidth)
                - f[self.o, 0],
                -0.26,
                0.26,
            ) * setting("RESTORE", 1)
            actual = d.xpos[[m.body(side + "_ankle_roll").id for side in "LR"]].copy()
            initial = int(actual[1, 1] > actual[0, 1] + 0.02)
            self.close_stance_first = (
                abs(actual[1, 0] - actual[0, 0]) > 1.50 * self.restwidth
                and abs(actual[1, 1] - actual[0, 1]) > 0.055
                and np.argmax(abs(self.pending)) != initial
            )
            if self.close_stance_first:
                f = actual.copy()
                self.pending[self.o] = np.clip(
                    f[self.s, 0]
                    + (self.restwidth if self.o else -self.restwidth)
                    - f[self.o, 0],
                    -0.34,
                    0.34,
                )
            self.__init__(
                m,
                d,
                dt,
                f.copy(),
                d.qpos[:3].copy(),
                self.com.copy(),
                self.period,
                self.stride,
                self.clear,
            )
            return super().update(t, m, d)
        # Once both feet have landed, select the center of pressure according to measured load.
        endfac = ease((age - self.end) / 0.17)
        maxw = setting("LOAD", 0.92)
        target = np.clip(0.5 + force / 100 * 0.47, 0.04, 0.96)
        b = endfac * (target - (maxw if self.sign > 0 else 1 - maxw))
        # Keep support on the outside leg while the other leg is taking its follow step.
        during = ease((age - self.after + 0.08) / 0.10) * (
            1 - ease((age - self.after - 0.32) / 0.1)
        )
        if self.after < 99:
            b *= ease((age - self.after - 0.32) / 0.15)
        w += np.array([-b, b]) * (1 - during)
        pos = self.baseref[k].copy()
        # b decays with the actual measured release, so the target returns to the new stance center.
        corr = np.r_[
            (f[1, :2] - f[0, :2]) * b * (1 - during),
            -setting("DROP", 0.09) * (abs(force) / 115) ** 1.5,
        ]
        shift = (
            setting("ALPHA", 1.0)
            * (force + setting("FL", 0.09) * self.fdot)
            / (self.mass * self.omega**2)
        )
        buffer = setting("BUFFER", 0)
        if buffer:
            edge = int(shift > 0)
            sg = np.sign(shift)
            available = np.clip(w[edge] * 4, 0, 1) * max(
                0, sg * (f[edge, 0] - w @ f[:, 0]) + 0.024
            )
            shift = sg * max(0, abs(shift) - buffer * available)
        if setting("PRESSI", 0):
            total = 0.0
            moment = 0.0
            reaction = np.zeros(6)
            for j, con in enumerate(d.contact):
                if 0 not in (con.geom1, con.geom2):
                    continue
                mj.mj_contactForce(m, d, j, reaction)
                fz = abs((con.frame.reshape(3, 3).T @ reaction[:3])[2])
                total += fz
                moment += fz * con.pos[0]
            if total > 30:
                err = moment / total - w @ f[:, 0]
                self.perror += dt / (dt + 0.035) * (err - self.perror)
                cross = np.sign(self.perror) * max(
                    0, abs(self.perror) - setting("DEAD", 0.008)
                )
                self.pressure_offset = np.clip(
                    self.pressure_offset - dt * setting("PRESSI", 5) * cross,
                    -0.50,
                    0.50,
                )
            corr[0] += self.pressure_offset
        else:
            corr[0] -= shift
        rate = setting("CRATE", 18)
        acc = rate**2 * (corr - self.extra) - 2 * rate * self.exv
        self.exv += dt * acc
        self.extra += dt * self.exv
        # Match reference position and velocity at takeover without teleporting the center of mass.
        dur = setting("MATCH", 0.45)
        u = np.clip(age / dur, 0, 1)
        adj = self.neutral * (1 - ease(u)) + self.velerr * dur * (
            u - 6 * u**3 + 8 * u**4 - 3 * u**5
        )
        dv = (
            (
                -self.neutral * (30 * u**2 * (1 - u) ** 2) / dur
                + self.velerr * (1 - 18 * u**2 + 32 * u**3 - 15 * u**4)
            )
            if u < 1
            else 0
        )
        da = (
            (
                -self.neutral * (60 * u * (1 - u) * (1 - 2 * u)) / dur**2
                + self.velerr * (-36 * u + 96 * u**2 - 60 * u**3) / dur
            )
            if u < 1
            else 0
        )
        p = np.r_[pos + adj, self.root0[2]] + self.extra
        v = np.r_[self.basevel[k] + dv, 0] + self.exv
        a = np.r_[self.baseacc[k] + da, 0] + acc
        fv = (f - self.footlast) / dt
        fa = (fv - self.fv) / dt
        self.fv = fv
        self.footlast = f.copy()
        return p, v, a, f, fv, fa, w, force * setting("FFR", 0.85), 0.0

    def plan(self, t):
        s, o = self.s, self.o
        both = self.both
        fv = self.initvel
        T = self.plant
        u = np.clip(t / T, 0, 1)
        e = ease(u)
        f = (
            self.initfoot
            + (both - self.initfoot) * e[:, None, None]
            + fv * T * (u - 6 * u**3 + 8 * u**4 - 3 * u**5)[:, None, None]
        )
        v = np.clip((t - self.begin) / (self.end - self.begin), 0, 1)
        a = ease(v)
        f[:, s, 0] += self.sign * self.offset * a
        f[:, s, 2] += setting("H", 0.025) * 64 * (v * (1 - v)) ** 3
        v2 = np.clip((t - self.after) / 0.32, 0, 1)
        a2 = ease(v2)
        f[:, o, 0] += self.sign * self.offset * setting("FOLLOW", 0.8) * a2
        f[:, o, 2] += 0.025 * 64 * (v2 * (1 - v2)) ** 3
        ww = self.ow[s] + (0.02 - self.ow[s]) * ease((t + 0.02) / max(0.04, self.begin))
        end_weight = (
            setting("LOAD", 0.92)
            if s == int(self.sign > 0)
            else 1 - setting("LOAD", 0.92)
        )
        ww += (end_weight - 0.02) * ease((t - self.end + 0.025) / 0.14)
        ww += (
            (0.99 - end_weight)
            * ease((t - self.after + setting("SHIFT", 0.35)) / setting("SHIFT", 0.35))
            * (1 - ease((t - self.after - 0.32) / 0.14))
        )
        if self.air is not None:
            T = self.end
            u = np.clip(t / T, 0, 1)
            land = both[s].copy()
            land[0] += self.sign * self.offset
            land[1] = self.initfoot[s, 1] + fv[s, 1] * T * 0.45
            f[:, s] = (
                self.initfoot[s]
                + (land - self.initfoot[s]) * ease(u)[:, None]
                + fv[s] * T * (u - 6 * u**3 + 8 * u**4 - 3 * u**5)[:, None]
            )
            ww = 0.02 + (end_weight - 0.02) * ease((t - self.end + 0.012) / 0.16)
            ww += (
                (0.99 - end_weight)
                * ease(
                    (t - self.after + setting("SHIFT", 0.35)) / setting("SHIFT", 0.35)
                )
                * (1 - ease((t - self.after - 0.32) / 0.14))
            )
        w = np.zeros((len(t), 2))
        w[:, s] = ww
        w[:, o] = 1 - ww
        return f, w
