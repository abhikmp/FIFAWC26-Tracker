import os
import json
import time
import httpx
from datetime import datetime, timezone
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

API_KEY = os.environ.get("API_FOOTBALL_KEY", "9d927a55f894b4f89aaec6bc8df1cc42")
API_BASE = "https://v3.football.api-sports.io"
LEAGUE_ID = 1
SEASON = 2026
DAILY_LIMIT = 100
CACHE_FILE = "cache.json"

HEADERS = {
    "x-apisports-key": API_KEY,
}


def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            return json.load(f)
    return {
        "data": None,
        "last_updated": None,
        "calls_today": 0,
        "calls_reset_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "calls_remaining": DAILY_LIMIT,
    }


def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f)


def check_and_reset_daily_calls(cache):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if cache.get("calls_reset_date") != today:
        cache["calls_today"] = 0
        cache["calls_reset_date"] = today
        cache["calls_remaining"] = DAILY_LIMIT
    return cache


async def fetch_api(client, endpoint, params=None):
    url = f"{API_BASE}/{endpoint}"
    r = await client.get(url, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()

    # Read remaining from response headers if available
    remaining = r.headers.get("x-ratelimit-requests-remaining")
    limit = r.headers.get("x-ratelimit-requests-limit")

    data = r.json()
    return data, remaining, limit


async def fetch_all_data():
    cache = load_cache()
    cache = check_and_reset_daily_calls(cache)

    # We make 3 API calls per refresh
    if cache["calls_remaining"] < 3:
        return None, cache, "insufficient_quota"

    async with httpx.AsyncClient() as client:
        try:
            # Call 1: standings (all 12 groups)
            standings_data, remaining, limit = await fetch_api(
                client, "standings", {"league": LEAGUE_ID, "season": SEASON}
            )
            cache["calls_today"] += 1

            # Call 2: top scorers (golden boot)
            scorers_data, remaining, limit = await fetch_api(
                client, "players/topscorers", {"league": LEAGUE_ID, "season": SEASON}
            )
            cache["calls_today"] += 1

            # Call 3: fixtures for knockout rounds (R32 onwards)
            fixtures_data, remaining, limit = await fetch_api(
                client, "fixtures", {"league": LEAGUE_ID, "season": SEASON}
            )
            cache["calls_today"] += 1

            # Update remaining from API headers (most accurate)
            if remaining is not None:
                cache["calls_remaining"] = int(remaining)
            else:
                cache["calls_remaining"] = DAILY_LIMIT - cache["calls_today"]

            result = {
                "standings": standings_data.get("response", []),
                "scorers": scorers_data.get("response", []),
                "fixtures": fixtures_data.get("response", []),
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "calls_remaining": cache["calls_remaining"],
                "calls_used_today": cache["calls_today"],
            }

            cache["data"] = result
            cache["last_updated"] = result["fetched_at"]
            save_cache(cache)

            return result, cache, "ok"

        except httpx.HTTPError as e:
            save_cache(cache)
            return None, cache, f"http_error: {str(e)}"
        except Exception as e:
            save_cache(cache)
            return None, cache, f"error: {str(e)}"


@app.get("/api/refresh")
async def refresh():
    data, cache, status = await fetch_all_data()

    if status == "insufficient_quota":
        return JSONResponse(
            status_code=429,
            content={
                "error": "Daily API quota too low to refresh (need 3 calls).",
                "calls_remaining": cache.get("calls_remaining", 0),
            },
        )

    if status != "ok" or data is None:
        # Return cached data with error note if we have it
        if cache.get("data"):
            return JSONResponse(
                content={
                    **cache["data"],
                    "error": status,
                    "from_cache": True,
                }
            )
        raise HTTPException(status_code=502, detail=status)

    return JSONResponse(content=data)


@app.get("/api/cache")
async def get_cache():
    """Return cached data without making any API calls."""
    cache = load_cache()
    cache = check_and_reset_daily_calls(cache)

    if cache.get("data"):
        return JSONResponse(
            content={
                **cache["data"],
                "from_cache": True,
                "calls_remaining": cache.get("calls_remaining", DAILY_LIMIT),
            }
        )

    return JSONResponse(
        content={
            "data": None,
            "calls_remaining": cache.get("calls_remaining", DAILY_LIMIT),
            "message": "No cached data yet. Click refresh to load.",
        }
    )


@app.get("/api/status")
async def status():
    cache = load_cache()
    cache = check_and_reset_daily_calls(cache)
    return {
        "calls_today": cache.get("calls_today", 0),
        "calls_remaining": cache.get("calls_remaining", DAILY_LIMIT),
        "last_updated": cache.get("last_updated"),
        "has_data": cache.get("data") is not None,
    }


# Serve static frontend
app.mount("/", StaticFiles(directory="static", html=True), name="static")
