# 天喜數據庫 · 實施計劃 & 當前狀態

**最後更新:** 2026-04-24
**版本:** Post Step-B (calendar-aware scheduling + sanity dashboard landed)
**下一個里程碑:** 2026-04-27 Pool A cutover

---

## A · 當前狀態（Backend 邏輯層）

### A1 · Workflow matrix (7 條 auto + 1 disabled)

| # | Workflow | Cron (HK) | Fixture Guard | 狀態 | 近 48h |
|---|---|---|---|---|---|
| 1 | `capy_pool_b_daily.yml` | 02:00 | – | ✅ auto | 2/2 success |
| 2 | `capy_pool_a.yml` | 04:00（gate ≥ 4/27）| 昨日有賽 + ≥4/27 cutover | ⏸ manual-only | 0 run (intentional) |
| 3 | `capy_race_daily.yml` | 賽日 15:30/11:30 UTC | 今日有賽 | ✅ auto | 1/1 success |
| 4 | `capy_entries.yml` | 賽前 03:00 UTC | 明日有賽 | ✅ auto | 1/1 success |
| 5 | `capy_trainer_fix.yml` | 01:00 | 過去 2 日有賽 | ✅ auto | 2/2 success |
| 6 | `capy_fixture_weekly.yml` | 週日 13:15 | – | ✅ auto | 2/2 success |
| 7 | `capy_sanity_daily.yml` | 10:03 | – | ✅ auto | 1/1 success (hotfix 後) |
| – | `update-hkjc-scraper.yml.disabled` | – | – | 🗑 deprecated | – |
| – | `elo-v11.yml` | on push to data/* | – | ✅ auto | green |

### A2 · 數據層規模（2026-04-24 量測）

```
data/             77 MB    ~67,000 race rows across 11 years (2016-2026)
horses/           9.5 MB   1,889 profiles + 1,899 form_records + trackwork + injury
trainers/         8 KB     67 profiles
jockeys/          456 KB   ~100 profiles + records
trials/           992 KB   試閘結果
entries/          20 KB    當日排位表
data/fixtures/    –        152 rows (2025-2026)
```

### A3 · 自動化覆蓋

- **當前:** 6/7 workflow 全自動（Pool A gate 住）
- **4/27 起:** 7/7 全自動
- **人手介入:** 零（除非 sanity dashboard 亮紅）

---

## B · 已完成里程碑

### B0 · P0 Pivot（2026-04-23, commit `133f714`）
- ✅ 放棄 httpx + SPA parser rewrite，改 reuse Replit 原生 selenium scraper
- ✅ GHA orchestrates `RunAll_Scrapers.py` + `RacingData_Scraper.py`
- ✅ `scraper_utils.py` 加 env override (`CHROMIUM_PATH` / `CHROMEDRIVER_PATH`)
- ✅ 7 個新 workflow 上線：`capy_pool_a/b`, `capy_race_daily`, `capy_entries`, `capy_trainer_fix`, `capy_fixture_weekly`, `capy_sanity_daily`

### B1 · RacingData hotfix（2026-04-24, commit `7e942a1`）
- ✅ 將 Replit 低 RAM flag (`--single-process`, `--max-old-space-size=128`) gated behind `LOW_MEMORY=1` env
- ✅ GHA 7GB runner 唔再 Chrome session crash

### B2 · Fixture calendar rewrite（2026-04-24, commit `1a6c51b` / `fa76a88`）
- ✅ `FixtureCalendar_Scraper.py` 由 Selenium 換 httpx + regex（zero-pad calmonth）
- ✅ Weekly workflow stdlib + httpx 夠，冇 Chrome overhead

### B3 · Step B（2026-04-24, commit `6094164`）
- ✅ `scripts/fixture_guard.sh` shared helper, fail-open
- ✅ Pool A cron + hard cutover guard `TODAY >= 2026-04-27`（dispatch `force=true` 可 bypass）
- ✅ Entries: tomorrow-race window
- ✅ Pool B daily: ±2-day window
- ✅ Trainer: past-2-day window
- ✅ `capy_sanity_daily.yml` 每日 10:03 HK 跑，生成 `reports/SANITY.md`

### B4 · Sanity fix（2026-04-24, commits `8dec668`, `c9f8e1c`）
- ✅ 去除 em-dash（GHA YAML parse 會 silent fail 到 422）
- ✅ 將 multi-line `python3 -c` flatten 做 single-line + single-quote wrap

### B5 · Elo v1.1 self-heal（2026-04-23, commit `a2ac07a`）
- ✅ Summarize step `continue-on-error: true`
- ✅ Runs #4, #5 green

### B6 · Repo rebrand（2026-04-24, 本次）
- ✅ 改名：`HKJC-Horse-Racing-Results` → `tianxi-database`
- ✅ Description: `天喜數據庫 · 香港賽馬 AI 數據平台`
- ✅ Topics: horse-racing / hkjc / hong-kong / data-pipeline / github-actions / elo-rating / sports-analytics / tianxi
- ✅ 舊 URL GitHub 自動 301 redirect（workflow / origin / 下游 integrations 零 break）
- ✅ 新 README.md（面向用戶，清晰運作邏輯）

---

## C · Pending（4/27 cutover window）

### C1 · Pool A cutover（2026-04-27）

**為何 4/27:**
1. Replit Reserved VM 仲跑緊 horse-DB first-pass（~3000 匹馬 × 25 小時 / 迴圈）
2. 預計 ~4/27 前完成 first-pass
3. 4/27 係非賽日 → 乾淨 cutover 窗口
4. 避免雙 scrape 同時打 HKJC（= 4 Chrome sessions，一定撞 rate limit）
5. 避免 CSV write conflict（同一 file 兩邊 push）

**步驟:**
- [ ] 4/26 12:00 UTC: Replit 做 final `git_sync` + tag `capy-handover-baseline-v1`
- [ ] 4/26: Replit Reserved VM 降頻（Pool A/B 間加 `sleep 600`）or 停機
- [ ] 4/27 00:00 HK: `capy_pool_a.yml` fixture guard 自動解除（`TODAY >= 2026-04-27`）
- [ ] 4/27 04:00 HK: 第一次 auto Pool A delta run
- [ ] 4/27 10:03 HK: Sanity dashboard confirm Pool A 48h 進入統計
- [ ] 4/28-5/4: 7 日 parity window，每日監察 SANITY.md
- [ ] 5/4: Replit 正式停 Reserved VM，歸檔 repo

### C2 · Parity exit criteria（4 個全要 pass）

1. Trainer fix: 67 trainers 全 profile + 完整 `records/` dir
2. Entries: GHA `racecard` CSV row-by-row = Replit `EntryList/*.csv`
3. Race day: 4/22, 4/26, 4/29 賽果 cell-level diff = 0
4. Horse form: 10 sample `form_XXXX.csv` 21-col 100% 相同

### C3 · Replit-side 退場

- [ ] Phase 1 停機：Replit Deployment → Stop
- [ ] Phase 2 撤銷 Replit-side `GH_TOKEN`
- [ ] Phase 3（≥1 個月後）Archive Replit project（不刪除，保留 history）

---

## D · 未來 Roadmap（post-cutover）

### D1 · 數據擴展
- [ ] Elo v2：多因子 model（場地、距離、馬場狀態）
- [ ] Trainer stats 完整 scrape（HKJC SPA stats parsing 現時失敗，silently 得 2 col）
- [ ] `horses/profiles/horse_profiles.csv` dynamic column 正規化
- [ ] 退役馬名尾 `(已退役)` suffix 自動 strip

### D2 · API 層
- [ ] Cloudflare Worker read-only proxy，畀非公開 repo 情況用
- [ ] JSONL export（畀 streaming 用家）
- [ ] Parquet mirror（畀 ML pipeline）

### D3 · 下游產品
- [ ] 前端 dashboard（直 fetch raw CSV）
- [ ] 選馬 AI 助手（基於 Elo + Form + Trackwork signal）
- [ ] Backtest framework（評估 rating model 長線準確度）

---

## E · Runbook 快速索引

| 情境 | 檔案 |
|---|---|
| 新人上手 | [README.md](./README.md) |
| 今日系統健康 | [reports/SANITY.md](./reports/SANITY.md) |
| 歷史 handover 記錄 | [HANDOVER.md](./HANDOVER.md) |
| P0 pivot 決策 log | [CAPY_P0_PIVOT.md](./CAPY_P0_PIVOT.md) |
| 開發日誌 | [BUILD_JOURNAL.md](./BUILD_JOURNAL.md) |
| Data schema 細節 | [DATA_NOTES.md](./DATA_NOTES.md) |
| 本計劃（狀態 + roadmap）| plan.md（本檔）|

### E1 · 手動觸發 workflow

```bash
# Dispatch Pool A（4/27 前 force 模式）
gh workflow run capy_pool_a.yml -f force=true

# Dispatch race day（任何日 manual smoke test）
gh workflow run capy_race_daily.yml

# Dispatch fixture refresh（24 個月）
gh workflow run capy_fixture_weekly.yml
```

### E2 · 查錯順序

1. 查 [`reports/SANITY.md`](./reports/SANITY.md) — 今日狀態一頁睇
2. GitHub Actions tab → 過濾 failed run → 睇 log
3. 如果 Chrome crash → 睇係咪又 trigger 咗 `LOW_MEMORY` 路徑（唔應該）
4. 如果 rate limit → 檢查有冇雙端同時跑（Replit + GHA）
5. 如果 fixture cache stale → 手動 dispatch `capy_fixture_weekly.yml`

---

*本 plan.md 係 living doc。每個里程碑 landed 後應即時更新。*
