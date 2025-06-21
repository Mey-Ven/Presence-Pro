"""
Module pour l'entraînement facial automatique lors de l'ajout d'étudiants
Ce module gère la capture de photos et la génération d'encodages
"""

import cv2
import os
import face_recognition
import pickle
import time
import sys
from datetime import datetime
from camera_manager import CameraManager

class FacialTrainingModule:
    def __init__(self, dataset_folder="dataset", encodings_file="encodings.pickle"):
        """
        Initialise le module d'entraînement facial
        
        Args:
            dataset_folder (str): Dossier contenant les images d'entraînement
            encodings_file (str): Fichier contenant les encodages
        """
        self.dataset_folder = dataset_folder
        self.encodings_file = encodings_file
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        
        # Créer le dossier dataset s'il n'existe pas
        if not os.path.exists(self.dataset_folder):
            os.makedirs(self.dataset_folder)
            print(f"Dossier {self.dataset_folder} créé")

    def find_camera(self):
        """
        Trouve la meilleure caméra disponible (priorité à la caméra intégrée)

        Returns:
            cv2.VideoCapture ou None: Objet caméra ou None si aucune caméra trouvée
        """
        print("🎥 Recherche de la caméra optimale pour l'entraînement...")
        print("=" * 50)

        # Utiliser le gestionnaire de caméras intelligent
        camera_manager = CameraManager()

        # Détecter toutes les caméras disponibles
        cameras = camera_manager.detect_cameras()

        if not cameras:
            print("❌ Aucune caméra détectée")
            return None

        # Obtenir la meilleure caméra (priorité à la caméra intégrée)
        cap = camera_manager.get_best_camera()

        if cap is not None:
            # Afficher les informations de la caméra sélectionnée
            camera_info = camera_manager.get_camera_info()
            if camera_info:
                print(f"\n✅ CAMÉRA SÉLECTIONNÉE POUR L'ENTRAÎNEMENT:")
                print(f"   📷 Nom: {camera_info['name']}")
                print(f"   🔢 Index: {camera_info['index']}")
                print(f"   🖥️  Type: {'Caméra intégrée' if camera_info['is_builtin'] else 'Caméra externe'}")
                print(f"   📐 Résolution: {camera_info['width']}x{camera_info['height']}")
                print("=" * 50)

            return cap
        else:
            print("❌ Impossible d'initialiser la caméra sélectionnée")
            return None

    def capture_student_photos(self, prenom, nom, max_photos=15):
        """
        Capture des photos d'un étudiant pour l'entraînement
        
        Args:
            prenom (str): Prénom de l'étudiant
            nom (str): Nom de l'étudiant
            max_photos (int): Nombre maximum de photos à capturer
            
        Returns:
            tuple: (bool, int) - (Succès, nombre de photos capturées)
        """
        print(f"\n=== CAPTURE DE PHOTOS POUR {prenom} {nom} ===")
        
        # Normaliser le nom pour le fichier
        full_name = f"{prenom}_{nom}".replace(" ", "_")
        
        # Trouver une caméra
        cap = self.find_camera()
        if cap is None:
            print("❌ Impossible de trouver une caméra. Capture annulée.")
            return False, 0
        
        try:
            # Configurer la caméra
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            
            count = 0
            last_capture_time = 0
            capture_interval = 1.0  # Intervalle minimum entre les captures (secondes)
            
            print(f"\n📸 INSTRUCTIONS DE CAPTURE:")
            print(f"• Objectif: {max_photos} photos")
            print(f"• Appuyez sur 'ESPACE' pour capturer une photo")
            print(f"• Appuyez sur 'a' pour capture automatique")
            print(f"• Appuyez sur 'q' pour terminer")
            print(f"• Variez les angles et expressions pour de meilleurs résultats")
            print(f"\n🎯 Positionnez votre visage dans le rectangle vert et commencez!")
            
            auto_capture = False
            
            while count < max_photos:
                ret, frame = cap.read()
                if not ret:
                    print("❌ Erreur lors de la lecture de la caméra")
                    break
                
                # Détecter les visages
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                
                # Dessiner les rectangles autour des visages
                face_detected = len(faces) > 0
                for (x, y, w, h) in faces:
                    color = (0, 255, 0) if face_detected else (0, 0, 255)
                    cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                    
                    # Ajouter du texte pour guider l'utilisateur
                    if face_detected:
                        cv2.putText(frame, "Visage detecte - Pret!", (x, y-10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Afficher les informations à l'écran
                cv2.putText(frame, f"Photos: {count}/{max_photos}", (10, 30),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
                
                cv2.putText(frame, f"Etudiant: {prenom} {nom}", (10, 60),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                if auto_capture:
                    cv2.putText(frame, "MODE AUTO - Capture en cours...", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
                else:
                    cv2.putText(frame, "ESPACE: Capturer | A: Auto | Q: Quitter", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                
                # Afficher le statut de détection
                if not face_detected:
                    cv2.putText(frame, "Aucun visage detecte", (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
                
                cv2.imshow(f"Capture Photos - {prenom} {nom}", frame)
                
                # Gestion des touches
                key = cv2.waitKey(1) & 0xFF
                current_time = time.time()
                
                # Capture manuelle avec ESPACE
                if key == ord(' '):
                    if face_detected and current_time - last_capture_time > capture_interval:
                        success = self._save_photo(frame, faces[0], full_name, count + 1)
                        if success:
                            count += 1
                            last_capture_time = current_time
                            print(f"📸 Photo {count}/{max_photos} capturée")
                    elif not face_detected:
                        print("⚠️  Aucun visage détecté. Repositionnez-vous.")
                    else:
                        print("⚠️  Attendez un moment avant la prochaine capture.")
                
                # Mode automatique
                elif key == ord('a'):
                    auto_capture = not auto_capture
                    mode = "activé" if auto_capture else "désactivé"
                    print(f"🤖 Mode automatique {mode}")
                
                # Capture automatique
                if auto_capture and face_detected and current_time - last_capture_time > capture_interval:
                    success = self._save_photo(frame, faces[0], full_name, count + 1)
                    if success:
                        count += 1
                        last_capture_time = current_time
                        print(f"📸 Photo {count}/{max_photos} capturée automatiquement")
                
                # Quitter
                if key == ord('q'):
                    print("🛑 Capture interrompue par l'utilisateur")
                    break
            
            print(f"\n✅ Capture terminée: {count} photos sauvegardées")
            return True, count
            
        except Exception as e:
            print(f"❌ Erreur lors de la capture: {e}")
            return False, 0
            
        finally:
            cap.release()
            cv2.destroyAllWindows()

    def _save_photo(self, frame, face_coords, full_name, photo_number):
        """
        Sauvegarde une photo de visage
        
        Args:
            frame: Image complète de la caméra
            face_coords: Coordonnées du visage (x, y, w, h)
            full_name: Nom complet formaté
            photo_number: Numéro de la photo
            
        Returns:
            bool: Succès de la sauvegarde
        """
        try:
            x, y, w, h = face_coords
            
            # Extraire le visage avec une marge
            margin = 20
            y_start = max(0, y - margin)
            y_end = min(frame.shape[0], y + h + margin)
            x_start = max(0, x - margin)
            x_end = min(frame.shape[1], x + w + margin)
            
            face = frame[y_start:y_end, x_start:x_end]
            
            # Redimensionner pour une taille standard
            face_resized = cv2.resize(face, (200, 200))
            
            # Sauvegarder
            filename = f"{self.dataset_folder}/{full_name}_{photo_number}.jpg"
            success = cv2.imwrite(filename, face_resized)
            
            if success:
                return True
            else:
                print(f"❌ Erreur lors de la sauvegarde de {filename}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la sauvegarde de la photo: {e}")
            return False

    def generate_encodings(self):
        """
        Génère les encodages pour toutes les images du dataset
        
        Returns:
            bool: Succès de la génération des encodages
        """
        print(f"\n=== GÉNÉRATION DES ENCODAGES ===")
        
        try:
            known_encodings = []
            known_names = []
            processed_files = 0
            skipped_files = 0
            
            # Parcourir toutes les images du dataset
            image_files = [f for f in os.listdir(self.dataset_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
            
            if not image_files:
                print("❌ Aucune image trouvée dans le dataset")
                return False
            
            print(f"📁 Traitement de {len(image_files)} images...")
            
            for filename in image_files:
                img_path = os.path.join(self.dataset_folder, filename)
                
                try:
                    # Charger l'image
                    image = face_recognition.load_image_file(img_path)
                    encodings = face_recognition.face_encodings(image)
                    
                    if len(encodings) > 0:
                        encoding = encodings[0]
                        # Extraire le nom (format: Prenom_Nom_X.jpg)
                        name_parts = filename.split("_")
                        if len(name_parts) >= 2:
                            name = "_".join(name_parts[:2])  # Prenom_Nom
                        else:
                            name = filename.split(".")[0]  # Fallback
                        
                        known_encodings.append(encoding)
                        known_names.append(name)
                        processed_files += 1
                        print(f"✅ {filename} -> {name}")
                    else:
                        skipped_files += 1
                        print(f"⚠️  Aucun visage détecté dans {filename}")
                        
                except Exception as e:
                    skipped_files += 1
                    print(f"❌ Erreur avec {filename}: {e}")
            
            if processed_files == 0:
                print("❌ Aucun encodage généré")
                return False
            
            # Sauvegarder les encodages
            data = {"encodings": known_encodings, "names": known_names}
            with open(self.encodings_file, "wb") as f:
                pickle.dump(data, f)
            
            print(f"\n✅ Encodages sauvegardés dans {self.encodings_file}")
            print(f"📊 Résumé: {processed_files} encodages générés, {skipped_files} fichiers ignorés")
            
            # Afficher les noms uniques
            unique_names = list(set(known_names))
            print(f"👥 Personnes enregistrées: {', '.join(unique_names)}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erreur lors de la génération des encodages: {e}")
            return False

    def train_student(self, prenom, nom, max_photos=15):
        """
        Processus complet d'entraînement pour un étudiant
        
        Args:
            prenom (str): Prénom de l'étudiant
            nom (str): Nom de l'étudiant
            max_photos (int): Nombre maximum de photos à capturer
            
        Returns:
            bool: Succès de l'entraînement complet
        """
        print(f"\n🎓 DÉBUT DE L'ENTRAÎNEMENT FACIAL POUR {prenom} {nom}")
        
        # Étape 1: Capture des photos
        capture_success, photos_count = self.capture_student_photos(prenom, nom, max_photos)
        
        if not capture_success or photos_count == 0:
            print("❌ Échec de la capture de photos")
            return False
        
        print(f"✅ {photos_count} photos capturées avec succès")
        
        # Étape 2: Génération des encodages
        encoding_success = self.generate_encodings()
        
        if not encoding_success:
            print("❌ Échec de la génération des encodages")
            return False
        
        print(f"✅ Encodages générés avec succès")
        print(f"🎉 Entraînement terminé pour {prenom} {nom}!")
        print(f"🔍 L'étudiant peut maintenant être reconnu par le système")
        
        return True

# Fonction utilitaire pour tester le module
if __name__ == "__main__":
    trainer = FacialTrainingModule()
    
    # Test avec un étudiant fictif
    prenom = input("Prénom de l'étudiant: ").strip()
    nom = input("Nom de l'étudiant: ").strip()
    
    if prenom and nom:
        success = trainer.train_student(prenom, nom)
        if success:
            print("🎉 Entraînement réussi!")
        else:
            print("❌ Entraînement échoué")
    else:
        print("❌ Nom ou prénom manquant")
