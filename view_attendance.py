"""
Script to view attendance records from Firebase.
"""

import firebase_config
from datetime import datetime
import sys

def display_attendance(attendance_list):
    """Display attendance records in a formatted way"""
    if not attendance_list:
        print("No attendance records found.")
        return

    print("\n{:<20} {:<12} {:<10}".format("Name", "Date", "Time"))
    print("-" * 45)

    for record in attendance_list:
        # Format the name for display (replace underscores with spaces)
        name = record.get('name', 'N/A').replace('_', ' ')

        print("{:<20} {:<12} {:<10}".format(
            name,
            record.get('date', 'N/A'),
            record.get('time', 'N/A')
        ))
    print()

def main():
    """Main function"""
    # Initialize Firebase
    if not firebase_config.initialize_firebase():
        print("Failed to initialize Firebase. Exiting.")
        sys.exit(1)

    # Parse command line arguments
    if len(sys.argv) == 1:
        # No arguments, show all records
        print("\nShowing all attendance records:")
        attendance_list = firebase_config.get_all_attendance()
        display_attendance(attendance_list)

    elif len(sys.argv) == 2 and sys.argv[1] == "today":
        # Show today's records
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\nShowing attendance records for today ({today}):")
        attendance_list = firebase_config.get_attendance_by_date(today)
        display_attendance(attendance_list)

    elif len(sys.argv) == 3 and sys.argv[1] == "date":
        # Show records for a specific date
        date = sys.argv[2]
        print(f"\nShowing attendance records for {date}:")
        attendance_list = firebase_config.get_attendance_by_date(date)
        display_attendance(attendance_list)

    elif len(sys.argv) == 3 and sys.argv[1] == "person":
        # Show records for a specific person
        name = sys.argv[2]
        # Normalize the name for the query but display the original format
        print(f"\nShowing attendance records for {name}:")
        attendance_list = firebase_config.get_attendance_by_person(name)
        display_attendance(attendance_list)

    else:
        # Invalid arguments
        print("\nUsage:")
        print("  python view_attendance.py                  - Show all records")
        print("  python view_attendance.py today            - Show today's records")
        print("  python view_attendance.py date YYYY-MM-DD  - Show records for a specific date")
        print("  python view_attendance.py person NAME      - Show records for a specific person")

if __name__ == "__main__":
    main()
