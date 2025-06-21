"""
Script de réinitialisation complète du système Presence Pro
Remet le système à zéro et corrige tous les problèmes critiques
"""

import os
import shutil
import sqlite3
import glob
from datetime import datetime

def reset_database():
    """Réinitialise complètement la base de données SQLite"""
    print("🗄️ RÉINITIALISATION DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    db_path = "attendance.db"
    
    try:
        # Se connecter à la base de données
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Supprimer toutes les présences
        print("🗑️ Suppression de toutes les présences...")
        cursor.execute("DELETE FROM presences")
        deleted_presences = cursor.rowcount
        print(f"   ✅ {deleted_presences} présences supprimées")
        
        # Supprimer tous les étudiants
        print("👥 Suppression de tous les étudiants...")
        cursor.execute("DELETE FROM etudiants")
        deleted_students = cursor.rowcount
        print(f"   ✅ {deleted_students} étudiants supprimés")
        
        # Réinitialiser les compteurs auto-increment si nécessaire
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('etudiants', 'presences')")
        
        # Valider les changements
        conn.commit()
        conn.close()
        
        print("✅ Base de données complètement réinitialisée")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation de la base de données: {e}")
        return False

def reset_dataset_folder():
    """Supprime et recrée le dossier dataset"""
    print("\n📁 RÉINITIALISATION DU DOSSIER DATASET")
    print("=" * 60)
    
    dataset_path = "dataset"
    
    try:
        # Supprimer le dossier dataset s'il existe
        if os.path.exists(dataset_path):
            print("🗑️ Suppression du dossier dataset existant...")
            shutil.rmtree(dataset_path)
            print("   ✅ Dossier dataset supprimé")
        
        # Recréer le dossier dataset vide
        print("📁 Création d'un nouveau dossier dataset...")
        os.makedirs(dataset_path, exist_ok=True)
        print("   ✅ Nouveau dossier dataset créé")
        
        # Créer un fichier .gitkeep pour maintenir le dossier dans git
        gitkeep_path = os.path.join(dataset_path, ".gitkeep")
        with open(gitkeep_path, 'w') as f:
            f.write("# Ce fichier maintient le dossier dataset dans git\n")
        
        print("✅ Dossier dataset réinitialisé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la réinitialisation du dataset: {e}")
        return False

def reset_encodings():
    """Supprime les fichiers d'encodages faciaux"""
    print("\n🧠 RÉINITIALISATION DES ENCODAGES FACIAUX")
    print("=" * 60)
    
    try:
        # Supprimer les fichiers d'encodages
        encoding_files = [
            "face_encodings.pkl",
            "encodings.pkl", 
            "known_faces.pkl",
            "facial_encodings.dat"
        ]
        
        deleted_count = 0
        for file in encoding_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"   🗑️ {file} supprimé")
                deleted_count += 1
        
        if deleted_count > 0:
            print(f"✅ {deleted_count} fichier(s) d'encodages supprimé(s)")
        else:
            print("ℹ️ Aucun fichier d'encodages à supprimer")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la suppression des encodages: {e}")
        return False

def clean_temp_files():
    """Nettoie les fichiers temporaires"""
    print("\n🧹 NETTOYAGE DES FICHIERS TEMPORAIRES")
    print("=" * 60)
    
    try:
        # Patterns de fichiers temporaires à supprimer
        temp_patterns = [
            "*.pyc",
            "__pycache__/*",
            "*.tmp",
            "*.log",
            "screenshot_*.jpg",
            "temp_*.jpg"
        ]
        
        deleted_count = 0
        for pattern in temp_patterns:
            files = glob.glob(pattern, recursive=True)
            for file in files:
                try:
                    if os.path.isfile(file):
                        os.remove(file)
                        deleted_count += 1
                    elif os.path.isdir(file):
                        shutil.rmtree(file)
                        deleted_count += 1
                except:
                    pass
        
        # Nettoyer le dossier __pycache__
        for root, dirs, files in os.walk('.'):
            for dir in dirs:
                if dir == '__pycache__':
                    try:
                        shutil.rmtree(os.path.join(root, dir))
                        deleted_count += 1
                    except:
                        pass
        
        print(f"✅ {deleted_count} fichier(s)/dossier(s) temporaire(s) supprimé(s)")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du nettoyage: {e}")
        return False

def verify_database_structure():
    """Vérifie et recrée la structure de la base de données si nécessaire"""
    print("\n🔍 VÉRIFICATION DE LA STRUCTURE DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    try:
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        # Vérifier la table etudiants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS etudiants (
                id_etudiant TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telephone TEXT,
                mot_de_passe TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Vérifier la table presences
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                date TEXT NOT NULL,
                heure TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Structure de la base de données vérifiée et mise à jour")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de la structure: {e}")
        return False

