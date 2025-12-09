from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from osm_function import POI, geocode
from ow_function import API_KEY, get_current_city_weather

BASE_DIR = Path(__file__).resolve().parent
MAP_FILE = BASE_DIR / "output.html"
TEMPLATES_DIR = BASE_DIR / "templates"


class LocationPayload(BaseModel):
    location: Optional[str] = None


app = FastAPI(title="Vietnam Explorer API")


@app.get("/", response_class=FileResponse)
def index():
    """Serve the React single page."""
    index_file = TEMPLATES_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="index.html not found.")
    return FileResponse(index_file)


@app.get("/poi", response_class=FileResponse)
def poi_page():
    """Serve SPA for the POI page (GET)."""
    return index()


@app.get("/weather", response_class=FileResponse)
def weather_page():
    """Serve SPA for the weather page (GET)."""
    return index()


@app.get("/map")
def map_view():
    if not MAP_FILE.exists():
        return JSONResponse(
            {"error": "Chưa có bản đồ nào được tạo. Hãy tìm kiếm một địa điểm để bắt đầu."},
            status_code=404,
        )
    return FileResponse(MAP_FILE)


@app.post("/poi")
def api_poi(payload: LocationPayload):
    location = (payload.location or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Vui lòng nhập địa điểm ở Việt Nam.")

    query = f"{location}, Việt Nam"
    try:
        lat, lon, display_name = geocode(query)
        POI(float(lat), float(lon), radius=1500, POI_count=5, output_path=str(MAP_FILE))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    map_url = f"/map?t={int(time.time())}"
    return {
        "displayName": display_name or location,
        "mapUrl": map_url,
        "message": f"Đang hiển thị quán cà phê quanh {display_name or location}.",
    }


@app.post("/weather")
def api_weather(payload: LocationPayload):
    location = (payload.location or "").strip()
    if not location:
        raise HTTPException(status_code=400, detail="Vui lòng nhập địa điểm để xem thời tiết.")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="Thiếu OPENWEATHER_API_KEY. Vui lòng cấu hình .env.")

    try:
        data = get_current_city_weather(location, API_KEY)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return {
        "location": data.get("name") or location,
        "description": (data.get("weather") or [{}])[0].get("description"),
        "temp": (data.get("main") or {}).get("temp"),
        "humidity": (data.get("main") or {}).get("humidity"),
        "feels_like": (data.get("main") or {}).get("feels_like"),
        "wind_speed": (data.get("wind") or {}).get("speed"),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        reload=True,
    )
