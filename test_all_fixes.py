"""
Test complet pour vérifier que tous les problèmes sont résolus
"""

import requests
import time
import subprocess
import sys
import socketio
import threading
from datetime import datetime

class ComprehensiveSystemTester:
    def __init__(self):
        self.session = requests.Session()
        self.dashboard_url = "http://localhost:5001"
        self.test_results = {}
        
    def login(self):
        """Se connecter au dashboard"""
        try:
            login_data = {'username': 'admin', 'password': 'admin123'}
            response = self.session.post(f"{self.dashboard_url}/login", data=login_data)
            return response.status_code == 200
        except:
            return False
    
    def test_no_autostart(self):
        """Test 1: Vérifier qu'il n'y a pas d'auto-start"""
        print("🚫 TEST 1: Absence d'auto-start")
        print("-" * 40)
        
        try:
            # Vérifier le statut initial
            response = self.session.get(f"{self.dashboard_url}/api/recognition/status")
            if response.status_code == 200:
                data = response.json()
                is_running = data.get('is_running', True)
                camera_status = data.get('camera_status', 'Inconnu')
                
                print(f"   Reconnaissance active: {is_running}")
                print(f"   Statut caméra: {camera_status}")
                
                if not is_running and camera_status == 'Déconnectée':
                    print("   ✅ PARFAIT: Aucun auto-start détecté")
                    return True
                else:
                    print("   ❌ PROBLÈME: Auto-start détecté")
                    return False
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False
    
    def test_camera_frames(self):
        """Test 2: Vérifier l'émission des frames caméra"""
        print("\n📷 TEST 2: Émission des frames caméra")
        print("-" * 40)
        
        frames_received = 0
        test_duration = 15  # secondes
        
        try:
            # Créer un client SocketIO
            sio = socketio.Client()
            
            @sio.on('camera_frame')
            def on_camera_frame(data):
                nonlocal frames_received
                frames_received += 1
                if frames_received <= 3:
                    frame_size = len(data.get('frame', ''))
                    print(f"   📷 Frame {frames_received} reçue: {frame_size} caractères")
            
            # Se connecter
            sio.connect(self.dashboard_url)
            print("   🔌 WebSocket connecté")
            
            # Démarrer la reconnaissance
            response = self.session.post(f"{self.dashboard_url}/api/recognition/start")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   ▶️ Reconnaissance démarrée")
                    
                    # Attendre les frames
                    print(f"   ⏳ Attente des frames ({test_duration}s)...")
                    time.sleep(test_duration)
                    
                    # Arrêter la reconnaissance
                    self.session.post(f"{self.dashboard_url}/api/recognition/stop")
                    print("   ⏹️ Reconnaissance arrêtée")
                    
                    sio.disconnect()
                    
                    print(f"   📊 Résultat: {frames_received} frames reçues")
                    
                    if frames_received > 0:
                        print("   ✅ SUCCÈS: Frames caméra émises correctement")
                        return True
                    else:
                        print("   ❌ ÉCHEC: Aucune frame reçue")
                        return False
                else:
                    print(f"   ❌ Échec démarrage: {data.get('message')}")
                    sio.disconnect()
                    return False
            else:
                print(f"   ❌ Erreur API: {response.status_code}")
                sio.disconnect()
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False
    
    def test_dashboard_features(self):
        """Test 3: Vérifier les fonctionnalités du dashboard"""
        print("\n🎛️ TEST 3: Fonctionnalités du dashboard")
        print("-" * 40)
        
        features_to_test = [
            ('/students', 'Page étudiants'),
            ('/settings', 'Page paramètres'),
            ('/attendance', 'Page présences'),
            ('/api/stats', 'API statistiques')
        ]
        
        all_working = True
        
        for url, name in features_to_test:
            try:
                response = self.session.get(f"{self.dashboard_url}{url}")
                if response.status_code == 200:
                    print(f"   ✅ {name}: OK")
                else:
                    print(f"   ❌ {name}: Erreur {response.status_code}")
                    all_working = False
            except Exception as e:
                print(f"   ❌ {name}: Erreur {e}")
                all_working = False
        
        return all_working
    
    def test_student_operations(self):
        """Test 4: Vérifier les opérations sur les étudiants"""
        print("\n👥 TEST 4: Opérations étudiants")
        print("-" * 40)
        
        try:
            # Obtenir la liste des étudiants
            response = self.session.get(f"{self.dashboard_url}/students")
            if response.status_code != 200:
                print("   ❌ Impossible d'accéder à la page étudiants")
                return False
            
            print("   ✅ Page étudiants accessible")
            
            # Tester l'API de statistiques
            response = self.session.get(f"{self.dashboard_url}/api/stats")
            if response.status_code == 200:
                data = response.json()
                student_count = data.get('total_students', 0)
                print(f"   ✅ API stats: {student_count} étudiants")
                return True
            else:
                print("   ❌ Erreur API stats")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False
    
    def test_recognition_control(self):
        """Test 5: Vérifier le contrôle de la reconnaissance"""
        print("\n🎯 TEST 5: Contrôle de la reconnaissance")
        print("-" * 40)
        
        try:
            # Test démarrage
            print("   ▶️ Test démarrage...")
            response = self.session.post(f"{self.dashboard_url}/api/recognition/start")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("   ✅ Démarrage réussi")
                    
                    # Attendre un peu
                    time.sleep(3)
                    
                    # Vérifier le statut
                    response = self.session.get(f"{self.dashboard_url}/api/recognition/status")
                    if response.status_code == 200:
                        status_data = response.json()
                        if status_data.get('is_running'):
                            print("   ✅ Statut confirmé: actif")
                            
                            # Test arrêt
                            print("   ⏹️ Test arrêt...")
                            response = self.session.post(f"{self.dashboard_url}/api/recognition/stop")
                            if response.status_code == 200:
                                stop_data = response.json()
                                if stop_data.get('success'):
                                    print("   ✅ Arrêt réussi")
                                    
                                    # Vérifier le statut final
                                    time.sleep(2)
                                    response = self.session.get(f"{self.dashboard_url}/api/recognition/status")
                                    if response.status_code == 200:
                                        final_status = response.json()
                                        if not final_status.get('is_running'):
                                            print("   ✅ Statut confirmé: inactif")
                                            return True
                                        else:
                                            print("   ❌ Reconnaissance encore active")
                                            return False
                                    else:
                                        print("   ❌ Erreur vérification statut final")
                                        return False
                                else:
                                    print(f"   ❌ Échec arrêt: {stop_data.get('message')}")
                                    return False
                            else:
                                print("   ❌ Erreur API arrêt")
                                return False
                        else:
                            print("   ❌ Reconnaissance non active après démarrage")
                            return False
                    else:
                        print("   ❌ Erreur vérification statut")
                        return False
                else:
                    print(f"   ❌ Échec démarrage: {data.get('message')}")
                    return False
            else:
                print("   ❌ Erreur API démarrage")
                return False
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
            return False
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🎯 TEST COMPLET DU SYSTÈME")
        print("=" * 60)
        print("Vérification de tous les correctifs appliqués")
        print()
        
        # Vérifier que le serveur est accessible
        try:
            response = requests.get(self.dashboard_url, timeout=5)
            print("✅ Serveur dashboard accessible")
        except Exception as e:
            print(f"❌ Serveur non accessible: {e}")
            return False
        
        # Se connecter
        if not self.login():
            print("❌ Impossible de se connecter")
            return False
        
        print("✅ Connexion réussie")
        
        # Exécuter tous les tests
        tests = [
            ('no_autostart', self.test_no_autostart),
            ('camera_frames', self.test_camera_frames),
            ('dashboard_features', self.test_dashboard_features),
            ('student_operations', self.test_student_operations),
            ('recognition_control', self.test_recognition_control)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            try:
                results[test_name] = test_func()
            except Exception as e:
                print(f"   ❌ Erreur dans le test {test_name}: {e}")
                results[test_name] = False
        
        # Résumé final
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        test_labels = {
            'no_autostart': 'Absence d\'auto-start',
            'camera_frames': 'Émission frames caméra',
            'dashboard_features': 'Fonctionnalités dashboard',
            'student_operations': 'Opérations étudiants',
            'recognition_control': 'Contrôle reconnaissance'
        }
        
        passed = 0
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            label = test_labels.get(test_name, test_name)
            print(f"{label}: {status}")
            if result:
                passed += 1
        
        success_rate = (passed / total) * 100
        print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis ({success_rate:.1f}%)")
        
        if passed == total:
            print("\n🎉 TOUS LES PROBLÈMES SONT RÉSOLUS!")
            print("   ✅ Aucun auto-start de la reconnaissance")
            print("   ✅ Flux caméra fonctionnel dans le dashboard")
            print("   ✅ Toutes les fonctionnalités accessibles")
            print("   ✅ Contrôle manuel complet")
            print("   ✅ Système prêt pour utilisation")
        else:
            print(f"\n⚠️ {total - passed} PROBLÈME(S) RESTANT(S)")
            for test_name, result in results.items():
                if not result:
                    label = test_labels.get(test_name, test_name)
                    print(f"   ❌ {label}")
            
            print("\n💡 Actions recommandées:")
            print("   - Redémarrer le serveur dashboard")
            print("   - Vérifier les logs du serveur")
            print("   - Tester individuellement chaque fonctionnalité")
        
        return passed == total

def main():
    """Fonction principale"""
    print("🔧 TESTEUR COMPLET DES CORRECTIFS")
    print("Ce script vérifie que tous les problèmes identifiés ont été résolus")
    print()
    
    tester = ComprehensiveSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎊 FÉLICITATIONS!")
        print("Votre système de reconnaissance faciale fonctionne parfaitement!")
    else:
        print("\n🔧 TRAVAIL SUPPLÉMENTAIRE NÉCESSAIRE")
        print("Certains problèmes nécessitent encore une attention.")

if __name__ == "__main__":
    main()
