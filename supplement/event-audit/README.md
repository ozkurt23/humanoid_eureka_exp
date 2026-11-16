# Supplementary event audit

`event_audit.tex` is an editable English LaTeX fragment (booktabs). `events.csv` records one row per observed onset across the final 15 runs, including the three loads still active at termination. A blank post-release distance denotes missing follow-up. Force onset for this audit is the first 2 ms sample above 0.002 N absolute magnitude, consistent with the event evaluator. The original film's caption clock labels the first nonzero forcing sample and can differ by a few milliseconds.

To reproduce from the restored project, run the following at the original project root, substituting the location of this directory if necessary.

```sh
python audit_events.py --traces work/parmak_denge --summary outputs/surpriz-denge/Olcumler.json --output events.csv
```

The script checks support at onset against the original evaluator, computes the extra post-onset foot-lift criterion from raw contact/ankle traces and reads the original signed landing/shaft-excursion summaries. It records foot support, release observability, pulse-window contact rates and post-release progress where observable. Geometry is sampled at 60 Hz and contacts at 500 Hz. Signed landing displacement is taken between bracketing pose frames; thresholds and event assignments follow the original evaluator. Lift-off after onset indicates temporal ordering alone. Neither the gait contribution nor the causal role of a particular swing is identified by this timing statistic.
