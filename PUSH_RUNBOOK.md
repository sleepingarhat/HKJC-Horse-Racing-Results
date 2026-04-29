# GitHub Push Runbook · 2026-04-29

> 呢份係你本地手動執行。Sandbox 無 gh auth、無法代 push。

## 前置

```bash
# 1. GitHub PAT with repo scope
export GITHUB_TOKEN="ghp_xxxxxxxxxx"
gh auth login --with-token <<< "$GITHUB_TOKEN"

# 2. 確認 remotes 已設
cd hkjc-data && git remote -v     # 應見 sleepingarhat/tianxi-database
cd ../outputs/tianxi-v2 && git remote -v  # 若未 init 見下文
```

---

## Repo 1 · `sleepingarhat/tianxi-database`（scraper + ELO pipeline）

從 `hkjc-data/` 目錄：

```bash
cd hkjc-data

# 改動 staging
git add RacingData_Scraper.py \
        .github/workflows/capy_race_daily.yml \
        .github/workflows/elo-post-race.yml

git commit -m "fix(scraper): resolve CHROMIUM_PATH via env with fallback chain

- RacingData_Scraper.py: env var → system paths → Nix default
- capy_race_daily.yml: pre/post mtime sanity check; fail loud on silent failures
- elo-post-race.yml (new): workflow_run auto-trigger + reconcile.db commit + D1 ingest chain

Fixes 14-day silent data gap (2026-04-15 → 2026-04-28).
Closes #TBD"

git push origin main
```

將 ROADMAP.md + DEV_JOURNAL_2026-04-29.md 都 copy 入 repo：

```bash
cp ../outputs/ROADMAP.md ../outputs/DEV_JOURNAL_2026-04-29.md docs/
git add docs/
git commit -m "docs: 2026-04-29 session roadmap + journal"
git push origin main
```

### 觸發 backfill

```bash
gh workflow run capy_race_daily.yml --repo sleepingarhat/tianxi-database --ref main
# 等 scraper 跑完（~15-25 min）→ 觀察 Actions tab
# 成功後 elo-post-race 會自動 fire
```

驗證：
```bash
# CSV 數量應增加至覆蓋 2026-04-16 ~ 2026-04-28
gh api "repos/sleepingarhat/tianxi-database/contents/data/2026?ref=main" \
  | jq '.[].name' | grep 'results_2026-04' | sort -u
```

---

## Repo 2 · `sleepingarhat/tianxi-frontend`（v2 React app）

⚠️ 呢個倉庫依家存 v1 (Next.js) · v2 係新 app。兩個選擇：

### 選項 A · 新分支 `v2` 推上現有 repo

```bash
cd outputs/tianxi-v2

# 首次 init
git init
git remote add origin git@github.com:sleepingarhat/tianxi-frontend.git
git fetch origin
git checkout -b v2

# 加 .gitignore
cat > .gitignore <<'EOF'
node_modules
dist
.env.local
.env
.vite
*.log
.DS_Store
EOF

git add -A
git commit -m "feat(v2): Magic UI shell + env-gated API client + 3-level nav

- 19 Magic UI components (RainbowButton / AuroraText / BorderBeam / ...)
- 3 pages: Home / Race / Horse (HKJC-style 3-level navigation)
- Flat light-only design per 2026-04-28 constitution
- src/lib/api.ts: typed fetch wrapper with ApiError
- src/lib/hooks.ts: useNextMeeting / useRace / useHorseExplain
- src/data/mock.ts: env-gated dispatcher (VITE_USE_MOCK)
- 2026-04-29 predictions shipped as static JSON for offline preview"

git push -u origin v2
```

### 選項 B · 新 repo `tianxi-frontend-v2`

```bash
gh repo create sleepingarhat/tianxi-frontend-v2 --public \
  --description "天喜 TIANXI v2 · React + Vite + Magic UI" --confirm

# 然後同選項 A 一樣，但 remote 指向新 repo
```

---

## 部署

### Backend (Cloudflare Workers)

```bash
cd tianxi-backend
wrangler deploy
# 假設 worker name: tianxi-api
# URL: https://tianxi-api.<account>.workers.dev
```

### Frontend (Cloudflare Pages / Vercel)

**Cloudflare Pages**：
```bash
cd outputs/tianxi-v2
npm run build
wrangler pages deploy dist --project-name tianxi-v2
# 環境變數喺 Pages UI 設:
#   VITE_USE_MOCK=0
#   VITE_API_BASE_URL=https://tianxi-api.<account>.workers.dev
```

**Vercel**：
```bash
cd outputs/tianxi-v2
vercel deploy --prod
# 同樣喺 Vercel dashboard 設環境變數
```

---

## Post-push smoke test

```bash
# 1. 賽程更新到未來日
curl -s "https://tianxi-api.<account>.workers.dev/api/meetings/smart/current" | jq '.date'
# 期望: "2026-05-xx"（或下一個 race day）

# 2. Top picks 含 factor breakdown
RACE_ID=$(curl -s "https://tianxi-api.<account>.workers.dev/api/meetings/smart/current" | jq -r '.races[0].id')
curl -s "https://tianxi-api.<account>.workers.dev/api/analyze/top-picks?raceId=$RACE_ID" \
  | jq '.picks[0] | {name: .name_ch, elo: .eloComposite, fb: .factorBonus, pWin: .pWin}'

# 3. Explain endpoint 返 comment + factorBreakdown
HORSE_ID=$(curl -s "https://tianxi-api.<account>.workers.dev/api/analyze/top-picks?raceId=$RACE_ID" | jq '.picks[0].horse_id')
curl -s "https://tianxi-api.<account>.workers.dev/api/analyze/explain?raceId=$RACE_ID&horseId=$HORSE_ID" \
  | jq '.factorBreakdown, .comment'
```

---

## Rollback

如有問題：

```bash
# Scraper / ELO workflows
cd hkjc-data
git revert <commit-sha>  # 例：scraper patch
git push origin main

# Frontend v2
cd outputs/tianxi-v2
git checkout main  # 或 v1 branch
# v2 branch 留住，只係唔 deploy
```

---

## Monitoring to-do（非本次 scope · 下一 session）

- [ ] GHA workflow 失敗 → Slack / Email webhook
- [ ] D1 daily row count snapshot → 如果 meetings 表 lastDate > 48h 前 → alert
- [ ] tianxi-api /health endpoint + uptimerobot
