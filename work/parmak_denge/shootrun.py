"""Centroidal walking reference and articulated inverse-dynamics tracking."""

from pathlib import Path
import sys, json
import numpy as np
import mujoco as mj
from scipy.spatial.transform import Rotation
from scipy.ndimage import convolve1d

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "duet"))
from grip import *

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tips"))
from tipctrl import Tip
from world import loads
from blindbalance import Balance

if os.environ.get("PLANTFIRST"):
    from plant import Reflex
else:
    from catch import Catch as Reflex
from contact import pressure, feasible
from powergrip import PowerGrip

H = W


def quint(x):
    x = np.clip(x, 0, 1)
    return x**3 * (10 - 15 * x + 6 * x * x)


def simulate(
    seed=1,
    record=False,
    push=0,
    period=0.64,
    stride=0.23,
    clear=0.065,
    linearize=False,
    side_step=None,
    offset=0.0,
    template=None,
):
    clear = float(os.environ.get("CLEAR", clear))
    stride = float(os.environ.get("STRIDE", stride))
    m = mj.MjModel.from_xml_path(str(W / os.environ.get("MODEL", "duet.xml")))
    d = mj.MjData(m)
    dt = m.opt.timestep
    bodyact = np.flatnonzero(m.actuator_trntype == 0)
    j = m.actuator_trnid[bodyact, 0]
    ix = m.jnt_qposadr[j]
    iv = m.jnt_dofadr[j]
    names = [m.joint(int(i)).name for i in j]
    ids = [m.body(k + "_ankle_roll").id for k in ["L", "R"]]

    def act(n):
        return names.index(n)

    legs = [
        [act("body_" + str(b + i)) for i in range(5)]
        + [act(s + "_ankle_pitch"), act(s + "_ankle_roll")]
        for s, b in [("L", 10), ("R", 15)]
    ]
    home = np.zeros(len(j))
    for L in legs:
        bend = float(os.environ.get("BEND", 0.40))
        home[L] = [-bend, 0, 0, 2 * bend, 0, bend + np.deg2rad(5), 0]
    for n, q in json.loads((W / "arm.json").read_text()).items():
        home[act(n)] = q
    d.qpos[ix] = home
    mj.mj_forward(m, d)
    widen = float(os.environ.get("WIDEN", 0))
    if widen:
        goals = d.xpos[ids].copy()
        goals[:, 0] += [-widen, widen]
        upright = Rotation.from_matrix(d.xmat[ids].reshape(2, 3, 3))
        for repeat in range(25):
            for side, leg in enumerate(legs):
                cols = iv[leg]
                jp = np.zeros((3, m.nv))
                jr = jp.copy()
                mj.mj_jacBody(m, d, jp, jr, ids[side])
                jac = np.vstack([jp[:, cols], jr[:, cols]])
                error = np.r_[
                    goals[side] - d.xpos[ids[side]],
                    (
                        upright[side]
                        * Rotation.from_matrix(d.xmat[ids[side]].reshape(3, 3)).inv()
                    ).as_rotvec(),
                ]
                d.qpos[ix[leg]] += jac.T @ np.linalg.solve(
                    jac @ jac.T + 0.0001 * np.eye(6), error
                )
                mj.mj_forward(m, d)
        home = d.qpos[ix].copy()
    feet0 = d.xpos[ids].copy()
    rot0 = d.xmat[ids].reshape(2, 3, 3).copy()
    low = min(
        d.geom_xpos[g, 2] - np.abs(d.geom_xmat[g].reshape(3, 3)[2]) @ m.geom_size[g]
        for g in range(m.ngeom)
        if "Foot_" in m.geom(g).name and "collider" in m.geom(g).name
    )
    d.qpos[2] -= low + 0.00025
    mj.mj_forward(m, d)
    for s in "LR":
        mount = m.body(s + "v_mount").id
        r = Rotation.from_quat(np.roll(m.body_quat[mount], -1)) * Rotation.from_rotvec(
            [np.deg2rad(float(os.environ.get("TILT", 40))), 0, 0]
        )
        m.body_quat[mount] = np.roll(r.as_quat(), 1)
    mj.mj_forward(m, d)
    for side in "LR":
        mid = m.body(side + "v_mount").id
        basis = Rotation.from_matrix(d.xmat[mid].reshape(3, 3))
        x = basis.as_matrix()[:, 0].copy()
        elevation = np.arcsin(x[2])
        desired = np.deg2rad(float(os.environ.get("LEVEL", 0))) * (
            1 if side == "L" else -1
        )
        horizontal = x.copy()
        horizontal[2] = 0
        horizontal /= np.linalg.norm(horizontal)
        trans = Rotation.from_rotvec(
            np.cross(horizontal, [0, 0, 1]) * (desired - elevation)
        )
        delta = basis.inv() * trans * basis
        m.body_quat[mid] = np.roll(
            (Rotation.from_quat(np.roll(m.body_quat[mid], -1)) * delta).as_quat(), 1
        )
    mj.mj_forward(m, d)
    grip = Tip(m, d)
    fingers = grip.measure()
    feet0 = d.xpos[ids].copy()
    root0 = d.qpos[:3].copy()
    comoff = d.subtree_com[1] - root0
    # Feet are stationary during support. A future support sequence determines the horizontal COM trajectory.
    steps = 83
    n = int((1.3 + (steps + 1) * period + 1) / dt)
    ts = np.arange(n) * dt
    feet = np.tile(feet0, (n, 1, 1))
    load = np.full((n, 2), 0.5)
    endpoints = feet0.copy()
    t0 = 1.3
    balance = (Reflex if os.environ.get("REFLEX") else Balance)(
        m, d, dt, feet0, root0, comoff, period, stride, clear
    )
    disturbances = loads(ts)
    rot = Rotation.from_matrix(rot0)
    d.qpos[ix] += np.random.default_rng(seed).normal(0, 0.0001, len(ix))
    mj.mj_forward(m, d)
    M = np.zeros((m.nv, m.nv))
    Jold = [None, None]
    meas = []
    poses = []
    qlog = []
    forces = []
    scr = mj.MjData(m)
    dex = []
    lin = []
    us = []
    xs = []
    if linearize:
        vid = np.r_[
            np.arange(6),
            iv[
                [
                    i
                    for i, nm in enumerate(names)
                    if nm.startswith("body_") or "ankle" in nm or "toe" in nm
                ]
            ],
        ]
        aid = np.array([i for i in range(m.nu) if iv[i] in vid])
        active = np.r_[vid, m.nv + vid]
    pen_bias = np.load(Path(__file__).parent / "bias.npy")
    pen_rows = json.loads((Path(__file__).parent / "penpop.json").read_text())
    mids, amps = np.reshape(pen_rows[int(os.environ.get("PEN", 0))][-1], (2, 11))
    planned = disturbances.copy()
    windows = np.flatnonzero(np.diff(np.r_[False, abs(planned) > 0, False])).reshape(
        -1, 2
    )
    disturbances[:] = 0
    previous_height = feet0[:, 2].copy()
    event_no = 0
    direct = bool(os.environ.get("DIRECT"))
    if direct:
        m.actuator_gainprm[bodyact, 0] = 1
        m.actuator_biasprm[bodyact, :] = 0
        m.actuator_ctrlrange[bodyact] = m.actuator_forcerange[bodyact]
    ticks = []

    initial_centers = []
    for mount, pen, *_ in grip.data:
        initial_centers.append(
            d.xmat[mount].reshape(3, 3).T @ (d.xpos[pen] - d.xpos[mount])
        )
    amplitude = np.ones(2)
    amplitude_goal = np.ones(2)

    def advance(k, t, force, capture):
        refs = balance.update(t, m, d)
        rootp, rootv, roota, footp, footv, foota, weights, estimate, roll = refs
        target = home.copy()
        arm = (
            0.15
            * np.sin(np.pi * (t - t0) / period)
            * quint((t - t0) / period)
            * (1 - quint((t - t0 - (steps - 1) * period) / period))
        )
        target[act("body_00")] += 0.02 * arm
        target[act("body_05")] -= 0.02 * arm
        for si, side in enumerate("LR"):
            phase = 2 * np.pi * t / (5.3 + 0.4 * si) + si * 0.70
            target[act(side + "_wrist_pitch")] += 0.16 * np.sin(phase) * min(t, 1)
            target[act(side + "_wrist_roll")] += 0.14 * np.sin(phase * 0.8) * min(t, 1)
            target[act(f"body_{si * 5 + 3:02d}")] += (
                0.085 * np.sin(phase * 0.8) * min(t, 1)
            )
        qdd = np.zeros(m.nv)
        qdd[iv] = 90 * (target - d.qpos[ix]) - 17 * d.qvel[iv]
        qdd[:3] = roota + 75 * (rootp - d.qpos[:3]) + 18 * (rootv - d.qvel[:3])
        qdd[3:6] = (
            -170 * Rotation.from_quat(d.qpos[[4, 5, 6, 3]]).as_rotvec()
            + 170 * np.array([0, roll, 0])
            - 25 * d.qvel[3:6]
        )
        yield_fraction = float(os.environ.get("YIELD", 0))
        if yield_fraction and getattr(balance, "holding", False):
            age = t - balance.t0
            hold = float(os.environ.get("SOFT", 0.4))
            free = yield_fraction * (1 - quint((age - hold) / 0.35))
            qdd[0] *= 1 - free
            estimate *= 1 - free
            qdd[4] *= float(os.environ.get("ROLLK", 0.45))
        Jlist = []
        for s, L in enumerate(legs):
            jp = np.empty((3, m.nv))
            jr = jp.copy()
            mj.mj_jacBody(m, d, jp, jr, ids[s])
            J = np.vstack((jp, jr))
            cols = iv[L]
            jl = J[:, cols]
            Jlist.append(J)
            orient = (
                rot[s] * Rotation.from_matrix(d.xmat[ids[s]].reshape(3, 3)).inv()
            ).as_rotvec()
            des = np.r_[
                foota[s]
                + 400 * (footp[s] - d.xpos[ids[s]])
                + 40 * (footv[s] - jp @ d.qvel),
                260 * orient - 32 * jr @ d.qvel,
            ]
            jd = 0 if Jold[s] is None else ((J - Jold[s]) / dt) @ d.qvel
            Jold[s] = J
            qdd[cols] += jl.T @ np.linalg.solve(
                jl @ jl.T + 0.00003 * np.eye(6), des - jd - J @ qdd
            )
        mj.mj_fullM(m, M, d.qM)
        required = M @ qdd + d.qfrc_bias - d.qfrc_passive
        # Distribute the six unactuated base equations between the two ankle wrenches.
        required[:3] -= [estimate, 0, 0]
        Jx = np.zeros((3, m.nv))
        mj.mj_jacBodyCom(
            m, d, Jx, None, m.body(os.environ.get("PUSHBODY", "body_20")).id
        )
        required[3:] -= Jx[0, 3:] * estimate
        if os.environ.get("QP", "1") == "1":
            required, weights = feasible(
                m, d, ids, Jlist, iv, legs, M, required, weights
            )
        residual = required.copy()
        if os.environ.get("PRESS", "0") == "1":
            weights = pressure(m, d, Jlist, required, weights)
        support = sum(w * J[:, :6].T for w, J in zip(weights, Jlist))
        wrench = np.linalg.solve(support, required[:6])
        for s, J in enumerate(Jlist):
            residual -= J.T @ wrench * weights[s]
        torque = np.clip(residual[iv], *m.actuator_forcerange[bodyact].T)
        if os.environ.get("SPINE") and getattr(balance, "holding", False):
            j_sp = act("body_21")
            v_sp = iv[j_sp]
            k_sp = float(os.environ["SPINE"])
            b_sp = float(os.environ.get("SPB", 2.5))
            # A true joint spring reacts to deflection; the inverse-dynamic acceleration command is absent.
            torque[j_sp] = np.clip(
                d.qfrc_bias[v_sp]
                + k_sp * (home[j_sp] - d.qpos[ix[j_sp]])
                - b_sp * d.qvel[v_sp],
                *m.actuator_forcerange[bodyact[j_sp]],
            )
        if direct:
            d.ctrl[bodyact] = torque
        else:
            d.ctrl[bodyact] = np.clip(
                d.qpos[ix]
                + (torque - m.actuator_biasprm[bodyact, 2] * d.qvel[iv])
                / m.actuator_gainprm[bodyact, 0],
                *m.actuator_ctrlrange[bodyact].T,
            )
        d.xfrc_applied[:] = 0
        d.xfrc_applied[m.body(os.environ.get("PUSHBODY", "body_20")).id, 0] = force
        for side, (mount, pen, ac, _, _) in enumerate(grip.data):
            if capture and (60 * k) // 500 != (60 * (k - 1)) // 500:
                center = d.xmat[mount].reshape(3, 3).T @ (d.xpos[pen] - d.xpos[mount])
                start = initial_centers[side]
                if (
                    center[2] < start[2] - 0.0068
                    or abs(center[0]) > abs(start[0]) + 0.010
                ):
                    if capture and amplitude_goal[side] == 1:
                        print("grip adjustment", side, round(t, 3), flush=True)
                    amplitude_goal[side] = 0.75
            amplitude[side] += (
                dt / (0.08 + dt) * (amplitude_goal[side] - amplitude[side])
            )
            d.ctrl[ac] = 0.006 * (
                pen_bias
                + mids
                + float(os.environ.get("HANDAMP", 1))
                * amplitude[side]
                * amps
                * np.sin(2 * np.pi * t / 3.2)
            )
        if capture:
            ticks.append(
                grip.contacts() + [float(estimate), roll, balance.gait, float(force)]
            )
            physical = [[] for s in ids]
            for c in d.contact:
                g = c.geom2 if c.geom1 == 0 else c.geom1 if c.geom2 == 0 else -1
                if g > 0 and "Foot_" in m.geom(g).name:
                    physical[int(m.geom(g).name.startswith("R"))].append(g)
            meas.append(
                [
                    t,
                    *d.qpos[:3],
                    *d.xpos[ids, 2],
                    *d.xpos[ids, 1],
                    *d.qpos[ix[[legs[0][3], legs[1][3]]]],
                    *[bool(ls) for ls in physical],
                    *rootp,
                    *d.qvel[:3],
                ]
            )
            if record and t + 1e-8 >= len(poses) / 60:
                dex.append(grip.measure())
                poses.append(np.c_[d.xpos, d.xquat].copy())
                qlog.append(d.qpos.copy())
        error = d.qpos[:3] - rootp
        angular = np.linalg.norm(d.qvel[3:5])
        balance.observe(m, d)
        mj.mj_step(m, d)
        return error, angular

    from strategies import select
    from shooting import choose, option
    from collections import deque

    history = deque(maxlen=100)
    for k, t in enumerate(ts):
        mj.mj_forward(m, d)
        history.append(balance.val)
        if not balance.holding and abs(balance.val) >= 2:

            def trial(candidate, profile):
                select(balance, candidate)
                option(candidate)
                cost = 0.0
                worst = 0.0
                start_xy = d.qpos[:2].copy()
                hand_cost = 0.0
                mount = [item[0] for item in grip.data]
                pen = [item[1] for item in grip.data]
                for j, force in enumerate(profile):
                    if j:
                        mj.mj_forward(m, d)
                    err, ang = advance(k + j, t + j * dt, force, False)
                    zloss = max(0, root0[2] - d.qpos[2] - 0.14)
                    instability = (
                        5 * abs(err[0]) + 8 * abs(err[1]) + 15 * zloss + 0.12 * ang
                    )
                    if not np.isfinite(instability) or instability > 4:
                        return 50 + (len(profile) - j) * dt
                    if j % 10 == 0:
                        if len(profile) > 2000:
                            basis = d.xmat[ids].reshape(2, 3, 3)
                            yaw = np.max(
                                np.abs(np.arctan2(basis[:, 1, 0], basis[:, 0, 0]))
                            )
                            hand_cost += 0.15 * max(0.0, yaw - 1.0)
                        distances = np.linalg.norm(d.xpos[pen] - d.xpos[mount], axis=1)
                        if max(distances) > 0.135:
                            return 40 + (len(profile) - j) * dt
                        contact = grip.contacts()
                        hand_cost += 0.03 * sum(flag != 3 for flag in contact[:2])
                    worst = max(worst, instability)
                    cost += dt * instability
                displacement = np.sign(profile[np.argmax(abs(profile))]) * (
                    d.qpos[0] - start_xy[0]
                )
                return (
                    hand_cost
                    + worst
                    + cost
                    + 0.4 * np.linalg.norm(d.qvel[:2])
                    - 3.6 * np.clip(displacement, -0.4, 0.4)
                )

            choice = choose(
                trial, np.array(history), dt, abs(d.xpos[ids[1], 0] - d.xpos[ids[0], 0])
            )
            select(balance, choice)
            option(choice)
        force = planned[k]
        if 0 <= int(os.environ.get("OMIT", -1)) < len(windows):
            lo, hi = windows[int(os.environ["OMIT"])]
            if lo <= k < hi:
                force = 0.0
        err, _ = advance(k, t, force, True)
        if (
            max(abs(err[:2])) > 0.65
            or abs(err[2]) > 0.30
            or t >= float(os.environ.get("END", 55))
        ):
            break
    if template is not None:
        np.savez(template, xs=xs, us=us)
    if linearize:
        np.savez(
            H.parents[1] / "work/smooth/linear.npz",
            a=np.array([z[0] for z in lin], dtype=np.float32),
            b=np.array([z[1] for z in lin], dtype=np.float32),
            xs=xs,
            us=us,
            vid=vid,
            aid=aid,
        )
    a = np.array(meas)
    if record:
        np.savez(
            Path(__file__).resolve().parent / (os.environ.get("RUN", "take") + ".npz"),
            poses=poses,
            qs=qlog,
            names=[m.body(i).name or "world" for i in range(m.nbody)],
            metrics=a,
            dex=dex,
            ticks=ticks,
        )
    return dict(
        time=round(t, 3),
        nominal=round(ts[-1], 3),
        forward=round(-d.qpos[1], 3),
        x=round(d.qpos[0], 3),
        height=round(d.qpos[2], 3),
        peak_error=np.round(abs(a[:, 1:4] - a[:, 12:15]).max(0), 4).tolist(),
    )


if __name__ == "__main__":
    print(simulate(record=True, push=float(os.environ.get("PUSH", 1))))
