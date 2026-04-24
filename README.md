# 天喜數據庫 · Tianxi Database

> **香港賽馬 AI 數據平台** — 2016–2026 全量歷史賽果 + 每日自動更新 + Elo rating pipeline，開箱即用嘅 backend-as-CSV 數據層。

[![Pool B](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_pool_b_daily.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_pool_b_daily.yml)
[![Race Day](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_race_daily.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_race_daily.yml)
[![Trainer](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_trainer_fix.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_trainer_fix.yml)
[![Fixture](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_fixture_weekly.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_fixture_weekly.yml)
[![Elo v1.1](https://github.com/sleepingarhat/tianxi-database/actions/workflows/elo-v11.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/elo-v11.yml)
[![Sanity](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_sanity_daily.yml/badge.svg)](https://github.com/sleepingarhat/tianxi-database/actions/workflows/capy_sanity_daily.yml)

---

## 亮點 (TL;DR)

| 指標 | 規模 |
|---|---|
| 歷史賽果年份 | **2016 – 2026**（11 年） |
| 總賽果 row 數 | **~67,000 場次** |
| 馬匹 Profile | **1,889 匹** |
| Form 往績檔 | **1,899 份** |
| 練馬師 Profile | **67 位** |
| 騎師 Profile | **~100 位** |
| 2025-2026 Fixture 日曆 | **152 場** 預先落 cache |
| 每日自動更新 workflow | **7 條** |
| 結構化數據總 size | **~88 MB** CSV (`utf-8-sig`) |

**所有數據** 直接由 GitHub raw endpoint 讀取 —— 前端可當 CDN，零 server 運維。

---

## 點解存在？

香港賽馬會（HKJC）官方只出 SPA + PDF，冇結構化 API。
天喜數據庫把 11 年公開賽果「抽象化」成標準 CSV schema，每日自動刷新，為下游 AI 產品（評分模型、選馬助手、賠率分析）提供穩定數據層。

- ✅ **全自動** — GitHub Actions cron + 賽事日曆感知調度
- ✅ **自愈** — 每日 sanity dashboard 監察 48h 成功率 + 數據新鮮度
- ✅ **零 vendor lock** — 所有 artefact 係純 CSV，Python / R / SQL / Excel 即開即用
- ✅ **Idempotent** — 已存在檔案會 skip，安全 re-run

---

## 架構一覽

```
┌──────────────────────────────────────────────────────────────┐
│                  HKJC 官方網站 (SPA + SSR)                    │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│  GitHub Actions Orchestrator (天喜數據庫 · 7 個 workflow)      │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Pool A      │  │  Pool B      │  │  Race Day    │        │
│  │  馬匹 DB      │  │  試閘/排位/   │  │  賽果        │        │
│  │  (日 delta)  │  │  騎師/練馬師  │  │  (race day)  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Trainer     │  │  Fixture     │  │  Elo v1.1    │        │
│  │  Refresh     │  │  Weekly      │  │  Rating      │        │
│  │  (SPA fix)   │  │  (年曆 cache) │  │  (post-proc) │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                              │
│                  Fixture Guard (pre-flight)                  │
│          checks data/fixtures/ 前先決定跑唔跑                │
│                                                              │
│            Daily Sanity Dashboard → reports/SANITY.md        │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│          Git main branch (CSV artefacts, utf-8-sig)          │
│                                                              │
│   data/20{16..26}/   horses/profiles/   trainers/            │
│   data/fixtures/     horses/form_records/   jockeys/         │
│   entries/           horses/trackwork/      trials/          │
└──────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│      下游產品 (前端 / ML / Backtest / BI dashboard)           │
│      直接 fetch `raw.githubusercontent.com/...csv`           │
└──────────────────────────────────────────────────────────────┘
```

---

## 運作邏輯

### 1. 調度策略（Calendar-Aware Scheduling）

每條 workflow 開工前先行 `scripts/fixture_guard.sh --window N --direction past|future|any`，
讀 `data/fixtures/YYYY_fixtures.csv` 確認「今日或相關窗口有冇賽日」。

| Workflow | Cron (HK) | Fixture Guard | 目的 |
|---|---|---|---|
| Pool B Daily | 02:00 | 冇 | 試閘/排位/騎師/練馬師 delta |
| Pool A Daily | 04:00 | ≥4/27 cutover + 昨日有賽 | 馬匹 DB delta |
| Race Day | 賽日晚 19:30 / 23:30 | 今日有賽 | 抓當日賽果 |
| Entries | 賽日早 09:00 | 明日有賽 | 排位表 |
| Trainer | 01:00 | 過去 2 日有賽 | 練馬師 SPA refresh |
| Fixture Weekly | 週日 HK 13:15 | 冇 | 更新年曆 cache（24 個月） |
| Sanity Daily | 10:03 | 冇 | 生成 reports/SANITY.md |

**結果:** 非賽日自動跳過，每月節省 ~60% GHA minutes，同時防 HKJC rate limit。

### 2. 數據層 (Data Artefacts)

```
data/
├── fixtures/                    # 年曆 + 賽日 cache
│   ├── fixtures.csv             # 152 rows (2025-2026)
│   └── 2026_fixtures.csv
├── 2016/ … 2026/                # 每年賽果
│   ├── results_YYYY-MM-DD.csv   # 25-col 固定 schema
│   └── commentary_YYYY-MM-DD.csv
horses/
├── profiles/horse_profiles.csv  # 1,889 匹馬（動態列，label match）
├── form_records/form_XXXX.csv   # 1,899 份（21-col schema）
├── trackwork/                   # 晨操
└── injury/                      # 傷患
trainers/
├── trainer_profiles.csv         # 67 位（dedup-clean，keep=last）
└── records/                     # 往績
jockeys/
├── jockey_profiles.csv
└── records/jockey_*.csv         # 19-col + 延伸
trials/trial_results.csv         # 18-col 試閘
entries/                         # 當日排位表
reports/SANITY.md                # 每日健康報告
```

所有 CSV：**UTF-8-BOM** (Excel-friendly) · **Schema 穩定** · **Column order pinned**。

### 3. 評分層 (Elo v1.1)

`.elo-pipeline/` Node.js sub-project，每次 race result commit 後觸發，計算每匹馬 Elo rating 增減，結果 commit 返 repo。

---

## 快速上手（下游用戶）

### Python

```python
import pandas as pd

BASE = "https://raw.githubusercontent.com/sleepingarhat/tianxi-database/main"

# 讀 2025 年某場賽果
df = pd.read_csv(f"{BASE}/data/2025/results_2025-09-07.csv", encoding="utf-8-sig")

# 讀全部 1,889 匹馬 profile
horses = pd.read_csv(f"{BASE}/horses/profiles/horse_profiles.csv", encoding="utf-8-sig")

# 讀練馬師
trainers = pd.read_csv(f"{BASE}/trainers/trainer_profiles.csv", encoding="utf-8-sig")
```

### JavaScript / Frontend

```javascript
const BASE = "https://raw.githubusercontent.com/sleepingarhat/tianxi-database/main";
const res  = await fetch(`${BASE}/data/fixtures/fixtures.csv`);
const text = await res.text();
// parse with PapaParse / d3.csvParse / etc.
```

### GitHub Actions (下游 CI)

```yaml
- uses: actions/checkout@v4
  with: { repository: sleepingarhat/tianxi-database, path: tianxi-data }
- run: ls tianxi-data/data/2026/
```

---

## 健康監察

- **每日 10:03 HK** sanity workflow 自動生成 `reports/SANITY.md`：
  - 7 條 workflow 近 5 run 狀態 + 48h 成功次數
  - 關鍵 artefact 最後 commit + row count
  - 今日 fixture（race day / non-race day）
- 查閱最新狀態：[reports/SANITY.md](./reports/SANITY.md)

---

## Roadmap

- [x] Replit scraper → GitHub Actions 遷移（P0 pivot）
- [x] Calendar-aware scheduling（fixture guard）
- [x] Sanity dashboard (daily poll)
- [x] Elo v1.1 batch
- [ ] **Pool A 自動化 cutover @ 2026-04-27** (Replit first-pass 完成後)
- [ ] Baseline tag `capy-handover-baseline-v1` @ 2026-04-26 12:00 UTC
- [ ] Replit Reserved VM 停機（cutover 成功後）
- [ ] Elo v2（多因子 + 場地修正）
- [ ] Public read-only API wrapper（Cloudflare Worker）

---

## 許可 & 使用條款

HKJC 原始賽果為公開資訊，本 repo 只做 **結構化重組** 與 **schema 穩定化**，不包括 HKJC 圖片、影片、或任何付費 pool 數據。下游使用請尊重 HKJC 原站 rate contract（≥0.4 req/s）。本 repo 內部爬取已限流 ~0.5-2.5 req/s，一個月未觸發封鎖。

---

## 技術支援

- GHA 狀態：<https://github.com/sleepingarhat/tianxi-database/actions>
- 每日 sanity：[reports/SANITY.md](./reports/SANITY.md)
- Cutover 進度：[plan.md](./plan.md)
- P0 pivot decision log：[CAPY_P0_PIVOT.md](./CAPY_P0_PIVOT.md)
- Handover cutoff reference：[HANDOVER.md](./HANDOVER.md)

*Maintained by Capy / GitHub Actions · 原 Replit-side VM 預計 2026-04-27 停機。*
