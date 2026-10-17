import requests

print("Running Test A...")
res = requests.post("http://localhost:8000/api/bookings/extract", data={"text": "Check my recent IndiGo flights"})
print("Test A Result:")
print(res.json())

print("\nRunning Test B...")
res2 = requests.post("http://localhost:8000/api/bookings/extract", data={"text": "Booking Confirmation: IndiGo 6E 652 Hyderabad to Goa PNR: 6F4A2B"})
print("Test B Result:")
print(res2.json())
