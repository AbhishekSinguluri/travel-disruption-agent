# Travel Disruption Recovery Agent

A dynamic travel itinerary monitoring and recovery system powered by AI.

## Features
- Interactive Trip Dashboard with Timeline and Maps
- Itinerary Validation & Parsing
- Real-time Trip Monitoring
- Disruption Detection & Impact Analysis
- Intelligent Recovery Strategies
- Seamless Replanning Engine

## Architecture
- **Frontend**: React, Vite, Tailwind, Zustand
- **Backend**: Python, FastAPI, LangGraph, WebSockets
- **Database**: Supabase PostgreSQL

## Setup Instructions
1. Copy `.env.example` to `.env` and fill in the dummy variables or actual keys.
2. In `frontend/`, run `npm install` and `npm run dev`.
3. In `backend/`, setup Python virtual environment and run `uvicorn app.main:app --reload`.

## Demo Mode
Simulate disruptions (e.g., Beach closure, weather issues) directly from the UI without relying on live APIs to demonstrate the agentic workflow.