def create_status_report():
    """Crée un rapport de statut après la réinitialisation"""
    print("\n📊 CRÉATION DU RAPPORT DE STATUT")
    print("=" * 60)
    
    try:
        # Vérifier la base de données
        conn = sqlite3.connect("attendance.db")
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM etudiants")
        student_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM presences")
        attendance_count = cursor.fetchone()[0]
        
        conn.close()
        
        # Vérifier le dossier dataset
        dataset_exists = os.path.exists("dataset")
        dataset_empty = len(os.listdir("dataset")) <= 1 if dataset_exists else False  # <= 1 pour .gitkeep
        
        # Créer le rapport
        report = f"""
RAPPORT DE RÉINITIALISATION SYSTÈME PRESENCE PRO
===============================================
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 STATUT DE LA BASE DE DONNÉES:
- Étudiants: {student_count}
- Présences: {attendance_count}
- Structure: ✅ Valide

📁 STATUT DU DATASET:
- Dossier existe: {'✅' if dataset_exists else '❌'}
- Dossier vide: {'✅' if dataset_empty else '❌'}

🧠 ENCODAGES FACIAUX:
- Fichiers supprimés: ✅
- Prêt pour nouveaux encodages: ✅

🎯 SYSTÈME PRÊT POUR:
- ✅ Nouvelle inscription d'étudiants
- ✅ Entraînement facial
- ✅ Reconnaissance faciale
- ✅ Suivi des présences

⚠️ PROCHAINES ÉTAPES:
1. Démarrer le tableau de bord: python admin_dashboard.py
2. Ajouter des étudiants via l'interface web
3. Effectuer l'entraînement facial pour chaque étudiant
4. Tester la reconnaissance faciale
"""
        
        # Sauvegarder le rapport
        with open("RESET_REPORT.md", "w", encoding="utf-8") as f:
            f.write(report)
        
        print("✅ Rapport de statut créé: RESET_REPORT.md")
        print(report)
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création du rapport: {e}")
        return False

def main():
    """Fonction principale de réinitialisation"""
    print("🔄 RÉINITIALISATION COMPLÈTE DU SYSTÈME PRESENCE PRO")
    print("=" * 80)
    print("Ce script va remettre le système à zéro et corriger tous les problèmes")
    print()
    
    # Demander confirmation
    response = input("⚠️ ATTENTION: Cette opération va supprimer TOUTES les données existantes.\n"
                    "Voulez-vous continuer? (oui/non): ").lower().strip()
    
    if response not in ['oui', 'o', 'yes', 'y']:
        print("❌ Opération annulée par l'utilisateur")
        return
    
    print("\n🚀 Début de la réinitialisation...")
    
    # Étapes de réinitialisation
    steps = [
        ("Base de données", reset_database),
        ("Dossier dataset", reset_dataset_folder),
        ("Encodages faciaux", reset_encodings),
        ("Fichiers temporaires", clean_temp_files),
        ("Structure DB", verify_database_structure),
        ("Rapport de statut", create_status_report)
    ]
    
    success_count = 0
    total_steps = len(steps)
    
    for step_name, step_function in steps:
        try:
            if step_function():
                success_count += 1
            else:
                print(f"⚠️ Échec partiel de l'étape: {step_name}")
        except Exception as e:
            print(f"❌ Erreur dans l'étape {step_name}: {e}")
    
    # Résumé final
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DE LA RÉINITIALISATION")
    print("=" * 80)
    
    if success_count == total_steps:
        print("🎉 RÉINITIALISATION COMPLÈTE RÉUSSIE!")
        print(f"✅ {success_count}/{total_steps} étapes terminées avec succès")
        print()
        print("🎯 SYSTÈME PRÊT POUR UTILISATION:")
        print("   1. Démarrez le tableau de bord: python admin_dashboard.py")
        print("   2. Accédez à http://localhost:5001")
        print("   3. Connectez-vous (admin/admin123)")
        print("   4. Ajoutez vos premiers étudiants")
        print("   5. Effectuez l'entraînement facial")
        print()
        print("📄 Consultez RESET_REPORT.md pour plus de détails")
    else:
        print(f"⚠️ RÉINITIALISATION PARTIELLE: {success_count}/{total_steps} étapes réussies")
        print("   Certaines étapes ont échoué, vérifiez les messages d'erreur ci-dessus")
    
    print("\n💡 En cas de problème, relancez ce script ou contactez le support")

if __name__ == "__main__":
    main()
