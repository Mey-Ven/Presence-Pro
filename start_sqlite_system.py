#!/usr/bin/env python3
"""
Script de démarrage rapide pour le système SQLite
Ce script fournit un menu principal pour accéder à toutes les fonctionnalités
"""

import os
import sys
import subprocess
from datetime import datetime

def print_banner():
    """Affiche la bannière du système"""
    print("=" * 60)
    print("🎯 SYSTÈME DE RECONNAISSANCE FACIALE - SQLite")
    print("=" * 60)
    print("Version SQLite - Plus rapide, plus simple, plus fiable")
    print(f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

def check_database():
    """Vérifie l'état de la base de données"""
    db_file = "attendance.db"
    if os.path.exists(db_file):
        size = os.path.getsize(db_file)
        print(f"📊 Base de données : {db_file} ({size} bytes)")
        return True
    else:
        print("⚠️  Base de données non trouvée - sera créée automatiquement")
        return False

def run_script(script_name, args=None):
    """Exécute un script Python"""
    try:
        cmd = [sys.executable, script_name]
        if args:
            cmd.extend(args)
        
        print(f"\n🚀 Lancement de {script_name}...")
        print("-" * 40)
        
        # Exécuter le script
        result = subprocess.run(cmd, check=False)
        
        print("-" * 40)
        if result.returncode == 0:
            print(f"✅ {script_name} terminé avec succès")
        else:
            print(f"⚠️  {script_name} terminé avec le code {result.returncode}")
        
        input("\nAppuyez sur Entrée pour continuer...")
        
    except FileNotFoundError:
        print(f"❌ Erreur : {script_name} non trouvé")
        input("Appuyez sur Entrée pour continuer...")
    except KeyboardInterrupt:
        print(f"\n⏹️  {script_name} interrompu par l'utilisateur")
        input("Appuyez sur Entrée pour continuer...")

def show_system_info():
    """Affiche les informations système"""
    print("\n📋 INFORMATIONS SYSTÈME")
    print("=" * 40)
    
    # Vérifier les fichiers principaux
    files_to_check = [
        ("sqlite_database.py", "Module principal SQLite"),
        ("sqlite_config.py", "Configuration SQLite"),
        ("manage_students_sqlite.py", "Gestion des étudiants"),
        ("view_attendance_sqlite.py", "Visualiseur de présences"),
        ("manual_add_sqlite.py", "Ajout manuel"),
        ("attendance.db", "Base de données")
    ]
    
    print("Fichiers du système :")
    for filename, description in files_to_check:
        if os.path.exists(filename):
            size = os.path.getsize(filename)
            print(f"  ✅ {filename:<25} - {description} ({size} bytes)")
        else:
            print(f"  ❌ {filename:<25} - {description} (MANQUANT)")
    
    # Informations sur la base de données
    if os.path.exists("attendance.db"):
        print(f"\n📊 Base de données :")
        print(f"  Fichier : attendance.db")
        print(f"  Taille : {os.path.getsize('attendance.db')} bytes")
        print(f"  Emplacement : {os.path.abspath('attendance.db')}")
    
    input("\nAppuyez sur Entrée pour continuer...")

def main_menu():
    """Menu principal"""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')  # Effacer l'écran
        
        print_banner()
        check_database()
        
        print("\n🎛️  MENU PRINCIPAL")
        print("=" * 30)
        print("1. 👥 Gestion des étudiants")
        print("2. 📊 Visualiser les présences")
        print("3. ➕ Ajouter des présences manuellement")
        print("4. 🔧 Tests et diagnostics")
        print("5. 📈 Benchmark de performance")
        print("6. 🔄 Migration depuis Firebase")
        print("7. ℹ️  Informations système")
        print("8. 📚 Documentation")
        print("9. ❌ Quitter")
        
        choice = input("\n👉 Choisissez une option (1-9) : ").strip()
        
        if choice == "1":
            # Gestion des étudiants
            run_script("manage_students_sqlite.py")
        
        elif choice == "2":
            # Visualisation des présences
            print("\n📊 OPTIONS DE VISUALISATION")
            print("1. Toutes les présences")
            print("2. Présences d'aujourd'hui")
            print("3. Présences par date")
            print("4. Présences par personne")
            print("5. Statistiques seulement")
            
            sub_choice = input("Choisissez (1-5) : ").strip()
            
            if sub_choice == "1":
                run_script("view_attendance_sqlite.py")
            elif sub_choice == "2":
                run_script("view_attendance_sqlite.py", ["today"])
            elif sub_choice == "3":
                date = input("Entrez la date (YYYY-MM-DD) : ").strip()
                if date:
                    run_script("view_attendance_sqlite.py", ["date", date])
            elif sub_choice == "4":
                person = input("Entrez le nom de la personne : ").strip()
                if person:
                    run_script("view_attendance_sqlite.py", ["person", person])
            elif sub_choice == "5":
                run_script("view_attendance_sqlite.py", ["stats"])
        
        elif choice == "3":
            # Ajout manuel de présences
            run_script("manual_add_sqlite.py")
        
        elif choice == "4":
            # Tests et diagnostics
            print("\n🔧 TESTS ET DIAGNOSTICS")
            print("1. Tests complets du système")
            print("2. Test de la base de données")
            print("3. Test de la configuration")
            
            sub_choice = input("Choisissez (1-3) : ").strip()
            
            if sub_choice == "1":
                run_script("test_sqlite_system.py")
            elif sub_choice == "2":
                run_script("sqlite_database.py")
            elif sub_choice == "3":
                run_script("sqlite_config.py")
        
        elif choice == "5":
            # Benchmark
            run_script("benchmark_sqlite_vs_firebase.py")
        
        elif choice == "6":
            # Migration
            print("\n⚠️  ATTENTION : Cette opération va migrer les données depuis Firebase")
            confirm = input("Voulez-vous continuer ? (o/n) : ").lower()
            if confirm == 'o':
                run_script("migrate_firebase_to_sqlite.py")
        
        elif choice == "7":
            # Informations système
            show_system_info()
        
        elif choice == "8":
            # Documentation
            print("\n📚 DOCUMENTATION DISPONIBLE")
            print("=" * 35)
            
            docs = [
                ("README_SQLite.md", "Documentation complète SQLite"),
                ("GUIDE_MIGRATION_COMPLETE.md", "Guide de migration"),
                ("README.md", "Documentation originale du projet")
            ]
            
            for filename, description in docs:
                if os.path.exists(filename):
                    print(f"✅ {filename} - {description}")
                else:
                    print(f"❌ {filename} - {description} (MANQUANT)")
            
            print("\nPour lire la documentation :")
            print("- Ouvrez les fichiers .md avec un éditeur de texte")
            print("- Ou utilisez un visualiseur Markdown")
            
            input("\nAppuyez sur Entrée pour continuer...")
        
        elif choice == "9":
            # Quitter
            print("\n👋 Au revoir !")
            print("Merci d'avoir utilisé le système SQLite de reconnaissance faciale")
            sys.exit(0)
        
        else:
            print("\n❌ Option invalide. Veuillez choisir entre 1 et 9.")
            input("Appuyez sur Entrée pour continuer...")

def check_requirements():
    """Vérifie que les fichiers requis sont présents"""
    required_files = [
        "sqlite_database.py",
        "sqlite_config.py",
        "manage_students_sqlite.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print("❌ ERREUR : Fichiers manquants")
        print("Les fichiers suivants sont requis :")
        for file in missing_files:
            print(f"  - {file}")
        print("\nAssurez-vous que tous les fichiers SQLite sont présents.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        # Vérifier les prérequis
        check_requirements()
        
        # Lancer le menu principal
        main_menu()
        
    except KeyboardInterrupt:
        print("\n\n👋 Programme interrompu par l'utilisateur. Au revoir !")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur inattendue : {e}")
        print("Veuillez vérifier votre installation et réessayer.")
        sys.exit(1)
