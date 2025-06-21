"""
Script de comparaison des performances entre SQLite et Firebase
Ce script teste les performances des deux systèmes côte à côte
"""

import time
import sqlite_database as sqlite_db
import sqlite_config as sqlite_config
import os
from datetime import datetime

# Essayer d'importer Firebase
try:
    import firebase_config
    import create_students_table as firebase_students
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Firebase non disponible pour les tests de comparaison")

def benchmark_sqlite():
    """Teste les performances de SQLite"""
    print("=== BENCHMARK SQLite ===")
    
    # Supprimer la base de données existante pour un test propre
    if os.path.exists(sqlite_db.DATABASE_FILE):
        os.remove(sqlite_db.DATABASE_FILE)
    
    results = {}
    
    # Test d'initialisation
    start_time = time.time()
    sqlite_db.initialize_database()
    results['init_time'] = time.time() - start_time
    
    # Test d'ajout d'étudiants
    print("Test d'ajout de 50 étudiants...")
    start_time = time.time()
    
    for i in range(50):
        sqlite_db.ajouter_etudiant(
            nom=f"TestNom{i}",
            prenom=f"TestPrenom{i}",
            email=f"test{i}@benchmark.com",
            telephone=f"+3312345{i:04d}"
        )
    
    results['add_students_time'] = time.time() - start_time
    
    # Test de récupération d'étudiants
    print("Test de récupération de tous les étudiants...")
    start_time = time.time()
    
    for _ in range(10):  # Répéter 10 fois pour avoir une moyenne
        etudiants = sqlite_db.obtenir_tous_etudiants()
    
    results['get_students_time'] = (time.time() - start_time) / 10
    results['students_count'] = len(etudiants)
    
    # Test d'ajout de présences
    print("Test d'ajout de 100 présences...")
    start_time = time.time()
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    for i in range(100):
        time_str = f"{10 + (i % 14):02d}:{(i % 60):02d}:{(i % 60):02d}"
        sqlite_db.ajouter_presence(f"TestPersonne{i % 20}", date_str, time_str)
    
    results['add_attendance_time'] = time.time() - start_time
    
    # Test de récupération de présences
    print("Test de récupération de toutes les présences...")
    start_time = time.time()
    
    for _ in range(10):  # Répéter 10 fois pour avoir une moyenne
        presences = sqlite_db.obtenir_toutes_presences()
    
    results['get_attendance_time'] = (time.time() - start_time) / 10
    results['attendance_count'] = len(presences)
    
    # Test de vérification de présence
    print("Test de vérification de présence...")
    start_time = time.time()
    
    for i in range(50):
        sqlite_db.est_present_aujourd_hui(f"TestPersonne{i % 20}", date_str)
    
    results['check_presence_time'] = time.time() - start_time
    
    return results

def benchmark_firebase():
    """Teste les performances de Firebase (si disponible)"""
    if not FIREBASE_AVAILABLE:
        return None
    
    print("=== BENCHMARK Firebase ===")
    
    results = {}
    
    # Test d'initialisation
    start_time = time.time()
    firebase_initialized = firebase_config.initialize_firebase()
    results['init_time'] = time.time() - start_time
    
    if not firebase_initialized:
        print("Impossible d'initialiser Firebase")
        return None
    
    # Test d'ajout d'étudiants
    print("Test d'ajout de 10 étudiants (réduit pour Firebase)...")
    start_time = time.time()
    added_count = 0
    
    for i in range(10):
        try:
            id_etudiant, _ = firebase_students.ajouter_etudiant(
                nom=f"TestNomFB{i}",
                prenom=f"TestPrenomFB{i}",
                email=f"testfb{i}@benchmark.com",
                telephone=f"+3312345{i:04d}"
            )
            if id_etudiant:
                added_count += 1
        except Exception as e:
            print(f"Erreur lors de l'ajout d'étudiant Firebase : {e}")
            break
    
    results['add_students_time'] = time.time() - start_time
    results['students_added'] = added_count
    
    # Test de récupération d'étudiants
    print("Test de récupération de tous les étudiants...")
    start_time = time.time()
    
    try:
        etudiants = firebase_students.obtenir_tous_etudiants()
        results['get_students_time'] = time.time() - start_time
        results['students_count'] = len(etudiants) if etudiants else 0
    except Exception as e:
        print(f"Erreur lors de la récupération d'étudiants Firebase : {e}")
        results['get_students_time'] = -1
        results['students_count'] = 0
    
    # Test d'ajout de présences
    print("Test d'ajout de 20 présences (réduit pour Firebase)...")
    start_time = time.time()
    added_attendance = 0
    
    now = datetime.now()
    date_str = now.strftime("%Y-%m-%d")
    
    for i in range(20):
        try:
            time_str = f"{10 + (i % 14):02d}:{(i % 60):02d}:{(i % 60):02d}"
            success = firebase_config.add_attendance(f"TestPersonneFB{i % 5}", date_str, time_str)
            if success:
                added_attendance += 1
        except Exception as e:
            print(f"Erreur lors de l'ajout de présence Firebase : {e}")
            break
    
    results['add_attendance_time'] = time.time() - start_time
    results['attendance_added'] = added_attendance
    
    # Test de récupération de présences
    print("Test de récupération de toutes les présences...")
    start_time = time.time()
    
    try:
        presences = firebase_config.get_all_attendance()
        results['get_attendance_time'] = time.time() - start_time
        results['attendance_count'] = len(presences) if presences else 0
    except Exception as e:
        print(f"Erreur lors de la récupération de présences Firebase : {e}")
        results['get_attendance_time'] = -1
        results['attendance_count'] = 0
    
    # Test de vérification de présence
    print("Test de vérification de présence...")
    start_time = time.time()
    
    try:
        for i in range(10):
            firebase_config.is_present_today(f"TestPersonneFB{i % 5}", date_str)
        results['check_presence_time'] = time.time() - start_time
    except Exception as e:
        print(f"Erreur lors de la vérification de présence Firebase : {e}")
        results['check_presence_time'] = -1
    
    return results

