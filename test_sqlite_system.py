"""
Script de test complet pour le système SQLite
Ce script teste toutes les fonctionnalités du système SQLite
"""

import sqlite_database as db
import sqlite_config as config
import os
from datetime import datetime

def test_database_initialization():
    """Test l'initialisation de la base de données"""
    print("=== Test d'initialisation de la base de données ===")
    
    try:
        db.initialize_database()
        print("✓ Initialisation de la base de données réussie")
        
        # Vérifier que le fichier de base de données existe
        if os.path.exists(db.DATABASE_FILE):
            print(f"✓ Fichier de base de données créé : {db.DATABASE_FILE}")
        else:
            print(f"✗ Fichier de base de données non trouvé : {db.DATABASE_FILE}")
            return False
            
        return True
    except Exception as e:
        print(f"✗ Erreur lors de l'initialisation : {e}")
        return False

def test_student_operations():
    """Test les opérations sur les étudiants"""
    print("\n=== Test des opérations sur les étudiants ===")
    
    try:
        # Test d'ajout d'étudiant
        print("Test d'ajout d'étudiant...")
        id_etudiant, mot_de_passe = db.ajouter_etudiant(
            nom="TestNom",
            prenom="TestPrenom",
            email="test.etudiant@example.com",
            telephone="+33123456789"
        )
        
        if id_etudiant:
            print(f"✓ Étudiant ajouté : ID={id_etudiant}, MDP={mot_de_passe}")
        else:
            print("✗ Échec de l'ajout d'étudiant")
            return False
        
        # Test de vérification d'existence
        print("Test de vérification d'existence...")
        existe_id = db.etudiant_existe(id_etudiant=id_etudiant)
        existe_email = db.etudiant_existe(email="test.etudiant@example.com")
        
        if existe_id and existe_email:
            print("✓ Vérification d'existence réussie")
        else:
            print("✗ Échec de la vérification d'existence")
            return False
        
        # Test de récupération de tous les étudiants
        print("Test de récupération de tous les étudiants...")
        etudiants = db.obtenir_tous_etudiants()
        
        if etudiants and len(etudiants) > 0:
            print(f"✓ Récupération réussie : {len(etudiants)} étudiants trouvés")
        else:
            print("✗ Échec de la récupération des étudiants")
            return False
        
        # Test de réinitialisation de mot de passe
        print("Test de réinitialisation de mot de passe...")
        succes, nouveau_mdp = db.reinitialiser_mot_de_passe(id_etudiant=id_etudiant)
        
        if succes and nouveau_mdp:
            print(f"✓ Réinitialisation réussie : nouveau MDP={nouveau_mdp}")
        else:
            print("✗ Échec de la réinitialisation du mot de passe")
            return False
        
        # Test de prévention des doublons
        print("Test de prévention des doublons...")
        id_doublon, _ = db.ajouter_etudiant(
            nom="TestNom",
            prenom="TestPrenom",
            email="test.etudiant@example.com",  # Même email
            telephone="+33123456789"
        )
        
        if id_doublon is None:
            print("✓ Prévention des doublons fonctionne")
        else:
            print("✗ Échec de la prévention des doublons")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors des tests d'étudiants : {e}")
        return False

def test_attendance_operations():
    """Test les opérations de présence"""
    print("\n=== Test des opérations de présence ===")
    
    try:
        # Préparer les données de test
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        test_name = "Test Personne Présence"
        
        # Test d'ajout de présence
        print("Test d'ajout de présence...")
        succes = db.ajouter_presence(test_name, date_str, time_str)
        
        if succes:
            print(f"✓ Présence ajoutée pour {test_name}")
        else:
            print("✗ Échec de l'ajout de présence")
            return False
        
        # Test de vérification de présence aujourd'hui
        print("Test de vérification de présence aujourd'hui...")
        present = db.est_present_aujourd_hui(test_name, date_str)
        
        if present:
            print(f"✓ Vérification réussie : {test_name} est présent")
        else:
            print("✗ Échec de la vérification de présence")
            return False
        
        # Test de récupération de toutes les présences
        print("Test de récupération de toutes les présences...")
        presences = db.obtenir_toutes_presences()
        
        if presences and len(presences) > 0:
            print(f"✓ Récupération réussie : {len(presences)} présences trouvées")
        else:
            print("✗ Échec de la récupération des présences")
            return False
        
        # Test de récupération par date
        print("Test de récupération par date...")
        presences_date = db.obtenir_presences_par_date(date_str)
        
        if presences_date and len(presences_date) > 0:
            print(f"✓ Récupération par date réussie : {len(presences_date)} présences")
        else:
            print("✗ Échec de la récupération par date")
            return False
        
        # Test de récupération par personne
        print("Test de récupération par personne...")
        presences_personne = db.obtenir_presences_par_personne(test_name)
        
        if presences_personne and len(presences_personne) > 0:
            print(f"✓ Récupération par personne réussie : {len(presences_personne)} présences")
        else:
            print("✗ Échec de la récupération par personne")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors des tests de présence : {e}")
        return False

