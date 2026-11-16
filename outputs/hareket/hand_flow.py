"""Fit a continuous multi-angle tendon command against physical pen tracking."""

from v3_model import H, HERE, OLD, Hand, mj, np
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json, sys


def ease(u):
    return u**3 * (10 - 15 * u + 6 * u * u)


@lru_cache(maxsize=16)
def initial(seed):
    h = Hand()
    h.m = mj.MjModel.from_binary_path(str(HERE / "hand_repaired.mjb"))
    h.d = mj.MjData(h.m)
    h.pen = h.m.body("pen").id
    h.barrel = h.m.geom("barrel").id
    h.reset(seed)
    cfg = np.load(OLD / "runs/hand_warm.npy")[0]
    start = h.d.qpos[11:14].copy()
    f = 0.0
    track = []
    held = 0
    for k in range(240):
        a = h.d.xmat[h.pen].reshape(3, 3)[:, 0]
        f += np.clip(-cfg[1] * np.arctan2(a[2], a[0]) - f, -0.018, 0.018)
        h.d.ctrl[:] = 0.006 * np.clip(h.pose(f) + cfg[2:], h.lo, h.hi)
        for j in range(10):
            if k < 15:
                h.d.qpos[11:14] = start
                h.d.qpos[14:] = [1, 0, 0, 0]
                h.d.qvel[11:] = 0
            mj.mj_step(h.m, h.d)
            track.append(h.d.qpos.copy())
        if k >= 15:
            ns = {
                h.m.geom(c.geom1 + c.geom2 - h.barrel).name.split("_")[0]
                for c in h.d.contact
                if h.barrel in (c.geom1, c.geom2)
                and "silicone_pad" in h.m.geom(c.geom1 + c.geom2 - h.barrel).name
            }
            ax = h.d.xmat[h.pen].reshape(3, 3)[:, 0]
            held = (
                held + 1
                if "Thumb" in ns and len(ns) > 1 and ax[0] > np.cos(np.deg2rad(5))
                else 0
            )
            if held == 150:
                break
    h.grasp_ok = held == 150
    spec = mj.mjtState.mjSTATE_INTEGRATION
    st = np.empty(mj.mj_stateSize(h.m, spec))
    mj.mj_getState(h.m, h.d, st, spec)
    return h, st, h.d.ctrl.copy() / 0.006, np.array(track)