def compare_results(sqlite_results, firebase_results):
    """Compare les résultats des deux systèmes"""
    print("\n" + "="*60)
    print("COMPARAISON DES PERFORMANCES")
    print("="*60)
    
    if firebase_results is None:
        print("Firebase non disponible pour la comparaison")
        print("\nRésultats SQLite uniquement :")
        print_results("SQLite", sqlite_results)
        return
    
    # Tableau de comparaison
    print(f"{'Opération':<30} {'SQLite':<15} {'Firebase':<15} {'Ratio':<10}")
    print("-" * 70)
    
    operations = [
        ('Initialisation (s)', 'init_time'),
        ('Ajout étudiants (s)', 'add_students_time'),
        ('Récup. étudiants (s)', 'get_students_time'),
        ('Ajout présences (s)', 'add_attendance_time'),
        ('Récup. présences (s)', 'get_attendance_time'),
        ('Vérif. présence (s)', 'check_presence_time')
    ]
    
    for op_name, key in operations:
        sqlite_val = sqlite_results.get(key, -1)
        firebase_val = firebase_results.get(key, -1)
        
        if sqlite_val > 0 and firebase_val > 0:
            ratio = firebase_val / sqlite_val
            ratio_str = f"{ratio:.1f}x"
        else:
            ratio_str = "N/A"
        
        sqlite_str = f"{sqlite_val:.4f}" if sqlite_val > 0 else "Erreur"
        firebase_str = f"{firebase_val:.4f}" if firebase_val > 0 else "Erreur"
        
        print(f"{op_name:<30} {sqlite_str:<15} {firebase_str:<15} {ratio_str:<10}")
    
    print("\nNombre d'enregistrements :")
    print(f"{'Type':<30} {'SQLite':<15} {'Firebase':<15}")
    print("-" * 60)
    print(f"{'Étudiants':<30} {sqlite_results.get('students_count', 0):<15} {firebase_results.get('students_count', 0):<15}")
    print(f"{'Présences':<30} {sqlite_results.get('attendance_count', 0):<15} {firebase_results.get('attendance_count', 0):<15}")
    
    # Analyse
    print("\n" + "="*60)
    print("ANALYSE")
    print("="*60)
    
    if firebase_results.get('init_time', -1) > 0 and sqlite_results.get('init_time', -1) > 0:
        init_ratio = firebase_results['init_time'] / sqlite_results['init_time']
        print(f"• SQLite est {init_ratio:.1f}x plus rapide à initialiser")
    
    if firebase_results.get('add_students_time', -1) > 0 and sqlite_results.get('add_students_time', -1) > 0:
        add_ratio = firebase_results['add_students_time'] / sqlite_results['add_students_time']
        print(f"• SQLite est {add_ratio:.1f}x plus rapide pour ajouter des étudiants")
    
    if firebase_results.get('get_students_time', -1) > 0 and sqlite_results.get('get_students_time', -1) > 0:
        get_ratio = firebase_results['get_students_time'] / sqlite_results['get_students_time']
        print(f"• SQLite est {get_ratio:.1f}x plus rapide pour récupérer des étudiants")
    
    # Taille de la base de données
    if os.path.exists(sqlite_db.DATABASE_FILE):
        db_size = os.path.getsize(sqlite_db.DATABASE_FILE)
        print(f"• Taille de la base SQLite : {db_size} bytes ({db_size/1024:.1f} KB)")

def print_results(system_name, results):
    """Affiche les résultats pour un système"""
    print(f"\n{system_name} - Résultats détaillés :")
    print("-" * 40)
    for key, value in results.items():
        if isinstance(value, float):
            print(f"{key}: {value:.4f}s")
        else:
            print(f"{key}: {value}")

def main():
    """Fonction principale"""
    print("=== BENCHMARK SQLite vs Firebase ===")
    print("Ce script compare les performances des deux systèmes")
    print()
    
    # Benchmark SQLite
    sqlite_results = benchmark_sqlite()
    print_results("SQLite", sqlite_results)
    
    print("\n" + "="*50)
    
    # Benchmark Firebase
    firebase_results = None
    if FIREBASE_AVAILABLE:
        try:
            firebase_results = benchmark_firebase()
            if firebase_results:
                print_results("Firebase", firebase_results)
        except Exception as e:
            print(f"Erreur lors du benchmark Firebase : {e}")
    
    # Comparaison
    compare_results(sqlite_results, firebase_results)
    
    print("\nNOTE : Les tests Firebase sont réduits en nombre pour éviter")
    print("les limitations de quota et les erreurs de réseau.")

if __name__ == "__main__":
    main()
