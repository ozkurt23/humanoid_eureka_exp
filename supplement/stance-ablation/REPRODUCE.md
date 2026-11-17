# Paired ablation of lateral-first stance closure

The enabled and disabled experiments use the same 15 schedules, MuJoCo plant, search candidates, grip controller, duration and compound success thresholds. The sole intervention assigns `False` to `Catch.close_stance_first` at gait restart. It affects the controller both in the live trajectory and in its candidate physics rollouts. The standard lateral recovery search and nominal stance-width correction are still active on both sides. Development schedules, including the archival film, were used during controller development. The final six schedules (1071–1076) were originally reserved for the frozen-controller check.

## Repeat

Use a second copy of the repository checkout and a Python environment satisfying its simulation requirements. Apply the supplied patch from the root of that copy. Run one or all of the schedules using the normal entry point.

```bash
git apply supplement/stance-ablation/lateral-first-off.patch
mkdir -p ablation-records
export PYTHON="$HOME/env_isaaclab/bin/python"
for seed in 714 715 716 727 905 924 1042 1051 1052 1071 1072 1073 1074 1075 1076; do
    RUN="../../ablation-records/off-$seed" bash work/parmak_denge/run.sh "$seed" > "ablation-records/off-$seed.log" 2>&1
done
```

The 15 matching enabled trajectories (`z<seed>.npz`) are in `work/parmak_denge/` in the full experiment archive. From the directory containing the analysis scripts, supply paths to those arrays, the disabled arrays, and the published controller code:

```bash
python analyze_pairs.py --on /path/to/full-archive/work/parmak_denge \
    --off /path/to/ablation-records --code /path/to/repo/work/parmak_denge --output results
python plot_pairs.py results/paired-results.json /path/to/full-archive/work/parmak_denge/z714.npz \
    /path/to/ablation-records/off-714.npz results/ablation
```

The comparison verifies the true applied force byte-for-byte over each pair's common recorded horizon and tests identical pre-onset observables. All six trace arrays are compared to identify identical runs. A short trace ends at the model's stopping threshold. No new prospective schedule and no model retuning were used for the paired analysis. Boolean success is computed with the published joint task criteria. Completed duration alone does not imply joint success. The two columns reflect paired outcomes; each outcome per schedule counts once.

## Recorded ablation trajectories

From the repository root, download the four release assets and verify before extraction.

```bash
mkdir -p ablation-records
gh release download v1.0.0 -R ozkurt23/humanoid_eureka_exp --pattern 'ablation-*.tar.zst' --dir ablation-records
(cd ablation-records && sha256sum -c ../supplement/stance-ablation/ABLATION-SHA256SUMS)
for bundle in ablation-records/*.tar.zst; do tar --zstd -xf "$bundle" -C ablation-records; done
```