def motion(arg, grasp=None, tolerance=4, save_name="hand.npz"):

    coeff, seed, seq, record, *gains = arg
    h, st, neutral, prefix = initial(seed) if grasp is None else grasp
    mj.mj_setState(h.m, h.d, st, mj.mjtState.mjSTATE_INTEGRATION)
    mj.mj_forward(h.m, h.d)
    data = []
    prev = 0
    score = 0.0
    hits = []
    qs = []
    co = np.reshape(coeff, (2, 11))
    contacts_ok = True
    integral = 0.0
    effective = 0.0
    kp, ki = gains[0] if gains else (0.0, 0.0)
    for dest in seq:
        phase = []
        hold = []
        errhist = []
        for k in range(45):
            u = ease(min((k + 1) / 30, 1))
            t = prev + (dest - prev) * u
            axis = h.d.xmat[h.pen].reshape(3, 3)[:, 0]
            pitch = np.rad2deg(np.arctan2(axis[2], axis[0]))
            err = t - pitch
            integral = np.clip(integral + ki * 0.04 * err, -12, 12)
            effective += np.clip(
                np.clip(t + kp * err + integral, -24, 24) - effective, -2, 2
            )
            cmd = neutral + abs(effective) / 15 * co[int(effective > 0)]
            h.d.ctrl[:] = 0.006 * np.clip(cmd, h.lo, h.hi)
            if record:
                for _ in range(20):
                    mj.mj_step(h.m, h.d)
                    qs.append(h.d.qpos.copy())
            else:
                mj.mj_step(h.m, h.d, nstep=20)
            axis = h.d.xmat[h.pen].reshape(3, 3)[:, 0]
            ang = np.deg2rad(t)
            error = np.rad2deg(
                np.arccos(np.clip(axis @ [np.cos(ang), 0, np.sin(ang)], -1, 1))
            )
            pos = np.linalg.norm(h.d.xpos[h.pen] - h.center)
            names = set()
            for c in h.d.contact:
                if h.barrel in (c.geom1, c.geom2):
                    name = h.m.geom(c.geom1 + c.geom2 - h.barrel).name
                    if "silicone_pad" in name:
                        names.add(name.split("_")[0])
            pair = "Thumb" in names and len(names) > 1
            contacts_ok = contacts_ok and pair
            val = np.exp(-error / 7) * np.exp(-pos * 35) * (0.65 + 0.35 * pair)
            phase.append(val)
            errhist.append(error)
            if k >= 30:
                hold.append(error <= tolerance and pair)
            if record:
                data.append(
                    [
                        h.d.time,
                        t,
                        np.rad2deg(np.arctan2(axis[2], axis[0])),
                        error,
                        pair,
                        pos,
                    ]
                )
            if h.d.xpos[h.pen, 2] < 0.025:
                break
        score += (sum(phase) + sum(phase[30:])) / 60
        hits.append(len(hold) == 15 and all(hold))
        if len(phase) < 45:
            break
        prev = dest
    if record:
        q = np.concatenate([prefix, np.array(qs)])
        times = np.arange(0, len(q) * 0.002, 1 / 60)
        idx = np.minimum((times / 0.002).round().astype(int), len(q) - 1)
        poses = []
        scratch = mj.MjData(h.m)
        for row in q[idx]:
            scratch.qpos[:] = row
            mj.mj_kinematics(h.m, scratch)
            poses.append(np.c_[scratch.xpos, scratch.xquat].copy())
        np.savez(
            H / save_name,
            poses=poses,
            qs=q[idx],
            names=[h.m.body(i).name or "world" for i in range(h.m.nbody)],
            radius=h.m.geom_size[h.barrel, 0],
            metrics=data,
        )
    return score / len(seq), sum(hits), hits


def train():
    h, _, _, _ = initial(129044)
    delta = np.array([h.pose(np.deg2rad(a)) - h.pose(0) for a in [-15, 15]]).ravel()
    rng = np.random.default_rng(705)
    mean = delta * 0.45
    std = np.full(22, 0.075)
    champ = mean
    best = -1
    seq = [-12, 12, 0, -8, 8, 0]
    with ProcessPoolExecutor(14) as pool:
        for gen in range(42):
            if gen == 17:
                std = np.maximum(std, 0.035)
            pop = np.clip(mean + rng.normal(size=(45, 22)) * std, -0.55, 0.55)
            pop[0] = champ
            seeds = [129044, 151000 + gen % 4]
            jobs = [(p, s, seq, False) for p in pop for s in seeds]
            r = list(pool.map(motion, jobs, chunksize=2))
            scores = (
                np.array([v[0] + 0.025 * v[1] for v in r]).reshape(len(pop), -1).mean(1)
            )
            elite = pop[np.argsort(scores)[-8:]]
            mean = 0.2 * mean + 0.8 * elite.mean(0)
            std = np.maximum(0.008, 0.2 * std + 0.8 * elite.std(0))
            z = elite[-1]
            valid = list(
                pool.map(motion, [(z, s, seq, False) for s in range(152000, 152006)])
            )
            val = np.mean([v[0] + 0.025 * v[1] for v in valid])
            if val > best:
                best = val
                champ = z.copy()
                np.save(H / "hand_flow.npy", champ)
            print(
                gen,
                round(scores.max(), 3),
                round(best, 3),
                [v[1] for v in valid],
                flush=True,
            )


if __name__ == "__main__":
    train()
