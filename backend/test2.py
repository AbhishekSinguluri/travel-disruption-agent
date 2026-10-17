import requests
try:
    res = requests.post('http://localhost:8000/api/bookings/extract', 
                        data={'text': 'indigo bookings'}, 
                        headers={'Origin': 'http://localhost:5173'})
    print(res.status_code)
    print(res.headers)
    print(res.text)
except Exception as e:
    print(e)
