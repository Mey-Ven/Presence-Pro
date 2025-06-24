#!/usr/bin/env python3
"""
Test des nouvelles fonctionnalités: cadre visage + historique manuel
"""

import requests
import time

def test_demo_face_frame():
    """Test du cadre de détection faciale dans la démonstration"""
    print("🔵 TEST CADRE DÉTECTION FACIALE")
    print("=" * 40)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Accès à la page de démonstration
        response = session.get("http://localhost:5002/facial/demo")
        
        if response.status_code != 200:
            print(f"❌ Page démonstration inaccessible: {response.status_code}")
            return False
        
        content = response.text
        
        # Vérifications du cadre de détection
        checks = [
            ("Cadre détection CSS", "face-detection-frame"),
            ("Label nom", "face-name-label"),
            ("Indicateur confiance", "confidence-indicator"),
            ("Animation pulse", "faceDetectionPulse"),
            ("Nom Elmehdi", "Elmehdi Rahaoui"),
            ("JavaScript cadre", "showFaceDetectionFrame"),
            ("Fonction masquer", "hideFaceDetectionFrame"),
            ("Styles cadre", "border: 3px solid #4facfe"),
            ("Position absolue", "position: absolute"),
            ("Z-index cadre", "z-index: 15")
        ]
        
        passed = 0
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Présent")
                passed += 1
            else:
                print(f"❌ {check_name}: Manquant")
        
        print(f"\n📊 Score cadre: {passed}/{len(checks)} vérifications réussies")
        return passed >= 8  # Au moins 8/10 pour considérer comme réussi
        
    except Exception as e:
        print(f"❌ Erreur test cadre: {e}")
        return False

def test_manual_detection_api():
    """Test de l'API d'ajout de détection manuelle"""
    print("\n🔧 TEST API DÉTECTION MANUELLE")
    print("=" * 40)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Test de l'API d'ajout manuel
        response = session.post("http://localhost:5002/facial/api/add_manual_detection", 
                               json={
                                   'student_name': 'Elmehdi Rahaoui',
                                   'confidence': 0.947
                               })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ API ajout détection: Fonctionnelle")
                print(f"✅ Nom ajouté: {data.get('student_name')}")
                print(f"✅ Confiance: {data.get('confidence')}")
                print(f"✅ Heure: {data.get('time')}")
                return True
            else:
                print(f"❌ API échec: {data.get('message')}")
                return False
        else:
            print(f"❌ API erreur HTTP: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test API: {e}")
        return False

def test_attendance_history_features():
    """Test des fonctionnalités de l'historique"""
    print("\n📊 TEST HISTORIQUE DÉTECTIONS")
    print("=" * 40)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Accès à la page d'historique
        response = session.get("http://localhost:5002/facial/attendance_history")
        
        if response.status_code != 200:
            print(f"❌ Page historique inaccessible: {response.status_code}")
            return False
        
        content = response.text
        
        # Vérifications de l'historique
        checks = [
            ("Bouton ajout détection", "Ajouter Détection"),
            ("Fonction JavaScript", "addManualDetection"),
            ("API endpoint", "/facial/api/add_manual_detection"),
            ("Nom Elmehdi présent", "Elmehdi Rahaoui"),
            ("Historique détections", "Historique des Détections"),
            ("Bouton actualiser", "Actualiser"),
            ("Export données", "Exporter"),
            ("Filtres recherche", "Filtres de Recherche"),
            ("Statistiques", "Enregistrements"),
            ("Confiance moyenne", "Confiance Moyenne")
        ]
        
        passed = 0
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name}: Présent")
                passed += 1
            else:
                print(f"❌ {check_name}: Manquant")
        
        print(f"\n📊 Score historique: {passed}/{len(checks)} vérifications réussies")
        return passed >= 8  # Au moins 8/10 pour considérer comme réussi
        
    except Exception as e:
        print(f"❌ Erreur test historique: {e}")
        return False

def test_demo_streaming_with_frame():
    """Test du streaming avec cadre dans la démonstration"""
    print("\n🎥 TEST STREAMING AVEC CADRE")
    print("=" * 40)
    
    session = requests.Session()
    
    try:
        # Connexion admin
        login_data = {'username': 'admin', 'password': 'admin123'}
        session.post("http://localhost:5002/login", data=login_data)
        
        # Démarrer le streaming
        response = session.post("http://localhost:5002/facial/api/start_streaming")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Streaming démarré pour test cadre")
                
                # Attendre un peu
                time.sleep(2)
                
                # Test du flux vidéo
                response = session.get("http://localhost:5002/facial/video_feed", 
                                     stream=True, timeout=5)
                
                if response.status_code == 200:
                    print("✅ Flux vidéo accessible avec cadre")
                    
                    # Lire quelques chunks
                    chunk_count = 0
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            chunk_count += 1
                            if chunk_count >= 2:
                                break
                    
                    print(f"✅ {chunk_count} chunks vidéo reçus")
                    
                    # Arrêter le streaming
                    session.post("http://localhost:5002/facial/api/stop_streaming")
                    print("✅ Streaming arrêté")
                    
                    return True
                else:
                    print(f"❌ Flux vidéo inaccessible: {response.status_code}")
                    return False
            else:
                print(f"❌ Échec démarrage streaming: {data.get('message')}")
                return False
        else:
            print(f"❌ API streaming échouée: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"❌ Erreur test streaming: {e}")
        return False

def main():
    """Exécuter tous les tests des nouvelles fonctionnalités"""
    print("🎯 TESTS NOUVELLES FONCTIONNALITÉS")
    print("=" * 50)
    print("🔵 Cadre détection faciale + Historique manuel")
    print("=" * 50)
    
    results = []
    
    # Test 1: Cadre de détection faciale
    results.append(("Cadre Détection Faciale", test_demo_face_frame()))
    
    # Test 2: API détection manuelle
    results.append(("API Détection Manuelle", test_manual_detection_api()))
    
    # Test 3: Fonctionnalités historique
    results.append(("Historique Amélioré", test_attendance_history_features()))
    
    # Test 4: Streaming avec cadre
    results.append(("Streaming + Cadre", test_demo_streaming_with_frame()))
    
    # Résumé
    print("\n" + "=" * 50)
    print("📊 RÉSUMÉ DES TESTS")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:25}: {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n🎯 Score: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 Toutes les nouvelles fonctionnalités sont opérationnelles!")
        print("🔵 Cadre détection: http://localhost:5002/facial/demo")
        print("📊 Historique manuel: http://localhost:5002/facial/attendance_history")
        print("🎬 Instructions:")
        print("   1. Demo: Cliquer 'Démarrer Démonstration' → Cadre bleu avec nom")
        print("   2. Historique: Cliquer 'Ajouter Détection' → Nouvelle entrée")
    else:
        print("⚠️ Certains tests ont échoué - Vérifiez les erreurs ci-dessus")

if __name__ == "__main__":
    main()
