import fs from 'fs';
import { transformSync } from '@babel/core';
import { JSDOM } from 'jsdom';
import React from 'react';
import { createRoot } from 'react-dom/client';
import { act } from '@testing-library/react';

// Setup basic dom
const dom = new JSDOM('<!doctype html><html><body><div id="root"></div></body></html>', { url: "http://localhost" });
global.window = dom.window;
global.document = dom.window.document;
global.navigator = { userAgent: 'node.js', geolocation: { watchPosition: () => {} } };
global.WebSocket = class { close() {} };
global.fetch = async () => ({ json: async () => ({}) });

// Mocks
jest.mock('./src/store/tripStore', () => ({
  useTripStore: () => ({
    trip: { id: '123' },
    trips: [],
    loadDemoTrip: () => {},
    fetchTrips: () => {},
    saveTrip: () => {},
    loadTrip: () => {},
    updateTrip: () => {},
    deleteTrip: () => {},
    toggleStopCheck: () => {},
    sendCompanionMessage: () => {},
    simulateDisruption: () => {},
    activeDisruption: null,
    impactAnalysis: null,
    submitPreferences: () => {},
    recoveryCandidates: [],
    selectCandidate: () => {}
  })
}));
jest.mock('./src/store/authStore', () => ({
  useAuthStore: () => ({
    isDemoMode: true,
    isAuthenticated: true,
    user: { id: 'test' },
    setUser: () => {},
    login: () => {},
    signup: () => {},
    loading: false,
    error: null,
    logout: () => {}
  })
}));
jest.mock('@splinetool/react-spline', () => () => <div />);
jest.mock('framer-motion', () => ({ motion: { div: (props) => <div {...props} /> } }));
jest.mock('./src/components/MapComponent', () => () => <div />);

import App from './src/App.jsx';

async function run() {
  const root = createRoot(document.getElementById('root'));
  await act(async () => {
    root.render(<App />);
  });
  
  // Find "MONITOR BOOKINGS" button and click it
  const buttons = Array.from(document.querySelectorAll('button'));
  const monitorBookingsBtn = buttons.find(b => b.textContent.includes('MONITOR BOOKINGS'));
  if (monitorBookingsBtn) {
    await act(async () => monitorBookingsBtn.click());
  }

  // Find "Paste Text" button and click it
  const pasteTextBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent.includes('Paste Text'));
  if (pasteTextBtn) {
    console.log("Found Paste Text button. Clicking...");
    await act(async () => pasteTextBtn.click());
  } else {
    console.log("Could not find Paste Text button");
  }

  console.log("Render completed successfully without crash.");
}
run().catch(console.error);
