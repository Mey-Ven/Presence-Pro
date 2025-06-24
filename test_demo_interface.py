#!/usr/bin/env python3
"""
Test de l'interface de démonstration
"""

import requests
import time

def test_demo_interface():
    """Test complet de l'interface de démonstration"""
    print("🎬 TEST INTERFACE DE DÉMONSTRATION")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # 1. Connexion admin
        print("🔐 Connexion admin...")
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post("http://localhost:5002/login", data=login_data)
        
        if response.status_code not in [200, 302]:
            print(f"❌ Connexion échouée: {response.status_code}")
            return False
        
        print("✅ Connexion réussie")
        
        # 2. Accès à la page de démonstration
        print("📄 Accès page démonstration...")
        response = session.get("http://localhost:5002/facial/demo")
        
        if response.status_code != 200:
            print(f"❌ Page démonstration inaccessible: {response.status_code}")
            return False
        
        print("✅ Page démonstration accessible")
        
        # Vérifier le contenu de la page
        content = response.text
        if "Système de Reconnaissance Faciale" in content:
            print("✅ Titre de démonstration présent")
        else:
            print("⚠️ Titre de démonstration manquant")
        
        if "Elmehdi Rahaoui" in content:
            print("✅ Nom utilisateur présent")
        else:
            print("⚠️ Nom utilisateur manquant")
        
        # 3. Test du streaming pour la démonstration
        print("🎥 Test streaming démonstration...")
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Streaming démarré pour démonstration")
                
                # Attendre un peu
                time.sleep(2)
                
                # Test du flux vidéo
                response = session.get("http://localhost:5002/facial/video_feed", 
                                     stream=True, timeout=5)
                
                if response.status_code == 200:
                    print("✅ Flux vidéo accessible pour démonstration")
                    
                    # Lire quelques chunks
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            chunk_count += 1
                            if chunk_count >= 2:
                                break
                    
                    print(f"✅ {chunk_count} chunks vidéo reçus")
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                
                # 4. Test de l'activation de détection
                print("🔍 Test activation détection...")
                response = session.post("http://localhost:5002/facial/api/enable_detection")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Détection activée pour démonstration")
                    else:
                        print(f"⚠️ Problème activation détection: {data.get('message')}")
                else:
                    print(f"❌ Erreur activation détection: {response.status_code}")
                
                # 5. Test du statut streaming
                print("📊 Test statut streaming...")
                response = session.get("http://localhost:5002/facial/api/streaming_status")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        status = data.get('status', {})
                        print(f"✅ Statut streaming: {status.get('is_streaming')}")
                        print(f"✅ Détection active: {status.get('detection_enabled')}")
                        print(f"✅ Visages connus: {status.get('known_faces_count')}")
                    else:
                        print(f"⚠️ Problème statut: {data.get('message')}")
                else:
                    print(f"❌ Erreur statut: {response.status_code}")
                
                # Arrêter le streaming
                print("🛑 Arrêt streaming...")
                response = session.post("http://localhost:5002/facial/api/stop_streaming")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        print("✅ Streaming arrêté")
                    else:
                        print(f"⚠️ Problème arrêt: {data.get('message')}")
                else:
                    print(f"❌ Erreur arrêt: {response.status_code}")
                
            else:
                print(f"❌ Échec démarrage streaming: {data.get('message')}")
        else:
            print(f"❌ API start_streaming échouée: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_demo_features():
    """Test des fonctionnalités spécifiques à la démonstration"""
    print("\n🎯 TEST FONCTIONNALITÉS DÉMONSTRATION")
    print("=" * 50)
    
    session = requests.Session()
    
    try:
        # Connexion
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Accès à la page de démonstration
        response = session.get("http://localhost:5002/facial/demo")
        content = response.text
        
        # Vérifications du contenu
        checks = [
            ("Titre système", "Système de Reconnaissance Faciale"),
            ("Nom démonstration", "Elmehdi Rahaoui"),
            ("Bouton démarrage", "Démarrer Démonstration"),
            ("Bouton simulation", "Simuler Reconnaissance"),
            ("Statistiques", "Étudiants Enregistrés"),
            ("Panneau détection", "Système de Détection"),
            ("Badge reconnaissance", "PRÉSENT"),
            ("Styles CSS", "demo-container"),
            ("JavaScript", "startDemo"),
            ("Overlay vidéo", "video-overlay")
        ]
        
        passed = 0
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Présent")
                passed += 1
            else:
                print(f"❌ {check_name}: Manquant")
        
        print(f"\n📊 Score: {passed}/{len(checks)} vérifications réussies")
        
        if passed == len(checks):
            print("🎉 Toutes les fonctionnalités de démonstration sont présentes!")
        else:
            print("⚠️ Certaines fonctionnalités manquent")
        
        return passed == len(checks)
        
    except Exception as e:
        print(f"❌ Erreur test fonctionnalités: {e}")
        return False

def main():
    """Exécuter tous les tests de démonstration"""
    print("🎬 TESTS COMPLETS INTERFACE DÉMONSTRATION")
    print("=" * 60)
    
    results = []
    
    # Test 1: Interface de base
    results.append(("Interface Démonstration", test_demo_interface()))
    
    # Test 2: Fonctionnalités spécifiques
    results.append(("Fonctionnalités Démo", test_demo_features()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:25}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Interface de démonstration prête pour l'enregistrement!")
        print("🎥 Accédez à: http://localhost:5002/facial/demo")
        print("🔐 Connexion: admin / admin123")
        print("📹 Cliquez 'Démarrer Démonstration' pour commencer")
    else:
        print("⚠️ Certains tests ont échoué - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
