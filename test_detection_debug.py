#!/usr/bin/env python3
"""
Test de détection faciale avec debug complet
"""

import cv2
import face_recognition
import numpy as np
from facial_recognition_system import facial_recognition_system

def test_detection_with_debug():
    print("🔍 TEST DE DÉTECTION FACIALE AVEC DEBUG")
    print("=" * 50)
    
    # Charger les encodages
    facial_recognition_system.load_encodings()
    print(f"📊 Encodages chargés: {len(facial_recognition_system.known_face_encodings)}")
    print(f"👥 Noms: {facial_recognition_system.known_face_names}")
    
    # Ouvrir la caméra
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra")
        return
    
    print("✅ Caméra ouverte")
    print("📋 Instructions:")
    print("   - 'q' pour quitter")
    print("   - 'd' pour debug détaillé")
    print("   - 's' pour sauvegarder une frame")
    
    frame_count = 0
    debug_mode = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Test de détection toutes les 10 frames
        if frame_count % 10 == 0:
            print(f"\n🔍 Frame {frame_count} - Test de détection...")
            
            # Redimensionner pour améliorer les performances
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_small_frame)
            print(f"   👥 {len(face_locations)} visage(s) détecté(s)")
            
            if len(face_locations) > 0:
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                print(f"   🧠 {len(face_encodings)} encodage(s) créé(s)")
                
                for i, face_encoding in enumerate(face_encodings):
                    print(f"   🔍 Test visage {i+1}:")
                    
                    if len(facial_recognition_system.known_face_encodings) > 0:
                        # Comparer avec les visages connus
                        face_distances = face_recognition.face_distance(
                            facial_recognition_system.known_face_encodings, 
                            face_encoding
                        )
                        
                        min_distance = np.min(face_distances)
                        print(f"      📏 Distance minimale: {min_distance:.3f}")
                        
                        matches = face_recognition.compare_faces(
                            facial_recognition_system.known_face_encodings, 
                            face_encoding,
                            tolerance=0.6  # Tolérance plus élevée pour le test
                        )
                        
                        if True in matches:
                            best_match_index = np.argmin(face_distances)
                            name = facial_recognition_system.known_face_names[best_match_index]
                            confidence = 1 - face_distances[best_match_index]
                            print(f"      ✅ MATCH: {name} (confiance: {confidence:.1%})")
                        else:
                            print(f"      ❌ Aucun match trouvé")
                    else:
                        print(f"      ⚠️ Aucun encodage de référence")
        
        # Dessiner les rectangles sur tous les visages détectés
        face_locations = face_recognition.face_locations(frame)
        for (top, right, bottom, left) in face_locations:
            # Rectangle vert pour indiquer la détection
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, "Visage detecte", (left, top-10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Afficher les informations
        cv2.putText(frame, f"Frame: {frame_count}", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Visages: {len(face_locations)}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Q=Quitter, D=Debug, S=Save", (10, frame.shape[0]-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        cv2.imshow('Test Detection Debug', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('d'):
            debug_mode = not debug_mode
            print(f"🔧 Mode debug: {'ON' if debug_mode else 'OFF'}")
        elif key == ord('s'):
            filename = f"debug_frame_{frame_count}.jpg"
            cv2.imwrite(filename, frame)
            print(f"💾 Frame sauvegardée: {filename}")
    
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Test terminé")

if __name__ == "__main__":
    test_detection_with_debug()
