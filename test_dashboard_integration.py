"""
Script de test pour vérifier l'intégration complète du système de reconnaissance faciale
avec le tableau de bord web
"""

import requests
import time
import json
from datetime import datetime

# Configuration
DASHBOARD_URL = "http://localhost:5001"
USERNAME = "admin"
PASSWORD = "admin123"

class DashboardTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self):
        """Se connecter au tableau de bord"""
        print("🔐 Connexion au tableau de bord...")
        
        # Obtenir la page de connexion
        response = self.session.get(f"{DASHBOARD_URL}/login")
        if response.status_code != 200:
            print(f"❌ Erreur lors de l'accès à la page de connexion: {response.status_code}")
            return False
        
        # Se connecter
        login_data = {
            'username': USERNAME,
            'password': PASSWORD
        }
        
        response = self.session.post(f"{DASHBOARD_URL}/login", data=login_data)
        if response.status_code == 200 and "dashboard" in response.url:
            print("✅ Connexion réussie")
            self.logged_in = True
            return True
        else:
            print(f"❌ Échec de la connexion: {response.status_code}")
            return False
    
    def test_recognition_status(self):
        """Tester l'API de statut de reconnaissance"""
        print("\n📊 Test du statut de reconnaissance...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.get(f"{DASHBOARD_URL}/api/recognition/status")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Statut récupéré:")
                print(f"   - Reconnaissance active: {data.get('is_running', False)}")
                print(f"   - Statut caméra: {data.get('camera_status', 'Inconnu')}")
                print(f"   - Visages connus: {data.get('known_faces_count', 0)}")
                print(f"   - Encodages chargés: {data.get('encodings_loaded', False)}")
                return True
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_start_recognition(self):
        """Tester le démarrage de la reconnaissance"""
        print("\n🚀 Test du démarrage de la reconnaissance...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.post(f"{DASHBOARD_URL}/api/recognition/start")
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    print(f"✅ Reconnaissance démarrée: {data.get('message', '')}")
                    return True
                else:
                    print(f"⚠️ Démarrage échoué: {data.get('message', '')}")
                    return False
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_stop_recognition(self):
        """Tester l'arrêt de la reconnaissance"""
        print("\n🛑 Test de l'arrêt de la reconnaissance...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.post(f"{DASHBOARD_URL}/api/recognition/stop")
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    print(f"✅ Reconnaissance arrêtée: {data.get('message', '')}")
                    return True
                else:
                    print(f"⚠️ Arrêt échoué: {data.get('message', '')}")
                    return False
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_reload_encodings(self):
        """Tester le rechargement des encodages"""
        print("\n🔄 Test du rechargement des encodages...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.post(f"{DASHBOARD_URL}/api/recognition/reload")
            if response.status_code == 200:
                data = response.json()
                if data.get('success', False):
                    print(f"✅ Encodages rechargés: {data.get('message', '')}")
                    return True
                else:
                    print(f"⚠️ Rechargement échoué: {data.get('message', '')}")
                    return False
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_stats_api(self):
        """Tester l'API des statistiques"""
        print("\n📈 Test de l'API des statistiques...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.get(f"{DASHBOARD_URL}/api/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Statistiques récupérées:")
                print(f"   - Total étudiants: {data.get('total_students', 0)}")
                print(f"   - Présences aujourd'hui: {data.get('today_attendance', 0)}")
                print(f"   - Total présences: {data.get('total_attendance', 0)}")
                print(f"   - Présences cette semaine: {data.get('week_attendance', 0)}")
                return True
            else:
                print(f"❌ Erreur API: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def test_dashboard_access(self):
        """Tester l'accès au tableau de bord"""
        print("\n🏠 Test d'accès au tableau de bord...")
        
        if not self.logged_in:
            print("❌ Non connecté")
            return False
        
        try:
            response = self.session.get(f"{DASHBOARD_URL}/dashboard")
            if response.status_code == 200:
                print("✅ Tableau de bord accessible")
                # Vérifier la présence de certains éléments
                content = response.text
                if "Contrôle de Reconnaissance Faciale" in content:
                    print("✅ Section de contrôle de reconnaissance trouvée")
                if "Démarrer Reconnaissance" in content:
                    print("✅ Bouton de démarrage trouvé")
                if "Flux Caméra en Direct" in content:
                    print("✅ Section de flux caméra trouvée")
                return True
            else:
                print(f"❌ Erreur d'accès: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def run_full_test(self):
        """Exécuter tous les tests"""
        print("🧪 DÉMARRAGE DES TESTS D'INTÉGRATION")
        print("=" * 60)
        
        tests = [
            ("Connexion", self.login),
            ("Accès tableau de bord", self.test_dashboard_access),
            ("API statistiques", self.test_stats_api),
            ("Statut reconnaissance", self.test_recognition_status),
            ("Rechargement encodages", self.test_reload_encodings),
            ("Démarrage reconnaissance", self.test_start_recognition),
            ("Statut après démarrage", self.test_recognition_status),
            ("Arrêt reconnaissance", self.test_stop_recognition),
            ("Statut après arrêt", self.test_recognition_status),
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
                print(f"   Résultat: {status}")
                
                # Petite pause entre les tests
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                results.append((test_name, False))
        
        # Résumé des résultats
        print("\n📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
            print("   L'intégration du tableau de bord fonctionne parfaitement.")
        elif passed >= total * 0.8:
            print("✅ LA PLUPART DES TESTS SONT RÉUSSIS")
            print("   L'intégration fonctionne globalement bien.")
        else:
            print("⚠️ PLUSIEURS TESTS ONT ÉCHOUÉ")
            print("   Vérifiez la configuration et les logs du serveur.")
        
        return passed, total

def main():
    """Fonction principale"""
    print("🎯 TESTEUR D'INTÉGRATION TABLEAU DE BORD")
    print("=" * 60)
    print("Ce script teste l'intégration complète du système de reconnaissance")
    print("faciale avec le tableau de bord web.")
    print()
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        print(f"✅ Serveur accessible à {DASHBOARD_URL}")
    except Exception as e:
        print(f"❌ Serveur non accessible: {e}")
        print("   Assurez-vous que le tableau de bord est démarré avec:")
        print("   python admin_dashboard.py")
        return
    
    # Exécuter les tests
    tester = DashboardTester()
    passed, total = tester.run_full_test()
    
    # Recommandations
    print("\n💡 RECOMMANDATIONS:")
    if passed == total:
        print("   - Le système est prêt pour la production")
        print("   - Vous pouvez utiliser toutes les fonctionnalités")
        print("   - Testez avec de vrais utilisateurs")
    else:
        print("   - Vérifiez les logs du serveur pour plus de détails")
        print("   - Assurez-vous que toutes les dépendances sont installées")
        print("   - Redémarrez le serveur si nécessaire")

if __name__ == "__main__":
    main()
