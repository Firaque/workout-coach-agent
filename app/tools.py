"""Firestore backend, computation, public API, and image generation tools for workout-coach-agent."""

import datetime
import json
import os
import subprocess
import urllib.request
from typing import Any, Dict, List

from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
import google.oauth2.credentials
from google.genai import types

# Hardcoded constants (required for Agent Platform deployment & Firestore/GCS)
PROJECT_ID = "qwiklabs-gcp-03-71206494f81b"
BUCKET_NAME = "workout-coach-agent-media-qwiklabs-gcp-03-71206494f81b"


def _get_db() -> firestore.Client:
    """Helper to initialize Firestore client with hardcoded project ID."""
    return firestore.Client(project=PROJECT_ID)


def search_exercises(category: str = "", target_muscle: str = "") -> List[Dict[str, Any]]:
    """Search the exercises catalog in Firestore by category or target muscle group.

    Args:
        category: Optional category filter (e.g. 'Strength', 'Bodyweight').
        target_muscle: Optional target muscle filter (e.g. 'Chest', 'Quadriceps', 'Deltoids').

    Returns:
        List of matching exercise documents from the catalog.
    """
    db = _get_db()
    docs = db.collection("exercises").stream()
    results = []

    for doc in docs:
        data = doc.to_dict()
        if category and category.lower() not in data.get("category", "").lower():
            continue
        if target_muscle and target_muscle.lower() not in data.get("target_muscle", "").lower():
            continue
        results.append(data)

    return results


def get_exercise_details(exercise_name: str) -> Dict[str, Any]:
    """Get full details and instructions for a specific exercise by name.

    Args:
        exercise_name: Name of the exercise (e.g. 'Barbell Bench Press', 'Pull-Ups').

    Returns:
        Dictionary containing exercise details or an error message if not found.
    """
    db = _get_db()
    docs = db.collection("exercises").stream()

    for doc in docs:
        data = doc.to_dict()
        if exercise_name.lower() in data.get("name", "").lower():
            return data

    return {"error": f"Exercise '{exercise_name}' not found in the catalog."}


def log_workout(
    user_id: str,
    exercise_name: str,
    sets: int,
    reps: int,
    weight_lbs: float,
    notes: str = "",
) -> Dict[str, Any]:
    """Log a completed exercise set to the user's workout history in Firestore.

    Args:
        user_id: The ID of the user logging the workout (e.g. 'athlete_1').
        exercise_name: Name of the exercise performed.
        sets: Number of completed sets.
        reps: Number of repetitions per set.
        weight_lbs: Weight used in pounds.
        notes: Optional notes on performance or form.

    Returns:
        Confirmation dictionary with the created log record.
    """
    db = _get_db()
    log_id = f"log-{int(datetime.datetime.now().timestamp())}"
    date_str = datetime.date.today().isoformat()

    log_data = {
        "log_id": log_id,
        "user_id": user_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "date": date_str,
        "notes": notes,
    }

    db.collection("workout_logs").document(log_id).set(log_data)
    return {
        "status": "success",
        "message": f"Successfully logged {sets}x{reps} {exercise_name} for {user_id}.",
        "log": log_data,
    }


def get_user_workout_history(user_id: str) -> List[Dict[str, Any]]:
    """Retrieve past workout logs for a given user from Firestore.

    Args:
        user_id: The ID of the user (e.g. 'athlete_1').

    Returns:
        List of workout log entries for the specified user.
    """
    db = _get_db()
    docs = db.collection("workout_logs").where("user_id", "==", user_id).stream()
    return [doc.to_dict() for doc in docs]


def calculate_one_rep_max(weight_lbs: float, reps: int) -> Dict[str, Any]:
    """Calculate estimated 1-Rep Max (1RM) and working weight percentages using Epley and Brzycki strength formulas.

    Args:
        weight_lbs: Weight lifted in pounds (must be > 0).
        reps: Number of repetitions performed (must be between 1 and 30).

    Returns:
        Dictionary containing estimated 1RM and target working weight percentages.
    """
    if weight_lbs <= 0 or reps <= 0:
        return {"error": "Weight and reps must both be positive numbers."}

    if reps == 1:
        estimated_1rm = float(weight_lbs)
    else:
        epley_1rm = weight_lbs * (1.0 + reps / 30.0)
        brzycki_1rm = weight_lbs * (36.0 / (37.0 - reps)) if reps < 37 else epley_1rm
        estimated_1rm = round((epley_1rm + brzycki_1rm) / 2.0, 1)

    percentages = {
        "100% (1RM)": round(estimated_1rm, 1),
        "95% (Heavy / 2-3 reps)": round(estimated_1rm * 0.95, 1),
        "90% (Strength / 3-5 reps)": round(estimated_1rm * 0.90, 1),
        "85% (Strength / 5-6 reps)": round(estimated_1rm * 0.85, 1),
        "80% (Hypertrophy / 8 reps)": round(estimated_1rm * 0.80, 1),
        "75% (Hypertrophy / 10 reps)": round(estimated_1rm * 0.75, 1),
        "70% (Endurance / 12+ reps)": round(estimated_1rm * 0.70, 1),
    }

    return {
        "weight_lifted_lbs": weight_lbs,
        "reps_performed": reps,
        "estimated_1rm_lbs": round(estimated_1rm, 1),
        "target_percentages_lbs": percentages,
    }


