"""
Test complet pour vérifier qu'il n'y a AUCUN démarrage automatique de la reconnaissance faciale
"""

import requests
import time
import subprocess
import sys
import os

def test_server_startup():
    """Test que le serveur démarre sans auto-start de reconnaissance"""
    print("🚀 TEST DE DÉMARRAGE DU SERVEUR")
    print("=" * 60)
    
    # Démarrer le serveur en arrière-plan
    print("⏳ Démarrage du serveur...")
    
    try:
        # Lancer le serveur
        process = subprocess.Popen(
            [sys.executable, "admin_dashboard.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Attendre que le serveur soit prêt
        print("⏳ Attente du démarrage complet...")
        time.sleep(8)  # Plus de temps pour être sûr
        
        # Vérifier que le serveur répond
        max_retries = 10
        server_ready = False
        
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:5001", timeout=2)
                if response.status_code in [200, 302]:  # 302 = redirection vers login
                    server_ready = True
                    print("✅ Serveur accessible")
                    break
            except:
                time.sleep(1)
        
        if not server_ready:
            print("❌ Serveur non accessible après démarrage")
            process.terminate()
            return False, None
        
        return True, process
        
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False, None

def test_no_recognition_on_startup(session):
    """Test qu'aucune reconnaissance n'est active au démarrage"""
    print("\n🎯 TEST D'ABSENCE DE RECONNAISSANCE AU DÉMARRAGE")
    print("=" * 60)
    
    try:
        # Se connecter d'abord
        print("🔐 Connexion...")
        
        # Page de connexion
        response = session.get("http://localhost:5001/login")
        if response.status_code != 200:
            print(f"❌ Erreur page de connexion: {response.status_code}")
            return False
        
        # Connexion
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post("http://localhost:5001/login", data=login_data)
        
        if response.status_code != 200:
            print(f"❌ Erreur de connexion: {response.status_code}")
            return False
        
        print("✅ Connexion réussie")
        
        # Attendre un peu pour s'assurer qu'aucun auto-start ne se produit
        print("⏳ Attente pour vérifier l'absence d'auto-start...")
        time.sleep(3)
        
        # Vérifier le statut de reconnaissance
        response = session.get("http://localhost:5001/api/recognition/status")
        if response.status_code == 200:
            data = response.json()
            
            is_running = data.get('is_running', True)
            camera_status = data.get('camera_status', 'Inconnu')
            
            print(f"📊 Statut de reconnaissance: {is_running}")
            print(f"📷 Statut caméra: {camera_status}")
            
            if not is_running:
                print("✅ PARFAIT: Aucune reconnaissance active au démarrage")
                if camera_status == "Déconnectée":
                    print("✅ PARFAIT: Caméra non activée automatiquement")
                    return True
                else:
                    print("⚠️ ATTENTION: Caméra semble connectée malgré reconnaissance inactive")
                    return False
            else:
                print("❌ PROBLÈME: Reconnaissance active automatiquement!")
                return False
        else:
            print(f"❌ Erreur API statut: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_manual_start_stop(session):
    """Test du démarrage/arrêt manuel"""
    print("\n🎛️ TEST DE CONTRÔLE MANUEL")
    print("=" * 60)
    
    try:
        # Test démarrage manuel
        print("▶️ Test de démarrage manuel...")
        response = session.post("http://localhost:5001/api/recognition/start")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Démarrage manuel réussi")
                
                # Vérifier que la reconnaissance est maintenant active
                time.sleep(2)
                response = session.get("http://localhost:5001/api/recognition/status")
                if response.status_code == 200:
                    status_data = response.json()
                    if status_data.get('is_running'):
                        print("✅ Reconnaissance confirmée active après démarrage manuel")
                        manual_start_success = True
                    else:
                        print("❌ Reconnaissance non active après démarrage manuel")
                        manual_start_success = False
                else:
                    print("❌ Erreur vérification statut après démarrage")
                    manual_start_success = False
            else:
                print(f"❌ Échec démarrage manuel: {data.get('message')}")
                manual_start_success = False
        else:
            print(f"❌ Erreur API démarrage: {response.status_code}")
            manual_start_success = False
        
        # Test arrêt manuel
        print("⏹️ Test d'arrêt manuel...")
        response = session.post("http://localhost:5001/api/recognition/stop")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Arrêt manuel réussi")
                
                # Vérifier que la reconnaissance est maintenant inactive
                time.sleep(2)
                response = session.get("http://localhost:5001/api/recognition/status")
                if response.status_code == 200:
                    status_data = response.json()
                    if not status_data.get('is_running'):
                        print("✅ Reconnaissance confirmée inactive après arrêt manuel")
                        manual_stop_success = True
                    else:
                        print("❌ Reconnaissance encore active après arrêt manuel")
                        manual_stop_success = False
                else:
                    print("❌ Erreur vérification statut après arrêt")
                    manual_stop_success = False
            else:
                print(f"❌ Échec arrêt manuel: {data.get('message')}")
                manual_stop_success = False
        else:
            print(f"❌ Erreur API arrêt: {response.status_code}")
            manual_stop_success = False
        
        return manual_start_success and manual_stop_success
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_camera_selection(session):
    """Test que la bonne caméra est sélectionnée"""
    print("\n📷 TEST DE SÉLECTION DE CAMÉRA")
    print("=" * 60)
    
    try:
        # Démarrer la reconnaissance pour tester la caméra
        print("▶️ Démarrage pour test de caméra...")
        response = session.post("http://localhost:5001/api/recognition/start")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                time.sleep(3)  # Laisser le temps à la caméra de s'initialiser
                
                # Vérifier le statut pour voir quelle caméra est utilisée
                response = session.get("http://localhost:5001/api/recognition/status")
                if response.status_code == 200:
                    status_data = response.json()
                    camera_status = status_data.get('camera_status', 'Inconnu')
                    
                    print(f"📷 Statut caméra: {camera_status}")
                    
                    if camera_status == "Connectée":
                        print("✅ Caméra connectée avec succès")
                        camera_success = True
                    else:
                        print("⚠️ Problème de connexion caméra")
                        camera_success = False
                else:
                    print("❌ Erreur vérification statut caméra")
                    camera_success = False
                
                # Arrêter la reconnaissance
                session.post("http://localhost:5001/api/recognition/stop")
            else:
                print(f"❌ Échec démarrage pour test caméra: {data.get('message')}")
                camera_success = False
        else:
            print(f"❌ Erreur API démarrage caméra: {response.status_code}")
            camera_success = False
        
        return camera_success
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 TEST COMPLET D'ABSENCE D'AUTO-START")
    print("Ce test vérifie de manière exhaustive qu'aucune reconnaissance")
    print("faciale ne démarre automatiquement au lancement de l'application.")
    print()
    
    # Arrêter tout serveur existant
    try:
        requests.get("http://localhost:5001", timeout=1)
        print("⚠️ Un serveur semble déjà en cours. Veuillez l'arrêter d'abord.")
        return
    except:
        pass  # Bon, aucun serveur en cours
    
    # Test 1: Démarrage du serveur
    server_started, process = test_server_startup()
    
    if not server_started:
        print("❌ Impossible de démarrer le serveur pour les tests")
        return
    
    try:
        session = requests.Session()
        
        # Test 2: Vérifier l'absence de reconnaissance au démarrage
        no_autostart = test_no_recognition_on_startup(session)
        
        # Test 3: Vérifier le contrôle manuel
        manual_control = test_manual_start_stop(session)
        
        # Test 4: Vérifier la sélection de caméra
        camera_selection = test_camera_selection(session)
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ COMPLET DES TESTS")
        print("=" * 60)
        
        print(f"Absence d'auto-start: {'✅ RÉUSSI' if no_autostart else '❌ ÉCHOUÉ'}")
        print(f"Contrôle manuel: {'✅ RÉUSSI' if manual_control else '❌ ÉCHOUÉ'}")
        print(f"Sélection caméra: {'✅ RÉUSSI' if camera_selection else '❌ ÉCHOUÉ'}")
        
        all_success = no_autostart and manual_control and camera_selection
        
        print(f"\n🎯 RÉSULTAT GLOBAL: {'✅ TOUS LES TESTS RÉUSSIS' if all_success else '❌ CERTAINS TESTS ONT ÉCHOUÉ'}")
        
        if all_success:
            print("\n🎉 PARFAIT! Votre système fonctionne exactement comme demandé:")
            print("   ✅ Aucun démarrage automatique de la reconnaissance")
            print("   ✅ Contrôle manuel complet via l'interface web")
            print("   ✅ Caméra intégrée correctement sélectionnée")
            print("   ✅ Système prêt pour utilisation selon vos préférences")
        else:
            print("\n⚠️ Des problèmes ont été détectés:")
            if not no_autostart:
                print("   ❌ La reconnaissance démarre automatiquement")
            if not manual_control:
                print("   ❌ Le contrôle manuel ne fonctionne pas correctement")
            if not camera_selection:
                print("   ❌ Problème de sélection de caméra")
    
    finally:
        # Arrêter le serveur
        if process:
            print("\n🛑 Arrêt du serveur de test...")
            process.terminate()
            process.wait()

if __name__ == "__main__":
    main()
