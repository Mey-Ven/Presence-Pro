"""
Test pour vérifier la connexion WebSocket et l'émission des frames caméra
"""

import requests
import time
import subprocess
import sys
import socketio

def test_websocket_connection():
    """Test de la connexion WebSocket"""
    print("🔌 TEST DE CONNEXION WEBSOCKET")
    print("=" * 60)
    
    try:
        # Créer un client SocketIO
        sio = socketio.Client()
        
        # Variables pour capturer les événements
        events_received = {
            'connect': False,
            'status': False,
            'recognition_status': False,
            'camera_frame': False
        }
        
        frames_received = 0
        
        @sio.event
        def connect():
            print("✅ WebSocket connecté")
            events_received['connect'] = True
        
        @sio.event
        def disconnect():
            print("🔌 WebSocket déconnecté")
        
        @sio.on('status')
        def on_status(data):
            print(f"📊 Statut reçu: {data}")
            events_received['status'] = True
        
        @sio.on('recognition_status')
        def on_recognition_status(data):
            print(f"🎯 Statut reconnaissance: {data}")
            events_received['recognition_status'] = True
        
        @sio.on('camera_frame')
        def on_camera_frame(data):
            nonlocal frames_received
            frames_received += 1
            if frames_received <= 3:  # Afficher seulement les 3 premières
                frame_size = len(data.get('frame', ''))
                print(f"📷 Frame {frames_received} reçue: {frame_size} caractères")
            events_received['camera_frame'] = True
        
        # Se connecter
        print("🔌 Connexion au WebSocket...")
        sio.connect('http://localhost:5001')
        
        # Attendre un peu pour recevoir les événements initiaux
        time.sleep(3)
        
        print(f"\n📊 Événements reçus:")
        for event, received in events_received.items():
            status = "✅" if received else "❌"
            print(f"   {status} {event}")
        
        # Déconnecter
        sio.disconnect()
        
        return events_received['connect']
        
    except Exception as e:
        print(f"❌ Erreur WebSocket: {e}")
        return False

