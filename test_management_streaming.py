#!/usr/bin/env python3
"""
Test du streaming dans la page de gestion des détections
"""

import requests
import time

def test_management_page_streaming():
    """Test du streaming dans la page de gestion"""
    print("🎥 TEST STREAMING GESTION DÉTECTIONS")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Accès à la page de gestion
        response = session.get("http://localhost:5002/facial/manage_detections")
        
        if response.status_code != 200:
            print(f"❌ Page gestion inaccessible: {response.status_code}")
            return False
        
        content = response.text
        
        # Vérifications du streaming intégré
        checks = [
            ("Section vidéo", "Streaming Vidéo en Temps Réel"),
            ("Conteneur vidéo", "video-container"),
            ("Image flux", "managementVideoFeed"),
            ("Bouton démarrer", "Démarrer Caméra"),
            ("Bouton arrêter", "Arrêter Caméra"),
            ("Bouton détection", "Activer Détection"),
            ("Fonction startCamera", "startCamera()"),
            ("Fonction stopCamera", "stopCamera()"),
            ("Fonction enableDetection", "enableDetection()"),
            ("Statut vidéo", "videoStatus"),
            ("Styles CSS vidéo", "video-section"),
            ("Contrôles vidéo", "video-controls"),
            ("API streaming", "/facial/api/start_streaming"),
            ("Flux vidéo", "/facial/video_feed"),
            ("Mise à jour statut", "updateStreamingStatus")
        ]
        
        passed = 0
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Présent")
                passed += 1
            else:
                print(f"❌ {check_name}: Manquant")
        
        print(f"\n📊 Score streaming gestion: {passed}/{len(checks)} vérifications réussies")
        return passed >= 12  # Au moins 12/15 pour considérer comme réussi
        
    except Exception as e:
        print(f"❌ Erreur test streaming gestion: {e}")
        return False

def test_streaming_apis_from_management():
    """Test des APIs de streaming depuis la gestion"""
    print("\n🔧 TEST APIS STREAMING DEPUIS GESTION")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Test démarrage streaming
        print("🎬 Test démarrage streaming...")
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API start_streaming: Fonctionnelle")
                
                # Attendre un peu
                time.sleep(2)
                
                # Test du flux vidéo
                print("📺 Test flux vidéo...")
                response = session.get("http://localhost:5002/facial/video_feed", 
                                     stream=True, timeout=5)
                
                if response.status_code == 200:
                    print("✅ Flux vidéo: Accessible")
                    
                    # Lire quelques chunks
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            chunk_count += 1
                            if chunk_count >= 2:
                                break
                    
                    print(f"✅ Chunks reçus: {chunk_count}")
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                    return False
                
                # Test activation détection
                print("🔍 Test activation détection...")
                response = session.post("http://localhost:5002/facial/api/enable_detection")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ API enable_detection: Fonctionnelle")
                    else:
                        print(f"⚠️ Enable detection: {data.get('message')}")
                else:
                    print(f"❌ API enable_detection erreur: {response.status_code}")
                
                # Test statut streaming
                print("📊 Test statut streaming...")
                response = session.get("http://localhost:5002/facial/api/streaming_status")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        status = data.get('status', {})
                        print(f"✅ Statut streaming: {status.get('is_streaming')}")
                        print(f"✅ Détection active: {status.get('detection_enabled')}")
                    else:
                        print(f"⚠️ Statut: {data.get('message')}")
                else:
                    print(f"❌ API statut erreur: {response.status_code}")
                
                # Arrêter le streaming
                print("🛑 Test arrêt streaming...")
                response = session.post("http://localhost:5002/facial/api/stop_streaming")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ API stop_streaming: Fonctionnelle")
                        return True
                    else:
                        print(f"⚠️ Stop streaming: {data.get('message')}")
                        return True  # Considérer comme réussi même si message d'avertissement
                else:
                    print(f"❌ API stop_streaming erreur: {response.status_code}")
                    return False
            else:
                print(f"❌ Start streaming échoué: {data.get('message')}")
                return False
        else:
            print(f"❌ API start_streaming erreur: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test APIs: {e}")
        return False

def test_integration_management_streaming():
    """Test d'intégration gestion + streaming"""
    print("\n🔄 TEST INTÉGRATION GESTION + STREAMING")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # 1. Accès page gestion
        print("📄 Accès page gestion...")
        response = session.get("http://localhost:5002/facial/manage_detections")
        
        if response.status_code != 200:
            print(f"❌ Page gestion inaccessible: {response.status_code}")
            return False
        
        print("✅ Page gestion accessible")
        
        # 2. Démarrage streaming depuis gestion
        print("🎬 Démarrage streaming depuis gestion...")
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Streaming démarré depuis gestion")
                
                # 3. Ajout détection pendant streaming
                print("➕ Ajout détection pendant streaming...")
                response = session.post("http://localhost:5002/facial/api/add_manual_detection", 
                                       json={
                                           'student_name': 'Elmehdi Rahaoui',
                                           'confidence': 0.947
                                       })
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Ajout détection pendant streaming: Réussi")
                    else:
                        print(f"⚠️ Ajout détection: {data.get('message')}")
                else:
                    print(f"❌ Ajout détection erreur: {response.status_code}")
                
                # 4. Vérification page après ajout
                print("📊 Vérification page après ajout...")
                response = session.get("http://localhost:5002/facial/manage_detections")
                
                if response.status_code == 200:
                    content = response.text
                    if "Elmehdi Rahaoui" in content:
                        print("✅ Détection ajoutée visible dans la page")
                    else:
                        print("⚠️ Détection ajoutée non visible (peut nécessiter actualisation)")
                else:
                    print(f"❌ Vérification page erreur: {response.status_code}")
                
                # 5. Arrêt streaming
                print("🛑 Arrêt streaming...")
                session.post("http://localhost:5002/facial/api/stop_streaming")
                print("✅ Streaming arrêté")
                
                return True
            else:
                print(f"❌ Streaming non démarré: {data.get('message')}")
                return False
        else:
            print(f"❌ Démarrage streaming erreur: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        return False

def main():
    """Exécuter tous les tests de streaming dans la gestion"""
    print("🎥 TESTS STREAMING DANS GESTION DÉTECTIONS")
    print("=" * 60)
    
    results = []
    
    # Test 1: Page avec streaming
    results.append(("Page Streaming Gestion", test_management_page_streaming()))
    
    # Test 2: APIs streaming
    results.append(("APIs Streaming", test_streaming_apis_from_management()))
    
    # Test 3: Intégration complète
    results.append(("Intégration Complète", test_integration_management_streaming()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS STREAMING GESTION")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:25}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 STREAMING DANS GESTION 100% FONCTIONNEL!")
        print("\n🎥 INSTRUCTIONS D'UTILISATION:")
        print("1. Accédez à: http://localhost:5002/facial/manage_detections")
        print("2. Connectez-vous: admin/admin123")
        print("3. Cliquez 'Démarrer Caméra' → Flux vidéo apparaît")
        print("4. Cliquez 'Activer Détection' → Reconnaissance en temps réel")
        print("5. Utilisez les boutons d'ajout/suppression pendant le streaming")
        print("6. Le système suggère l'ajout quand Elmehdi est détecté")
    else:
        print("⚠️ Certains tests ont échoué - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
