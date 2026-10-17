from pydantic import BaseModel
from typing import Optional

class WeatherData(BaseModel):
    temperature: float
    condition: str
    description: str
    rain_probability: float
    precipitation: float
    wind_speed: float
    humidity: float
    timestamp: str
    source: str

class WeatherCompatibility(BaseModel):
    weather_compatible: bool
    risk_level: str
    reason: str
