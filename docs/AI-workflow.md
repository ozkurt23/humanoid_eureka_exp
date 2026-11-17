# How AI participated in this project

The motivating question was whether an AI agent could carry a substantial robotics experiment through design, implementation, debugging, evaluation, rendering, and publication. The user specified the tasks, reviewed videos, identified unsatisfactory movement, and asked for changes. The AI agent operated the development and experiment tools, inspected recorded measurements, made changes, and produced the deliverables.

Simulation and rendering ran on one Ubuntu workstation. AI-agent inference used the assistant service, while the identified Qwen reward proposal experiments ran locally. A local workstation for physics does not imply that every language-model computation occurred on that workstation.

## From task to evidence

1. The user proposed a pen-manipulation task inspired by Eureka and a humanoid push-recovery task.
2. The AI agent assembled the user's humanoid and V3 hand models into simulation, implemented control and evaluation scripts, and ran experiments.
3. The user reviewed the movement and requested corrections to walking, recovery steps, push duration, fingertip grasp, and continuing pen motion.
4. The AI agent inspected logs, compared motion and contact records, developed the final physics-based step search, and evaluated changed push schedules.
5. The final evidence includes 15 frozen-controller schedules, five selected-force omission comparisons, and 15 matched runs with the lateral-first stance-closing rule disabled.
6. The same recorded physics trajectory drove the Blender movie. The AI agent created the scene, camera views, wrist-locked insets, captions, encoding and playback checks.
7. Recorded data and analysis scripts supplied the figures, tables, failure analysis and editable LaTeX paper.

The process provides a case study of sustained AI-assisted experimental execution with human direction and review. General autonomous research capability across tasks requires a separate evaluation.

## Where Qwen was used

`work/qwen` in the full archive stores Qwen2.5-Coder-1.5B-Instruct, downloaded for early reward-proposal experiments. `model.safetensors` is the pretrained language model checkpoint, approximately 3.1 GB. The simulator's robot controllers and learned policies are separate files.

The following paths are relative to the restored full experiment archive.

- `outputs/deneyler/reward_search.py` loads Qwen with Transformers/CUDA and requests five numerical reward coefficients. `outputs/deneyler/runs/reward_history.jsonl` records the suggestions and experiment results.
- `outputs/deneyler/run_hand.py` uses the proposed coefficients in a hand-controller search. `outputs/deneyler/balance_comparison.py` evaluates proposed humanoid rewards through PPO runs.
- `outputs/ikinci-tur/compare.py` runs a later comparison of manual, random and Qwen-proposed rewards, with model proposals recorded in `llm.jsonl`.

These historical results are mixed. For example, the initial humanoid comparison records 178/360 recoveries using Qwen-proposed rewards and 173/360 with manual rewards, while calm walking was 68/120 and 120/120 respectively. A later comparison records 115/720 recoveries for Qwen-proposed rewards and 174/720 for manual rewards. These counts come from distinct earlier protocols and should not be compared directly to the final 12/15 compound-task result.

## Final demonstration

The final `work/parmak_denge/shootrun.py` estimates disturbances, evaluates candidate foot placements through physics rollouts, and applies tendon motions with grip feedback. Its normal execution path loads the recorded grasp and model inputs. The archived Qwen files preserve the earlier reward-proposal experiments, and are unnecessary for running the final demonstration.

The final film demonstrates a model-based controller developed during the AI-assisted workflow. The research agent used tools to implement and evaluate that controller, with human direction and feedback throughout the project.

[Technical paper](../makale/Makale.pdf) · [Runnable controller](../work/parmak_denge/README.md) · [Full archive](../arsiv/README.md) · [Original Qwen model](https://huggingface.co/Qwen/Qwen2.5-Coder-1.5B-Instruct)
