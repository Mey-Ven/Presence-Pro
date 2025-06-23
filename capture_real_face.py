#!/usr/bin/env python3
"""
Script pour capturer votre vraie photo et créer un encodage facial
"""

import cv2
import face_recognition
import numpy as np
import os
import sqlite3
from datetime import datetime

def capture_and_create_encoding():
    print("📸 CAPTURE DE VOTRE PHOTO POUR LA RECONNAISSANCE FACIALE")
    print("=" * 60)
    
    # Créer le dossier pour vos photos
    user_folder = "dataset/Votre_Visage"
    os.makedirs(user_folder, exist_ok=True)
    
    # Ouvrir la caméra
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("❌ Impossible d'ouvrir la caméra")
        return False
    
    print("✅ Caméra ouverte")
    print("📋 Instructions:")
    print("   - Placez-vous bien en face de la caméra")
    print("   - Assurez-vous d'avoir un bon éclairage")
    print("   - Appuyez sur ESPACE pour capturer votre photo")
    print("   - Appuyez sur 'q' pour quitter")
    
    photo_count = 0
    captured_photos = []
    
    while photo_count < 5:  # Capturer 5 photos pour un meilleur encodage
        ret, frame = cap.read()
        if not ret:
            print("❌ Impossible de lire la frame")
            break
        
        # Détecter les visages dans la frame actuelle
        face_locations = face_recognition.face_locations(frame)
        
        # Dessiner les rectangles autour des visages
        for (top, right, bottom, left) in face_locations:
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, f"Visage detecte - Photo {photo_count+1}/5", 
                       (left, top-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Afficher les instructions
        cv2.putText(frame, "ESPACE = Capturer, Q = Quitter", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f"Photos capturees: {photo_count}/5", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow('Capture de votre visage', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):  # Espace pour capturer
            if len(face_locations) > 0:
                photo_path = f"{user_folder}/photo_{photo_count:03d}.jpg"
                cv2.imwrite(photo_path, frame)
                captured_photos.append(photo_path)
                photo_count += 1
                print(f"📸 Photo {photo_count} capturée: {photo_path}")
            else:
                print("⚠️ Aucun visage détecté, repositionnez-vous")
        elif key == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if photo_count == 0:
        print("❌ Aucune photo capturée")
        return False
    
    print(f"✅ {photo_count} photos capturées avec succès")
    
    # Créer l'encodage facial
    print("🧠 Création de l'encodage facial...")
    
    all_encodings = []
    
    for photo_path in captured_photos:
        print(f"   Traitement: {photo_path}")
        image = face_recognition.load_image_file(photo_path)
        face_encodings = face_recognition.face_encodings(image)
        
        if len(face_encodings) > 0:
            all_encodings.append(face_encodings[0])
            print(f"   ✅ Encodage créé")
        else:
            print(f"   ⚠️ Aucun visage détecté dans cette photo")
    
    if len(all_encodings) == 0:
        print("❌ Impossible de créer un encodage facial")
        return False
    
    # Calculer l'encodage moyen pour plus de précision
    average_encoding = np.mean(all_encodings, axis=0)
    
    # Sauvegarder dans la base de données
    print("💾 Sauvegarde dans la base de données...")
    
    conn = sqlite3.connect('attendance.db')
    cursor = conn.cursor()
    
    # Supprimer l'ancien encodage d'Elmehdi
    cursor.execute('DELETE FROM facial_encodings WHERE student_id = ?', 
                   ('b098c21e-238e-49f3-b53a-9e5b3e1276f2',))
    
    # Insérer le nouvel encodage
    cursor.execute('''
        INSERT INTO facial_encodings (student_id, encoding_data, image_path, created_at)
        VALUES (?, ?, ?, ?)
    ''', ('b098c21e-238e-49f3-b53a-9e5b3e1276f2', 
          average_encoding.tobytes(), 
          f"real_capture/{datetime.now().strftime('%Y%m%d_%H%M%S')}", 
          datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    
    print("✅ Encodage sauvegardé avec succès!")
    print("🔄 Redémarrez l'application pour charger le nouvel encodage")
    
    return True

if __name__ == "__main__":
    success = capture_and_create_encoding()
    if success:
        print("\n🎉 SUCCÈS! Votre visage a été enregistré.")
        print("📋 Prochaines étapes:")
        print("   1. Redémarrez l'application Flask")
        print("   2. Allez sur /facial/recognition")
        print("   3. Démarrez la caméra et activez la détection")
        print("   4. Votre visage devrait maintenant être reconnu!")
    else:
        print("\n❌ Échec de l'enregistrement. Réessayez.")
