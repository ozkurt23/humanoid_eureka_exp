"""Audit force windows and foot support from the frozen 500 Hz state traces.

Usage: python audit_events.py --traces work/parmak_denge --summary outputs/surpriz-denge/Olcumler.json --output events.csv
Requires NumPy. One CSV row per observed onset, including interrupted forces.
"""
import argparse
import csv
import json
from pathlib import Path

import numpy as np


def intervals(mask):
    return np.flatnonzero(np.diff(np.r_[False, mask, False])).reshape(-1, 2)


def audit(traces, summary):
    records = []
    for trial in summary["trials"]:
        run = trial["data"]
        seed = int(run["name"][1:])
        with np.load(traces / f"z{seed}.npz") as z:
            tick, m, poses = z["ticks"], z["metrics"], z["poses"]
            force = tick[:, -1]
            names = z["names"].tolist()
            foot = poses[:, [names.index(side + "_ankle_roll") for side in "LR"], :3]
            observed = intervals(np.abs(force) > 0.002)
            assert len(observed) == len(run["events"])
            for j, ((a, b), event) in enumerate(zip(observed, run["events"]), 1):
                closed = b < len(force)
                sign = np.sign(force[a:b].mean())
                contact = m[a, 10:12].astype(bool)
                support = {(False,False):"flight",(True,True):"both",(True,False):"L",(False,True):"R"}[tuple(contact)]
                assert support == event["support"]
                longest = max([0.0] + [s["shift_cm"] for s in event["landings"] if s["lift_cm"] >= 0.5])
                after_onset = []
                for side in (0, 1):
                    for lift, land in intervals(~m[:, 10 + side].astype(bool)):
                        if lift < a or lift > b or land > min(b + 150, len(m) - 1) or land - lift < 15:
                            continue
                        start = max(0, round(lift * 0.12) - 1)
                        end = min(len(foot) - 1, round(land * 0.12) + 1)
                        xyz = foot[start:end + 1, side]
                        height = xyz[:, 2].max() - min(xyz[0, 2], xyz[-1, 2])
                        delta = sign * (xyz[-1, 0] - xyz[0, 0])
                        if height >= 0.005 and delta >= 0.03:
                            after_onset.append((lift - a) * .002)
                records.append(dict(
                    seed=seed, event=j, onset_s=round(m[a, 0], 3), release_observed=int(closed), support=support,
                    force_sign=int(sign), observed_peak_N=event["force"], step_cm=longest,
                    post_onset_step=int(bool(after_onset)),
                    first_post_onset_lift_s=round(min(after_onset), 3) if after_onset else "",
                    subsequent_forward_cm=event["walk_cm"] if closed else "",
                    left_pen_excursion_deg=event["shaft_deg"][0], right_pen_excursion_deg=event["shaft_deg"][1],
                    palm_contact_during_load=int(tick[a:b, 2:4].max() != 0),
                    left_opposed_pct=round(100 * np.mean(tick[a:b, 0] == 3), 3),
                    right_opposed_pct=round(100 * np.mean(tick[a:b, 1] == 3), 3),
                ))
    return records


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--traces", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = audit(args.traces, json.loads(args.summary.read_text()))
    with args.output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=records[0].keys())
        writer.writeheader()
        writer.writerows(records)
