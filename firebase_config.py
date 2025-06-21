"""
Firebase configuration file for the facial recognition attendance system.
This file contains the Firebase initialization code and helper functions.
"""

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import os
import datetime

# Function to normalize name format (ensure consistency between encodings and Firebase)
def normalize_name(name):
    """Normalize name format to ensure consistency

    This function ensures that names are stored in a consistent format
    regardless of whether they contain spaces or underscores.

    Args:
        name (str): Name to normalize

    Returns:
        str: Normalized name (with underscores instead of spaces)
    """
    # Replace spaces with underscores to match the format in encodings.pickle
    return name.replace(" ", "_")

# Path to the Firebase service account key file
# You need to download this file from your Firebase project settings
# and place it in the same directory as this script
CREDS_FILE = "serviceAccountKey.json"

# Initialize Firebase if not already initialized
def initialize_firebase():
    """Initialize Firebase if not already initialized"""
    try:
        # Check if Firebase is already initialized
        firebase_admin.get_app()
        print("Firebase already initialized")
    except ValueError:
        # If not, initialize Firebase with credentials
        if os.path.exists(CREDS_FILE):
            cred = credentials.Certificate(CREDS_FILE)
            firebase_admin.initialize_app(cred)
            print("Firebase initialized successfully")
        else:
            print(f"ERROR: {CREDS_FILE} not found. Please download it from Firebase console.")
            print("Firebase initialization failed")
            return False
    return True

# Get Firestore database instance
def get_db():
    """Get Firestore database instance"""
    if initialize_firebase():
        return firestore.client()
    return None

# Add attendance record to Firestore
def add_attendance(name, date, time):
    """Add attendance record to Firestore

    Args:
        name (str): Name of the person
        date (str): Date in YYYY-MM-DD format
        time (str): Time in HH:MM:SS format

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        db = get_db()
        if not db:
            return False

        # Normalize the name to ensure consistency
        normalized_name = normalize_name(name)

        # Create a reference to the attendance collection
        attendance_ref = db.collection('attendance')

        # Create a document with a timestamp as the ID
        doc_ref = attendance_ref.document()

        # Add the attendance record
        doc_ref.set({
            'name': normalized_name,
            'date': date,
            'time': time,
            'timestamp': firestore.SERVER_TIMESTAMP
        })

        print(f"Attendance record added to Firebase for {name}")
        return True
    except Exception as e:
        print(f"Error adding attendance record to Firebase: {e}")
        return False

# Check if a person is already marked present today
def is_present_today(name, date):
    """Check if a person is already marked present today

    Args:
        name (str): Name of the person
        date (str): Date in YYYY-MM-DD format

    Returns:
        bool: True if present, False otherwise
    """
    try:
        db = get_db()
        if not db:
            return False

        # Normalize the name to ensure consistency
        normalized_name = normalize_name(name)

        # Query the attendance collection
        query = db.collection('attendance').where('name', '==', normalized_name).where('date', '==', date)
        results = query.get()

        # If there are any results, the person is already marked present
        return len(results) > 0
    except Exception as e:
        print(f"Error checking attendance record in Firebase: {e}")
        return False

# Get all attendance records
def get_all_attendance():
    """Get all attendance records

    Returns:
        list: List of attendance records
    """
    try:
        db = get_db()
        if not db:
            return []

        # Query the attendance collection
        results = db.collection('attendance').order_by('timestamp', direction=firestore.Query.DESCENDING).get()

        # Convert the results to a list of dictionaries
        attendance_list = []
        for doc in results:
            data = doc.to_dict()
            attendance_list.append(data)

        return attendance_list
    except Exception as e:
        print(f"Error getting attendance records from Firebase: {e}")
        return []

# Get attendance records for a specific date
def get_attendance_by_date(date):
    """Get attendance records for a specific date

    Args:
        date (str): Date in YYYY-MM-DD format

    Returns:
        list: List of attendance records for the specified date
    """
    try:
        db = get_db()
        if not db:
            return []

        # Query the attendance collection
        results = db.collection('attendance').where('date', '==', date).get()

        # Convert the results to a list of dictionaries
        attendance_list = []
        for doc in results:
            data = doc.to_dict()
            attendance_list.append(data)

        return attendance_list
    except Exception as e:
        print(f"Error getting attendance records from Firebase: {e}")
        return []

# Get attendance records for a specific person
def get_attendance_by_person(name):
    """Get attendance records for a specific person

    Args:
        name (str): Name of the person

    Returns:
        list: List of attendance records for the specified person
    """
    try:
        db = get_db()
        if not db:
            return []

        # Normalize the name to ensure consistency
        normalized_name = normalize_name(name)

        # Query the attendance collection
        results = db.collection('attendance').where('name', '==', normalized_name).order_by('timestamp', direction=firestore.Query.DESCENDING).get()

        # Convert the results to a list of dictionaries
        attendance_list = []
        for doc in results:
            data = doc.to_dict()
            attendance_list.append(data)

        return attendance_list
    except Exception as e:
        print(f"Error getting attendance records from Firebase: {e}")
        return []
