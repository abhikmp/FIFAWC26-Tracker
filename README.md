# WC26 Tracker ⚽

A lightweight, dark-mode web app for tracking the FIFA World Cup 2026 — group standings, 3rd place rankings, golden boot/glove leaderboards, and a projected knockout bracket, all in one page.

---

## What it does

The FIFA World Cup 2026 expands to 48 teams across 12 groups, making it harder than ever to keep track of who's qualifying and where teams stand. WC26 Tracker pulls live data from the [api-football.com](https://www.api-football.com/) API and presents everything you need on a single, clean page — no ads, no clutter.

---

## Features

### Group Standings
All 12 groups (A through L) in one card. Use the letter pills or the left/right arrows to jump between groups. Shows MP, W, D, L, GF, GA, GD, Pts, and last-5 form for every team. A green qualifying line marks the top 2 who advance automatically.

### 3rd Place Leaderboard
All 12 third-placed teams ranked against each other by points, then goal difference. The top 8 qualify for the Round of 32. Top 8 are highlighted in green with a cutoff line marking the qualification boundary — critical in a 12-group tournament where 8 of 12 third-place teams go through.

### Golden Boot / Golden Glove
Toggle between the top scorers (golden boot) and top goalkeepers (golden glove), pulled live from the API.

### Projected Knockout Bracket
A full R32 → R16 → QF → SF → Final bracket, horizontally scrollable, built from the official FIFA match numbering (M73–M104). R32 slots are populated with real projected teams based on current standings, including the complex "best 3rd from groups ABCDF" style slots resolved using the official Annexe C combinations. Later rounds show match winner references since those can't yet be determined.

### Manual Refresh with Quota Tracker
Data refreshes only when you click the Refresh button — no background polling, no wasted API calls. Each refresh costs exactly 3 API calls (standings + scorers + fixtures). A pill in the top-right corner shows how many calls you have left today, turning yellow when low and red when critical.

### Smart Caching
The backend caches the last successful API response to disk. Page loads always serve from cache instantly — the API is only hit when you explicitly refresh. Cache survives server restarts.

---

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla HTML/CSS/JS, single file, no framework |
| Backend | Python, FastAPI |
| Data | api-football.com v3 API |
| Hosting | Render (free tier) |

---

## Running locally

You need Python 3.8+ installed.

**1. Install dependencies**
```bash
pip install -r requirements.txt
```

**2. Start the server**

macOS / Linux:
```bash
API_FOOTBALL_KEY=your_key uvicorn server:app --reload --port 8000
```

Windows (PowerShell):
```powershell
$env:API_FOOTBALL_KEY="your_key"
uvicorn server:app --reload --port 8000
```

Windows (Command Prompt):
```cmd
set API_FOOTBALL_KEY=your_key
uvicorn server:app --reload --port 8000
```

**3. Open the app**

Go to http://localhost:8000 and click **Refresh** to load data.

**Useful endpoints for debugging:**
- http://localhost:8000/api/status — quota and cache info
- http://localhost:8000/api/cache — current cached data as JSON

---

## Deploying to Render

1. Push this repo to GitHub
2. Go to [render.com](https://render.com) → New → Web Service
3. Connect your GitHub repo
4. Configure:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add environment variable: `API_FOOTBALL_KEY` → your api-football.com key
6. Deploy — you'll get a free `.onrender.com` URL

> **Note:** Render's free tier spins down after 15 minutes of inactivity. The first visit after idle may take 20–30 seconds to wake up. Data will be served from cache as soon as the server is up.

---

## API call budget

| Action | Calls used |
|---|---|
| Page load (from cache) | 0 |
| Manual refresh | 3 |
| Free tier daily limit | 100 |
| **Max refreshes per day** | **~33** |

---

## Project structure

```
wc26-tracker/
├── server.py          ← FastAPI backend, caching, API integration
├── requirements.txt
├── render.yaml        ← Render deployment config
├── .gitignore
└── static/
    └── index.html     ← Entire frontend (one file, no build step)
```
