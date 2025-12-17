# Location Web

A FastAPI-backed mini toolkit for location-based utilities with lightweight static pages. It lets you search nearby cafes via OpenStreetMap, check live weather via OpenWeather, translate any text to Vietnamese, and demo Firebase email/password login.

## Features
- Home landing page linking to all tools.
- Nearby cafe search: geocode an address, query Overpass API for cafes, and plot them with Leaflet.
- Weather lookup: OpenWeather current conditions (temp, humidity, wind, description).
- Text translation: translate arbitrary text to Vietnamese using `deep-translator`.
- Firebase auth demo: `POST /api/login` to sign in with email/password and return tokens.
- Health check endpoint for uptime probes.

## Project layout
- `backend/app.py` – FastAPI app with page routes and API endpoints.
- `backend/osm_function.py` – Nominatim geocoding and Overpass POI lookup helpers.
- `backend/ow_function.py` – OpenWeather calls for current conditions and forecasts.
- `backend/translate.py` – GoogleTranslator wrapper to Vietnamese.
- `backend/firebase_function.py` – Firebase Auth config and login helper.
- `frontend/*.html` – Static pages for home, POI, weather, and translate flows.
- `run.sh` – Convenience script to start Uvicorn in reload mode.

## Prerequisites
- Python 3.12+ (includes shim for requests on 3.13).
- API keys: OpenWeather and Firebase project credentials.

## Setup
1) Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Add environment variables (root `.env` is loaded automatically). Never commit secrets.
```bash
# OpenWeather
OPENWEATHER_API_KEY=your_openweather_key

# Firebase Auth (email/password)
FIREBASE_API_KEY=your_api_key
FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
FIREBASE_PROJECT_ID=your_project_id
FIREBASE_STORAGE_BUCKET=your_project.appspot.com
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
FIREBASE_MEASUREMENT_ID=G-xxxxxxxxxx          # optional
FIREBASE_DATABASE_URL=https://your-db.firebaseio.com  # optional
```

## Running locally
```bash
# From the repo root
./run.sh
# or
uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```
Then open `http://localhost:8000` for the landing page, or the specific tools:
- `http://localhost:8000/poi`
- `http://localhost:8000/weather`
- `http://localhost:8000/translate`

## API reference
- `POST /api/poi` – Body: `{ "query": "<address>", "radius": 1000, "count": 10 }`. Returns geocoded location and cafes from Overpass.
- `POST /api/weather` – Body: `{ "city": "<city name>" }`. Returns current conditions from OpenWeather.
- `POST /api/translate` – Body: `{ "text": "<any text>" }`. Returns Vietnamese translation.
- `POST /api/login` – Body: `{ "email": "...", "password": "..." }`. Uses Firebase email/password auth.
- `GET /health` – Simple status payload.

## Notes
- Frontend pages are served directly by FastAPI; no build step is required.
- The project performs external HTTP calls (OSM/Overpass, OpenWeather, translation provider, Firebase); ensure outbound network access when running locally.
