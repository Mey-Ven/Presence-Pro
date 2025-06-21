"""
Script de migration des données de Firebase vers SQLite
Ce script permet de transférer les données existantes de Firebase vers la nouvelle base SQLite
"""

import sqlite_database as sqlite_db
import sys
import os

# Essayer d'importer les modules Firebase
try:
    import create_students_table as firebase_students
    import firebase_config
    FIREBASE_AVAILABLE = True
    print("Modules Firebase détectés")
except ImportError as e:
    FIREBASE_AVAILABLE = False
    print(f"Modules Firebase non disponibles : {e}")
    print("Migration impossible sans les modules Firebase")

def migrate_students():
    """
    Migre les étudiants de Firebase vers SQLite
    
    Returns:
        bool: True si la migration réussit, False sinon
    """
    if not FIREBASE_AVAILABLE:
        print("Firebase non disponible, impossible de migrer les étudiants")
        return False
    
    try:
        print("Migration des étudiants de Firebase vers SQLite...")
        
        # Récupérer tous les étudiants de Firebase
        firebase_students_list = firebase_students.obtenir_tous_etudiants()
        
        if not firebase_students_list:
            print("Aucun étudiant trouvé dans Firebase")
            return True
        
        print(f"Trouvé {len(firebase_students_list)} étudiants dans Firebase")
        
        migrated_count = 0
        skipped_count = 0
        
        for student in firebase_students_list:
            # Extraire les informations de l'étudiant
            id_etudiant = student.get('IdEtudiant')
            nom = student.get('NomEtudiant')
            prenom = student.get('PrenomEtudiant')
            email = student.get('EmailEtudiant')
            telephone = student.get('TelephoneEtudiant')
            
            # Vérifier si l'étudiant existe déjà dans SQLite
            if sqlite_db.etudiant_existe(id_etudiant=id_etudiant, email=email):
                print(f"Étudiant {id_etudiant} ({email}) existe déjà dans SQLite, ignoré")
                skipped_count += 1
                continue
            
            # Ajouter l'étudiant dans SQLite avec un mot de passe temporaire
            # Note: Le mot de passe original ne peut pas être récupéré de Firebase car il est hashé
            success, _ = sqlite_db.ajouter_etudiant(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                mot_de_passe="MotDePasseTemporaire123!",  # Mot de passe temporaire
                id_etudiant=id_etudiant
            )
            
            if success:
                print(f"✓ Étudiant migré : {id_etudiant} - {prenom} {nom}")
                migrated_count += 1
            else:
                print(f"✗ Échec de migration pour : {id_etudiant} - {prenom} {nom}")
        
        print(f"\nMigration des étudiants terminée :")
        print(f"- Migrés : {migrated_count}")
        print(f"- Ignorés (déjà existants) : {skipped_count}")
        print(f"- Total traités : {len(firebase_students_list)}")
        
        if migrated_count > 0:
            print("\nIMPORTANT : Les mots de passe ont été réinitialisés à 'MotDePasseTemporaire123!'")
            print("Vous devrez réinitialiser les mots de passe pour chaque étudiant migré.")
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la migration des étudiants : {e}")
        return False

def migrate_attendance():
    """
    Migre les enregistrements de présence de Firebase vers SQLite
    
    Returns:
        bool: True si la migration réussit, False sinon
    """
    if not FIREBASE_AVAILABLE:
        print("Firebase non disponible, impossible de migrer les présences")
        return False
    
    try:
        print("Migration des présences de Firebase vers SQLite...")
        
        # Initialiser Firebase
        if not firebase_config.initialize_firebase():
            print("Impossible d'initialiser Firebase")
            return False
        
        # Récupérer tous les enregistrements de présence de Firebase
        firebase_attendance_list = firebase_config.get_all_attendance()
        
        if not firebase_attendance_list:
            print("Aucun enregistrement de présence trouvé dans Firebase")
            return True
        
        print(f"Trouvé {len(firebase_attendance_list)} enregistrements de présence dans Firebase")
        
        migrated_count = 0
        skipped_count = 0
        
        for attendance in firebase_attendance_list:
            # Extraire les informations de présence
            name = attendance.get('name')
            date = attendance.get('date')
            time = attendance.get('time')
            
            # Vérifier si cet enregistrement existe déjà dans SQLite
            if sqlite_db.est_present_aujourd_hui(name, date):
                print(f"Présence pour {name} le {date} existe déjà dans SQLite, ignoré")
                skipped_count += 1
                continue
            
            # Ajouter l'enregistrement de présence dans SQLite
            success = sqlite_db.ajouter_presence(name, date, time)
            
            if success:
                print(f"✓ Présence migrée : {name} - {date} {time}")
                migrated_count += 1
            else:
                print(f"✗ Échec de migration pour : {name} - {date} {time}")
        
        print(f"\nMigration des présences terminée :")
        print(f"- Migrées : {migrated_count}")
        print(f"- Ignorées (déjà existantes) : {skipped_count}")
        print(f"- Total traitées : {len(firebase_attendance_list)}")
        
        return True
        
    except Exception as e:
        print(f"Erreur lors de la migration des présences : {e}")
        return False

def main():
    """
    Fonction principale de migration
    """
    print("=== MIGRATION FIREBASE VERS SQLITE ===")
    print()
    
    if not FIREBASE_AVAILABLE:
        print("Les modules Firebase ne sont pas disponibles.")
        print("Assurez-vous que firebase_config.py et create_students_table.py sont présents.")
        sys.exit(1)
    
    # Vérifier si le fichier serviceAccountKey.json existe
    if not os.path.exists("serviceAccountKey.json"):
        print("Le fichier serviceAccountKey.json n'est pas trouvé.")
        print("Ce fichier est nécessaire pour accéder à Firebase.")
        sys.exit(1)
    
    # Initialiser SQLite
    print("Initialisation de SQLite...")
    sqlite_db.initialize_database()
    
    # Demander confirmation
    print("\nCette opération va migrer les données de Firebase vers SQLite.")
    print("Les données existantes dans SQLite ne seront pas supprimées.")
    print("Les doublons seront ignorés.")
    
    confirmation = input("\nVoulez-vous continuer ? (o/n) : ").lower()
    if confirmation != 'o':
        print("Migration annulée.")
        sys.exit(0)
    
    print("\nDébut de la migration...")
    
    # Migrer les étudiants
    students_success = migrate_students()
    print()
    
    # Migrer les présences
    attendance_success = migrate_attendance()
    print()
    
    # Résumé
    if students_success and attendance_success:
        print("✓ Migration terminée avec succès !")
        print("\nVous pouvez maintenant utiliser le système SQLite :")
        print("- python manage_students_sqlite.py  # Pour gérer les étudiants")
        print("- Modifiez face_recognition_attendance_improved.py pour utiliser sqlite_config au lieu de firebase_config")
    else:
        print("✗ La migration a échoué partiellement.")
        print("Vérifiez les erreurs ci-dessus et réessayez si nécessaire.")

if __name__ == "__main__":
    main()
