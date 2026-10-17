import React from 'react';
import { renderToString } from 'react-dom/server';
import App from './src/App.jsx';

// Mock browser APIs and stores
global.window = {};
global.navigator = { geolocation: { watchPosition: () => {} } };
global.WebSocket = class { close() {} };

jest.mock('./src/store/tripStore', () => ({
  useTripStore: () => ({
    trip: { id: 'test' },
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
jest.mock('framer-motion', () => ({
  motion: { div: 'div' }
}));
jest.mock('./src/components/MapComponent', () => () => <div />);

try {
  console.log('Rendering App...');
  const element = React.createElement(App);
  renderToString(element);
  console.log('Render successful (initial)');

  // We can't easily simulate hooks state changes in renderToString,
  // but we can check if it throws initially.
} catch (e) {
  console.error('Error rendering:', e);
}