def test_recognition_api():
    """Test des APIs de reconnaissance"""
    print("\n🎯 TEST DES APIS DE RECONNAISSANCE")
    print("=" * 60)
    
    session = requests.Session()
    
    try:
        # Se connecter
        print("🔐 Connexion...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post("http://localhost:5001/login", data=login_data)
        
        if response.status_code != 200:
            print(f"❌ Échec de connexion: {response.status_code}")
            return False
        
        print("✅ Connexion réussie")
        
        # Vérifier le statut initial
        print("\n📊 Vérification du statut initial...")
        response = session.get("http://localhost:5001/api/recognition/status")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Reconnaissance active: {data.get('is_running', 'Inconnu')}")
            print(f"   Statut caméra: {data.get('camera_status', 'Inconnu')}")
            print(f"   Visages connus: {data.get('known_faces_count', 0)}")
            
            # Si la reconnaissance est déjà active, l'arrêter d'abord
            if data.get('is_running'):
                print("\n⏹️ Arrêt de la reconnaissance...")
                session.post("http://localhost:5001/api/recognition/stop")
                time.sleep(2)
        
        # Démarrer la reconnaissance
        print("\n▶️ Démarrage de la reconnaissance...")
        response = session.post("http://localhost:5001/api/recognition/start")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Reconnaissance démarrée avec succès")
                
                # Attendre un peu pour que la caméra s'initialise
                time.sleep(3)
                
                # Vérifier le statut après démarrage
                response = session.get("http://localhost:5001/api/recognition/status")
                if response.status_code == 200:
                    status_data = response.json()
                    print(f"   Reconnaissance active: {status_data.get('is_running', 'Inconnu')}")
                    print(f"   Statut caméra: {status_data.get('camera_status', 'Inconnu')}")
                    
                    if status_data.get('is_running') and status_data.get('camera_status') == 'Connectée':
                        print("✅ Reconnaissance et caméra fonctionnelles")
                        
                        # Attendre un peu pour voir si des frames sont émises
                        print("\n⏳ Attente des frames caméra (10 secondes)...")
                        time.sleep(10)
                        
                        # Arrêter la reconnaissance
                        print("\n⏹️ Arrêt de la reconnaissance...")
                        session.post("http://localhost:5001/api/recognition/stop")
                        
                        return True
                    else:
                        print("❌ Problème avec la reconnaissance ou la caméra")
                        return False
                else:
                    print("❌ Erreur lors de la vérification du statut")
                    return False
            else:
                print(f"❌ Échec du démarrage: {data.get('message', 'Erreur inconnue')}")
                return False
        else:
            print(f"❌ Erreur API démarrage: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_combined_websocket_recognition():
    """Test combiné WebSocket + Reconnaissance"""
    print("\n🔄 TEST COMBINÉ WEBSOCKET + RECONNAISSANCE")
    print("=" * 60)
    
    # Créer un client SocketIO
    sio = socketio.Client()
    session = requests.Session()
    
    frames_received = 0
    recognition_events = 0
    
    @sio.event
    def connect():
        print("✅ WebSocket connecté")
    
    @sio.on('camera_frame')
    def on_camera_frame(data):
        nonlocal frames_received
        frames_received += 1
        if frames_received <= 5:
            frame_size = len(data.get('frame', ''))
            print(f"📷 Frame {frames_received}: {frame_size} caractères")
    
    @sio.on('recognition_status')
    def on_recognition_status(data):
        nonlocal recognition_events
        recognition_events += 1
        print(f"🎯 Événement reconnaissance {recognition_events}: {data.get('message', 'N/A')}")
    
    try:
        # Se connecter au WebSocket
        print("🔌 Connexion WebSocket...")
        sio.connect('http://localhost:5001')
        time.sleep(1)
        
        # Se connecter à l'API
        print("🔐 Connexion API...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5001/login", data=login_data)
        
        # Démarrer la reconnaissance
        print("▶️ Démarrage reconnaissance...")
        response = session.post("http://localhost:5001/api/recognition/start")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Reconnaissance démarrée")
                
                # Attendre et compter les frames
                print("⏳ Attente des frames (15 secondes)...")
                time.sleep(15)
                
                # Arrêter
                print("⏹️ Arrêt reconnaissance...")
                session.post("http://localhost:5001/api/recognition/stop")
                time.sleep(2)
                
                print(f"\n📊 Résultats:")
                print(f"   Frames reçues: {frames_received}")
                print(f"   Événements reconnaissance: {recognition_events}")
                
                success = frames_received > 0
                
                if success:
                    print("✅ WebSocket et reconnaissance fonctionnent ensemble")
                else:
                    print("❌ Aucune frame reçue via WebSocket")
                
                sio.disconnect()
                return success
            else:
                print(f"❌ Échec démarrage: {data.get('message')}")
                sio.disconnect()
                return False
        else:
            print(f"❌ Erreur API: {response.status_code}")
            sio.disconnect()
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        try:
            sio.disconnect()
        except:
            pass
        return False

def main():
    """Fonction principale"""
    print("🎯 TEST WEBSOCKET ET FLUX CAMÉRA")
    print("Ce test vérifie la connexion WebSocket et l'émission des frames caméra")
    print()
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ Serveur dashboard accessible")
    except Exception as e:
        print(f"❌ Serveur non accessible: {e}")
        print("   Démarrez le dashboard avec: python admin_dashboard.py")
        return
    
    # Tests
    websocket_ok = test_websocket_connection()
    api_ok = test_recognition_api()
    combined_ok = test_combined_websocket_recognition()
    
    # Résumé
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    print(f"Connexion WebSocket: {'✅ OK' if websocket_ok else '❌ ÉCHEC'}")
    print(f"API Reconnaissance: {'✅ OK' if api_ok else '❌ ÉCHEC'}")
    print(f"Test combiné: {'✅ OK' if combined_ok else '❌ ÉCHEC'}")
    
    if websocket_ok and api_ok and combined_ok:
        print("\n🎉 TOUS LES TESTS RÉUSSIS!")
        print("   Le flux caméra devrait fonctionner dans le dashboard")
        print("   Si vous voyez encore un écran noir:")
        print("   - Vérifiez la console JavaScript du navigateur")
        print("   - Actualisez la page du dashboard")
        print("   - Vérifiez que la reconnaissance est bien démarrée")
    else:
        print("\n⚠️ PROBLÈMES DÉTECTÉS")
        if not websocket_ok:
            print("   ❌ Problème de connexion WebSocket")
        if not api_ok:
            print("   ❌ Problème avec l'API de reconnaissance")
        if not combined_ok:
            print("   ❌ Problème d'intégration WebSocket/Reconnaissance")
        
        print("\n💡 Solutions recommandées:")
        print("   - Redémarrer le serveur dashboard")
        print("   - Vérifier les logs du serveur")
        print("   - Tester avec un autre navigateur")

if __name__ == "__main__":
    main()