def get_motivational_quote() -> Dict[str, Any]:
    """Fetch a real-time motivational quote to inspire workouts and athletic mindset from ZenQuotes API.

    Reads optional API key from ZENQUOTES_API_KEY environment variable.

    Returns:
        Dictionary containing quote text, author, and API source.
    """
    api_key = os.getenv("ZENQUOTES_API_KEY", "")
    url = "https://zenquotes.io/api/random"
    if api_key:
        url = f"https://zenquotes.io/api/random/{api_key}"

    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "WorkoutCoachAgent/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                return {
                    "quote": item.get("q", ""),
                    "author": item.get("a", "Unknown"),
                    "source": "ZenQuotes API",
                }
    except Exception as e:
        return {
            "quote": "Push harder than yesterday if you want a different tomorrow.",
            "author": "Workout Coach",
            "fallback": True,
            "error": str(e),
        }

    return {
        "quote": "Success starts with self-discipline.",
        "author": "Unknown",
        "source": "ZenQuotes API",
    }


def generate_workout_image(
    prompt: str,
    tool_context: ToolContext = None,
) -> Dict[str, Any]:
    """Generate an exercise illustration or workout visual using gemini-3.1-flash-lite-image model in global location.

    Saves generated image bytes to Playground Artifacts via tool_context.save_artifact
    and uploads image bytes directly to public Cloud Storage bucket.

    Args:
        prompt: Description of exercise or workout item to illustrate (e.g. 'A athletic person performing a barbell bench press with proper form').

    Returns:
        Dictionary containing filename and public Cloud Storage https URL.
    """
    # 1. Initialize GenAI Client using Vertex AI in global location
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    # 2. Generate Image using gemini-3.1-flash-lite-image
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
    )

    image_bytes = None
    mime_type = "image/jpeg"

    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Failed to generate image from model response."}

    ext = "png" if "png" in mime_type else "jpg"
    filename = f"workout_{int(datetime.datetime.now().timestamp())}.{ext}"

    # (1) Save image bytes with tool_context.save_artifact for Playground Artifacts panel
    if tool_context is not None:
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload image bytes directly to public Cloud Storage bucket without local file write
    try:
        try:
            token = (
                subprocess.check_output(
                    ["gcloud", "auth", "print-access-token"], text=True
                )
                .strip()
            )
            creds = google.oauth2.credentials.Credentials(token)
            storage_client = storage.Client(project=PROJECT_ID, credentials=creds)
        except Exception:
            storage_client = storage.Client(project=PROJECT_ID)

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(image_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        public_url = f"Error uploading to Cloud Storage: {str(e)}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
    }


def generate_workout_video(
    prompt: str,
    tool_context: ToolContext = None,
) -> Dict[str, Any]:
    """Generate a short exercise demonstration or workout video clip using gemini-omni-flash-preview model in global location.

    Saves generated video bytes to Playground Artifacts via tool_context.save_artifact
    and uploads video bytes directly to public Cloud Storage bucket.

    Args:
        prompt: Description of exercise or workout action to demonstrate in video (e.g. 'Demonstrate a dumbbell bicep curl with proper form').

    Returns:
        Dictionary containing filename and public Cloud Storage https URL.
    """
    # 1. Initialize GenAI Client using Vertex AI in global location
    client = genai.Client(
        vertexai=True,
        project=PROJECT_ID,
        location="global",
    )

    # 2. Generate video using gemini-omni-flash-preview via interactions API
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    if res and getattr(res, "output_video", None) and getattr(res.output_video, "data", None):
        video_bytes = res.output_video.data
        if getattr(res.output_video, "mime_type", None):
            mime_type = res.output_video.mime_type

    if not video_bytes:
        return {"error": "Failed to generate video from gemini-omni-flash-preview response."}

    filename = f"workout_video_{int(datetime.datetime.now().timestamp())}.mp4"

    # (1) Save video bytes with tool_context.save_artifact for Playground Artifacts panel
    if tool_context is not None:
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # (2) Upload video bytes directly to public Cloud Storage bucket without local file write
    try:
        try:
            token = (
                subprocess.check_output(
                    ["gcloud", "auth", "print-access-token"], text=True
                )
                .strip()
            )
            creds = google.oauth2.credentials.Credentials(token)
            storage_client = storage.Client(project=PROJECT_ID, credentials=creds)
        except Exception:
            storage_client = storage.Client(project=PROJECT_ID)

        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(filename)
        blob.upload_from_string(video_bytes, content_type=mime_type)
        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"
    except Exception as e:
        public_url = f"Error uploading to Cloud Storage: {str(e)}"

    return {
        "status": "success",
        "filename": filename,
        "public_url": public_url,
    }

