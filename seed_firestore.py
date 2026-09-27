"""Seed script for Firestore database (workout-coach-agent)."""

import subprocess
from google.cloud import firestore
import google.auth
import google.oauth2.credentials

# Hardcode the project ID as a string literal (required for Agent Platform)
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-03-71206494f81b"


def get_firestore_client() -> firestore.Client:
    """Gets a Firestore client using gcloud auth token when running locally."""
    try:
        token = (
            subprocess.check_output(
                ["gcloud", "auth", "print-access-token"], text=True
            )
            .strip()
        )
        creds = google.oauth2.credentials.Credentials(token)
        return firestore.Client(project=FIRESTORE_PROJECT_ID, credentials=creds)
    except Exception:
        return firestore.Client(project=FIRESTORE_PROJECT_ID)


def seed_database():
    db = get_firestore_client()

    # 1. Seed Exercises Catalog
    exercises = [
        {
            "exercise_id": "ex-01",
            "name": "Barbell Bench Press",
            "category": "Strength",
            "target_muscle": "Chest",
            "difficulty": "Intermediate",
            "equipment": "Barbell & Bench",
            "instructions": "Lie flat on the bench, grip the barbell slightly wider than shoulder-width, lower the bar smoothly to your mid-chest, and press explosively upwards.",
        },
        {
            "exercise_id": "ex-02",
            "name": "Barbell Back Squat",
            "category": "Strength",
            "target_muscle": "Quadriceps & Glutes",
            "difficulty": "Intermediate",
            "equipment": "Barbell & Squat Rack",
            "instructions": "Place barbell on upper traps, brace core, sit back into hips until thighs are parallel to ground, and drive through heels to stand.",
        },
        {
            "exercise_id": "ex-03",
            "name": "Conventional Deadlift",
            "category": "Strength",
            "target_muscle": "Hamstrings & Lower Back",
            "difficulty": "Advanced",
            "equipment": "Barbell",
            "instructions": "Stand with feet hip-width under bar, hinge at hips, grip bar, engage lats, pull chest up, and push floor away to lockout.",
        },
        {
            "exercise_id": "ex-04",
            "name": "Dumbbell Shoulder Press",
            "category": "Strength",
            "target_muscle": "Deltoids",
            "difficulty": "Beginner",
            "equipment": "Dumbbells",
            "instructions": "Sit upright with dumbbells at shoulder height, palms forward, and press upward until arms are fully extended above head.",
        },
        {
            "exercise_id": "ex-05",
            "name": "Pull-Ups",
            "category": "Bodyweight",
            "target_muscle": "Latissimus Dorsi",
            "difficulty": "Intermediate",
            "equipment": "Pull-Up Bar",
            "instructions": "Grip bar overhead palms facing away, pull chest toward bar squeezing shoulder blades together, then lower with control.",
        },
    ]

    print("Seeding exercises...")
    for ex in exercises:
        doc_ref = db.collection("exercises").document(ex["exercise_id"])
        doc_ref.set(ex)
        print(f"  ✓ Added exercise: {ex['name']}")

    # 2. Seed Sample Workout Logs
    logs = [
        {
            "log_id": "log-101",
            "user_id": "athlete_1",
            "exercise_name": "Barbell Bench Press",
            "sets": 4,
            "reps": 8,
            "weight_lbs": 185.0,
            "date": "2026-09-25",
            "notes": "Felt strong, good form on last set.",
        },
        {
            "log_id": "log-102",
            "user_id": "athlete_1",
            "exercise_name": "Barbell Back Squat",
            "sets": 3,
            "reps": 10,
            "weight_lbs": 225.0,
            "date": "2026-09-26",
            "notes": "Focused on depth and hip drive.",
        },
    ]

    print("Seeding sample workout logs...")
    for log in logs:
        doc_ref = db.collection("workout_logs").document(log["log_id"])
        doc_ref.set(log)
        print(f"  ✓ Added workout log for user '{log['user_id']}': {log['exercise_name']}")

    print("\nDatabase seeding completed successfully! ✅")


if __name__ == "__main__":
    seed_database()
