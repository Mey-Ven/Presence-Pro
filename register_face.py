import cv2
import os

# Create the dataset folder if it doesn't exist
if not os.path.exists("dataset"):
    os.makedirs("dataset")

# Get student's first and last name
prenom = input("Enter student's first name: ").strip()
nom = input("Enter student's last name: ").strip()
full_name = f"{prenom}_{nom}"
count = 0
max_photos = 10

# Open the camera
def open_camera():
    for i in range(3):  # Try camera index 0, 1, 2
        cap = cv2.VideoCapture(i)
        if cap is not None and cap.isOpened():
            print(f"Camera found at index {i}")
            return cap
    return None

cap = open_camera()
if cap is None:
    print("No camera found. Please check your connection.")
    exit()

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

print(f"Press 's' to save a photo, 'q' to quit. Max: {max_photos} photos.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error accessing camera.")
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Draw rectangles and show count
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Display counter on screen
    cv2.putText(frame, f"Photos saved: {count}/{max_photos}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    cv2.imshow("Press 's' to save, 'q' to quit", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('s'):
        if len(faces) == 0:
            print("No face detected. Try again.")
            continue
        if count >= max_photos:
            print("Max number of photos reached.")
            break
        for (x, y, w, h) in faces:
            face = frame[y:y+h, x:x+w]
            count += 1
            cv2.imwrite(f"dataset/{full_name}_{count}.jpg", face)
            print(f"Image {count} saved.")
            break  # Save one face at a time
    elif key == ord('q'):
        break

    if count >= max_photos:
        print("Photo limit reached. Ending session.")
        break

cap.release()
cv2.destroyAllWindows()
print(f"{count} photo(s) saved for {full_name}.")