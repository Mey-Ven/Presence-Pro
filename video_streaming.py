#!/usr/bin/env python3
"""
Module de Streaming Vidéo pour Reconnaissance Faciale
Gère le streaming en temps réel avec détection et reconnaissance faciale

Author: Facial Attendance System
Date: 2025-06-23
"""

import cv2
import face_recognition
import numpy as np
import threading
import time
from datetime import datetime, date
import base64
import io
from PIL import Image
import sqlite3

class VideoStreamer:
    def __init__(self, facial_recognition_system):
        self.facial_system = facial_recognition_system
        self.camera = None
        self.is_streaming = False
        self.current_frame = None
        self.frame_lock = threading.Lock()
        self.detection_enabled = False
        self.last_detections = []
        self.last_detection_time = {}  # Pour éviter les détections répétées
        self.detection_cooldown = 30  # 30 secondes entre les détections du même visage
        self.frame_count = 0
        self.detection_stats = {
            'total_frames': 0,
            'frames_with_faces': 0,
            'successful_recognitions': 0
        }
        
    def start_streaming(self):
        """Démarrer le streaming vidéo"""
        if self.is_streaming:
            return True, "Streaming déjà actif"
            
        try:
            # Libérer toute caméra existante
            if self.camera is not None:
                self.camera.release()

            # Initialiser la caméra
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                return False, "Impossible d'accéder à la caméra"

            # Configurer la caméra pour de meilleures performances
            self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.camera.set(cv2.CAP_PROP_FPS, 30)
            self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Réduire le buffer

            # Test de capture immédiat
            ret, test_frame = self.camera.read()
            if not ret:
                self.camera.release()
                return False, "Caméra accessible mais aucune image"

            self.is_streaming = True

            # Démarrer le thread de capture
            self.capture_thread = threading.Thread(target=self._capture_loop)
            self.capture_thread.daemon = True
            self.capture_thread.start()

            print(f"✅ Streaming démarré - Résolution: {test_frame.shape}")
            return True, "Streaming démarré avec succès"

        except Exception as e:
            if self.camera:
                self.camera.release()
            return False, f"Erreur lors du démarrage: {str(e)}"
    
    def stop_streaming(self):
        """Arrêter le streaming vidéo"""
        self.is_streaming = False
        self.detection_enabled = False
        
        if self.camera:
            self.camera.release()
            self.camera = None
            
        return True, "Streaming arrêté"
    
    def enable_detection(self):
        """Activer la détection faciale"""
        self.detection_enabled = True
        return True, "Détection faciale activée"
    
    def disable_detection(self):
        """Désactiver la détection faciale"""
        self.detection_enabled = False
        self.last_detections = []
        return True, "Détection faciale désactivée"
    
    def _capture_loop(self):
        """Boucle principale de capture vidéo"""
        while self.is_streaming and self.camera:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    continue
                
                # Traitement du frame
                processed_frame = self._process_frame(frame)
                
                # Stocker le frame traité
                with self.frame_lock:
                    self.current_frame = processed_frame
                
                # Petite pause pour éviter la surcharge
                time.sleep(0.033)  # ~30 FPS
                
            except Exception as e:
                print(f"Erreur dans la boucle de capture: {e}")
                break
    
    def _process_frame(self, frame):
        """Traiter un frame avec détection faciale optionnelle"""
        if not self.detection_enabled:
            return frame
        
        try:
            # Redimensionner pour améliorer les performances
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = small_frame[:, :, ::-1]
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            # Debug: afficher le nombre de visages détectés
            if len(face_locations) > 0:
                print(f"🔍 {len(face_locations)} visage(s) détecté(s) dans la frame")
            
            current_detections = []
            
            # Traiter chaque visage détecté
            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                # Redimensionner les coordonnées
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                
                # Identifier le visage
                name = "Inconnu"
                confidence = 0.0
                color = (0, 0, 255)  # Rouge par défaut
                
                if len(self.facial_system.known_face_encodings) > 0:
                    matches = face_recognition.compare_faces(
                        self.facial_system.known_face_encodings,
                        face_encoding,
                        tolerance=0.6  # Augmenter la tolérance pour plus de détections
                    )
                    face_distances = face_recognition.face_distance(
                        self.facial_system.known_face_encodings,
                        face_encoding
                    )
                    
                    if len(face_distances) > 0:
                        best_match_index = np.argmin(face_distances)
                        distance = face_distances[best_match_index]

                        print(f"🎯 Distance minimale: {distance:.3f} (seuil: 0.5)")

                        if matches[best_match_index] and distance < 0.6:
                            name = self.facial_system.known_face_names[best_match_index]
                            confidence = 1 - distance
                            color = (255, 0, 0)  # Bleu pour visage reconnu

                            # Enregistrer la présence (marquée comme présent)
                            student_id = self.facial_system.known_face_ids[best_match_index]
                            self._record_attendance(student_id, confidence, "Present")

                            print(f"✅ RECONNAISSANCE: {name} détecté avec {confidence:.1%} de confiance - Marqué PRÉSENT")
                        else:
                            print(f"❌ Visage non reconnu (distance: {distance:.3f})")
                
                # Dessiner le rectangle bleu autour du visage
                cv2.rectangle(frame, (left, top), (right, bottom), color, 3)

                # Fond semi-transparent pour le texte
                overlay = frame.copy()
                cv2.rectangle(overlay, (left, bottom - 40), (right, bottom), color, -1)
                cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

                # Texte avec nom et confiance
                text = f"{name}"
                if confidence > 0:
                    text += f" ({confidence:.1%})"

                # Texte principal (nom)
                cv2.putText(frame, text, (left + 6, bottom - 20),
                           cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 2)

                # Texte secondaire (statut)
                status_text = "PRÉSENT" if name != "Inconnu" else "NON RECONNU"
                cv2.putText(frame, status_text, (left + 6, bottom - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                current_detections.append({
                    'name': name,
                    'confidence': confidence,
                    'location': (left, top, right, bottom)
                })
            
            self.last_detections = current_detections
            
            # Ajouter des informations de statut
            self._add_status_overlay(frame)
            
            return frame
            
        except Exception as e:
            print(f"Erreur lors du traitement du frame: {e}")
            return frame
    
    def _add_status_overlay(self, frame):
        """Ajouter des informations de statut sur le frame"""
        height, width = frame.shape[:2]
        
        # Fond semi-transparent pour les informations
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (width - 10, 100), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)
        
        # Informations de statut
        status_text = f"Reconnaissance: {'ACTIVE' if self.detection_enabled else 'INACTIVE'}"
        cv2.putText(frame, status_text, (20, 35), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if self.detection_enabled else (0, 0, 255), 2)
        
        faces_text = f"Visages detectes: {len(self.last_detections)}"
        cv2.putText(frame, faces_text, (20, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        known_faces_text = f"Visages connus: {len(self.facial_system.known_face_encodings)}"
        cv2.putText(frame, known_faces_text, (20, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (width - 200, height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _record_attendance(self, student_id, confidence, status="Present"):
        """Enregistrer une présence (marquée comme absence selon les exigences)"""
        try:
            # Éviter les doublons pour la même journée
            today_key = f"{student_id}_{date.today()}"
            if hasattr(self, '_recorded_today'):
                if today_key in self._recorded_today:
                    return
            else:
                self._recorded_today = set()
            
            self._recorded_today.add(today_key)
            
            # Enregistrer dans la base de données
            conn = sqlite3.connect("attendance.db")
            cursor = conn.cursor()
            
            current_date = date.today()
            current_time = datetime.now().strftime("%H:%M:%S")
            
            cursor.execute('''
                INSERT INTO presences (student_id, date, time, status, detection_confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (student_id, current_date, current_time, status, confidence))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Présence enregistrée: {student_id} - {status} (confiance: {confidence:.2f})")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'enregistrement: {e}")
    
    def get_current_frame_base64(self):
        """Obtenir le frame actuel encodé en base64 pour le streaming web"""
        with self.frame_lock:
            if self.current_frame is None:
                return None
            
            try:
                # Encoder le frame en JPEG
                _, buffer = cv2.imencode('.jpg', self.current_frame, 
                                       [cv2.IMWRITE_JPEG_QUALITY, 85])
                
                # Convertir en base64
                frame_base64 = base64.b64encode(buffer).decode('utf-8')
                return frame_base64
                
            except Exception as e:
                print(f"Erreur lors de l'encodage du frame: {e}")
                return None
    
    def get_detection_info(self):
        """Obtenir les informations de détection actuelles"""
        return {
            'is_streaming': self.is_streaming,
            'detection_enabled': self.detection_enabled,
            'detections': self.last_detections,
            'known_faces_count': len(self.facial_system.known_face_encodings)
        }

# Instance globale
video_streamer = None

def get_video_streamer(facial_system):
    """Obtenir l'instance du streamer vidéo"""
    global video_streamer
    if video_streamer is None:
        video_streamer = VideoStreamer(facial_system)
    return video_streamer
