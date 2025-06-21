"""
Script de test pour le système intégré de gestion des étudiants avec entraînement facial
"""

import os
import sys
import sqlite_database as db
import facial_training_module as ftm
import pickle

def test_database_integration():
    """Test l'intégration avec la base de données SQLite"""
    print("=== TEST D'INTÉGRATION BASE DE DONNÉES ===")
    
    try:
        # Initialiser la base de données
        db.initialize_database()
        print("✅ Base de données initialisée")
        
        # Compter les étudiants
        etudiants = db.obtenir_tous_etudiants()
        print(f"✅ {len(etudiants)} étudiants trouvés dans la base")
        
        return True
    except Exception as e:
        print(f"❌ Erreur base de données: {e}")
        return False

def test_facial_module():
    """Test le module d'entraînement facial"""
    print("\n=== TEST MODULE ENTRAÎNEMENT FACIAL ===")
    
    try:
        # Initialiser le module
        trainer = ftm.FacialTrainingModule()
        print("✅ Module d'entraînement initialisé")
        
        # Vérifier le dossier dataset
        if os.path.exists(trainer.dataset_folder):
            images = [f for f in os.listdir(trainer.dataset_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
            print(f"✅ Dossier dataset trouvé avec {len(images)} images")
        else:
            print("⚠️  Dossier dataset non trouvé (sera créé automatiquement)")
        
        return True
    except Exception as e:
        print(f"❌ Erreur module facial: {e}")
        return False

def test_encodings_file():
    """Test le fichier d'encodages"""
    print("\n=== TEST FICHIER ENCODAGES ===")
    
    try:
        encodings_file = "encodings.pickle"
        
        if os.path.exists(encodings_file):
            with open(encodings_file, "rb") as f:
                data = pickle.load(f)
            
            encodings = data.get("encodings", [])
            names = data.get("names", [])
            
            print(f"✅ Fichier encodings.pickle trouvé")
            print(f"✅ {len(encodings)} encodages trouvés")
            print(f"✅ {len(names)} noms trouvés")
            
            # Afficher les noms uniques
            unique_names = list(set(names))
            print(f"👥 Personnes enregistrées: {', '.join(unique_names)}")
            
            return True
        else:
            print("⚠️  Fichier encodings.pickle non trouvé")
            print("💡 Utilisez l'option 7 du système pour générer les encodages")
            return False
            
    except Exception as e:
        print(f"❌ Erreur fichier encodages: {e}")
        return False

def test_dataset_images():
    """Test les images du dataset"""
    print("\n=== TEST IMAGES DATASET ===")
    
    try:
        dataset_folder = "dataset"
        
        if not os.path.exists(dataset_folder):
            print("⚠️  Dossier dataset non trouvé")
            return False
        
        # Lister toutes les images
        image_files = [f for f in os.listdir(dataset_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        if not image_files:
            print("⚠️  Aucune image trouvée dans le dataset")
            return False
        
        print(f"📁 {len(image_files)} images trouvées dans le dataset")
        
        # Analyser les noms
        persons = {}
        for img in image_files:
            # Format attendu: Prenom_Nom_X.jpg
            parts = img.split("_")
            if len(parts) >= 2:
                person_name = "_".join(parts[:2])
                if person_name not in persons:
                    persons[person_name] = []
                persons[person_name].append(img)
        
        print(f"👥 Personnes dans le dataset:")
        for person, images in persons.items():
            print(f"   - {person}: {len(images)} images")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur dataset: {e}")
        return False

def test_camera_availability():
    """Test la disponibilité de la caméra"""
    print("\n=== TEST DISPONIBILITÉ CAMÉRA ===")
    
    try:
        trainer = ftm.FacialTrainingModule()
        cap = trainer.find_camera()
        
        if cap is not None:
            print("✅ Caméra trouvée et fonctionnelle")
            cap.release()
            return True
        else:
            print("⚠️  Aucune caméra fonctionnelle trouvée")
            print("💡 L'entraînement facial nécessite une caméra")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test caméra: {e}")
        return False

def test_face_recognition_compatibility():
    """Test la compatibilité avec le système de reconnaissance faciale"""
    print("\n=== TEST COMPATIBILITÉ RECONNAISSANCE FACIALE ===")
    
    try:
        # Vérifier que le fichier principal existe
        main_file = "face_recognition_attendance_improved.py"
        if os.path.exists(main_file):
            print(f"✅ Fichier principal trouvé: {main_file}")
        else:
            print(f"⚠️  Fichier principal non trouvé: {main_file}")
            return False
        
        # Vérifier l'import SQLite dans le fichier principal
        with open(main_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if "sqlite_config" in content:
            print("✅ Configuration SQLite détectée dans le fichier principal")
        elif "firebase_config" in content:
            print("⚠️  Configuration Firebase détectée")
            print("💡 Modifiez l'import pour utiliser SQLite:")
            print("   import sqlite_config as firebase_config")
        else:
            print("⚠️  Configuration non détectée")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur test compatibilité: {e}")
        return False

def test_student_in_both_systems():
    """Test qu'un étudiant existe dans les deux systèmes"""
    print("\n=== TEST ÉTUDIANT DANS LES DEUX SYSTÈMES ===")
    
    try:
        # Vérifier Elmehdi Rahaoui dans la base de données
        elmehdi_in_db = db.etudiant_existe(email="elmehdi.rahaoui@example.com")
        print(f"📊 Elmehdi Rahaoui dans la base de données: {'✅ Oui' if elmehdi_in_db else '❌ Non'}")
        
        # Vérifier Elmehdi Rahaoui dans les encodages
        encodings_file = "encodings.pickle"
        elmehdi_in_encodings = False
        
        if os.path.exists(encodings_file):
            with open(encodings_file, "rb") as f:
                data = pickle.load(f)
            names = data.get("names", [])
            elmehdi_in_encodings = any("Elmehdi" in name for name in names)
        
        print(f"🔍 Elmehdi Rahaoui dans les encodages: {'✅ Oui' if elmehdi_in_encodings else '❌ Non'}")
        
        if elmehdi_in_db and elmehdi_in_encodings:
            print("🎉 Elmehdi Rahaoui est prêt pour la reconnaissance faciale!")
            return True
        else:
            print("⚠️  Elmehdi Rahaoui n'est pas complètement configuré")
            if not elmehdi_in_db:
                print("💡 Ajoutez-le dans la base de données avec le système de gestion")
            if not elmehdi_in_encodings:
                print("💡 Ajoutez son entraînement facial avec l'option 6")
            return False
            
    except Exception as e:
        print(f"❌ Erreur test étudiant: {e}")
        return False

def generate_test_report():
    """Génère un rapport de test complet"""
    print("🔍 GÉNÉRATION DU RAPPORT DE TEST")
    print("=" * 60)
    
    tests = [
        ("Base de données SQLite", test_database_integration),
        ("Module entraînement facial", test_facial_module),
        ("Fichier encodages", test_encodings_file),
        ("Images dataset", test_dataset_images),
        ("Disponibilité caméra", test_camera_availability),
        ("Compatibilité reconnaissance", test_face_recognition_compatibility),
        ("Étudiant dans les deux systèmes", test_student_in_both_systems)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🧪 Test: {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            results.append((test_name, False))
    
    # Résumé final
    print("\n" + "=" * 60)
    print("📋 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ RÉUSSI" if result else "❌ ÉCHOUÉ"
        print(f"{test_name:<35} : {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Résultat global: {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 SYSTÈME COMPLÈTEMENT OPÉRATIONNEL!")
        print("🚀 Vous pouvez utiliser le système de reconnaissance faciale")
    elif passed >= total * 0.8:
        print("⚠️  SYSTÈME MAJORITAIREMENT OPÉRATIONNEL")
        print("🔧 Quelques ajustements mineurs peuvent être nécessaires")
    else:
        print("❌ SYSTÈME NÉCESSITE DES CORRECTIONS")
        print("🛠️  Veuillez corriger les erreurs avant utilisation")
    
    # Recommandations
    print(f"\n💡 RECOMMANDATIONS:")
    
    if not any(result for name, result in results if "caméra" in name.lower()):
        print("📸 Connectez une caméra pour l'entraînement facial")
    
    if not any(result for name, result in results if "encodages" in name.lower()):
        print("🔧 Générez les encodages avec l'option 7 du système de gestion")
    
    if not any(result for name, result in results if "étudiant" in name.lower()):
        print("👤 Ajoutez Elmehdi Rahaoui dans le système complet")
    
    print(f"\n🎯 Pour utiliser le système:")
    print(f"   python manage_students_with_facial_training.py")
    print(f"   python face_recognition_attendance_improved.py")

def main():
    """Fonction principale"""
    print("🧪 TEST DU SYSTÈME INTÉGRÉ DE RECONNAISSANCE FACIALE")
    print("=" * 60)
    print("Ce script teste tous les composants du système intégré")
    print()
    
    generate_test_report()

if __name__ == "__main__":
    main()
