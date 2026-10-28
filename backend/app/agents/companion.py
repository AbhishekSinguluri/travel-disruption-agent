import os
import json
from typing import Dict, Any
from app.services.travel_companion import TravelCompanionService
from dotenv import load_dotenv

def chat_with_companion(trip: Dict[str, Any], user_message: str) -> str:
    load_dotenv()
    svc = TravelCompanionService(trip)
    msg_low = user_message.lower()

    # Import live event service and mappings
    from app.services.live_events import get_live_events_service, INDIAN_STATES_DATA, CITY_TO_STATE_MAP

    # 1. Detect if an Indian city or state was specifically mentioned in the user message
    detected_loc = None
    for city_key in CITY_TO_STATE_MAP:
        if city_key in msg_low:
            detected_loc = city_key
            break
    if not detected_loc:
        for state_key in INDIAN_STATES_DATA:
            if state_key in msg_low:
                detected_loc = state_key
                break

    target_loc = detected_loc or trip.get("destination") or "maharashtra"
    ev_svc = get_live_events_service()
    ev_data = ev_svc.get_city_events(target_loc, force_refresh=False)
    events_list = ev_data.get("events", [])
    city_disp = ev_data.get("city", target_loc.title())

    # 2. If the user explicitly asks for events/shows/festivals, serve the EXACT live events with Book & Official links
    if any(k in msg_low for k in ["event", "events", "show", "shows", "bookmyshow", "festival", "festivals", "tonight", "happening", "ticket", "tickets", "attend", "concert", "concerts", "gig", "gigs"]):
        if events_list:
            intro = f"Here are verified live events and shows happening in **{city_disp}** directly tracked via BookMyShow & Google Events:\n\n"
            event_items = []
            for e in events_list[:5]:
                clean_title = str(e.get('title', '')).replace('|', '-').replace(':::', '-')
                clean_venue = str(e.get('venue', '')).replace('|', '-').replace(':::', '-')
                price_val = str(e.get('price', '₹350'))
                from app.services.live_events import resolve_booking_url
                t_url = resolve_booking_url(e.get('ticket_url'), target_loc, clean_title, clean_venue)
                e_id = str(e.get('id', 'evt-1'))
                
                event_items.append(
                    f"• **{e['title']}**\n"
                    f"  📍 {e['venue']}  |  🗓️ {e['timing']}  |  🎟️ **{e['price']}**\n"
                    f"  [🎟️ Buy Ticket](book:{e_id}:::{clean_title}:::{clean_venue}:::{price_val}:::{t_url})  •  [Official Booking Page ↗]({t_url})"
                )
            return intro + "\n\n".join(event_items) + f"\n\n💡 *Click **[🎟️ Buy Ticket]** to reserve passes via our autonomous agent, or click **[Official Booking Page ↗]** to redirect directly to the authentic live ticket page!*"
        else:
            return f"I checked for live events in **{city_disp}**, but none are currently listed. Try searching Maharashtra, Rajasthan, Karnataka or Delhi in the Live Events tab!"

    # 3. Context gathering for general conversation
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

    events_summary = ""
    if events_list:
        from app.services.live_events import resolve_booking_url
        events_summary = f"\nVERIFIED LIVE EVENTS FOR {city_disp.upper()}:\n" + "\n".join([
            f"- {e['title']} at {e['venue']} ({e['timing']}) | Price: {e['price']} | Link: {resolve_booking_url(e.get('ticket_url'), target_loc, e.get('title', ''), e.get('venue', ''))}"
            for e in events_list[:5]
        ])

    if context["days"]:
        trip_info = f"The traveler is viewing their itinerary to {trip.get('destination', 'their destination')}.\nTRIP CONTEXT & ITINERARY:\n{json.dumps(context, indent=2)}{events_summary}"
    else:
        trip_info = f"The user is on the ROAM home/events page exploring India.\nLOCATION IN FOCUS: {city_disp}{events_summary}"

    system_prompt = f"""You are Rome Buddy, an intelligent, friendly personal AI concierge on the ROAM platform.
{trip_info}

STRICT GROUNDING & INDIA-ONLY RULES:
1. You are operating strictly within India. Never mention cities outside India (e.g. no Rome, no California, no USA, no Europe).
2. If the user asks about live events, shows, BookMyShow, or festivals, ONLY use the verified events listed above. Never hallucinate fake event names or US venues. If they ask about events in any Indian city, format each with its exact Title, Venue, Timing, Price, and provide:
   [🎟️ Buy Ticket](book:<id>:::<title>:::<venue>:::<price>:::<url>) • [Official Booking Page ↗](<url>)
3. If they ask about trip planning, food (e.g. famous biryani, street food, cafes), heritage, or transit: give rich, practical recommendations for Indian cities.
4. If they ask about trip schedule, timings, or delays: answer accurately based on their current schedule.
5. Format your response cleanly and engagingly with bullet points.
"""

    try:
        from groq import Groq
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        if api_key and api_key != "your_groq_api_key_here":
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=1000,
                temperature=0.6
            )
            content = completion.choices[0].message.content
            if content and content.strip():
                return content.strip()
    except Exception as e:
        print("Groq API error in Rome Buddy:", e)

    # Conversational fallbacks
    if "next" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Your next stop is {next_s['title']} at {next_s.get('start_time', 'scheduled time')}."
        return "You have completed all scheduled stops for today!"
    if "skip" in msg_low:
        next_s = svc.get_next_stop()
        if next_s:
            return f"Skipping {next_s['title']} will advance your next scheduled stop. Would you like me to skip it for you? [ Skip {next_s['title']} ]"
        return "I can help you skip any stop on your itinerary."
    if "close" in msg_low or "hours" in msg_low:
        next_s = svc.get_next_stop()
        if next_s and next_s.get("opening_hours"):
            return f"{next_s['title']} opening hours: {next_s['opening_hours']}."
        return "Most monuments and heritage sites close at 5:30 PM."
    if "food" in msg_low or "eat" in msg_low:
        return ("Here are some must-try local specialties:\n"
                "• Street Food: Pani puri, vada pav, freshly fried samosas and kebabs.\n"
                "• Regional Specialties: Authentic Dum Biryani, Irani Chai with Osmania Biscuits.\n"
                "• Desserts: Warm Gulab Jamun, Double Ka Meetha, and Kulfi Falooda.")

    return f"Hi! I'm Rome Buddy, your personal local concierge for {city_disp}. Ask me about live BookMyShow events, tickets, local cuisine, or sightseeing!"
