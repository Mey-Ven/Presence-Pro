"""
Module de gestion intelligente des caméras pour le système de reconnaissance faciale
Ce module détecte et priorise automatiquement la caméra intégrée de l'ordinateur
"""

import cv2
import platform
import subprocess
import re
import time

class CameraManager:
    def __init__(self):
        """Initialise le gestionnaire de caméras"""
        self.system = platform.system()
        self.available_cameras = []
        self.preferred_camera = None
        
    def detect_cameras(self):
        """
        Détecte toutes les caméras disponibles et identifie la caméra intégrée
        
        Returns:
            list: Liste des caméras disponibles avec leurs informations
        """
        print("🔍 Détection des caméras disponibles...")
        cameras = []
        
        # Tester les indices de caméra de 0 à 10
        for i in range(11):
            try:
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    # Tester si la caméra fonctionne
                    ret, frame = cap.read()
                    if ret and frame is not None and frame.size > 0:
                        # Obtenir les informations de la caméra
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        fps = int(cap.get(cv2.CAP_PROP_FPS))
                        
                        camera_info = {
                            'index': i,
                            'width': width,
                            'height': height,
                            'fps': fps,
                            'name': self._get_camera_name(i),
                            'is_builtin': self._is_builtin_camera(i),
                            'priority': self._calculate_priority(i, width, height)
                        }
                        
                        cameras.append(camera_info)
                        print(f"✅ Caméra {i}: {camera_info['name']} ({width}x{height})")
                        
                    cap.release()
                else:
                    # Caméra non accessible
                    pass
                    
            except Exception as e:
                # Erreur lors du test de la caméra
                pass
        
        # Trier les caméras par priorité (caméra intégrée en premier)
        cameras.sort(key=lambda x: x['priority'], reverse=True)
        self.available_cameras = cameras
        
        if cameras:
            print(f"📷 {len(cameras)} caméra(s) détectée(s)")
            for cam in cameras:
                builtin_status = "🖥️  Intégrée" if cam['is_builtin'] else "🔌 Externe"
                print(f"   {cam['index']}: {cam['name']} - {builtin_status} (Priorité: {cam['priority']})")
        else:
            print("❌ Aucune caméra détectée")
            
        return cameras
    
    def _get_camera_name(self, index):
        """
        Obtient le nom de la caméra selon le système d'exploitation
        
        Args:
            index (int): Index de la caméra
            
        Returns:
            str: Nom de la caméra
        """
        try:
            if self.system == "Windows":
                return self._get_windows_camera_name(index)
            elif self.system == "Darwin":  # macOS
                return self._get_macos_camera_name(index)
            elif self.system == "Linux":
                return self._get_linux_camera_name(index)
            else:
                return f"Caméra {index}"
        except:
            return f"Caméra {index}"
    
    def _get_windows_camera_name(self, index):
        """Obtient le nom de la caméra sur Windows"""
        try:
            # Utiliser PowerShell pour obtenir les informations des caméras
            cmd = "Get-WmiObject -Class Win32_PnPEntity | Where-Object {$_.Name -like '*camera*' -or $_.Name -like '*webcam*'} | Select-Object Name"
            result = subprocess.run(["powershell", "-Command", cmd], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split('\n')
                camera_names = [line.strip() for line in lines if line.strip() and 'Name' not in line and '---' not in line]
                if index < len(camera_names):
                    return camera_names[index]
        except:
            pass
        
        # Noms par défaut basés sur l'index
        if index == 0:
            return "Caméra intégrée"
        else:
            return f"Caméra externe {index}"
    
    def _get_macos_camera_name(self, index):
        """Obtient le nom de la caméra sur macOS"""
        try:
            # Utiliser system_profiler pour obtenir les informations des caméras
            result = subprocess.run(["system_profiler", "SPCameraDataType"], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Analyser la sortie pour trouver les noms des caméras
                lines = result.stdout.split('\n')
                camera_names = []
                
                for line in lines:
                    if 'Model ID:' in line or 'Unique ID:' in line:
                        # Extraire le nom de la caméra
                        name = line.split(':')[-1].strip()
                        if name and name not in camera_names:
                            camera_names.append(name)
                
                if index < len(camera_names):
                    return camera_names[index]
        except:
            pass
        
        # Noms par défaut pour macOS
        if index == 0:
            return "FaceTime HD Camera (Intégrée)"
        else:
            return f"Caméra externe {index}"
    
    def _get_linux_camera_name(self, index):
        """Obtient le nom de la caméra sur Linux"""
        try:
            # Utiliser v4l2-ctl pour obtenir les informations des caméras
            device_path = f"/dev/video{index}"
            result = subprocess.run(["v4l2-ctl", "--device", device_path, "--info"], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # Extraire le nom de la caméra
                for line in result.stdout.split('\n'):
                    if 'Card type' in line:
                        return line.split(':')[-1].strip()
        except:
            pass
        
        # Noms par défaut pour Linux
        if index == 0:
            return "Caméra intégrée USB"
        else:
            return f"Caméra USB {index}"
    
    def _is_builtin_camera(self, index):
        """
        Détermine si une caméra est intégrée à l'ordinateur
        
        Args:
            index (int): Index de la caméra
            
        Returns:
            bool: True si la caméra est intégrée
        """
        # La caméra index 0 est généralement la caméra intégrée
        if index == 0:
            return True
        
        # Vérifications supplémentaires selon le système
        camera_name = self._get_camera_name(index).lower()
        
        # Mots-clés indiquant une caméra intégrée
        builtin_keywords = [
            'facetime', 'integrated', 'built-in', 'internal', 
            'intégrée', 'intégré', 'webcam intégrée', 'hd camera'
        ]
        
        # Mots-clés indiquant une caméra externe
        external_keywords = [
            'usb', 'external', 'logitech', 'microsoft', 'creative',
            'externe', 'phone', 'mobile', 'android', 'iphone'
        ]
        
        # Vérifier les mots-clés
        for keyword in external_keywords:
            if keyword in camera_name:
                return False
                
        for keyword in builtin_keywords:
            if keyword in camera_name:
                return True
        
        # Par défaut, considérer les indices faibles comme intégrés
        return index <= 1
    
    def _calculate_priority(self, index, width, height):
        """
        Calcule la priorité d'une caméra
        
        Args:
            index (int): Index de la caméra
            width (int): Largeur de l'image
            height (int): Hauteur de l'image
            
        Returns:
            int: Score de priorité (plus élevé = plus prioritaire)
        """
        priority = 0
        
        # Priorité basée sur le type de caméra
        if self._is_builtin_camera(index):
            priority += 1000  # Très haute priorité pour les caméras intégrées
        
        # Priorité basée sur l'index (plus bas = plus prioritaire)
        priority += (10 - index) * 10
        
        # Priorité basée sur la résolution (résolutions standard privilégiées)
        resolution_score = 0
        if width >= 1280 and height >= 720:  # HD ou mieux
            resolution_score = 50
        elif width >= 640 and height >= 480:  # VGA ou mieux
            resolution_score = 30
        else:
            resolution_score = 10
        
        priority += resolution_score
        
        return priority
    
    def get_best_camera(self):
        """
        Obtient la meilleure caméra disponible (priorité à la caméra intégrée)
        
        Returns:
            cv2.VideoCapture ou None: Objet caméra ou None si aucune caméra
        """
        if not self.available_cameras:
            self.detect_cameras()
        
        if not self.available_cameras:
            print("❌ Aucune caméra disponible")
            return None
        
        # Prendre la caméra avec la plus haute priorité
        best_camera = self.available_cameras[0]
        
        print(f"🎯 Sélection de la caméra: {best_camera['name']} (Index: {best_camera['index']})")
        
        try:
            cap = cv2.VideoCapture(best_camera['index'])
            
            if cap.isOpened():
                # Configurer la caméra pour de meilleures performances
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Tester la caméra
                ret, frame = cap.read()
                if ret and frame is not None and frame.size > 0:
                    print(f"✅ Caméra {best_camera['index']} initialisée avec succès")
                    print(f"📷 Type: {'🖥️  Caméra intégrée' if best_camera['is_builtin'] else '🔌 Caméra externe'}")
                    print(f"📐 Résolution: {best_camera['width']}x{best_camera['height']}")
                    
                    self.preferred_camera = best_camera
                    return cap
                else:
                    print(f"❌ La caméra {best_camera['index']} ne fournit pas d'images valides")
                    cap.release()
            else:
                print(f"❌ Impossible d'ouvrir la caméra {best_camera['index']}")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'initialisation de la caméra: {e}")
        
        return None
    
    def get_camera_info(self):
        """
        Retourne les informations de la caméra actuellement utilisée
        
        Returns:
            dict: Informations de la caméra ou None
        """
        return self.preferred_camera
    
    def list_all_cameras(self):
        """
        Affiche la liste de toutes les caméras détectées
        """
        if not self.available_cameras:
            self.detect_cameras()
        
        if not self.available_cameras:
            print("❌ Aucune caméra détectée")
            return
        
        print("\n📷 CAMÉRAS DISPONIBLES:")
        print("=" * 60)
        
        for i, cam in enumerate(self.available_cameras):
            status = "🖥️  INTÉGRÉE" if cam['is_builtin'] else "🔌 EXTERNE"
            priority_stars = "⭐" * min(5, cam['priority'] // 200)
            
            print(f"{i+1}. Index {cam['index']}: {cam['name']}")
            print(f"   Type: {status}")
            print(f"   Résolution: {cam['width']}x{cam['height']} @ {cam['fps']} FPS")
            print(f"   Priorité: {cam['priority']} {priority_stars}")
            print()

# Fonction utilitaire pour tester le gestionnaire de caméras
if __name__ == "__main__":
    print("🎥 Test du gestionnaire de caméras")
    print("=" * 50)
    
    manager = CameraManager()
    
    # Lister toutes les caméras
    manager.list_all_cameras()
    
    # Obtenir la meilleure caméra
    cap = manager.get_best_camera()
    
    if cap:
        print("\n🎯 Test de capture d'image...")
        ret, frame = cap.read()
        if ret:
            print("✅ Capture d'image réussie!")
            print(f"📐 Taille de l'image: {frame.shape}")
        else:
            print("❌ Échec de la capture d'image")
        
        cap.release()
    else:
        print("❌ Aucune caméra disponible pour le test")
