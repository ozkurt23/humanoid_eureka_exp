import sys, numpy as np, json
from pathlib import Path
from scipy.spatial.transform import Rotation


def measure(file):
    z = np.load(file)
    m = z["metrics"]
    p = z["poses"]
    n = z["names"].tolist()
    tips = z["ticks"]
    dex = z["dex"]
    force = tips[:, -1]
    ev = np.flatnonzero(np.diff(np.r_[False, abs(force) > 0.002, False])).reshape(-1, 2)
    feet = p[:, [n.index(a + "_ankle_roll") for a in "LR"], :3]
    axes = []
    for side in "LR":
        arm = Rotation.from_quat(p[:, n.index(side + "v_mount")][:, [4, 5, 6, 3]])
        pen = Rotation.from_quat(p[:, n.index(side + "v_pen")][:, [4, 5, 6, 3]])
        axes.append((arm.inv() * pen).apply([1, 0, 0]))
    roll = Rotation.from_quat(p[:, n.index("base_link")][:, [4, 5, 6, 3]]).as_euler(
        "xyz", degrees=True
    )[:, 1]
    records = []
    for j, (a, b) in enumerate(ev):
        lo = round(a * 0.12)
        hi = min(len(p) - 1, round(b * 0.12))
        end = min(
            len(p) - 1,
            round(ev[j + 1][0] * 0.12) - 1 if j + 1 < len(ev) else len(p) - 1,
        )
        f = force[a:b]
        sg = np.sign(f.mean())
        phase = np.where(m[a, 10:12] == 0)[0]
        fpos = feet[lo : hi + 1, :, 0]
        advance = -(m[min(len(m) - 1, round(end / 0.12)), 2] - m[min(len(m) - 1, b), 2])
        pitch = dex[lo : hi + 1][:, [1, 4]]
        # Signed planar shaft inclination is periodic at +/-180 degrees.
        span = np.ptp(np.rad2deg(np.unwrap(np.deg2rad(pitch), axis=0)), axis=0)
        disp = sg * (fpos - fpos[0])
        landings = []
        for side in range(2):
            off = np.logical_not(m[:, 10 + side].astype(bool))
            for first, last in np.flatnonzero(
                np.diff(np.r_[False, off, False])
            ).reshape(-1, 2):
                if (
                    last < a
                    or first > b
                    or last > min(b + 150, len(m) - 1)
                    or last - first < 15
                ):
                    continue
                flo = max(0, round(first * 0.12) - 1)
                fhi = min(len(feet) - 1, round(last * 0.12) + 1)
                path = feet[flo : fhi + 1, side]
                landings.append(
                    dict(
                        side="LR"[side],
                        shift_cm=round(100 * sg * (path[-1, 0] - path[0, 0]), 1),
                        lift_cm=round(
                            100 * (max(path[:, 2]) - min(path[0, 2], path[-1, 2])), 1
                        ),
                    )
                )
        shaft = [
            round(
                np.rad2deg(
                    np.arccos(
                        np.clip((axis[lo : hi + 1] @ axis[lo : hi + 1].T).min(), -1, 1)
                    )
                ),
                1,
            )
            for axis in axes
        ]
        records.append(
            dict(
                shaft_deg=shaft,
                roll_range_deg=round(np.ptp(roll[lo : hi + 1]), 1),
                landings=landings,
                t=round(a * 0.002, 3),
                force=round(sg * max(abs(f)), 1),
                support="LR"[1 - phase[0]]
                if len(phase) == 1
                else ("both" if not len(phase) else "none"),
                step_cm=round(100 * disp.max(), 1),
                walk_cm=round(advance * 100, 1),
                pen_deg=span.round(1).tolist(),
            )
        )
    return dict(
        name=Path(file).stem,
        seconds=m[-1, 0],
        min_height=round(min(m[:, 3]), 3),
        forward=round(-m[-1, 2] + m[0, 2], 3),
        opposed=(100 * (tips[:, :2] == 3).mean(0)).round(2).tolist(),
        palm=tips[:, 2:4].max(),
        ground=tips[:, 4].max(),
        events=records,
    )


if __name__ == "__main__":
    for f in sys.argv[1:]:
        print(json.dumps(measure(f)))
