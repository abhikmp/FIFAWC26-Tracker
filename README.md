# WC26 Tracker

FIFA World Cup 2026 live standings tracker, powered by api-football.com.

## Local development

```bash
pip install -r requirements.txt
API_FOOTBALL_KEY=your_key_here uvicorn server:app --reload --port 8000
```

Open http://localhost:8000

## Deploy to Render (free)

1. Push this repo to GitHub
2. Go to https://render.com → New → Web Service
3. Connect your GitHub repo
4. Set these:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn server:app --host 0.0.0.0 --port $PORT`
5. Add environment variable:
   - Key: `API_FOOTBALL_KEY`
   - Value: your api-football.com key
6. Click Deploy

## API endpoints

| Endpoint | Description |
|---|---|
| `GET /api/refresh` | Fetch fresh data from api-football (costs 3 calls) |
| `GET /api/cache` | Return last cached data (free, no API call) |
| `GET /api/status` | Show quota and cache status |

## Budget

- 3 API calls per manual refresh
- 100 calls/day on free tier = ~33 refreshes per day
- Cache persists between refreshes so page loads are free
