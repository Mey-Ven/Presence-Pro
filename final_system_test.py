"""
Test final du système Presence Pro après réinitialisation complète
"""

import requests
import sqlite3
import os
import pickle
from datetime import datetime

def test_database_reset():
    """Teste que la base de données a été réinitialisée"""
    print("🗄️ TEST DE LA BASE DE DONNÉES")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Compter les étudiants
        cursor.execute("SELECT COUNT(*) FROM etudiants")
        student_count = cursor.fetchone()[0]
        
        # Compter les présences
        cursor.execute("SELECT COUNT(*) FROM presences")
        attendance_count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   📊 Étudiants: {student_count}")
        print(f"   📊 Présences: {attendance_count}")
        
        if student_count == 0 and attendance_count == 0:
            print("   ✅ Base de données correctement réinitialisée")
            return True
        else:
            print("   ❌ Base de données non vide")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_dataset_reset():
    """Teste que le dossier dataset a été réinitialisé"""
    print("\n📁 TEST DU DOSSIER DATASET")
    print("=" * 40)
    
    try:
        if not os.path.exists("dataset"):
            print("   ❌ Dossier dataset n'existe pas")
            return False
        
        # Lister le contenu
        contents = os.listdir("dataset")
        # Filtrer les fichiers cachés comme .gitkeep
        visible_contents = [f for f in contents if not f.startswith('.')]
        
        print(f"   📂 Contenu visible: {len(visible_contents)} éléments")
        
        if len(visible_contents) == 0:
            print("   ✅ Dossier dataset vide (correct)")
            return True
        else:
            print(f"   ⚠️ Contenu trouvé: {visible_contents}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_encodings_reset():
    """Teste que les encodages faciaux ont été réinitialisés"""
    print("\n🧠 TEST DES ENCODAGES FACIAUX")
    print("=" * 40)
    
    try:
        if not os.path.exists("encodings.pickle"):
            print("   ❌ Fichier encodings.pickle n'existe pas")
            return False
        
        with open("encodings.pickle", "rb") as f:
            data = pickle.load(f)
        
        encodings_count = len(data.get("encodings", []))
        names_count = len(data.get("names", []))
        
        print(f"   📊 Encodages: {encodings_count}")
        print(f"   📊 Noms: {names_count}")
        
        if encodings_count == 0 and names_count == 0:
            print("   ✅ Encodages correctement réinitialisés")
            return True
        else:
            print("   ❌ Encodages non vides")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_dashboard_access():
    """Teste l'accès au tableau de bord"""
    print("\n🌐 TEST D'ACCÈS AU TABLEAU DE BORD")
    print("=" * 40)
    
    try:
        # Test de la page principale
        response = requests.get("http://localhost:5001", timeout=5)
        print(f"   🏠 Page principale: {response.status_code}")
        
        # Test de la page de connexion
        response = requests.get("http://localhost:5001/login", timeout=5)
        print(f"   🔐 Page de connexion: {response.status_code}")
        
        # Test de l'API de statut (sans authentification)
        response = requests.get("http://localhost:5001/api/recognition/status", timeout=5)
        print(f"   📡 API statut: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_facial_recognition_ready():
    """Teste que le système de reconnaissance est prêt"""
    print("\n🎯 TEST DE PRÉPARATION RECONNAISSANCE FACIALE")
    print("=" * 40)
    
    try:
        # Vérifier les modules nécessaires
        import face_recognition
        import cv2
        print("   ✅ Modules face_recognition et cv2 importés")
        
        # Vérifier la caméra
        cap = cv2.VideoCapture(0)
        if cap.isOpened():
            print("   ✅ Caméra accessible")
            cap.release()
        else:
            print("   ⚠️ Caméra non accessible (normal si aucune caméra)")
        
        return True
        
    except ImportError as e:
        print(f"   ❌ Module manquant: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

def test_templates_exist():
    """Teste que tous les templates nécessaires existent"""
    print("\n📄 TEST DES TEMPLATES")
    print("=" * 40)
    
    required_templates = [
        "templates/base.html",
        "templates/dashboard.html",
        "templates/students.html",
        "templates/add_student.html",
        "templates/edit_student.html",
        "templates/train_student.html",
        "templates/attendance.html",
        "templates/settings.html",
        "templates/login.html"
    ]
    
    missing_templates = []
    
    for template in required_templates:
        if os.path.exists(template):
            print(f"   ✅ {template}")
        else:
            print(f"   ❌ {template}")
            missing_templates.append(template)
    
    if len(missing_templates) == 0:
        print("   ✅ Tous les templates sont présents")
        return True
    else:
        print(f"   ❌ {len(missing_templates)} template(s) manquant(s)")
        return False

def run_final_test():
    """Exécute tous les tests finaux"""
    print("🎯 TEST FINAL DU SYSTÈME PRESENCE PRO")
    print("=" * 80)
    print("Vérification après réinitialisation complète")
    print()
    
    tests = [
        ("Base de données", test_database_reset),
        ("Dossier dataset", test_dataset_reset),
        ("Encodages faciaux", test_encodings_reset),
        ("Accès dashboard", test_dashboard_access),
        ("Reconnaissance faciale", test_facial_recognition_ready),
        ("Templates", test_templates_exist)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"   ❌ Erreur dans le test {test_name}: {e}")
            results[test_name] = False
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ FINAL")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    success_rate = (passed / total) * 100
    print(f"\n🎯 RÉSULTAT GLOBAL: {passed}/{total} tests réussis ({success_rate:.1f}%)")
    
    if passed == total:
        print("\n🎉 SYSTÈME COMPLÈTEMENT RÉINITIALISÉ ET PRÊT!")
        print("=" * 60)
        print("✅ Base de données vide")
        print("✅ Dossier dataset vide") 
        print("✅ Encodages faciaux réinitialisés")
        print("✅ Dashboard accessible")
        print("✅ Reconnaissance faciale prête")
        print("✅ Tous les templates présents")
        print()
        print("🚀 PROCHAINES ÉTAPES:")
        print("1. Accédez à http://localhost:5001")
        print("2. Connectez-vous (admin/admin123)")
        print("3. Ajoutez vos premiers étudiants")
        print("4. Effectuez l'entraînement facial pour chaque étudiant")
        print("5. Testez la reconnaissance faciale")
        print()
        print("💡 Le système est maintenant dans un état propre,")
        print("   prêt pour une utilisation en production!")
        
    else:
        print(f"\n⚠️ {total - passed} PROBLÈME(S) DÉTECTÉ(S)")
        for test_name, result in results.items():
            if not result:
                print(f"   ❌ {test_name}")
        
        print("\n🔧 ACTIONS RECOMMANDÉES:")
        print("- Vérifiez les erreurs ci-dessus")
        print("- Relancez le script de réinitialisation si nécessaire")
        print("- Contactez le support en cas de problème persistant")
    
    return passed == total

if __name__ == "__main__":
    success = run_final_test()
    
    if success:
        print("\n🎊 FÉLICITATIONS!")
        print("Votre système Presence Pro est parfaitement réinitialisé!")
    else:
        print("\n🔧 TRAVAIL SUPPLÉMENTAIRE NÉCESSAIRE")
        print("Certains éléments nécessitent encore une attention.")
