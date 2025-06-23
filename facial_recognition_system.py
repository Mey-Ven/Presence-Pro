#!/usr/bin/env python3
"""
Système de Reconnaissance Faciale Intégré
Intègre la reconnaissance faciale avec l'interface web

Author: Facial Attendance System
Date: 2025-06-23
"""

import cv2
import face_recognition
import numpy as np
import sqlite3
import pickle
import os
import json
from datetime import datetime, date
import threading
import time
from flask_socketio import emit
import base64

class FacialRecognitionSystem:
    def __init__(self, database_path="attendance.db"):
        self.database_path = database_path
        self.known_face_encodings = []
        self.known_face_names = []
        self.known_face_ids = []
        self.camera = None
        self.is_running = False
        self.current_session_id = None
        self.detection_thread = None
        
        # Charger les encodages existants
        self.load_encodings()
    
    def get_connection(self):
        """Obtenir une connexion à la base de données"""
        return sqlite3.connect(self.database_path)
    
    def load_encodings(self):
        """Charger les encodages faciaux depuis la base de données"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fe.student_id, fe.encoding_data, u.first_name, u.last_name
                FROM facial_encodings fe
                JOIN users u ON fe.student_id = u.id
                WHERE u.role = 'student'
            ''')
            
            results = cursor.fetchall()
            
            self.known_face_encodings = []
            self.known_face_names = []
            self.known_face_ids = []
            
            for student_id, encoding_blob, first_name, last_name in results:
                # Décoder l'encodage depuis la base de données
                encoding = np.frombuffer(encoding_blob, dtype=np.float64)
                self.known_face_encodings.append(encoding)
                self.known_face_names.append(f"{first_name} {last_name}")
                self.known_face_ids.append(student_id)
            
            print(f"✅ {len(self.known_face_encodings)} encodages faciaux chargés")
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors du chargement des encodages: {e}")
    
    def capture_student_image(self, student_id, num_images=5):
        """Capturer des images d'un étudiant pour l'entraînement"""
        try:
            # Créer le dossier dataset s'il n'existe pas
            dataset_dir = "dataset"
            if not os.path.exists(dataset_dir):
                os.makedirs(dataset_dir)
            
            # Obtenir les informations de l'étudiant
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT first_name, last_name FROM users WHERE id = ? AND role = 'student'
            ''', (student_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "Étudiant non trouvé"
            
            first_name, last_name = result
            student_name = f"{first_name} {last_name}"
            
            # Créer le dossier pour cet étudiant
            student_dir = os.path.join(dataset_dir, student_name)
            if not os.path.exists(student_dir):
                os.makedirs(student_dir)
            
            # Initialiser la caméra
            camera = cv2.VideoCapture(0)
            if not camera.isOpened():
                return False, "Impossible d'accéder à la caméra"
            
            captured_images = 0
            print(f"📸 Capture d'images pour {student_name}...")
            print("Appuyez sur ESPACE pour capturer une image, ESC pour terminer")
            
            while captured_images < num_images:
                ret, frame = camera.read()
                if not ret:
                    break
                
                # Afficher le frame
                cv2.putText(frame, f"Images capturees: {captured_images}/{num_images}", 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "ESPACE: Capturer, ESC: Terminer", 
                           (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                
                cv2.imshow(f"Capture - {student_name}", frame)
                
                key = cv2.waitKey(1) & 0xFF
                if key == 32:  # ESPACE
                    # Sauvegarder l'image
                    image_path = os.path.join(student_dir, f"photo_{captured_images:03d}.jpg")
                    cv2.imwrite(image_path, frame)
                    captured_images += 1
                    print(f"✅ Image {captured_images} capturée: {image_path}")
                    
                elif key == 27:  # ESC
                    break
            
            camera.release()
            cv2.destroyAllWindows()
            conn.close()
            
            if captured_images > 0:
                return True, f"{captured_images} images capturées avec succès"
            else:
                return False, "Aucune image capturée"
                
        except Exception as e:
            return False, f"Erreur lors de la capture: {str(e)}"
    
    def train_student_encodings(self, student_id):
        """Entraîner les encodages faciaux pour un étudiant"""
        try:
            # Obtenir les informations de l'étudiant
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT first_name, last_name FROM users WHERE id = ? AND role = 'student'
            ''', (student_id,))
            
            result = cursor.fetchone()
            if not result:
                return False, "Étudiant non trouvé"
            
            first_name, last_name = result
            student_name = f"{first_name} {last_name}"
            student_dir = os.path.join("dataset", student_name)
            
            if not os.path.exists(student_dir):
                return False, f"Dossier d'images non trouvé: {student_dir}"
            
            # Traiter toutes les images dans le dossier
            encodings = []
            image_files = [f for f in os.listdir(student_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            
            if not image_files:
                return False, "Aucune image trouvée dans le dossier"
            
            print(f"🔄 Traitement de {len(image_files)} images pour {student_name}...")
            
            for image_file in image_files:
                image_path = os.path.join(student_dir, image_file)
                
                # Charger et traiter l'image
                image = face_recognition.load_image_file(image_path)
                face_encodings = face_recognition.face_encodings(image)
                
                if face_encodings:
                    encodings.append(face_encodings[0])
                    print(f"✅ Encodage créé pour {image_file}")
                else:
                    print(f"⚠️ Aucun visage détecté dans {image_file}")
            
            if not encodings:
                return False, "Aucun visage détecté dans les images"
            
            # Calculer l'encodage moyen
            average_encoding = np.mean(encodings, axis=0)
            
            # Supprimer les anciens encodages pour cet étudiant
            cursor.execute('DELETE FROM facial_encodings WHERE student_id = ?', (student_id,))
            
            # Sauvegarder le nouvel encodage
            encoding_blob = average_encoding.tobytes()
            cursor.execute('''
                INSERT INTO facial_encodings (student_id, encoding_data, image_path)
                VALUES (?, ?, ?)
            ''', (student_id, encoding_blob, student_dir))
            
            conn.commit()
            conn.close()
            
            # Recharger les encodages
            self.load_encodings()
            
            return True, f"Encodage créé avec succès pour {student_name} ({len(encodings)} images traitées)"
            
        except Exception as e:
            return False, f"Erreur lors de l'entraînement: {str(e)}"
    
    def start_recognition_session(self, session_name="Session de Présence", course_id=None, created_by=None):
        """Démarrer une session de reconnaissance faciale"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Créer une nouvelle session
            cursor.execute('''
                INSERT INTO attendance_sessions (session_name, course_id, created_by)
                VALUES (?, ?, ?)
            ''', (session_name, course_id, created_by))
            
            self.current_session_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Démarrer la reconnaissance
            self.is_running = True
            self.detection_thread = threading.Thread(target=self._recognition_loop)
            self.detection_thread.daemon = True
            self.detection_thread.start()
            
            return True, f"Session démarrée: {session_name}"
            
        except Exception as e:
            return False, f"Erreur lors du démarrage: {str(e)}"
    
    def stop_recognition_session(self):
        """Arrêter la session de reconnaissance faciale"""
        try:
            self.is_running = False
            
            if self.camera:
                self.camera.release()
                self.camera = None
            
            if self.current_session_id:
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE attendance_sessions 
                    SET end_time = CURRENT_TIMESTAMP, status = 'completed'
                    WHERE id = ?
                ''', (self.current_session_id,))
                conn.commit()
                conn.close()
                
                self.current_session_id = None
            
            return True, "Session arrêtée avec succès"
            
        except Exception as e:
            return False, f"Erreur lors de l'arrêt: {str(e)}"
    
    def _recognition_loop(self):
        """Boucle principale de reconnaissance faciale"""
        try:
            # Initialiser la caméra
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                print("❌ Impossible d'accéder à la caméra")
                return
            
            print("🎥 Reconnaissance faciale démarrée...")
            detected_today = set()  # Pour éviter les doublons
            
            while self.is_running:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                
                # Redimensionner pour améliorer les performances
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = small_frame[:, :, ::-1]
                
                # Détecter les visages
                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
                
                for face_encoding in face_encodings:
                    # Comparer avec les visages connus
                    matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                    face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        
                        if matches[best_match_index] and face_distances[best_match_index] < 0.6:
                            student_id = self.known_face_ids[best_match_index]
                            student_name = self.known_face_names[best_match_index]
                            confidence = 1 - face_distances[best_match_index]
                            
                            # Éviter les doublons pour aujourd'hui
                            today_key = f"{student_id}_{date.today()}"
                            if today_key not in detected_today:
                                detected_today.add(today_key)
                                self._record_attendance(student_id, confidence)
                                print(f"✅ Présence enregistrée: {student_name} (confiance: {confidence:.2f})")
                
                time.sleep(0.1)  # Petite pause pour éviter la surcharge
                
        except Exception as e:
            print(f"❌ Erreur dans la boucle de reconnaissance: {e}")
        finally:
            if self.camera:
                self.camera.release()
    
    def _record_attendance(self, student_id, confidence):
        """Enregistrer une présence dans la base de données"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            current_date = date.today()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            cursor.execute('''
                INSERT INTO presences (student_id, date, time, status, detection_confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, current_date, current_time, 'Present', confidence))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement: {e}")
    
    def get_today_attendance(self):
        """Obtenir les présences d'aujourd'hui"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT p.*, u.first_name, u.last_name
                FROM presences p
                JOIN users u ON p.student_id = u.id
                WHERE p.date = ?
                ORDER BY p.time DESC
            ''', (date.today(),))
            
            results = cursor.fetchall()
            conn.close()
            
            attendance = []
            for row in results:
                attendance.append({
                    'id': row[0],
                    'student_id': row[1],
                    'date': row[3],
                    'time': row[4],
                    'status': row[5],
                    'confidence': row[6],
                    'student_name': f"{row[8]} {row[9]}"
                })
            
            return attendance
            
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return []

# Instance globale
facial_recognition_system = FacialRecognitionSystem()
