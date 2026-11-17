# humanoid_eureka_exp

**Bimanual Fingertip Manipulation During Humanoid Push Recovery**  
Ali Özkurt · November 2026

An AI-assisted robotics research project, from experiment design and debugging to simulation, evaluation, rendering, and a technical paper. The human set goals, reviewed motion, and requested corrections. The AI agent implemented and iterated on the experiments using local tools.

**[Read the paper](makale/Makale.pdf) · [Watch the 1080p / 60 fps film](medya/Film.mp4) · [Reproduce the experiment](docs/Yeniden-calistirma.md) · [Reuse and licenses](LICENSING.md)**

[![A humanoid recovers from a lateral push while moving a pen in each hand. Click to watch the complete film.](medya/Izleme.gif)](medya/Film.mp4)

The 55-second movie follows one continuous MuJoCo trajectory through ten camera views. Wrist-mounted views show each pen moving relative to its hand. Download the repository and open [index.html](index.html) to jump between the five pushes and inspect the measurements.

## What the robot does

The simulation combines a humanoid, two tendon-driven V3 hands, and two free pens. An external generator varies lateral push timing, direction, strength, and duration. The controller estimates the load from the robot's observed dynamics and simulates candidate recovery steps. It then resumes forward walking while both hands keep moving their pens.

| Example from the film | Measurement |
|---|---:|
| Strongest lateral push | 107.7 N, held for 1.82 s |
| Corresponding downwind recovery step | 29.4 cm |
| Forward progress before the next push | 30.2 cm |
| Pen-axis excursion relative to each hand during that push | 33.9° left / 33.9° right |

All physics runs and renders were performed on one Ubuntu workstation. Candidate rollout search can take longer than the simulated motion.

## What the evaluation supports

The complete task passed on **12 of 15 schedules**, including **5 of 6 schedules reserved after freezing the controller**. A pass requires all five pushes to meet the step, subsequent walking, fingertip-contact, and pen-motion criteria. Failed and interrupted trials are included.

Disabling the lateral-first stance-closing rule produced **11 of 15** complete-task passes on the same schedules. Both versions passed the same five reserved schedules. In seed 714 both remained upright, while the intervention changed the fifth recovery step from downwind to upwind.

- [All trial measurements](veri/Olcumler.json)
- [Audit of complete and interrupted push events](supplement/event-audit/README.md)
- [Paired controller ablation, patch, and raw-record instructions](supplement/stance-ablation/REPRODUCE.md)
- [Paper and editable LaTeX, figures, and data](makale/)

The study covers lateral pelvis pushes on one simulated robot. Hardware transfer and real-time control remain to be evaluated.

## AI's role and Eureka

Eureka's reward-design experiments motivated the initial hand manipulation task. Early experiments used a local Qwen2.5-Coder-1.5B-Instruct model to propose numerical reward coefficients, followed by local controller search and PPO comparisons. Those exploratory records are preserved in the full archive.

The final demonstration uses a model-based step-search controller and a tendon-motion controller with grip feedback. See [AI workflow and the historical role of Qwen](docs/AI-workflow.md) for the exact distinction.

## Code, CAD, data, and media

The runnable checkout includes the final controller and required model inputs. The [complete experiment archive](arsiv/README.md) includes editable CAD, previous experiments, learned checkpoints, successful and failed runs, Blender scenes, and the final movie's 3,300 rendered frames. Large records are available as release assets.

Original code is **MIT**, original CAD and model designs are **CERN-OHL-P-2.0**, and the paper, original data and media are **CC BY 4.0**. Commercial reuse is allowed under these licenses. [Scope and attribution](LICENSING.md) · [Third-party software and model notices](THIRD_PARTY.md)

## Research background

- [Eureka: Human-Level Reward Design via Coding Large Language Models](https://eureka-research.github.io/)
- [Capture Point: A Step toward Humanoid Push Recovery](https://doi.org/10.1109/ICHR.2006.321385)
- [MuJoCo](https://mujoco.org/)
- [π0.5: A Vision-Language-Action Model with Open-World Generalization](https://proceedings.mlr.press/v305/black25a.html)
- [DreamZero: World Action Models are Zero-shot Policies](https://dreamzero0.github.io/DreamZero.pdf)

[Citation metadata](CITATION.cff) · [Project plan](docs/Proje-plani.md) · [Türkçe proje özeti](docs/README-tr.md)
