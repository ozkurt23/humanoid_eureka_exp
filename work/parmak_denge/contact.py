import numpy as np


def pressure(m, d, jac, req, weights):
    rot = d.xmat[1].reshape(3, 3)
    f = req[:3]
    moment = rot @ req[3:6]
    z = d.qpos[2]
    cop = d.qpos[:2] + np.array([-z * f[0] - moment[1], moment[0] - z * f[1]]) / max(
        80, f[2]
    )
    pts = np.array(
        [d.geom_xpos[m.geom(s + "_Foot_sole_collider").id, :2] for s in "LR"]
    )
    line = pts[1] - pts[0]
    frac = np.clip((cop - pts[0]) @ line / (line @ line), 0.015, 0.985)
    # Transfer only through a physically loaded foot, with a smooth transition at lift-off.
    strength = np.clip(min(weights) * 6, 0, 1)
    return (1 - strength) * weights + strength * np.array([1 - frac, frac])


def feasible(m, d, ids, Jlist, iv, legs, M, req, weights):
    root = d.qpos[:3]
    rot = d.xmat[1].reshape(3, 3)
    pts = np.array(
        [d.geom_xpos[m.geom(s + "_Foot_sole_collider").id, :2] for s in "LR"]
    )
    line = pts[1] - pts[0]
    # Select the physically available region of the sole as the foot unloads.
    lo = np.clip((weights[1] - 0.80) / 0.20, 0, 1)
    hi = np.clip(weights[1] / 0.20, 0, 1)
    D = np.zeros((m.nv, 4))
    D[[0, 1, 3, 4]] = np.eye(4)
    for J, L in zip(Jlist, legs):
        cols = iv[L]
        A = J[:, cols]
        D[cols] = -A.T @ np.linalg.solve(A @ A.T + 0.00003 * np.eye(6), J @ D)
    delta = M @ D
    F = req[:3]
    tau = rot @ req[3:6]
    z = root[2] - 0.001
    fz = max(60, F[2])
    cop = root[:2] + np.array([-z * F[0] - tau[1], tau[0] - z * F[1]]) / fz
    frac = np.clip((cop - pts[0]) @ line / (line @ line), lo, hi)
    center = pts[0] + frac * line
    target = center + np.clip(cop - center, [-0.033, -0.061], [0.033, 0.069])
    if np.linalg.norm(target - cop) > 0.00005:
        md = rot @ delta[3:6]
        a = (
            np.stack([-z * delta[0] - md[1], md[0] - z * delta[1]])
            + (root[:2] - target)[:, None] * delta[2]
        )
        # Prefer yielding laterally before sacrificing trunk attitude.
        inv = np.array([1.0, 1.0, 0.8, 0.8])
        ai = a * inv
        corr = inv * (
            ai.T @ np.linalg.solve(ai @ ai.T + 0.002 * np.eye(2), (target - cop) * fz)
        )
        req = req + delta @ corr
    return req, np.array([1 - frac, frac])
