# Data Integrity Audit · 2026-04-24

**Overall:** 🔴 `critical`  ·  critical gaps: **2547**  ·  warn gaps: 73

**Recommendation:** `replit_fallback_required`

## Per-category

| Category | Severity | Expected | Present | Missing | Stale | Notes |
|---|---|---|---|---|---|---|
| race_artefacts | 🔴 critical | 600 | 590 | 10 | 0 | days with any missing artefact: 2 |
| fixtures_cache | 🟢 ok | 1 | 143 | 0 | 0 | total cached race days: 143 |
| horse_profiles | 🔴 critical | 1272 | 4 | 1268 | 0 | 1268 horses raced in last 180d have NO profile; total profiles in DB: 1886 |
| horse_form_records | 🔴 critical | 1272 | 4 | 1268 | 0 | 1268 recent-cohort horses have NO form_records file; total form_records files: 1899 |
| jockey_profiles | 🔴 critical | 44 | 43 | 1 | 0 | 1 jockeys raced recently but NO profile; total jockey profiles: 64 |
| jockey_records | 🟡 warn | 64 | 59 | 5 | 0 | 5 jockey profiles have no records file |
| trainer_profiles | 🟢 ok | 38 | 38 | 0 | 0 | total trainer profiles: 67 |
| trainer_records | 🟡 warn | 67 | 0 | 67 | 0 | 67 trainer profiles have no records file |
| trial_results | 🟢 ok | 1 | 1 | 0 | 0 | trial rows: 5579 |
| entries_upcoming | 🟡 warn | 2 | 1 | 1 | 0 | 1 upcoming race days lack entries file |

### 🔴 race_artefacts — sample missing (first 20)

```
results_2026-04-19
commentary_2026-04-19
dividends_2026-04-19
sectional_times_2026-04-19
video_links_2026-04-19
results_2026-04-22
commentary_2026-04-22
dividends_2026-04-22
sectional_times_2026-04-22
video_links_2026-04-22
```

### 🔴 horse_profiles — sample missing (first 20)

```
D075
E058
E061
E175
E184
E301
E321
E356
E392
E403
E413
E430
E432
E434
E435
E436
E448
E459
E471
E472
```

### 🔴 horse_form_records — sample missing (first 20)

```
D075
E058
E061
E175
E184
E301
E321
E356
E392
E403
E413
E430
E432
E434
E435
E436
E448
E459
E471
E472
```

### 🔴 jockey_profiles — sample missing (first 20)

```
---
```