def test_config_compatibility():
    """Test la compatibilité avec l'interface firebase_config"""
    print("\n=== Test de compatibilité avec firebase_config ===")
    
    try:
        # Test d'initialisation
        print("Test d'initialisation SQLite via config...")
        init_success = config.initialize_firebase()  # Utilise la fonction de compatibilité
        
        if init_success:
            print("✓ Initialisation via config réussie")
        else:
            print("✗ Échec de l'initialisation via config")
            return False
        
        # Test d'ajout de présence via config
        print("Test d'ajout de présence via config...")
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        test_name = "Test Config Personne"
        
        add_success = config.add_attendance(test_name, date_str, time_str)
        
        if add_success:
            print(f"✓ Ajout de présence via config réussi pour {test_name}")
        else:
            print("✗ Échec de l'ajout de présence via config")
            return False
        
        # Test de vérification via config
        print("Test de vérification via config...")
        present = config.is_present_today(test_name, date_str)
        
        if present:
            print(f"✓ Vérification via config réussie : {test_name} est présent")
        else:
            print("✗ Échec de la vérification via config")
            return False
        
        # Test de récupération via config
        print("Test de récupération via config...")
        all_attendance = config.get_all_attendance()
        date_attendance = config.get_attendance_by_date(date_str)
        person_attendance = config.get_attendance_by_person(test_name)
        
        if all_attendance and date_attendance and person_attendance:
            print("✓ Toutes les récupérations via config réussies")
        else:
            print("✗ Échec d'une ou plusieurs récupérations via config")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors des tests de compatibilité : {e}")
        return False

def test_performance():
    """Test basique de performance"""
    print("\n=== Test de performance ===")
    
    try:
        import time
        
        # Test d'ajout en masse
        print("Test d'ajout de 100 étudiants...")
        start_time = time.time()
        
        for i in range(100):
            db.ajouter_etudiant(
                nom=f"TestNom{i}",
                prenom=f"TestPrenom{i}",
                email=f"test{i}@performance.com",
                telephone=f"+3312345{i:04d}"
            )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✓ Ajout de 100 étudiants en {duration:.2f} secondes")
        
        # Test de récupération
        print("Test de récupération de tous les étudiants...")
        start_time = time.time()
        
        etudiants = db.obtenir_tous_etudiants()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✓ Récupération de {len(etudiants)} étudiants en {duration:.4f} secondes")
        
        return True
        
    except Exception as e:
        print(f"✗ Erreur lors des tests de performance : {e}")
        return False

def main():
    """Fonction principale de test"""
    print("=== TESTS COMPLETS DU SYSTÈME SQLITE ===")
    print()
    
    # Supprimer la base de données existante pour un test propre
    if os.path.exists(db.DATABASE_FILE):
        os.remove(db.DATABASE_FILE)
        print(f"Base de données existante supprimée : {db.DATABASE_FILE}")
    
    # Exécuter tous les tests
    tests = [
        ("Initialisation", test_database_initialization),
        ("Opérations étudiants", test_student_operations),
        ("Opérations présences", test_attendance_operations),
        ("Compatibilité config", test_config_compatibility),
        ("Performance", test_performance)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Exécution du test : {test_name}")
        print(f"{'='*50}")
        
        try:
            result = test_func()
            results.append((test_name, result))
            
            if result:
                print(f"\n✓ Test '{test_name}' RÉUSSI")
            else:
                print(f"\n✗ Test '{test_name}' ÉCHOUÉ")
                
        except Exception as e:
            print(f"\n✗ Test '{test_name}' ÉCHOUÉ avec exception : {e}")
            results.append((test_name, False))
    
    # Résumé final
    print(f"\n{'='*50}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*50}")
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ RÉUSSI" if result else "✗ ÉCHOUÉ"
        print(f"{test_name:<25} : {status}")
        if result:
            passed += 1
    
    print(f"\nRésultat global : {passed}/{total} tests réussis")
    
    if passed == total:
        print("🎉 TOUS LES TESTS SONT RÉUSSIS ! Le système SQLite est prêt à être utilisé.")
    else:
        print("⚠️  Certains tests ont échoué. Vérifiez les erreurs ci-dessus.")
    
    # Informations sur la base de données finale
    if os.path.exists(db.DATABASE_FILE):
        file_size = os.path.getsize(db.DATABASE_FILE)
        print(f"\nTaille de la base de données finale : {file_size} bytes")
        print(f"Emplacement : {os.path.abspath(db.DATABASE_FILE)}")

if __name__ == "__main__":
    main()
