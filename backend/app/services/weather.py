import os
import logging
import json
import urllib.request
import urllib.parse
from typing import Protocol, Dict, Optional, Any
from app.schemas.weather import WeatherData, WeatherCompatibility

logger = logging.getLogger(__name__)

class WeatherProvider(Protocol):
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData: ...

class MockWeatherProvider:
    def __init__(self, condition: str = "Rain", description: str = "Light rain"):
        self.condition = condition
        self.description = description

    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        return WeatherData(
            temperature=28.0, condition=self.condition, description=self.description,
            rain_probability=80.0, precipitation=2.0, wind_speed=10.0,
            humidity=75.0, timestamp=time, source="mock"
        )

class OpenWeatherProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        logger.info(f"[OPENWEATHER] Real-time request for lat={lat}, lng={lng}")
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lng}&appid={self.api_key}&units=metric"
            req = urllib.request.Request(url, headers={"User-Agent": "RoamTravelAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    weather_arr = data.get("weather", [])
                    weather_item = weather_arr[0] if weather_arr else {}
                    main_info = data.get("main", {})
                    wind_info = data.get("wind", {})
                    rain_info = data.get("rain", {})
                    
                    cond = weather_item.get("main", "Clear")
                    desc = weather_item.get("description", "clear sky")
                    temp = float(main_info.get("temp", 25.0))
                    humidity = float(main_info.get("humidity", 50.0))
                    wind_spd = float(wind_info.get("speed", 5.0))
                    precip = float(rain_info.get("1h", 0.0) or rain_info.get("3h", 0.0) or 0.0)
                    
                    weather_id = weather_item.get("id", 800)
                    is_rain = (200 <= weather_id < 600) or any(w in cond.lower() for w in ["rain", "drizzle", "thunderstorm", "snow"]) or "rain" in desc.lower()
                    rain_prob = 85.0 if is_rain else 0.0
                    
                    return WeatherData(
                        temperature=temp,
                        condition=cond,
                        description=desc.capitalize(),
                        rain_probability=rain_prob,
                        precipitation=precip if is_rain and precip > 0 else (2.5 if is_rain else 0.0),
                        wind_speed=wind_spd,
                        humidity=humidity,
                        timestamp=time,
                        source="openweather"
                    )
        except Exception as e:
            logger.warning(f"[OPENWEATHER] Failed to fetch real weather: {e}. Falling back to default.")
            
        return WeatherData(
            temperature=26.0, condition="Clear", description="Clear sky",
            rain_probability=0.0, precipitation=0.0, wind_speed=5.0,
            humidity=50.0, timestamp=time, source="openweather_cached"
        )

    def get_weather_by_query(self, query: str, time: str) -> WeatherData:
        logger.info(f"[OPENWEATHER] Real-time request for query='{query}'")
        try:
            encoded_q = urllib.parse.quote(query)
            url = f"https://api.openweathermap.org/data/2.5/weather?q={encoded_q}&appid={self.api_key}&units=metric"
            req = urllib.request.Request(url, headers={"User-Agent": "RoamTravelAgent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode('utf-8'))
                    weather_arr = data.get("weather", [])
                    weather_item = weather_arr[0] if weather_arr else {}
                    main_info = data.get("main", {})
                    wind_info = data.get("wind", {})
                    rain_info = data.get("rain", {})
                    
                    cond = weather_item.get("main", "Clear")
                    desc = weather_item.get("description", "clear sky")
                    temp = float(main_info.get("temp", 25.0))
                    humidity = float(main_info.get("humidity", 50.0))
                    wind_spd = float(wind_info.get("speed", 5.0))
                    precip = float(rain_info.get("1h", 0.0) or rain_info.get("3h", 0.0) or 0.0)
                    
                    weather_id = weather_item.get("id", 800)
                    is_rain = (200 <= weather_id < 600) or any(w in cond.lower() for w in ["rain", "drizzle", "thunderstorm", "snow"]) or "rain" in desc.lower()
                    rain_prob = 85.0 if is_rain else 0.0
                    
                    return WeatherData(
                        temperature=temp,
                        condition=cond,
                        description=desc.capitalize(),
                        rain_probability=rain_prob,
                        precipitation=precip if is_rain and precip > 0 else (2.5 if is_rain else 0.0),
                        wind_speed=wind_spd,
                        humidity=humidity,
                        timestamp=time,
                        source="openweather"
                    )
        except Exception as e:
            logger.warning(f"[OPENWEATHER] Failed to fetch query weather: {e}")
            
        return WeatherData(
            temperature=26.0, condition="Clear", description="Clear sky",
            rain_probability=0.0, precipitation=0.0, wind_speed=5.0,
            humidity=50.0, timestamp=time, source="openweather_cached"
        )

def get_weather_provider() -> WeatherProvider:
    key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHERMAP_API_KEY")
    if key and key.strip() and key.strip() != "your_openweather_api_key_here":
        return OpenWeatherProvider(key.strip())
    logger.info("[WEATHER] No valid OpenWeather API key found in .env; ready for key to be set.")
    return MockWeatherProvider()

def check_weather_compatibility(weather: WeatherData, category: str) -> WeatherCompatibility:
    if "Rain" in weather.condition and category.lower() in ["outdoor", "beach", "sightseeing"]:
        if weather.precipitation > 5.0:
            return WeatherCompatibility(weather_compatible=False, risk_level="HIGH RISK", reason="Heavy rain expected during outdoor activity.")
        return WeatherCompatibility(weather_compatible=False, risk_level="MEDIUM RISK", reason="Light rain expected during outdoor activity.")
    return WeatherCompatibility(weather_compatible=True, risk_level="LOW RISK", reason="Weather is suitable.")

def check_stop_realtime_weather(stop: dict, destination: str = "", force_rain: bool = False) -> Dict[str, Any]:
    """
    Checks real-time weather for a given stop using OpenWeather if key is available.
    """
    key = os.getenv("OPENWEATHER_API_KEY") or os.getenv("OPENWEATHERMAP_API_KEY")
    has_key = bool(key and key.strip() and key.strip() != "your_openweather_api_key_here")
    
    lat = stop.get("latitude") or stop.get("lat")
    if lat is None and isinstance(stop.get("location"), dict):
        lat = stop["location"].get("lat") or stop["location"].get("latitude")
        
    lng = stop.get("longitude") or stop.get("lng") or stop.get("lon")
    if lng is None and isinstance(stop.get("location"), dict):
        lng = stop["location"].get("lng") or stop["location"].get("longitude") or stop["location"].get("lon")
        
    title = stop.get("title") or stop.get("location_name") or stop.get("name") or stop.get("address") or "Location"
    import datetime
    now_str = datetime.datetime.now().isoformat()
    
    if force_rain:
        return {
            "stop_id": stop.get("id"),
            "stop_title": title,
            "is_raining": True,
            "condition": "Rain",
            "description": "Heavy rainfall detected",
            "temperature": 23.5,
            "precipitation": 4.5,
            "humidity": 88,
            "source": "simulated_rain",
            "has_api_key": has_key
        }

    provider = get_weather_provider()
    w_data: Optional[WeatherData] = None
    
    if isinstance(provider, OpenWeatherProvider):
        if lat is not None and lng is not None:
            w_data = provider.get_weather(float(lat), float(lng), now_str)
        else:
            q = f"{title}, {destination}" if destination else title
            w_data = provider.get_weather_by_query(q, now_str)
    else:
        # Provider is Mock
        w_data = provider.get_weather(lat or 17.3850, lng or 78.4867, now_str)
        
    cond = w_data.condition if w_data else "Clear"
    desc = w_data.description if w_data else "Clear sky"
    is_rain = any(k in cond.lower() for k in ["rain", "drizzle", "thunderstorm", "snow"]) or "rain" in desc.lower()
    
    return {
        "stop_id": stop.get("id"),
        "stop_title": title,
        "is_raining": is_rain,
        "condition": cond,
        "description": desc,
        "temperature": w_data.temperature if w_data else 25.0,
        "precipitation": w_data.precipitation if w_data else 0.0,
        "humidity": w_data.humidity if w_data else 50.0,
        "source": w_data.source if w_data else "unknown",
        "has_api_key": has_key
    }
