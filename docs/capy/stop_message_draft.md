# Stop Message — Phase 2 Cutover

> **Status:** DRAFT — do not send until all pre-flight checks pass.
> **Audience:** Replit (via user forward).
> **Purpose:** Formal handoff from Replit's Selenium scraper to Capy's
> httpx async pipeline. After this message, Replit stops writing to `main`
> for scraper concerns; Capy owns the pipeline.
>
> **Expected send window:** 2026-04-26 12:00 UTC ± 2 hours (aligned with
> baseline tag `capy-handover-baseline-v1`).

---

## Pre-flight checks (all must be ✅ before sending)

- [ ] Baseline tag `capy-handover-baseline-v1` exists on `main` at agreed SHA
- [ ] `capy/scraper-v2` branch has full parity test green on the baseline
      (see `docs/capy/parity_testing.md` §3 and CI artifact from last run)
- [ ] Last 3 Replit scheduled runs on `main` all produced identical rows
      to Capy dry-run on same dates (entries / race-day / trainer)
- [ ] GitHub Actions `capy_*.yml` all passed at least one manual dispatch
      run end-to-end with real commit to `capy/scraper-v2`
- [ ] `HANDOVER.md` pulled into `capy/scraper-v2` and merged
- [ ] Pool A full-universe dry-run (5,827 horses minus phantoms) completed
      without > 1% hard failures
- [ ] D1 trainer silent-fail proven fixed: `trainers/records/<TID>.csv`
      files exist for ≥ 95% of active trainers
- [ ] Rollback runbook (below) tested on a scratch branch

If any box is unchecked → postpone send, escalate to user.

---

## Message body (copy-paste to Replit)

Replit 你好 ✅

Phase 2 cutover 準備就緒。以下係正式交接清單。

### A. 即刻停

從 `{CUTOVER_ISO}` 開始，**請停止以下 workflows 自動觸發**：

| Workflow | Replit path | 動作 |
|---|---|---|
| `update-hkjc-scraper.yml` | `.github/workflows/` | Disable scheduled trigger (保留 `workflow_dispatch` 做 emergency fallback) |
| `TrainerData_Scraper.py` cron | Replit scheduler | Disable |
| 任何 always-on Reserved VM | Replit Deployments | Shutdown / pause |

Replit repo 嘅 Python 代碼（`RacingData_Scraper.py`、`TrainerData_Scraper.py`、`EloRating.py` 等）保留喺 `main` 上 **Replit 唔會主動 delete**，作為 rollback artifact。

7+ 日（見 §D）穩定後，**Tianxi（用戶）可自行決定** archive Replit project。Capy 唔會代為操作。Replit 側嘅 `git_sync_periodic.py` 亦請同 Reserved VM 一齊停（避免 ghost commit）。

### B. Capy 即刻接手

以下由 Capy 嘅 GHA workflows 自動運行：

| Workflow | 時間（UTC）| 負責 |
|---|---|---|
| `capy_race_daily.yml` | 15:30 daily | 賽後 5 CSV |
| `capy_entries.yml` | 12:00 Mon/Tue/Sat | 下場 racecard |
| `capy_trainer_fix.yml` | 17:00 daily | 教練 profile + 歷史（D1 fix）|
| `capy_pool_a.yml` | 20:00 Sat | 5,827 馬 profile + form refresh |

Capy 每次 commit 會署名 `Capy Scraper Bot <capy-bot@noreply.github.com>`。

**Branch / merge 流程（三段）：**

| 階段 | 時間 | Capy push 去邊 | Merge 機制 |
|---|---|---|---|
| 1. Pre-baseline | 今日 → 2026-04-26 12:00 UTC | `capy/scraper-v2` | 不 merge，feature branch 孤立開發 |
| 2. Cutover ceremony | 2026-04-26 12:00 UTC (±30min) | — | **由 Tianxi（用戶）人手**執行 `git merge --ff-only capy/scraper-v2` into `main`，然後打 tag `capy-owns-main-v1` |
| 3. Post-cutover | 2026-04-26 12:30 UTC 之後 | `main` (直推，同 Replit 當初一樣) | 不再走 feature branch |

Cutover ceremony 由用戶人手執行，Capy 唔自行 fast-forward，避免搶時機。

### C. Baseline & 責任分界

- **Baseline SHA**: `{BASELINE_SHA}` (tag `capy-handover-baseline-v1`)
- **Before baseline (含)**: Replit 責任，歷史不動
- **After baseline**: Capy 責任；Replit 唔 commit scraper-產生嘅 data 去 main
- **Non-scraper changes**: Replit 可繼續 commit（例如 ELO 模型、notebook、docs）

### D. 14 日 standby 期（2026-04-26 → 2026-05-10）

雖然 Capy 已接手，但為防萬一：

- Replit 請 **保持 workflow config 可 re-enable**（即只係 disable schedule，唔好 delete）
- Replit 請 **每日被動 check** Capy 有冇成功 commit（可睇 `main` 最新 commit 署名）
- 若連續 24 小時 Capy 未 commit → 參考 §E rollback

**點解 14 日（而唔係 7 日）**：
1. Capy GHA 第 1 週通常會撞到 corner case（週末停賽日、夜馬日、特別賽）
2. 14 日覆蓋 2 個完整 race week + 試閘 cycle
3. Cost 低：Reserved VM idle 14 日無額外 spend（本身就係 always-on tier）
4. 4/26 + 14d = 5/10，啱啱跨過 5 月第一個賽期

5/10 之後如果穩定，Replit 可完全撤出 scraper 範疇。

