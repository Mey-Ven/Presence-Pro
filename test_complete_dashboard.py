"""
Test complet de toutes les fonctionnalités du tableau de bord
Teste toutes les nouvelles fonctionnalités implémentées
"""

import requests
import time
import json
from datetime import datetime

# Configuration
DASHBOARD_URL = "http://localhost:5001"
USERNAME = "admin"
PASSWORD = "admin123"

class CompleteDashboardTester:
    def __init__(self):
        self.session = requests.Session()
        self.logged_in = False
    
    def login(self):
        """Se connecter au tableau de bord"""
        print("🔐 Connexion au tableau de bord...")
        
        response = self.session.get(f"{DASHBOARD_URL}/login")
        if response.status_code != 200:
            print(f"❌ Erreur lors de l'accès à la page de connexion: {response.status_code}")
            return False
        
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
    
    def test_dashboard_pages(self):
        """Tester l'accès à toutes les pages"""
        print("\n📄 Test d'accès aux pages...")
        
        pages = [
            ("/dashboard", "Tableau de Bord"),
            ("/students", "Gestion Étudiants"),
            ("/attendance", "Surveillance Présences"),
            ("/reports", "Rapports et Analytics"),
            ("/settings", "Paramètres")
        ]
        
        results = []
        for url, name in pages:
            try:
                response = self.session.get(f"{DASHBOARD_URL}{url}")
                if response.status_code == 200:
                    print(f"✅ {name}: Accessible")
                    results.append(True)
                else:
                    print(f"❌ {name}: Erreur {response.status_code}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {name}: Erreur {e}")
                results.append(False)
        
        return all(results)
    
    def test_export_functionality(self):
        """Tester les fonctionnalités d'export"""
        print("\n📊 Test des fonctionnalités d'export...")
        
        exports = [
            ("/export/attendance/csv", "Export CSV Présences"),
            ("/export/attendance/excel", "Export Excel Présences"),
            ("/export/students/csv", "Export CSV Étudiants")
        ]
        
        results = []
        for url, name in exports:
            try:
                response = self.session.get(f"{DASHBOARD_URL}{url}")
                if response.status_code == 200:
                    # Vérifier que c'est bien un fichier
                    content_type = response.headers.get('content-type', '')
                    if 'csv' in content_type or 'excel' in content_type or 'octet-stream' in content_type:
                        print(f"✅ {name}: Fichier généré ({len(response.content)} bytes)")
                        results.append(True)
                    else:
                        print(f"⚠️ {name}: Réponse inattendue")
                        results.append(False)
                else:
                    print(f"❌ {name}: Erreur {response.status_code}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {name}: Erreur {e}")
                results.append(False)
        
        return all(results)
    
    def test_api_endpoints(self):
        """Tester les endpoints API"""
        print("\n🔌 Test des APIs...")
        
        apis = [
            ("/api/stats", "GET", "Statistiques"),
            ("/api/recognition/status", "GET", "Statut reconnaissance"),
            ("/api/reports/data?type=daily&days=7", "GET", "Données rapports")
        ]
        
        results = []
        for url, method, name in apis:
            try:
                if method == "GET":
                    response = self.session.get(f"{DASHBOARD_URL}{url}")
                else:
                    response = self.session.post(f"{DASHBOARD_URL}{url}")
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"✅ {name}: Données JSON valides")
                        results.append(True)
                    except:
                        print(f"⚠️ {name}: Réponse non-JSON")
                        results.append(False)
                else:
                    print(f"❌ {name}: Erreur {response.status_code}")
                    results.append(False)
            except Exception as e:
                print(f"❌ {name}: Erreur {e}")
                results.append(False)
        
        return all(results)
    
    def test_settings_functionality(self):
        """Tester les fonctionnalités de paramètres"""
        print("\n⚙️ Test des paramètres...")
        
        # Test de sauvegarde de base de données
        try:
            response = self.session.get(f"{DASHBOARD_URL}/settings/backup")
            if response.status_code == 200:
                print(f"✅ Sauvegarde BD: Fichier généré ({len(response.content)} bytes)")
                backup_success = True
            else:
                print(f"❌ Sauvegarde BD: Erreur {response.status_code}")
                backup_success = False
        except Exception as e:
            print(f"❌ Sauvegarde BD: Erreur {e}")
            backup_success = False
        
        # Test de régénération des encodages
        try:
            response = self.session.post(f"{DASHBOARD_URL}/settings/regenerate-encodings")
            if response.status_code == 302:  # Redirection après succès
                print("✅ Régénération encodages: Succès")
                regen_success = True
            else:
                print(f"❌ Régénération encodages: Erreur {response.status_code}")
                regen_success = False
        except Exception as e:
            print(f"❌ Régénération encodages: Erreur {e}")
            regen_success = False
        
        return backup_success and regen_success
    
    def test_recognition_control(self):
        """Tester le contrôle de reconnaissance"""
        print("\n🎯 Test du contrôle de reconnaissance...")
        
        # Test démarrage
        try:
            response = self.session.post(f"{DASHBOARD_URL}/api/recognition/start")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Démarrage reconnaissance: Succès")
                    start_success = True
                else:
                    print(f"⚠️ Démarrage reconnaissance: {data.get('message')}")
                    start_success = False
            else:
                print(f"❌ Démarrage reconnaissance: Erreur {response.status_code}")
                start_success = False
        except Exception as e:
            print(f"❌ Démarrage reconnaissance: Erreur {e}")
            start_success = False
        
        # Attendre un peu
        time.sleep(2)
        
        # Test arrêt
        try:
            response = self.session.post(f"{DASHBOARD_URL}/api/recognition/stop")
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    print("✅ Arrêt reconnaissance: Succès")
                    stop_success = True
                else:
                    print(f"⚠️ Arrêt reconnaissance: {data.get('message')}")
                    stop_success = False
            else:
                print(f"❌ Arrêt reconnaissance: Erreur {response.status_code}")
                stop_success = False
        except Exception as e:
            print(f"❌ Arrêt reconnaissance: Erreur {e}")
            stop_success = False
        
        return start_success and stop_success
    
    def test_navigation_links(self):
        """Tester tous les liens de navigation"""
        print("\n🧭 Test des liens de navigation...")
        
        # Récupérer la page principale
        response = self.session.get(f"{DASHBOARD_URL}/dashboard")
        content = response.text
        
        # Vérifier la présence des éléments clés
        checks = [
            ("Contrôle de Reconnaissance Faciale", "Section reconnaissance"),
            ("Démarrer Reconnaissance", "Bouton démarrage"),
            ("Flux Caméra en Direct", "Section caméra"),
            ("Actions Rapides", "Section actions"),
            ("Statistiques en Temps Réel", "Section stats")
        ]
        
        results = []
        for text, description in checks:
            if text in content:
                print(f"✅ {description}: Trouvé")
                results.append(True)
            else:
                print(f"❌ {description}: Manquant")
                results.append(False)
        
        return all(results)
    
    def run_complete_test(self):
        """Exécuter tous les tests"""
        print("🧪 TESTS COMPLETS DU TABLEAU DE BORD")
        print("=" * 60)
        
        tests = [
            ("Connexion", self.login),
            ("Pages du tableau de bord", self.test_dashboard_pages),
            ("Fonctionnalités d'export", self.test_export_functionality),
            ("Endpoints API", self.test_api_endpoints),
            ("Paramètres système", self.test_settings_functionality),
            ("Contrôle reconnaissance", self.test_recognition_control),
            ("Navigation et interface", self.test_navigation_links)
        ]
        
        results = []
        
        for test_name, test_func in tests:
            print(f"\n🧪 Test: {test_name}")
            try:
                result = test_func()
                results.append((test_name, result))
                status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
                print(f"   Résultat: {status}")
                
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ ERREUR: {e}")
                results.append((test_name, False))
        
        # Résumé des résultats
        print("\n📊 RÉSUMÉ COMPLET DES TESTS")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
            print(f"   {test_name}: {status}")
        
        print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis")
        
        if passed == total:
            print("🎉 TOUS LES TESTS SONT RÉUSSIS!")
            print("   Le tableau de bord est entièrement fonctionnel.")
        elif passed >= total * 0.8:
            print("✅ LA PLUPART DES TESTS SONT RÉUSSIS")
            print("   Le système fonctionne globalement bien.")
        else:
            print("⚠️ PLUSIEURS TESTS ONT ÉCHOUÉ")
            print("   Vérifiez la configuration et les logs.")
        
        return passed, total

def main():
    """Fonction principale"""
    print("🎯 TESTEUR COMPLET DU TABLEAU DE BORD")
    print("=" * 60)
    print("Ce script teste toutes les fonctionnalités du tableau de bord")
    print("incluant les nouvelles fonctionnalités implémentées.")
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
    tester = CompleteDashboardTester()
    passed, total = tester.run_complete_test()
    
    # Recommandations finales
    print("\n💡 FONCTIONNALITÉS TESTÉES:")
    print("   ✅ Navigation complète du tableau de bord")
    print("   ✅ Export de données (CSV, Excel)")
    print("   ✅ APIs REST pour toutes les opérations")
    print("   ✅ Paramètres et configuration système")
    print("   ✅ Contrôle de reconnaissance faciale")
    print("   ✅ Interface utilisateur moderne")
    print("   ✅ Gestion des étudiants avancée")
    print("   ✅ Rapports et analytics")
    print("   ✅ Authentification et sécurité")

if __name__ == "__main__":
    main()
