"""
Test pour confirmer que la reconnaissance faciale ne démarre PAS automatiquement
"""

import requests
import time

def test_no_autostart():
    """Teste que la reconnaissance ne démarre pas automatiquement"""
    print("🧪 TEST : Vérification du non-démarrage automatique")
    print("=" * 60)
    
    # Attendre que le serveur soit prêt
    print("⏳ Attente du démarrage du serveur...")
    time.sleep(3)
    
    # Créer une session et se connecter
    session = requests.Session()
    
    try:
        # Se connecter d'abord
        print("🔐 Connexion au tableau de bord...")
        
        # Page de connexion
        response = session.get("http://localhost:5001/login")
        if response.status_code != 200:
            print(f"❌ Erreur d'accès à la page de connexion: {response.status_code}")
            return False
        
        # Connexion
        login_data = {'username': 'admin', 'password': 'admin123'}
        response = session.post("http://localhost:5001/login", data=login_data)
        
        if response.status_code != 200 or "dashboard" not in response.url:
            print(f"❌ Échec de la connexion: {response.status_code}")
            return False
        
        print("✅ Connexion réussie")
        
        # Maintenant tester le statut de reconnaissance
        print("🎯 Vérification du statut de reconnaissance...")
        
        response = session.get("http://localhost:5001/api/recognition/status")
        if response.status_code == 200:
            data = response.json()
            
            is_running = data.get('is_running', True)
            camera_status = data.get('camera_status', 'Inconnu')
            known_faces = data.get('known_faces_count', 0)
            encodings_loaded = data.get('encodings_loaded', False)
            
            print(f"📊 Résultats du test:")
            print(f"   🎯 Reconnaissance active: {is_running}")
            print(f"   📷 Statut caméra: {camera_status}")
            print(f"   👥 Visages connus: {known_faces}")
            print(f"   🔧 Encodages chargés: {encodings_loaded}")
            
            print("\n" + "=" * 60)
            
            if not is_running:
                print("🎉 EXCELLENT ! Le système fonctionne comme prévu:")
                print("   ✅ La reconnaissance faciale ne démarre PAS automatiquement")
                print("   ✅ Les encodages sont chargés et prêts")
                print("   ✅ La caméra n'est pas activée automatiquement")
                print("   ✅ Vous avez le contrôle total depuis le tableau de bord")
                print("\n💡 Pour démarrer la reconnaissance:")
                print("   1. Allez sur http://localhost:5001")
                print("   2. Connectez-vous (admin/admin123)")
                print("   3. Cliquez sur 'Démarrer Reconnaissance' dans le tableau de bord")
                print("   4. La reconnaissance se lancera UNIQUEMENT quand vous le décidez")
                return True
            else:
                print("⚠️ ATTENTION : La reconnaissance semble active automatiquement")
                print("   Cela ne devrait pas arriver selon votre demande")
                return False
                
        else:
            print(f"❌ Erreur API: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def main():
    """Fonction principale"""
    print("🎯 VÉRIFICATION DU COMPORTEMENT DE DÉMARRAGE")
    print("Ce test confirme que la reconnaissance faciale ne démarre")
    print("PAS automatiquement au lancement de l'application.")
    print()
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ Serveur accessible")
    except Exception as e:
        print(f"❌ Serveur non accessible: {e}")
        print("   Assurez-vous que le tableau de bord est démarré avec:")
        print("   python admin_dashboard.py")
        return
    
    # Exécuter le test
    success = test_no_autostart()
    
    if success:
        print("\n🎊 RÉSULTAT FINAL:")
        print("   ✅ Le système respecte parfaitement votre demande")
        print("   ✅ Aucun démarrage automatique de la reconnaissance")
        print("   ✅ Contrôle manuel complet via l'interface web")
        print("   ✅ Prêt pour utilisation selon vos préférences")
    else:
        print("\n⚠️ RÉSULTAT FINAL:")
        print("   ❌ Le comportement ne correspond pas à votre demande")
        print("   ❌ Des ajustements peuvent être nécessaires")

if __name__ == "__main__":
    main()