### E. Rollback runbook（Capy 全面失敗時）

如 Capy pipeline 出問題，Replit 可 4 步 re-activate：

```bash
# 1. Re-enable Replit workflow
cd path/to/repo
gh workflow enable update-hkjc-scraper.yml

# 2. Disable Capy workflows (可選，避免衝突)
gh workflow disable capy_race_daily.yml
gh workflow disable capy_entries.yml
gh workflow disable capy_trainer_fix.yml
gh workflow disable capy_pool_a.yml

# 3. Manual kick Replit scraper for missing date(s)
gh workflow run update-hkjc-scraper.yml

# 4. 通知用戶 + 通知 Capy（via 用戶 forward）
```

### F. Parity 證明

全部 byte-parity test 結果喺：
- CI run: `{PARITY_CI_URL}`
- Artifact: `parity-report-{CUTOVER_DATE}.html`
- 涵蓋 dates: `{DATE_RANGE}`
- Row-level diff: 0

Minor deliberate divergences（唔係 bug，唔 block cutover）：
- `horse_profiles.csv` 新增 `profile_last_scraped` 欄位（Replit schema 冇）
- `trainers/records/*.csv` 全新輸出（Replit 從來冇產生過呢批檔）
- Column 順序：如 Replit schema 本身 stable 就完全對齊；如之前 drift 過，Capy 用 PINNED schema

### G. 感謝

感謝 Replit 團隊兩年來嘅 scraper 基建 —
- 5,827 匹馬嘅歷史 form 數據、
- 教練 / 騎師 aggregated CSV、
- Selenium 處理 HKJC 動態頁嘅 pattern，

都係 Capy 今日能夠快速重寫嘅基礎。交接書、phantom 清單、rate-limit 建議、D1 bug 分析，每一項都令 Capy 嘅工作輕咗好多。

呢個 baseline 之後，Capy 會以 `main` 上嘅 `docs/capy/handover_log.md` 做 journal，
每次主要 schema 或 endpoint 變動都記錄，保持你隨時可以 review / 介入。

如任何問題，用戶會 forward 畀我。

### H. GH_TOKEN 移交（避免 dual-write race condition）

Replit 現時用嘅 GH_TOKEN（scopes: `repo`, `workflow`）係 Capy 之前 flag 過「太闊」嘅 token。Phase 2 cutover 同時做 token 收緊，防止兩邊同時 push 造成 race condition。

**時序（hard-ordered，唔好打亂）：**

| T | 動作 | 執行者 |
|---|---|---|
| T-0 (cutover 時刻) | Tianxi 執行 `git merge --ff-only capy/scraper-v2` + push main | 用戶 |
| T+0min | Replit **revoke** 舊 GH_TOKEN（喺 https://github.com/settings/tokens） | Replit（或用戶代執行）|
| T+0min | Replit Reserved VM + scheduler 已喺 §A 停咗，即使有殘留 cron 都 push 唔到 | — |
| T+5min | Tianxi 生成**新 fine-grained PAT**（scopes 最小化：只需 `contents:write` + `actions:write` 對應 `HKJC-Horse-Racing-Results` repo，**唔需要 full `repo`**）| 用戶 |
| T+5min | 新 PAT 加入 GHA repo secrets 做 `CAPY_GH_TOKEN`，所有 `capy_*.yml` 已用呢個 name 讀取 | 用戶 |
| T+10min | Capy 手動 dispatch 任何一個 `capy_*.yml` 做 smoke test | Capy |

**唔好做嘅事：**
- ❌ 舊 token revoke 之前早啟用新 token → race
- ❌ 舊 token + 新 token 同時有效 → 兩邊 scraper 可能同時 commit，造成 merge conflict 或 duplicate row
- ❌ 新 token 用 classic PAT 或 full `repo` scope → 安全倒退，違反最小權限原則

**Rollback 下 fine-grained PAT 夠唔夠？**
夠。`update-hkjc-scraper.yml` 只需要 `contents:write`（commit data）同 `actions:write`（自己 dispatch）。呢兩個 scope 同 Capy workflow 完全共用，rollback 唔需要再換 token。

— Capy, 2026-04-26

---

## 變量填充清單（send 之前全部 resolve）

| 變量 | 填法 |
|---|---|
| `{CUTOVER_ISO}` | 實際 cutover 時間，e.g. `2026-04-26T12:00Z` |
| `{BASELINE_SHA}` | `git rev-parse capy-handover-baseline-v1` 結果 |
| `{PARITY_CI_URL}` | GHA run URL of last green parity test |
| `{CUTOVER_DATE}` | YYYY-MM-DD |
| `{DATE_RANGE}` | Parity coverage 日期範圍 e.g. `2026-04-15 ~ 2026-04-25` |

## 發送後動作

- [ ] Tag 加 annotation: `git tag -a capy-owns-main-v1 -m "Capy takes main ownership from this SHA"`
- [ ] 更新 `docs/capy/handover_log.md` 加入 cutover 日誌
- [ ] `README.md` 頂部加 **badges + 細字 tagline**（唔加大 banner）：
      ```markdown
      ![Maintained by](https://img.shields.io/badge/scraper-Capy_GHA-blue)
      ![Phase](https://img.shields.io/badge/handover-phase_2_complete-green)

      > Active scraper runs via GitHub Actions since 2026-04-26. See [`docs/capy/handover_log.md`](docs/capy/handover_log.md).
      ```
- [ ] 14 日後（2026-05-10）review standby 期，考慮 archive old Replit scrapers（由 Tianxi 決定）
