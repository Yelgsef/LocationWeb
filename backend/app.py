from __future__ import annotations

import collections
import collections.abc
from datetime import UTC, datetime
import sys
import types
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, EmailStr, Field

def _patch_requests_for_py313():
    """
    Shim missing urllib3 constants for the vendored requests copy on Python 3.13.
    This keeps other modules simple.
    """
    if not hasattr(collections, "MutableMapping"):  # pragma: no cover
        collections.MutableMapping = collections.abc.MutableMapping  # type: ignore[attr-defined]
    if not hasattr(collections, "MutableSet"):  # pragma: no cover
        collections.MutableSet = collections.abc.MutableSet  # type: ignore[attr-defined]
    if not hasattr(collections, "Mapping"):  # pragma: no cover
        collections.Mapping = collections.abc.Mapping  # type: ignore[attr-defined]
    if "requests.packages.urllib3.util.request" in sys.modules:
        return
    try:
        import urllib3.util.request as req_mod  # type: ignore
        if hasattr(req_mod, "SKIP_HEADER"):
            sys.modules["requests.packages.urllib3.util.request"] = req_mod
            sys.modules["requests.packages.urllib3.util"] = sys.modules.get("urllib3.util", req_mod)
            sys.modules["requests.packages.urllib3"] = sys.modules.get("urllib3")
            return
    except Exception:
        pass

    compat = types.ModuleType("urllib3.util.request")
    compat.SKIP_HEADER = frozenset(["accept-encoding", "host", "user-agent", "cookie"])
    compat.SKIPPABLE_HEADERS = compat.SKIP_HEADER

    def make_headers(
        keep_alive=None,
        accept_encoding=None,
        user_agent=None,
        basic_auth=None,
        proxy_basic_auth=None,
        disable_cache=None,
    ):
        headers = {}
        if keep_alive:
            headers["connection"] = "keep-alive"
        if accept_encoding:
            headers["accept-encoding"] = (
                accept_encoding if isinstance(accept_encoding, str) else "gzip,deflate"
            )
        if user_agent:
            headers["user-agent"] = user_agent
        if basic_auth:
            headers["authorization"] = f"Basic {basic_auth}"
        if proxy_basic_auth:
            headers["proxy-authorization"] = f"Basic {proxy_basic_auth}"
        if disable_cache:
            headers["cache-control"] = "no-cache"
        return headers

    compat.make_headers = make_headers  # type: ignore[attr-defined]
    sys.modules["urllib3.util.request"] = compat
    util_mod = types.ModuleType("requests.packages.urllib3.util")
    util_mod.request = compat  # type: ignore[attr-defined]
    sys.modules["requests.packages.urllib3.util"] = util_mod
    urllib3_mod = types.ModuleType("requests.packages.urllib3")
    urllib3_mod.util = util_mod  # type: ignore[attr-defined]
    sys.modules["requests.packages.urllib3"] = urllib3_mod
    sys.modules.setdefault("requests.packages", types.ModuleType("requests.packages")).urllib3 = urllib3_mod  # type: ignore[attr-defined]


_patch_requests_for_py313()

from .osm_function import _call_overpass, geocode
from .ow_function import API_KEY as OPENWEATHER_API_KEY, get_current_city_weather
from .translate import translate_to_vietnamese
from .firebase_function import sign_in_with_email_password

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


app = FastAPI(title="Location Web", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _frontend_page(name: str) -> FileResponse:
    """Serve a static HTML page from the frontend folder."""
    path = FRONTEND_DIR / name
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"Missing frontend page: {name}")
    return FileResponse(path)


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return _frontend_page("index.html")


@app.get("/poi", include_in_schema=False)
def poi_page() -> FileResponse:
    return _frontend_page("poi.html")


@app.get("/weather", include_in_schema=False)
def weather_page() -> FileResponse:
    return _frontend_page("weather.html")


@app.get("/translate", include_in_schema=False)
def translate_page() -> FileResponse:
    return _frontend_page("translate.html")


class POIRequest(BaseModel):
    query: str = Field(..., min_length=2, description="Tên địa điểm hoặc địa chỉ")
    radius: int = Field(1000, ge=100, le=5000, description="Bán kính tìm kiếm (m)")
    count: int = Field(10, ge=1, le=50, description="Số lượng quán cafe trả về")


class WeatherRequest(BaseModel):
    city: str = Field(..., min_length=2, description="Tên thành phố")


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Văn bản cần dịch")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Mật khẩu tối thiểu 6 ký tự")


@app.post("/api/poi")
def api_poi(payload: POIRequest):
    try:
        lat, lon, display_name = geocode(payload.query)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    overpass_query = f"""
    [out:json][timeout:25];
    nwr(around:{payload.radius},{lat},{lon})["amenity"="cafe"];
    out center {payload.count};
    """
    try:
        elements = _call_overpass(overpass_query)
    except Exception:
        raise HTTPException(status_code=502, detail="Không thể lấy dữ liệu POI ngay bây giờ.")

    cafes: List[dict] = []
    for item in elements[: payload.count]: # type: ignore
        tags = item.get("tags", {})
        cafe_name = tags.get("name") or "(không tên)"
        cafe_lat = item.get("lat") or item.get("center", {}).get("lat")
        cafe_lon = item.get("lon") or item.get("center", {}).get("lon")
        if cafe_lat is None or cafe_lon is None:
            continue
        cafes.append(
            {
                "name": cafe_name,
                "lat": float(cafe_lat),
                "lon": float(cafe_lon),
                "amenity": tags.get("amenity"),
                "address": tags.get("addr:full") or tags.get("addr:street"),
            }
        )

    return {
        "query": payload.query,
        "location": {"lat": float(lat), "lon": float(lon), "display_name": display_name},
        "cafes": cafes,
    }


@app.post("/api/weather")
def api_weather(payload: WeatherRequest):
    if not OPENWEATHER_API_KEY:
        raise HTTPException(status_code=500, detail="Thiếu biến môi trường OPENWEATHER_API_KEY.")
    try:
        data = get_current_city_weather(payload.city, OPENWEATHER_API_KEY)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    main = data.get("main", {})
    weather = (data.get("weather") or [{}])[0]
    coord = data.get("coord", {})

    return {
        "city": payload.city,
        "location": {"lat": coord.get("lat"), "lon": coord.get("lon")},
        "summary": weather.get("main"),
        "description": weather.get("description"),
        "icon": weather.get("icon"),
        "temperature": {
            "current": main.get("temp"),
            "feels_like": main.get("feels_like"),
            "min": main.get("temp_min"),
            "max": main.get("temp_max"),
        },
        "humidity": main.get("humidity"),
        "wind": data.get("wind"),
        "timestamp": datetime.fromtimestamp(data.get("dt", 0), tz=UTC).isoformat(),
    }


@app.post("/api/translate")
def api_translate(payload: TranslateRequest):
    try:
        translated = translate_to_vietnamese(payload.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return {"input": payload.text, "output": translated}


@app.post("/api/login")
def api_login(payload: LoginRequest):
    try:
        session = sign_in_with_email_password(payload.email, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    return session


@app.get("/health", include_in_schema=False)
def healthcheck():
    return {"status": "ok"}
