import urllib.request
import urllib.parse
import json

base_url = 'http://localhost:8000'

print("--- 1. Testing Booking 1 Extraction with Email Metadata ---")
data1 = urllib.parse.urlencode({
    'text': 'From: bookings@emirates.com\nDate: Tue, 14 Oct 2026 15:30:00 +0000\nSubject: Booking Confirmation\nFlight EK202 from DXB to JFK confirmed for departure 2026-10-25T08:30:00Z. Booking reference: EK987654.'
}).encode()
req1 = urllib.request.Request(f'{base_url}/api/bookings/extract', data=data1)
res1 = urllib.request.urlopen(req1)
b1 = json.loads(res1.read())
print(f"Extracted B1: Provider={b1.get('provider')}, Ref={b1.get('booking_reference')}, Date={b1.get('email_date')}, Time={b1.get('email_time')}, Sender={b1.get('sender_email')}")
assert b1.get('email_date') == '2026-10-14', f"Expected 2026-10-14, got {b1.get('email_date')}"
assert b1.get('email_time', '').startswith('15:30'), f"Expected 15:30, got {b1.get('email_time')}"
assert b1.get('sender_email') == 'bookings@emirates.com', f"Expected bookings@emirates.com, got {b1.get('sender_email')}"
print("[PASS] B1 Email metadata passed.")

print("\n--- 2. Testing Booking 2 Extraction (Multiple Searches without Refresh) ---")
data2 = urllib.parse.urlencode({
    'text': 'From: reservations@eurostar.com\nDate: Wed, 15 Oct 2026 09:15:00 +0000\nSubject: Eurostar Confirmation 9014\nEurostar train 9014 from London to Paris confirmed. Booking Reference: EST5544.'
}).encode()
req2 = urllib.request.Request(f'{base_url}/api/bookings/extract', data=data2)
res2 = urllib.request.urlopen(req2)
b2 = json.loads(res2.read())
print(f"Extracted B2: Provider={b2.get('provider')}, Ref={b2.get('booking_reference')}, Date={b2.get('email_date')}, Time={b2.get('email_time')}, Sender={b2.get('sender_email')}")
assert b2.get('id') != b1.get('id'), "B1 and B2 must have distinct, independent IDs"
assert b2.get('booking_reference') == 'EST5544'
assert b2.get('email_date') == '2026-10-15'
assert b2.get('email_time', '').startswith('09:15')
assert b2.get('sender_email') == 'reservations@eurostar.com'
print("[PASS] B2 independent extraction passed.")

print("\n--- 3. Testing SQLite Persistence across Searches ---")
res_list = urllib.request.urlopen(f'{base_url}/api/bookings')
all_bookings = json.loads(res_list.read())
print(f"Total bookings in SQLite: {len(all_bookings)}")
ids = [b['id'] for b in all_bookings]
assert b1['id'] in ids, "B1 must be persisted in SQLite"
assert b2['id'] in ids, "B2 must be persisted in SQLite"
print("[PASS] Both bookings verified in SQLite persistence.")

print("\n--- 4. Testing Monitoring Activation for Booking 1 ---")
req_mon = urllib.request.Request(
    f'{base_url}/api/monitor/booking/activate',
    data=json.dumps(b1).encode(),
    headers={'Content-Type': 'application/json'}
)
res_mon = urllib.request.urlopen(req_mon)
mon_res = json.loads(res_mon.read())
print(f"Monitoring result: status={mon_res.get('status')}, monitor_id={mon_res.get('monitor_id')}")
assert mon_res.get('status') in ['ACTIVE', 'monitoring_active']
print("[PASS] Independent monitoring activation passed.")

print("\n--- 5. Testing Booking Deletion (X button functionality) ---")
b1_id = b1['id']
req_del = urllib.request.Request(f'{base_url}/api/bookings/{b1_id}', method='DELETE')
res_del = urllib.request.urlopen(req_del)
assert res_del.status == 200
print(f"Deleted booking {b1_id} successfully.")

# Verify B1 is deleted and B2 remains
res_list2 = urllib.request.urlopen(f'{base_url}/api/bookings')
remaining = json.loads(res_list2.read())
rem_ids = [b['id'] for b in remaining]
assert b1_id not in rem_ids, f"B1 ({b1_id}) should no longer exist in database"
assert b2['id'] in rem_ids, f"B2 ({b2['id']}) must still exist in database"
print(f"[PASS] Deletion verified: B1 removed, B2 preserved.")

print("\n--- 6. Testing Voice Itinerary Creation Flow ---")
voice_text = "Trip to Rome visiting Colosseum at 09:00, Vatican Museums at 14:00, and Trevi Fountain in the evening."
req_voice = urllib.request.Request(
    f'{base_url}/api/import/text',
    data=json.dumps({'text': voice_text}).encode(),
    headers={'Content-Type': 'application/json'}
)
res_voice = urllib.request.urlopen(req_voice)
trip_res = json.loads(res_voice.read())
print(f"Structured itinerary: Destination={trip_res.get('destination')}, Days={len(trip_res.get('days', []))}")
stops = trip_res.get('days', [{}])[0].get('stops', [])
print(f"Extracted {len(stops)} stops from voice text.")
assert len(stops) > 0, "Voice text must structure at least one stop"
print("[PASS] Voice-to-itinerary flow passed.")

print("\n=======================================================")
print(" ALL 6 VERIFICATION TEST SUITES PASSED FLAWLESSLY 100% ")
print("=======================================================")
