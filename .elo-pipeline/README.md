# Elo v1.1 Compute Pipeline

This folder contains the batch Elo compute pipeline for HKJC race data.
It runs nightly in GitHub Actions (see `.github/workflows/elo-v11.yml`).

## What it produces

A SQLite database `bulk.db` containing:

- Raw ingested tables: `horses`, `horse_form_records`, `horse_trackwork`, `horse_injury`, `trial_sessions`, `trial_runners`, `jockey_season_records`, `entries_upcoming`, etc.
- Elo snapshots: `horse_elo_snapshots`, `jockey_elo_snapshots`, `trainer_elo_snapshots`
- Run metadata: `elo_runs`, `ingestion_runs`, `sync_state`

Downloadable as a workflow artifact after each successful run.

## Local test (optional)

```bash
cd .elo-pipeline
npm ci
npx tsx scripts/ingest/index.ts all --data-dir=.. --db=./bulk.db
npx tsx scripts/elo/compute_v11.ts --db=./bulk.db --run-label=v11_local
```

## Axes (v1.1)

- Overall (horse, jockey, trainer)
- Per-horse axis: `{surface} × {distance_bucket}` where surface ∈ {turf, awt} and bucket ∈ {sprint, mile, middle, staying}
- 180-day idle decay: `R_new = R × 0.9 + 1500 × 0.1`

See `../uploads/文件 (2) - 複本.docx` (賽馬 Elo 等級分系統開發手冊 v1.1) for the full spec.
