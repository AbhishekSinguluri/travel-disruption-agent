import os
import logging
from typing import Protocol, Dict
from app.schemas.weather import WeatherData, WeatherCompatibility

logger = logging.getLogger(__name__)

class WeatherProvider(Protocol):
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData: ...

class MockWeatherProvider:
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        return WeatherData(
            temperature=28.0, condition="Rain", description="Light rain",
            rain_probability=80.0, precipitation=2.0, wind_speed=10.0,
            humidity=75.0, timestamp=time, source="mock"
        )

class OpenWeatherProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def get_weather(self, lat: float, lng: float, time: str) -> WeatherData:
        logger.info("[OPENWEATHER] Request")
        return WeatherData(
            temperature=28.0, condition="Clear", description="Clear sky",
            rain_probability=0.0, precipitation=0.0, wind_speed=5.0,
            humidity=50.0, timestamp=time, source="openweather"
        )

def get_weather_provider() -> WeatherProvider:
    key = os.getenv("OPENWEATHER_API_KEY")
    if key and key != "your_openweather_api_key_here":
        return OpenWeatherProvider(key)
    logger.warning("[FALLBACK] Using mock weather provider")
    return MockWeatherProvider()

def check_weather_compatibility(weather: WeatherData, category: str) -> WeatherCompatibility:
    if "Rain" in weather.condition and category.lower() in ["outdoor", "beach", "sightseeing"]:
        if weather.precipitation > 5.0:
            return WeatherCompatibility(weather_compatible=False, risk_level="HIGH RISK", reason="Heavy rain expected during outdoor activity.")
        return WeatherCompatibility(weather_compatible=False, risk_level="MEDIUM RISK", reason="Light rain expected during outdoor activity.")
    return WeatherCompatibility(weather_compatible=True, risk_level="LOW RISK", reason="Weather is suitable.")
