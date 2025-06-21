"""
Configuration SQLite pour le système de reconnaissance faciale.
Ce fichier remplace firebase_config.py pour utiliser SQLite au lieu de Firebase.
"""

import sqlite_database as db
from datetime import datetime

def initialize_sqlite():
    """
    Initialise la base de données SQLite
    
    Returns:
        bool: True si l'initialisation réussit, False sinon
    """
    try:
        db.initialize_database()
        print("SQLite initialisé avec succès")
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de SQLite : {e}")
        return False

def normalize_name(name):
    """
    Normalise le nom pour assurer la cohérence
    
    Args:
        name (str): Nom à normaliser
        
    Returns:
        str: Nom normalisé
    """
    # Supprimer les espaces en début et fin, et normaliser la casse
    return name.strip().title()

def add_attendance(name, date, time):
    """
    Ajoute un enregistrement de présence dans SQLite
    
    Args:
        name (str): Nom de la personne
        date (str): Date au format YYYY-MM-DD
        time (str): Heure au format HH:MM:SS
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        # Normaliser le nom pour assurer la cohérence
        normalized_name = normalize_name(name)
        
        # Ajouter l'enregistrement de présence
        success = db.ajouter_presence(normalized_name, date, time)
        
        if success:
            print(f"Enregistrement de présence ajouté dans SQLite pour {name}")
        
        return success
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'enregistrement de présence dans SQLite : {e}")
        return False

def is_present_today(name, date):
    """
    Vérifie si une personne est déjà marquée présente aujourd'hui

    Args:
        name (str): Nom de la personne
        date (str): Date au format YYYY-MM-DD

    Returns:
        bool: True si présent, False sinon
    """
    try:
        # Normaliser le nom pour assurer la cohérence
        normalized_name = normalize_name(name)

        # Vérifier la présence
        return db.est_present_aujourd_hui(normalized_name, date)
    except Exception as e:
        print(f"Erreur lors de la vérification de l'enregistrement de présence dans SQLite : {e}")
        return False

def is_already_present(name, date):
    """
    Alias pour is_present_today pour compatibilité avec le contrôleur de reconnaissance

    Args:
        name (str): Nom de la personne
        date (str): Date au format YYYY-MM-DD

    Returns:
        bool: True si présent, False sinon
    """
    return is_present_today(name, date)

def get_all_attendance():
    """
    Récupère tous les enregistrements de présence
    
    Returns:
        list: Liste des enregistrements de présence
    """
    try:
        return db.obtenir_toutes_presences()
    except Exception as e:
        print(f"Erreur lors de la récupération des enregistrements de présence depuis SQLite : {e}")
        return []

def get_attendance_by_date(date):
    """
    Récupère les enregistrements de présence pour une date spécifique
    
    Args:
        date (str): Date au format YYYY-MM-DD
        
    Returns:
        list: Liste des enregistrements de présence pour la date spécifiée
    """
    try:
        return db.obtenir_presences_par_date(date)
    except Exception as e:
        print(f"Erreur lors de la récupération des enregistrements de présence depuis SQLite : {e}")
        return []

def get_attendance_by_person(name):
    """
    Récupère les enregistrements de présence pour une personne spécifique
    
    Args:
        name (str): Nom de la personne
        
    Returns:
        list: Liste des enregistrements de présence pour la personne spécifiée
    """
    try:
        # Normaliser le nom pour assurer la cohérence
        normalized_name = normalize_name(name)
        
        return db.obtenir_presences_par_personne(normalized_name)
    except Exception as e:
        print(f"Erreur lors de la récupération des enregistrements de présence depuis SQLite : {e}")
        return []

# Fonctions de compatibilité pour maintenir l'interface existante
def initialize_firebase():
    """
    Fonction de compatibilité pour remplacer initialize_firebase()
    
    Returns:
        bool: True si l'initialisation réussit, False sinon
    """
    return initialize_sqlite()

def get_db():
    """
    Fonction de compatibilité pour remplacer get_db()
    Cette fonction n'est pas nécessaire avec SQLite car chaque fonction
    gère sa propre connexion, mais elle est maintenue pour la compatibilité
    
    Returns:
        bool: True si la base de données est disponible
    """
    try:
        # Test simple pour vérifier que la base de données est accessible
        db.get_connection().close()
        return True
    except:
        return False

# Test des fonctions si le script est exécuté directement
if __name__ == "__main__":
    print("Test de la configuration SQLite...")
    
    # Initialiser SQLite
    if initialize_sqlite():
        print("✓ Initialisation SQLite réussie")
        
        # Test d'ajout de présence
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        test_name = "Test Personne"
        
        # Ajouter une présence
        if add_attendance(test_name, date_str, time_str):
            print(f"✓ Ajout de présence réussi pour {test_name}")
            
            # Vérifier si présent aujourd'hui
            if is_present_today(test_name, date_str):
                print(f"✓ Vérification de présence réussie pour {test_name}")
            else:
                print(f"✗ Échec de la vérification de présence pour {test_name}")
            
            # Récupérer toutes les présences
            all_attendance = get_all_attendance()
            print(f"✓ Récupération de {len(all_attendance)} enregistrements de présence")
            
            # Récupérer les présences par date
            date_attendance = get_attendance_by_date(date_str)
            print(f"✓ Récupération de {len(date_attendance)} enregistrements pour {date_str}")
            
            # Récupérer les présences par personne
            person_attendance = get_attendance_by_person(test_name)
            print(f"✓ Récupération de {len(person_attendance)} enregistrements pour {test_name}")
            
        else:
            print(f"✗ Échec de l'ajout de présence pour {test_name}")
    else:
        print("✗ Échec de l'initialisation SQLite")
    
    print("Test terminé.")
