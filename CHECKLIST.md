# Reproduction Checklist

## Briefing
- [x] `briefing/problem.md`
- [x] `briefing/evaluation.md`
- [x] `briefing/method.md`
- [x] `briefing/overview.md`

## Scoring
- [x] `scoring/reference.json`
- [x] `scoring/scores.json`
- [x] `scoring/EXPERIMENTS.md`
- [x] `scoring/TARGETS.md`
- [x] `scoring/CONSTRAINTS.md`
- [x] `scoring/DIRECTION.md`
- [x] Workspace validated with `python validate.py --compare` locally after adding files to git
- [x] MovingAI public benchmark subset included in scoring

## Code And Scripts
- [x] Evaluation code in `eval/`
- [x] Method implementation in `method/`
- [x] Baseline implementation in `baseline/`
- [x] `scripts/evaluate.sh`
- [x] `scripts/reproduce.sh`
- [x] `scripts/download.sh`
- [x] `scripts/method.sh`
- [x] `scripts/baseline.sh`
- [x] `scripts/run.sh`
- [x] MovingAI benchmark parser in `data/mapf_benchmarks.py`

## Environment
- [x] `environment/container.def`
- [x] `environment/setup.sh`

## Milestones
- [x] `method_runs`
- [x] `core_claim`
- [ ] `core_claim_plus`
- [ ] `secondary_claims`
- [ ] `majority`
- [ ] `near_complete`
- [ ] `full`
