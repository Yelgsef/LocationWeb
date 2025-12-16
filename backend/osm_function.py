# -*- coding: utf-8 -*-
import time
from typing import List

import requests
import folium

NOMINATIM = "https://nominatim.openstreetmap.org"
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36"}
OSRM = "https://router.project-osrm.org"
# Try fast/stable Overpass mirrors in order; fail fast to fall back.
OVERPASS_ENDPOINTS: List[str] = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Name -> Lat Lon
def geocode (q: str):
    response = requests.get(url=f"{NOMINATIM}/search", params={
        "q": q, "format":"jsonv2", "limit":1, "addressdetails":1
    }, headers=UA, timeout=60)
    response.raise_for_status()

    data = response.json()
    if not data: raise ValueError("Không tìm thấy kết quả")
    item = data[0]
    # print("Query:", q)
    # print("Lat/Lon:", item["lat"], item["lon"])
    # print("Display name:", item["display_name"])
    return item["lat"], item["lon"], item.get("display_name", q)


# Lat Lon -> Address
def reverse_geocode(lat: float, lon: float):
    response = requests.get(f"{NOMINATIM}/reverse", params={
        "lat": lat, "lon": lon, "format": "jsonv2", "zoom": 16, "addressdetails": 1
    }, headers=UA, timeout=60)
    response.raise_for_status()
    data = response.json()
    if not data: raise ValueError("Không tìm thấy kết quả")
    # print(data)
    return data["type"], data["display_name"]

# Road from A -> B 
def route(lon1, lat1, lon2, lat2):
    response = requests.get(url=f"{OSRM}/route/v1/driving/{lon1},{lat1};{lon2},{lat2}",
                            params={"overview":"full", "geometries":"geojson"}, headers=UA, timeout=120)
    response.raise_for_status()
    data = response.json()
    route = data["routes"][0]
    dist_km = route["distance"]/1000.0
    dur_min = route["duration"]/60.0
    return route["geometry"],dist_km, dur_min

# POI 
def POI (lat: float, lon: float, radius: int, POI_count: int, output_path: str = "output.html"): #Radius in meters
    QL = f"""
    [out:json][timeout:25];
    nwr(around:{radius},{lat},{lon})["amenity"="cafe"];
    out center {POI_count};
    """
    data = _call_overpass(QL)
    
    g_map = folium.Map(location=[lat, lon], zoom_start=15, control_scale=False)
    folium.Marker([lat, lon], popup="Your location",icon=folium.Icon(color="red")).add_to(g_map)
    for location in data[:POI_count]: # type: ignore
        name = location.get("tags", {}).get("name", "(no name)")
        location_lat = (location.get("lat") or location.get("center", {}).get("lat"))
        location_lon = (location.get("lon") or location.get("center", {}).get("lon"))
        folium.Marker([location_lat, location_lon], popup=name).add_to(g_map)
    g_map.save(output_path)
    print("Done")


def _call_overpass(query: str, timeout_s: int = 20):
    """Try multiple Overpass mirrors quickly, return elements list or raise."""
    last_exc = None
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            response = requests.post(endpoint, data=query.encode("utf-8"), headers=UA, timeout=timeout_s)
            response.raise_for_status()
            return response.json().get("elements", [])
        except Exception as exc:
            last_exc = exc
            continue
    if last_exc:
        raise last_exc
