#!/usr/bin/env python3
"""
Diagnostic complet du système de streaming vidéo
"""

import cv2
import requests
import time
from video_streaming import get_video_streamer
from facial_recognition_system import facial_recognition_system

def test_camera_access():
    """Test d'accès direct à la caméra"""
    print("🎥 TEST 1: ACCÈS DIRECT À LA CAMÉRA")
    print("-" * 50)
    
    try:
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            print("✅ Caméra accessible")
            
            ret, frame = cap.read()
            if ret:
                print(f"✅ Frame capturée: {frame.shape}")
                print(f"   Résolution: {frame.shape[1]}x{frame.shape[0]}")
                print(f"   Canaux: {frame.shape[2]}")
            else:
                print("❌ Impossible de capturer une frame")
            
            cap.release()
            return True
        else:
            print("❌ Impossible d'ouvrir la caméra")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_video_streamer():
    """Test du système VideoStreamer"""
    print("\n🎬 TEST 2: SYSTÈME VIDEO STREAMER")
    print("-" * 50)
    
    try:
        # Charger les encodages
        facial_recognition_system.load_encodings()
        print(f"✅ Encodages chargés: {len(facial_recognition_system.known_face_encodings)}")
        
        # Obtenir le streamer
        streamer = get_video_streamer(facial_recognition_system)
        print("✅ VideoStreamer créé")
        
        # Tester le démarrage
        success, message = streamer.start_streaming()
        print(f"📡 Démarrage streaming: {'✅' if success else '❌'} {message}")
        
        if success:
            # Attendre un peu pour que le streaming se stabilise
            time.sleep(2)
            
            # Tester l'obtention d'une frame
            frame_base64 = streamer.get_current_frame_base64()
            if frame_base64:
                print(f"✅ Frame base64 obtenue: {len(frame_base64)} caractères")
            else:
                print("❌ Aucune frame base64 disponible")
            
            # Tester les informations de détection
            info = streamer.get_detection_info()
            print(f"📊 Info détection: {info}")
            
            # Arrêter le streaming
            success, message = streamer.stop_streaming()
            print(f"🛑 Arrêt streaming: {'✅' if success else '❌'} {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ Erreur VideoStreamer: {e}")
        return False

def test_web_apis():
    """Test des APIs web"""
    print("\n🌐 TEST 3: APIS WEB")
    print("-" * 50)
    
    base_url = "http://localhost:5002"
    
    # Test de connexion
    try:
        session = requests.Session()
        
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post(f"{base_url}/login", data=login_data)
        
        if response.status_code == 302:
            print("✅ Connexion admin réussie")
        else:
            print(f"❌ Connexion échouée: {response.status_code}")
            return False
        
        # Test API camera test
        response = session.get(f"{base_url}/facial/api/camera_test")
        if response.status_code == 200:
            data = response.json()
            print(f"🎥 Test caméra API: {'✅' if data.get('success') else '❌'} {data.get('message')}")
        else:
            print(f"❌ API camera test échouée: {response.status_code}")
        
        # Test API start streaming
        response = session.post(f"{base_url}/facial/api/start_streaming")
        if response.status_code == 200:
            data = response.json()
            print(f"📡 Start streaming API: {'✅' if data.get('success') else '❌'} {data.get('message')}")
            
            if data.get('success'):
                # Attendre un peu
                time.sleep(2)
                
                # Test du flux vidéo
                response = session.get(f"{base_url}/facial/video_feed", stream=True)
                if response.status_code == 200:
                    print("✅ Flux vidéo accessible")
                    
                    # Lire quelques bytes pour vérifier
                    chunk = next(response.iter_content(chunk_size=1024))
                    if chunk:
                        print(f"✅ Données reçues: {len(chunk)} bytes")
                    else:
                        print("❌ Aucune donnée dans le flux")
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                
                # Arrêter le streaming
                response = session.post(f"{base_url}/facial/api/stop_streaming")
                if response.status_code == 200:
                    data = response.json()
                    print(f"🛑 Stop streaming API: {'✅' if data.get('success') else '❌'} {data.get('message')}")
        else:
            print(f"❌ Start streaming API échouée: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur APIs web: {e}")
        return False

def test_javascript_simulation():
    """Simulation du comportement JavaScript"""
    print("\n🖥️ TEST 4: SIMULATION JAVASCRIPT")
    print("-" * 50)
    
    try:
        session = requests.Session()
        
        # Connexion
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Accès à la page de reconnaissance
        response = session.get("http://localhost:5002/facial/recognition")
        if response.status_code == 200:
            print("✅ Page reconnaissance accessible")
        else:
            print(f"❌ Page reconnaissance inaccessible: {response.status_code}")
            return False
        
        # Simulation: Démarrer la caméra
        print("🎬 Simulation: Clic sur 'Démarrer la Caméra'")
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Streaming démarré avec succès")
                
                # Simulation: Accès au flux vidéo (comme le fait le JavaScript)
                print("📺 Simulation: Chargement du flux vidéo")
                video_url = f"http://localhost:5002/facial/video_feed?{int(time.time())}"
                
                response = session.get(video_url, stream=True, timeout=5)
                if response.status_code == 200:
                    print("✅ Flux vidéo accessible via JavaScript simulation")
                    
                    # Lire le premier chunk
                    try:
                        chunk = next(response.iter_content(chunk_size=1024))
                        if b'--frame' in chunk or b'Content-Type' in chunk:
                            print("✅ Format de streaming multipart détecté")
                        else:
                            print(f"⚠️ Format inattendu: {chunk[:100]}")
                    except StopIteration:
                        print("❌ Aucune donnée dans le flux")
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                
                # Arrêter
                session.post("http://localhost:5002/facial/api/stop_streaming")
            else:
                print(f"❌ Échec démarrage: {data.get('message')}")
        else:
            print(f"❌ API start_streaming échouée: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur simulation JavaScript: {e}")
        return False

def main():
    """Exécuter tous les tests de diagnostic"""
    print("🔍 DIAGNOSTIC COMPLET DU STREAMING VIDÉO")
    print("=" * 60)
    
    results = []
    
    # Test 1: Accès caméra
    results.append(("Accès Caméra", test_camera_access()))
    
    # Test 2: VideoStreamer
    results.append(("VideoStreamer", test_video_streamer()))
    
    # Test 3: APIs Web
    results.append(("APIs Web", test_web_apis()))
    
    # Test 4: Simulation JavaScript
    results.append(("Simulation JS", test_javascript_simulation()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:20}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Tous les tests sont réussis - Le streaming devrait fonctionner!")
    else:
        print("⚠️ Certains tests ont échoué - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
