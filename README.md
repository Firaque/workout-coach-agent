# Workout Coach AI Agent 🏋️‍♂️

A smart, personalized fitness and exercise assistant built with the Google Agent Development Kit (ADK), Vertex AI, Firestore, and A2UI (Agent-to-User Interface). The Workout Coach helps athletes search exercises, view form instructions, calculate 1-Rep Max (1RM) training weights, log completed workouts, fetch motivational quotes, and generate exercise visual illustrations and video demonstrations.

![Workout Coach Demo](./demo.gif)

---

## 🌟 Key Features & Tooling

The Workout Coach agent implements the following integrated tools and services:

### 🏋️‍♂️ Exercise Catalog & History (Google Cloud Firestore)
- **`search_exercises`**: Search the exercises database in Firestore by muscle group (e.g., Chest, Quadriceps) or exercise category.
- **`get_exercise_details`**: Retrieve step-by-step instructions, equipment requirements, and target muscles for specific exercises.
- **`log_workout`**: Record completed exercise sets (reps, weight in lbs, notes) directly to the user's Firestore workout history.
- **`get_user_workout_history`**: Retrieve past logged workouts to track progression over time.

### 🧮 Strength & Performance Calculations
- **`calculate_one_rep_max`**: Computes estimated 1-Rep Max (1RM) using Epley & Brzycki formulas and returns target working weight percentages (70% to 100%).

### 🎨 Visual & Media Generation (Vertex AI & Cloud Storage)
- **`generate_workout_image`**: Generates visual exercise form illustrations using Google's `gemini-3.1-flash-lite-image` model in global region. Saves bytes to Playground Artifacts and uploads to a public Google Cloud Storage bucket (`workout-coach-agent-media-...`).
- **`generate_workout_video`**: Generates short exercise demonstration videos using Google's Omni model (`gemini-omni-flash-preview`) in global region. Saves bytes to Playground Artifacts and uploads to a public Cloud Storage bucket.

### 🧠 Long-Term Memory & Persistence (Vertex AI Memory Bank)
- **`VertexAiMemoryBankService`**: Stores personal records, user preferences, and target muscle goals across chat sessions to deliver personalized fitness coaching.

### 💡 Motivation & Real-time Web APIs
- **`get_motivational_quote`**: Fetches real-time fitness mindset quotes from the ZenQuotes API.

### 📱 Adaptive UI Rendering (A2UI)
- Structured A2UI (Agent-to-User Interface) payload formatting (`Card`, `Column`, `Row`, `Text`, `Image`) rendered directly in the custom web frontend.

---

## 📋 Planned / Future Features

The following capabilities were discussed in early design briefs but are **not yet implemented**:
- ⌚ **Live Wearable Integration**: Real-time heart rate and smartwatch activity sync.
- 🥗 **Macro & Meal Planner**: Calorie and nutrition tracking calculator.
- 🏆 **Social Leaderboards**: Athlete friend networks and community challenge boards.

---

## 🏗 Project Structure

```
workout-coach-agent/
├── app/
│   ├── agent.py               # Root ADK agent, Memory Bank setup, instructions & callbacks
│   ├── tools.py               # Firestore, 1RM, Imagen, Omni video, and quote tools
│   ├── a2ui_utils.py          # A2UI model callback utilities
│   └── __init__.py
├── frontend/
│   ├── main.py                # FastAPI proxy server for ADK Agent Engine
│   ├── requirements.txt       # Frontend dependencies (FastAPI, uvicorn, a2a-sdk)
│   └── static/
│       ├── index.html         # Custom dark-mode UI, prompt chips, dialogue layout, A2UI renderer
│       └── app.js             # Client-side chat interaction scripts
├── agents-cli-manifest.yaml   # Project manifest for agents-cli deployment
├── deployment_metadata.json   # Reasoning Engine resource details
├── demo.gif                   # Looping demonstration GIF of the frontend interface
└── README.md
```

---

## 🚀 Local Setup & Execution Guide

Follow these steps to run the Workout Coach frontend and agent locally:

### 1. Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) authenticated to your GCP project with Firestore and Vertex AI enabled.

### 2. Environment Setup

Install project dependencies:
```bash
pip install -r frontend/requirements.txt
```

Set the required environment variables pointing to your deployed Reasoning Engine and agent directory:
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<YOUR_PROJECT_ID>/locations/<LOCATION>/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
```

### 3. Launch the Frontend Server

Navigate to the `frontend/` directory and run the FastAPI server:
```bash
cd frontend
python main.py
```

The application will start locally on port `8080`. Open your browser and navigate to port `8080` on your localhost interface to interact with the Workout Coach agent.

---

## 🧪 Testing

To verify agent tools and database connectivity locally, run:
```bash
python3 -c '
from app.tools import search_exercises, calculate_one_rep_max
print("Catalog Search:", search_exercises(target_muscle="Chest"))
print("1RM Calc:", calculate_one_rep_max(185, 8))
'
```
