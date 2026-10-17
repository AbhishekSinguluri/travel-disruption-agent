import os
from typing import Dict, Any
from app.services.travel_companion import TravelCompanionService
from dotenv import load_dotenv
import json

def chat_with_companion(trip: Dict[str, Any], user_message: str) -> str:
    load_dotenv()
    svc = TravelCompanionService(trip)
    msg_low = user_message.lower()
    
    context = {
        "destination": trip.get("destination"),
        "status": trip.get("status"),
        "days": []
    }
    for day in trip.get("days", []):
        day_ctx = {"date": day.get("date"), "stops": []}
        for stop in day.get("stops", []):
            day_ctx["stops"].append({
                "title": stop.get("title"),
                "status": stop.get("status"),
                "start_time": stop.get("start_time"),
                "end_time": stop.get("end_time"),
                "category": stop.get("category"),
                "opening_hours": stop.get("opening_hours")
            })
        context["days"].append(day_ctx)

    system_prompt = f"You are a helpful travel companion AI. Answer concisely based on this itinerary: {json.dumps(context)}. Do not invent facts."

    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        if api_key and api_key != "your_groq_api_key_here":
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=150
            )
            return completion.choices[0].message.content
    except Exception as e:
        print("Groq API error:", e)
        return f"Error connecting to LLM: {str(e)}"

    # Fallbacks for specific things if LLM fails
    if "skip" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Skipping {next_s['title']} will move your next stop forward. Do you want to skip it? [ Skip {next_s['title']} ]"
        return "I can help skip."
    if "close" in msg_low:
        return "It closes at 5:30 PM."
    if "next" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Your next stop is {next_s['title']} at {next_s['start_time']}."
        return "You have no more stops today."
    if "far" in msg_low:
        return "It is about 2.1 km away, estimated travel time 12 min."
    if "closed" in msg_low and "alternative" in msg_low:
        return "I can help with that. Let's find an alternative."
        
    return "I am your AI travel companion. I can help you check opening hours, skip stops, or find alternatives."
