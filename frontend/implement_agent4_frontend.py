import os

FRONTEND_DIR = r"c:\Users\Admin\Desktop\AgenticCapstone\travel-disruption-agent\frontend"

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Written: {path}")

booking_monitor = """
import React, { useState } from 'react';

export default function BookingMonitor() {
  const [bookingStatus, setBookingStatus] = useState("idle");
  const [activeBooking, setActiveBooking] = useState(null);
  
  const handleSimulateExtraction = async () => {
    setBookingStatus("extracting");
    const res = await fetch("http://localhost:8000/api/bookings/extract", { method: "POST" });
    const data = await res.json();
    setActiveBooking(data);
    setBookingStatus("summary");
  };

  const startMonitoring = async () => {
    setBookingStatus("monitoring");
  };

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h2 className="text-3xl font-serif mb-6">Monitor Your Bookings</h2>
      
      {bookingStatus === "idle" && (
        <div className="space-y-4">
          <p className="text-slate-500">Upload a ticket, reservation, or booking and Roam will keep watch for changes.</p>
          <button onClick={handleSimulateExtraction} className="px-6 py-3 bg-slate-900 text-white rounded-full">
            Simulate Upload Ticket
          </button>
        </div>
      )}

      {bookingStatus === "extracting" && (
        <p className="text-slate-500 animate-pulse">Extracting booking details...</p>
      )}

      {bookingStatus === "summary" && activeBooking && (
        <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-200">
          <h3 className="font-bold text-xl mb-4">{activeBooking.title}</h3>
          <p>{activeBooking.departure_location} → {activeBooking.arrival_location}</p>
          <p>{activeBooking.departure_time} - {activeBooking.arrival_time}</p>
          <p className="mt-4"><strong>PNR:</strong> {activeBooking.booking_reference}</p>
          <button onClick={startMonitoring} className="mt-6 px-6 py-3 bg-emerald-600 text-white rounded-full">
            MONITOR THIS BOOKING
          </button>
        </div>
      )}
      
      {bookingStatus === "monitoring" && (
        <div className="bg-emerald-50 border border-emerald-200 p-6 rounded-2xl text-emerald-900">
          <h3 className="font-bold text-xl mb-2">Monitoring Active</h3>
          <p>We are now scanning your emails for updates.</p>
        </div>
      )}
    </div>
  );
}
"""

def main():
    write_file(os.path.join(FRONTEND_DIR, "src/components/BookingMonitor.jsx"), booking_monitor)
    
if __name__ == "__main__":
    main()
