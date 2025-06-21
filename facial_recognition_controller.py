"""
Contrôleur de reconnaissance faciale pour l'intégration avec le tableau de bord web
Ce module permet de contrôler le système de reconnaissance faciale depuis l'interface web
"""

import cv2
import face_recognition
import pickle
import numpy as np
import threading
import time
import os
import base64
from datetime import datetime
from camera_manager import CameraManager
import sqlite_database as db
import sqlite_config as config

class FacialRecognitionController:
    def __init__(self, socketio=None):
        """
        Initialise le contrôleur de reconnaissance faciale
        
        Args:
            socketio: Instance SocketIO pour les mises à jour en temps réel
        """
        self.socketio = socketio
        self.is_running = False
        self.camera = None
        self.camera_manager = None
        self.recognition_thread = None
        self.known_face_encodings = []
        self.known_face_names = []
        self.frame_count = 0
        self.last_recognition_time = {}
        self.recognition_cooldown = 30  # 30 secondes entre les reconnaissances
        
        # Charger les encodages faciaux
        self.load_face_encodings()
    
    def load_face_encodings(self):
        """Charge les encodages faciaux depuis le fichier pickle"""
        try:
            if os.path.exists("encodings.pickle"):
                with open("encodings.pickle", "rb") as f:
                    data = pickle.load(f)
                    self.known_face_encodings = data["encodings"]
                    self.known_face_names = data["names"]
                
                self.emit_status(f"✅ {len(self.known_face_names)} visages chargés")
                return True
            else:
                self.emit_status("⚠️ Aucun fichier d'encodages trouvé")
                return False
        except Exception as e:
            self.emit_status(f"❌ Erreur lors du chargement des encodages: {e}")
            return False
    
    def emit_status(self, message, status_type="info"):
        """Émet un message de statut via WebSocket"""
        if self.socketio:
            self.socketio.emit('recognition_status', {
                'message': message,
                'type': status_type,
                'timestamp': datetime.now().isoformat()
            })
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    def emit_attendance(self, name, confidence=None):
        """Émet une notification de présence via WebSocket"""
        if self.socketio:
            now = datetime.now()
            self.socketio.emit('attendance_detected', {
                'name': name,
                'date': now.strftime("%Y-%m-%d"),
                'time': now.strftime("%H:%M:%S"),
                'confidence': confidence,
                'timestamp': now.isoformat()
            })
    
    def emit_frame(self, frame):
        """Émet une frame de caméra via WebSocket pour l'affichage en direct"""
        if self.socketio:
            try:
                # Redimensionner la frame pour l'affichage web
                display_frame = cv2.resize(frame, (640, 480))

                # Encoder en JPEG
                _, buffer = cv2.imencode('.jpg', display_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])

                # Encoder en base64
                frame_base64 = base64.b64encode(buffer).decode('utf-8')

                # Debug: Log frame emission (only every 30 frames to avoid spam)
                if self.frame_count % 30 == 0:
                    print(f"[DEBUG] Émission frame {self.frame_count}: {len(frame_base64)} caractères")

                self.socketio.emit('camera_frame', {
                    'frame': frame_base64,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                print(f"Erreur lors de l'émission de la frame: {e}")
        else:
            # Debug: Log when socketio is not available
            if self.frame_count % 30 == 0:
                print(f"[DEBUG] SocketIO non disponible pour l'émission de frame {self.frame_count}")
    
    def start_recognition(self):
        """Démarre le système de reconnaissance faciale"""
        if self.is_running:
            self.emit_status("⚠️ La reconnaissance est déjà en cours", "warning")
            return False
        
        self.emit_status("🚀 Démarrage de la reconnaissance faciale...")
        
        # Initialiser la caméra
        if not self.initialize_camera():
            return False
        
        # Vérifier les encodages
        if not self.known_face_encodings:
            if not self.load_face_encodings():
                self.emit_status("❌ Impossible de charger les encodages faciaux", "error")
                return False
        
        # Démarrer le thread de reconnaissance
        self.is_running = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop, daemon=True)
        self.recognition_thread.start()
        
        self.emit_status("✅ Reconnaissance faciale démarrée", "success")
        return True
    
    def stop_recognition(self):
        """Arrête le système de reconnaissance faciale"""
        if not self.is_running:
            self.emit_status("⚠️ La reconnaissance n'est pas en cours", "warning")
            return False
        
        self.emit_status("🛑 Arrêt de la reconnaissance faciale...")
        
        self.is_running = False
        
        # Attendre que le thread se termine
        if self.recognition_thread and self.recognition_thread.is_alive():
            self.recognition_thread.join(timeout=5)
        
        # Libérer la caméra
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.emit_status("✅ Reconnaissance faciale arrêtée", "success")
        return True
    
    def initialize_camera(self):
        """Initialise la caméra avec le gestionnaire intelligent"""
        try:
            self.emit_status("🎥 Initialisation de la caméra...")
            
            self.camera_manager = CameraManager()
            self.camera = self.camera_manager.get_best_camera()
            
            if self.camera is None:
                self.emit_status("❌ Aucune caméra disponible", "error")
                return False
            
            # Obtenir les informations de la caméra
            camera_info = self.camera_manager.get_camera_info()
            if camera_info:
                camera_type = "🖥️ Intégrée" if camera_info['is_builtin'] else "🔌 Externe"
                self.emit_status(f"✅ Caméra connectée: {camera_info['name']} ({camera_type})", "success")
            
            return True
            
        except Exception as e:
            self.emit_status(f"❌ Erreur d'initialisation de la caméra: {e}", "error")
            return False
    
    def _recognition_loop(self):
        """Boucle principale de reconnaissance faciale"""
        self.emit_status("🔄 Démarrage de la boucle de reconnaissance...")
        
        frame_skip = 2  # Traiter une frame sur 2 pour les performances
        
        while self.is_running:
            try:
                ret, frame = self.camera.read()
                if not ret:
                    self.emit_status("❌ Erreur de lecture de la caméra", "error")
                    break
                
                self.frame_count += 1
                
                # Émettre la frame pour l'affichage (toutes les 3 frames pour plus de fluidité)
                if self.frame_count % 3 == 0:
                    self.emit_frame(frame)
                
                # Traiter la reconnaissance (toutes les frame_skip frames)
                if self.frame_count % frame_skip == 0:
                    self._process_frame(frame)
                
                # Petite pause pour éviter la surcharge CPU
                time.sleep(0.03)  # ~30 FPS
                
            except Exception as e:
                self.emit_status(f"❌ Erreur dans la boucle de reconnaissance: {e}", "error")
                break
        
        self.emit_status("🔄 Boucle de reconnaissance terminée")
    
    def _process_frame(self, frame):
        """Traite une frame pour la reconnaissance faciale"""
        try:
            # Redimensionner pour améliorer les performances
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            
            # Détecter les visages
            face_locations = face_recognition.face_locations(rgb_small_frame)
            
            if not face_locations:
                return
            
            # Calculer les encodages
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)
            
            # Comparer avec les visages connus
            for face_encoding in face_encodings:
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding)
                face_distances = face_recognition.face_distance(self.known_face_encodings, face_encoding)
                
                if len(face_distances) > 0:
                    best_match_index = np.argmin(face_distances)
                    
                    if matches[best_match_index]:
                        name = self.known_face_names[best_match_index]
                        confidence = 1 - face_distances[best_match_index]
                        
                        # Vérifier le cooldown
                        current_time = time.time()
                        if name not in self.last_recognition_time or \
                           current_time - self.last_recognition_time[name] > self.recognition_cooldown:
                            
                            # Enregistrer la présence
                            self._record_attendance(name, confidence)
                            self.last_recognition_time[name] = current_time
                
        except Exception as e:
            print(f"Erreur lors du traitement de la frame: {e}")
    
    def _record_attendance(self, name, confidence):
        """Enregistre une présence dans la base de données"""
        try:
            now = datetime.now()
            date = now.strftime("%Y-%m-%d")
            time_str = now.strftime("%H:%M:%S")
            
            # Vérifier si déjà présent aujourd'hui
            if config.is_already_present(name, date):
                self.emit_status(f"ℹ️ {name} déjà marqué présent aujourd'hui", "info")
                return
            
            # Enregistrer dans la base de données SQLite
            success = db.ajouter_presence(name, date, time_str)
            
            if success:
                self.emit_status(f"✅ Présence enregistrée: {name} ({confidence:.2%})", "success")
                self.emit_attendance(name, confidence)
                
                # Émettre une mise à jour des statistiques
                if self.socketio:
                    self.socketio.emit('stats_update', {
                        'type': 'attendance_added',
                        'name': name,
                        'date': date,
                        'time': time_str
                    })
            else:
                self.emit_status(f"❌ Erreur lors de l'enregistrement de {name}", "error")
                
        except Exception as e:
            self.emit_status(f"❌ Erreur lors de l'enregistrement: {e}", "error")
    
    def get_status(self):
        """Retourne le statut actuel du système"""
        camera_status = "Connectée" if self.camera and self.camera.isOpened() else "Déconnectée"
        
        return {
            'is_running': self.is_running,
            'camera_status': camera_status,
            'known_faces_count': len(self.known_face_names),
            'encodings_loaded': len(self.known_face_encodings) > 0,
            'frame_count': self.frame_count,
            'last_update': datetime.now().isoformat()
        }
    
    def reload_encodings(self):
        """Recharge les encodages faciaux"""
        self.emit_status("🔄 Rechargement des encodages faciaux...")
        success = self.load_face_encodings()
        
        if success:
            self.emit_status(f"✅ Encodages rechargés: {len(self.known_face_names)} visages", "success")
        else:
            self.emit_status("❌ Échec du rechargement des encodages", "error")
        
        return success
    
    def capture_screenshot(self):
        """Capture une capture d'écran de la caméra actuelle"""
        if not self.camera or not self.camera.isOpened():
            return None
        
        try:
            ret, frame = self.camera.read()
            if ret:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"screenshot_{timestamp}.jpg"
                cv2.imwrite(filename, frame)
                self.emit_status(f"📸 Capture d'écran sauvegardée: {filename}", "success")
                return filename
            else:
                self.emit_status("❌ Impossible de capturer l'image", "error")
                return None
        except Exception as e:
            self.emit_status(f"❌ Erreur lors de la capture: {e}", "error")
            return None

# Instance globale pour l'utilisation dans le tableau de bord
recognition_controller = None

def get_recognition_controller(socketio=None):
    """Obtient l'instance du contrôleur de reconnaissance (singleton)"""
    global recognition_controller
    if recognition_controller is None:
        recognition_controller = FacialRecognitionController(socketio)
    elif socketio and not recognition_controller.socketio:
        recognition_controller.socketio = socketio
    return recognition_controller
