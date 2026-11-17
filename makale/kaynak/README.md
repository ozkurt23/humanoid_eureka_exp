# Building the research paper

`Makale.tex` is the editable English manuscript. Compile it from this directory with Tectonic 0.17 or XeLaTeX. The layouts use Liberation Serif, Liberation Sans, and Liberation Mono, which are available on Ubuntu through the Liberation fonts package. All figures are included, so the typesetting step does not require Python.

```sh
tectonic --outdir .. Makale.tex
```

For XeLaTeX, compile twice to resolve the bibliography and cross-references.

## Source data and visual material

- `olcumler.json` contains the filmed run, five matched force-omission comparisons, and the 15 complete or interrupted study records.
- `yuruyus.csv` contains the force and forward-position traces subsampled from the 500 Hz physics record at 20 Hz for display. `kalem.csv` contains 60 Hz pen-angle measurements in each wrist frame.
- `sekiller.py` reads the data and writes the vector figure PDFs, controller schematic, and LaTeX outcome rows. Use `python3 sekiller.py` with NumPy and Matplotlib. When updating the dataset, replace Table 1's inline data lines with the generated rows from `sekiller/kosular.tex`.
- `gorseller/` contains crops from the original Blender-rendered take. `kareler.json` records the numbers and normalized crop bounds of the underlying frames. Frame 1 corresponds to 0 s. `veri_hazirla.py` includes the exact additional crops used for the equal-aspect-ratio overview panels.
- To regenerate the paper samples and images after restoring the full experimental workspace, run `python3 veri_hazirla.py /path/to/restored/project`. This requires NumPy and Pillow.
- `audit/` contains the independent event-level audit, the observed event table, and the editable appendix fragment. Its README gives the command and the exposure and latency conventions.
- `paired-traces.csv` contains five observed-minus-omitted pelvis displacement profiles in the load direction, downsampled to 50 Hz with exact release samples retained. These data generate the time-aligned force-omission plot.
- `ablation/` contains the paired controller analysis, single-factor patch, plotting script, instructions, and all 15 paired numerical outcomes. The corresponding full-width vector figure is `sekiller/ablation.pdf`. The supplementary raw trajectories and integrity manifest are in the project archive.
- `pipeline.tex` documents the implementation from CAD assembly to MP4 decoding. Its simulation reconstruction uses `pipeline_figures.py /path/to/restored/project` with MuJoCo 3.8, NumPy and Pillow; the other panels reuse the corresponding Blender and decoded frames. The three images are included for compilation without MuJoCo.

## Availability and licensing

The public project is [humanoid_eureka_exp](https://github.com/ozkurt23/humanoid_eureka_exp). Original code uses the MIT license. Original design files use CERN-OHL-P-2.0. The paper, media, and data use CC BY 4.0. Third-party material retains its applicable license.
