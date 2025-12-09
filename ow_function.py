import os
from datetime import datetime, UTC
from pathlib import Path

import requests
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
API_KEY = os.environ.get("OPENWEATHER_API_KEY")

def get_current_city_lat_lon(city_name: str, api_key: str) -> tuple:
  """This function get the latitude and longtitude of `city_name`"""
  url = "http://api.openweathermap.org/geo/1.0/direct"

  params = {
    "q": city_name,
    "limit": 1,               # Change this for more results
    "appid": api_key
  }

  response = requests.get(url, params=params)
  response.raise_for_status()
  data = response.json()      # Remember to parse to JSON!

  if len(data) == 0:
    raise Exception("No city found")

  else:
    # Return the coordinate of the first result.
    return data[0]["lat"], data[0]["lon"]
  
def get_current_city_weather(city_name: str, api_key: str) -> dict:
  """This function get the current weather of `city_name`."""

  url = "https://api.openweathermap.org/data/2.5/weather"

  # Since the API required latitude and longtitude of the city,
  city_lat, city_lon = get_current_city_lat_lon(
      city_name=city_name,
      api_key=api_key
  )

  params = {
    "lat": city_lat,
    "lon": city_lon,
    "APPID": api_key,
    "units": "metric",   # or "imperial", "standard"
  }

  response = requests.get(url, params=params)
  response.raise_for_status()
  data = response.json()

  return data


def get_3_hours_city_weather(city_name: str, api_key: str, cnt: int) -> dict:
  """This function get the weather forecast for the 5 days with data every 3 hours

  In professional applications, you should never hardcode (keep fixed) the API URL directly in your code.
  Instead, you should always define the API URL as a configuration or setting variable.
  """
  url = "https://api.openweathermap.org/data/2.5/forecast"

  # Since the API required latitude and longtitude of the city,
  city_lat, city_lon = get_current_city_lat_lon(
      city_name=city_name,
      api_key=api_key
  )

  params = {
    "lat": city_lat,
    "lon": city_lon,
    "cnt": cnt,
    "appid": api_key,
    "units": "metric",   # or "imperial", "standard"
  }

  response = requests.get(url, params=params)
  response.raise_for_status()

  data = response.json()

  return data
