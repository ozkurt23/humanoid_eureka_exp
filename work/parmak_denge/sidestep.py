import numpy as np
from scipy.ndimage import convolve1d
from blindbalance import Balance, ease, setting


class RecoverySteps(Balance):
    """Plan a lateral landing after the measured momentum residual exceeds the detection threshold."""

    def __init__(self, *args):
        super().__init__(*args)
        self.pulse = False
        self.config = {}

    def tuning(self, k, default):
        return self.config.get(k, setting(k, default))

    def plan(self, d, dt):
        feet = d.xpos[[self.model.body(s + "_ankle_roll").id for s in "LR"], 0]
        capture_x = d.subtree_com[1, 0] + d.qvel[0] / self.omega
        span = abs(feet[1] - feet[0])
        center = abs(capture_x - feet.mean()) < 0.20 * span
        # Near the center of the support span either leg can catch. Use a shorter
        # transfer and reserve sagittal ankle travel for absorbing the next landing.
        self.config = (
            dict(
                LEADLEN=0.285,
                TRAIL=0.174,
                FIRST=0.291,
                SQUAT=0.154,
                LAG=0.636,
                YGAPTIME=0.257,
                YJOIN=0.724,
                BACK=0.36,
                TORSO=2.18,
            )
            if center
            else {}
        )

        initial_feet = self.footlast.copy()
        self.orig = initial_feet.copy()
        initial_foot_velocity = self.fv.copy()
        sign = np.sign(self.val)
        air = np.max(initial_feet[:, 2] - self.base[:, 2]) > 0.004
        started_airborne = air
        side = (
            int(np.argmax(initial_feet[:, 2] - self.base[:, 2]))
            if air
            else int(
                d.qpos[0]
                + self.com[0]
                + d.qvel[0] / self.omega
                + sign * self.tuning("MARGIN", 0)
                < self.footlast[:, 0].mean()
            )
        )
        times_s = np.arange(0, 5, dt)
        n = len(times_s)
        feet_path = np.tile(initial_feet, (n, 1, 1))
        w = np.full((n, 2), 0.5)
        if air:
            w[:, side] = 0.0
            w[:, 1 - side] = 1.0
        step_start = 0.0
        target = initial_feet.copy()
        delta = self.tuning("DELTA", 0.17)
        step_duration = self.tuning("SIDE_T", 0.55)
        air = (
            air
            or abs(d.qpos[0] + d.qvel[0] / self.omega - self.footlast[:, 0].mean())
            > 0.075
        )
        if air:
            w[:, side] = 0.0
            w[:, 1 - side] = 1.0
        starts_downwind = side == int(sign > 0)
        if starts_downwind:
            delta = self.tuning("LEADLEN", 0.26)
        ne = int(self.tuning("ADDITIONAL", 0)) if starts_downwind else 0
        for j in range((2 + ne) if starts_downwind else 3):
            s = (side + j) % 2
            begin = step_start
            dur = self.tuning("PLANT", 0.25) if air and j == 0 else step_duration
            if j == 0:
                dur += self.tuning("YGAPTIME", 0.3) * abs(
                    initial_feet[0, 1] - initial_feet[1, 1]
                )
            u = np.clip((times_s - begin) / dur, 0, 1)
            lift = 0.0 if air and j == 0 else 0.24
            land = 0.8
            up = np.clip((u - lift) / (land - lift), 0, 1)
            coef = ease(up)
            old = target[s].copy()
            if starts_downwind and j >= 2:
                target[s, 0] += sign * self.tuning("MORE", 0.16)
            else:
                target[s, 0] = initial_feet[s, 0] + sign * (
                    self.tuning("FIRST", 0.36)
                    if j == 0 and s != int(sign > 0)
                    else (
                        self.tuning("TRAIL", 0.29)
                        if starts_downwind and j == 1
                        else delta
                    )
                )
            if j == 0:
                target[s, 1] += (
                    self.tuning("YJOIN", 0.85)
                    * (initial_feet[1 - s, 1] - initial_feet[s, 1])
                    + initial_foot_velocity[s, 1] * dur * 0.15
                )
            target[s, 2] = self.base[s, 2]
            feet_path[:, s] += coef[:, None] * (target[s] - old)
            feet_path[:, s, 2] += (
                (0 if started_airborne and j == 0 else self.tuning("UP", 0.025))
                * 64
                * (up * (1 - up)) ** 3
            )
            if j == 0 and air:
                l = ease((u - land) / (1 - land))
                w[:, s] = 0.5 * l
                w[:, 1 - s] = 1 - 0.5 * l
            else:
                liftw = ease(u / lift) * (1 - ease((u - land) / (1 - land)))
                w[:, s] -= 0.5 * liftw
                w[:, 1 - s] += 0.5 * liftw
            step_start += dur
        times = np.arange(-int(1.6 / dt), int(1.6 / dt) + 1) * dt
        ker = np.exp(-self.omega * abs(times))
        ker /= ker.sum()
        zmp = (feet_path[:, :, :2] * w[:, :, None]).sum(1)
        zmp[:, 1] -= 0.05
        root = np.tile(self.root0, (n, 1))
        root[:, :2] = convolve1d(zmp, ker, axis=0, mode="nearest") - self.com[:2]
        u = ease(times_s / 0.4)
        root[:, :2] = (1 - u[:, None]) * (
            d.qpos[:2] + times_s[:, None] * d.qvel[:2]
        ) + u[:, None] * root[:, :2]
        root[:, 2] = self.root0[2] - self.tuning("SQUAT", 0.15) * ease(times_s / 0.6)
        self.pelvis_position = root
        self.pelvis_velocity = np.gradient(root, dt, axis=0)
        self.pelvis_acceleration = np.gradient(self.pelvis_velocity, dt, axis=0)
        self.foot_position = feet_path
        self.foot_velocity = np.gradient(feet_path, dt, axis=0)
        self.foot_acceleration = np.gradient(self.foot_velocity, dt, axis=0)
        self.load = w
        self.age = 0
        self.quiet = 0
        self.travel = np.clip(
            target[:, 0].mean() - initial_feet[:, 0].mean(), -delta, delta
        )
        self.eventsign = sign
        self.hip_offset = 0.0
        self.hip_offset_velocity = 0.0
        self.height_offset = 0.0
        self.height_offset_velocity = 0.0
        self.pulse = True

    def update(self, t, m, d):
        if not self.pulse:
            if abs(self.val) < self.tuning("EARLY", 1):
                return super().update(t, m, d)
            self.plan(d, self.dt)
        dt = self.dt
        self.estimate += dt / (0.035 + dt) * (self.val - self.estimate)
        k = min(self.age, len(self.pelvis_position) - 1)
        self.age += 1
        p = self.pelvis_position[k].copy()
        v = self.pelvis_velocity[k].copy()
        a = self.pelvis_acceleration[k].copy()
        f = self.estimate
        w = self.load[k].copy()
        w += np.array([-1.0, 1.0]) * np.clip(f / 115, -1, 1) * 0.4 * 2 * min(w)
        # Pressure feedback moves the hip only as far as needed after the feet_path shifts.
        load = np.clip(abs(f) / self.tuning("WAKE", 45), 0, 1)
        aim = (
            -self.travel * self.tuning("LAG", 0.55) * ease((self.age * dt) / 0.9) * load
        )
        aim -= (
            self.tuning("VELFB", 0.35)
            * np.clip(
                d.qpos[0]
                - self.pelvis_position[k, 0]
                + 0.20 * (d.qvel[0] - self.pelvis_velocity[k, 0]),
                -0.20,
                0.20,
            )
            * load
        )
        rr = self.tuning("FRATE", 8)
        aa = rr**2 * (aim - self.hip_offset) - 2 * rr * self.hip_offset_velocity
        self.hip_offset_velocity += dt * aa
        self.hip_offset += dt * self.hip_offset_velocity
        p[0] += self.hip_offset
        v[0] += self.hip_offset_velocity
        a[0] += aa
        self.footlast = self.foot_position[k]
        self.fv = self.foot_velocity[k]
        release = (
            np.clip(1 - abs(f) / 30, 0, 1)
            * ease((self.age * dt - 1.7) / 0.3)
            * self.tuning("SQUAT", 0.15)
        )
        za = 64 * (release - self.height_offset) - 16 * self.height_offset_velocity
        self.height_offset_velocity += dt * za
        self.height_offset += dt * self.height_offset_velocity
        p[2] += self.height_offset
        v[2] += self.height_offset_velocity
        a[2] += za
        self.quiet = self.quiet + dt if abs(f) < 2 and self.age * dt > 1.2 else 0.0
        if self.quiet > 0.75:
            feet = d.xpos[[m.body(s + "_ankle_roll").id for s in "LR"]].copy()
            self.__init__(
                m,
                d,
                dt,
                feet,
                d.qpos[:3].copy(),
                d.subtree_com[1].copy() - d.qpos[:3],
                self.period,
                self.stride,
                self.clear,
            )
            return super().update(t, m, d)
        return (
            p,
            v,
            a,
            self.foot_position[k],
            self.foot_velocity[k],
            self.foot_acceleration[k],
            w,
            0.0,
            0.0,
        )
