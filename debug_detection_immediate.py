#!/usr/bin/env python3
"""
Debug immédiat de la détection faciale
"""

import cv2
import face_recognition
import numpy as np
from facial_recognition_system import facial_recognition_system

def debug_detection_immediate():
    print("🔍 DEBUG IMMÉDIAT - DÉTECTION FACIALE")
    print("=" * 50)
    
    # Charger les encodages
    facial_recognition_system.load_encodings()
    print(f"📊 Encodages chargés: {len(facial_recognition_system.known_face_encodings)}")
    print(f"👥 Noms: {facial_recognition_system.known_face_names}")
    
    if len(facial_recognition_system.known_face_encodings) == 0:
        print("❌ Aucun encodage chargé!")
        return
    
    # Ouvrir la caméra
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra")
        return
    
    print("✅ Caméra ouverte")
    print("📋 Instructions:")
    print("   - Placez-vous devant la caméra")
    print("   - 'q' pour quitter")
    print("   - 't' pour test de reconnaissance forcé")
    
    frame_count = 0
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Test toutes les 15 frames (environ 0.5 seconde)
        if frame_count % 15 == 0:
            print(f"\n🔍 Frame {frame_count} - Test détection...")
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(frame)
            print(f"   👥 {len(face_locations)} visage(s) détecté(s)")
            
            if len(face_locations) > 0:
                # Créer les encodages
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                print(f"   🧠 {len(face_encodings)} encodage(s) créé(s)")
                
                for i, face_encoding in enumerate(face_encodings):
                    print(f"   🎯 Test visage {i+1}:")
                    
                    # Calculer les distances
                    face_distances = face_recognition.face_distance(
                        facial_recognition_system.known_face_encodings, 
                        face_encoding
                    )
                    
                    min_distance = np.min(face_distances)
                    print(f"      📏 Distance: {min_distance:.3f}")
                    
                    # Test avec différentes tolérances
                    tolerances = [0.4, 0.5, 0.6, 0.7]
                    for tolerance in tolerances:
                        matches = face_recognition.compare_faces(
                            facial_recognition_system.known_face_encodings, 
                            face_encoding,
                            tolerance=tolerance
                        )
                        
                        if True in matches:
                            best_match_index = np.argmin(face_distances)
                            name = facial_recognition_system.known_face_names[best_match_index]
                            confidence = 1 - face_distances[best_match_index]
                            print(f"      ✅ MATCH avec tolérance {tolerance}: {name} ({confidence:.1%})")
                            break
                    else:
                        print(f"      ❌ Aucun match avec toutes les tolérances testées")
            else:
                print("   ⚠️ Aucun visage détecté dans cette frame")
        
        # Dessiner les rectangles sur tous les visages
        face_locations = face_recognition.face_locations(frame)
        for (top, right, bottom, left) in face_locations:
            # Rectangle vert pour indiquer la détection
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"Visage {len(face_locations)}", (left, top-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Afficher les informations
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Visages: {len(face_locations)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Encodages: {len(facial_recognition_system.known_face_encodings)}", (10, 90), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('Debug Detection Immediate', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('t'):
            print("\n🔍 TEST FORCÉ DE RECONNAISSANCE...")
            # Test immédiat
            face_locations = face_recognition.face_locations(frame)
            if len(face_locations) > 0:
                face_encodings = face_recognition.face_encodings(frame, face_locations)
                for face_encoding in face_encodings:
                    face_distances = face_recognition.face_distance(
                        facial_recognition_system.known_face_encodings, 
                        face_encoding
                    )
                    print(f"Distance calculée: {face_distances[0]:.3f}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test terminé")

if __name__ == "__main__":
    debug_detection_immediate()
