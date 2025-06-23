#!/usr/bin/env python3
"""
Test rapide de la caméra pour vérifier la reconnaissance faciale
"""

import cv2
import face_recognition
import numpy as np
from facial_recognition_system import facial_recognition_system

def test_camera():
    print("🎥 Test de la caméra et reconnaissance faciale...")
    
    # Charger les encodages
    facial_recognition_system.load_encodings()
    print(f"✅ {len(facial_recognition_system.known_face_encodings)} encodages chargés")
    print(f"👥 Personnes connues: {facial_recognition_system.known_face_names}")
    
    # Ouvrir la caméra
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra")
        return False
    
    print("✅ Caméra ouverte avec succès")
    print("📹 Appuyez sur 'q' pour quitter, 'ESPACE' pour tester la reconnaissance")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Impossible de lire la frame")
            break
        
        frame_count += 1
        
        # Test de reconnaissance toutes les 30 frames (environ 1 seconde)
        if frame_count % 30 == 0:
            # Redimensionner pour améliorer les performances
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            print(f"🔍 Frame {frame_count}: {len(face_locations)} visage(s) détecté(s)")
            
            for face_encoding in face_encodings:
                # Comparer avec les visages connus
                matches = face_recognition.compare_faces(
                    facial_recognition_system.known_face_encodings, 
                    face_encoding, 
                    tolerance=0.6
                )
                
                if True in matches:
                    face_distances = face_recognition.face_distance(
                        facial_recognition_system.known_face_encodings, 
                        face_encoding
                    )
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        name = facial_recognition_system.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        print(f"🎯 RECONNAISSANCE: {name} détecté avec {confidence:.1%} de confiance!")
        
        # Dessiner les rectangles sur les visages détectés
        face_locations = face_recognition.face_locations(frame)
        for (top, right, bottom, left) in face_locations:
            # Dessiner rectangle bleu
            cv2.rectangle(frame, (left, top), (right, bottom), (255, 0, 0), 2)
            cv2.putText(frame, "Visage detecte", (left, top-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Afficher la frame
        cv2.imshow('Test Camera - Reconnaissance Faciale', frame)
        
        # Contrôles clavier
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):
            print("🔍 Test de reconnaissance forcé...")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test terminé")
    return True

if __name__ == "__main__":
    test_camera()
