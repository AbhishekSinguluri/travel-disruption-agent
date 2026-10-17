from app.services.weather import get_weather_provider, MockWeatherProvider, check_weather_compatibility, WeatherData

def test_weather_fallback():
    provider = get_weather_provider()
    assert isinstance(provider, MockWeatherProvider)

def test_weather_compatibility():
    weather = WeatherData(
        temperature=25, condition="Rain", description="Heavy rain",
        rain_probability=90, precipitation=10, wind_speed=15,
        humidity=80, timestamp="14:00", source="mock"
    )
    comp = check_weather_compatibility(weather, "Outdoor")
    assert comp.weather_compatible is False
    assert comp.risk_level == "HIGH RISK"
    
    comp2 = check_weather_compatibility(weather, "Indoor")
    assert comp2.weather_compatible is True
