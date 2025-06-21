import face_recognition
import os
import cv2
import pickle

path = 'dataset'
known_encodings = []
known_names = []

# Parcours des images
for filename in os.listdir(path):
    if filename.endswith(".jpg"):
        img_path = os.path.join(path, filename)
        image = face_recognition.load_image_file(img_path)
        encodings = face_recognition.face_encodings(image)

        if len(encodings) > 0:
            encoding = encodings[0]
            name = "_".join(filename.split("_")[:2])  # Ex: mehdi_rahaoui
            known_encodings.append(encoding)
            known_names.append(name)
            print(f"[OK] Encodé : {filename}")
        else:
            print(f"[SKIPPED] Aucun visage détecté dans {filename}")

# Sauvegarde dans un fichier .pickle
data = {"encodings": known_encodings, "names": known_names}
with open("encodings.pickle", "wb") as f:
    pickle.dump(data, f)

print("Tous les encodages sont sauvegardés dans encodings.pickle.")