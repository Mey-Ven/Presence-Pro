import sqlite3
import hashlib
import uuid
import random
import string
from datetime import datetime
import os

# Nom du fichier de base de données
DATABASE_FILE = "attendance.db"

def get_connection():
    """
    Obtient une connexion à la base de données SQLite
    
    Returns:
        sqlite3.Connection: Connexion à la base de données
    """
    return sqlite3.connect(DATABASE_FILE)

def initialize_database():
    """
    Initialise la base de données SQLite avec les tables nécessaires
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Table des étudiants
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS etudiants (
                id_etudiant TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                telephone TEXT,
                mot_de_passe_hash TEXT NOT NULL,
                date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table des présences
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nom TEXT NOT NULL,
                date TEXT NOT NULL,
                heure TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print(f"Base de données SQLite initialisée : {DATABASE_FILE}")
        
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données : {e}")
        conn.rollback()
    finally:
        conn.close()

def generer_id_etudiant():
    """
    Génère un ID étudiant unique au format E-XXXX
    
    Returns:
        str: ID étudiant unique
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Récupérer le dernier ID utilisé
        cursor.execute('''
            SELECT id_etudiant FROM etudiants 
            ORDER BY id_etudiant DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        
        # Déterminer le prochain ID
        if result is None:
            # Aucun étudiant dans la base, commencer à E-0001
            prochain_numero = 1
        else:
            # Extraire le numéro du dernier ID
            dernier_id = result[0]
            try:
                # Si le format est E-XXXX
                if '-' in dernier_id:
                    prochain_numero = int(dernier_id.split('-')[1]) + 1
                else:
                    # Fallback si le format est différent
                    prochain_numero = 1
            except:
                # En cas d'erreur, générer un ID aléatoire
                return f"E-{uuid.uuid4().hex[:4].upper()}"
        
        # Formater l'ID avec des zéros devant (E-0001, E-0002, etc.)
        return f"E-{prochain_numero:04d}"
        
    except Exception as e:
        print(f"Erreur lors de la génération de l'ID étudiant : {e}")
        return f"E-{uuid.uuid4().hex[:4].upper()}"
    finally:
        conn.close()

def generer_mot_de_passe(longueur=10):
    """
    Génère un mot de passe aléatoire sécurisé
    
    Args:
        longueur (int): Longueur du mot de passe (par défaut 10)
        
    Returns:
        str: Mot de passe généré
    """
    # Caractères pour le mot de passe
    lettres = string.ascii_letters  # a-z, A-Z
    chiffres = string.digits  # 0-9
    symboles = "!@#$%^&*()-_=+"
    
    # S'assurer que le mot de passe contient au moins un caractère de chaque type
    mot_de_passe = [
        random.choice(lettres.upper()),  # Au moins une majuscule
        random.choice(lettres.lower()),  # Au moins une minuscule
        random.choice(chiffres),         # Au moins un chiffre
        random.choice(symboles)          # Au moins un symbole
    ]
    
    # Compléter avec des caractères aléatoires
    caracteres = lettres + chiffres + symboles
    for _ in range(longueur - 4):
        mot_de_passe.append(random.choice(caracteres))
    
    # Mélanger le mot de passe
    random.shuffle(mot_de_passe)
    
    # Convertir la liste en chaîne
    return ''.join(mot_de_passe)

def ajouter_etudiant(nom, prenom, email, telephone, mot_de_passe=None, id_etudiant=None):
    """
    Ajoute un nouvel étudiant dans la base de données SQLite
    
    Args:
        nom (str): Nom de l'étudiant
        prenom (str): Prénom de l'étudiant
        email (str): Email de l'étudiant
        telephone (str): Numéro de téléphone de l'étudiant
        mot_de_passe (str, optional): Mot de passe de l'étudiant. Si None, un mot de passe sera généré
        id_etudiant (str, optional): ID étudiant. Si None, un ID sera généré automatiquement
    
    Returns:
        tuple: (ID de l'étudiant ajouté, mot de passe généré si applicable)
    """
    # Vérifier si l'email existe déjà
    if etudiant_existe(email=email):
        print(f"Un étudiant avec l'email {email} existe déjà!")
        return None, None
    
    # Générer un ID si non fourni
    if id_etudiant is None:
        id_etudiant = generer_id_etudiant()
    
    # Générer un mot de passe si non fourni
    mot_de_passe_genere = False
    if mot_de_passe is None:
        mot_de_passe = generer_mot_de_passe()
        mot_de_passe_genere = True
    
    # Hasher le mot de passe pour la sécurité
    mot_de_passe_hash = hashlib.sha256(mot_de_passe.encode()).hexdigest()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Insérer l'étudiant dans la base de données
        cursor.execute('''
            INSERT INTO etudiants (id_etudiant, nom, prenom, email, telephone, mot_de_passe_hash)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (id_etudiant, nom, prenom, email, telephone, mot_de_passe_hash))
        
        conn.commit()
        
        if mot_de_passe_genere:
            print(f"Étudiant {prenom} {nom} ajouté avec succès! ID: {id_etudiant}, Mot de passe: {mot_de_passe}")
            return id_etudiant, mot_de_passe
        else:
            print(f"Étudiant {prenom} {nom} ajouté avec succès! ID: {id_etudiant}")
            return id_etudiant, None
            
    except Exception as e:
        print(f"Erreur lors de l'ajout de l'étudiant : {e}")
        conn.rollback()
        return None, None
    finally:
        conn.close()

def etudiant_existe(id_etudiant=None, email=None):
    """
    Vérifie si un étudiant existe déjà par ID ou email
    
    Args:
        id_etudiant (str, optional): ID de l'étudiant à vérifier
        email (str, optional): Email de l'étudiant à vérifier
        
    Returns:
        bool: True si l'étudiant existe, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if id_etudiant:
            cursor.execute('SELECT 1 FROM etudiants WHERE id_etudiant = ?', (id_etudiant,))
            result = cursor.fetchone()
            if result:
                return True
                
        if email:
            cursor.execute('SELECT 1 FROM etudiants WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result:
                return True
                
        return False
        
    except Exception as e:
        print(f"Erreur lors de la vérification de l'existence de l'étudiant : {e}")
        return False
    finally:
        conn.close()

def obtenir_tous_etudiants():
    """
    Récupère tous les étudiants de la base de données SQLite

    Returns:
        list: Liste de dictionnaires contenant les informations des étudiants
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id_etudiant, nom, prenom, email, telephone, date_creation
            FROM etudiants
            ORDER BY id_etudiant
        ''')

        results = cursor.fetchall()

        # Convertir les résultats en liste de dictionnaires
        etudiants = []
        for row in results:
            etudiant = {
                'IdEtudiant': row[0],
                'NomEtudiant': row[1],
                'PrenomEtudiant': row[2],
                'EmailEtudiant': row[3],
                'TelephoneEtudiant': row[4],
                'DateCreation': row[5]
            }
            etudiants.append(etudiant)

        return etudiants

    except Exception as e:
        print(f"Erreur lors de la récupération des étudiants : {e}")
        return []
    finally:
        conn.close()

def reinitialiser_mot_de_passe(id_etudiant=None, email=None):
    """
    Réinitialise le mot de passe d'un étudiant

    Args:
        id_etudiant (str, optional): ID de l'étudiant
        email (str, optional): Email de l'étudiant

    Returns:
        tuple: (bool, str) - (Succès, Nouveau mot de passe)
    """
    # Vérifier si l'étudiant existe
    if not etudiant_existe(id_etudiant=id_etudiant, email=email):
        print("Étudiant non trouvé.")
        return False, None

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Trouver l'ID de l'étudiant si on a fourni l'email
        if email and not id_etudiant:
            cursor.execute('SELECT id_etudiant FROM etudiants WHERE email = ?', (email,))
            result = cursor.fetchone()
            if result:
                id_etudiant = result[0]
            else:
                print(f"Aucun étudiant trouvé avec l'email {email}")
                return False, None

        # Générer un nouveau mot de passe
        nouveau_mot_de_passe = generer_mot_de_passe()

        # Hasher le nouveau mot de passe
        mot_de_passe_hash = hashlib.sha256(nouveau_mot_de_passe.encode()).hexdigest()

        # Mettre à jour le mot de passe dans la base de données
        cursor.execute('''
            UPDATE etudiants
            SET mot_de_passe_hash = ?
            WHERE id_etudiant = ?
        ''', (mot_de_passe_hash, id_etudiant))

        conn.commit()

        print(f"Mot de passe réinitialisé avec succès pour l'étudiant avec ID: {id_etudiant}")
        return True, nouveau_mot_de_passe

    except Exception as e:
        print(f"Erreur lors de la réinitialisation du mot de passe : {e}")
        conn.rollback()
        return False, None
    finally:
        conn.close()

# Fonctions pour la gestion des présences

def ajouter_presence(nom, date, heure):
    """
    Ajoute un enregistrement de présence dans la base de données

    Args:
        nom (str): Nom de la personne
        date (str): Date au format YYYY-MM-DD
        heure (str): Heure au format HH:MM:SS

    Returns:
        bool: True si succès, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO presences (nom, date, heure)
            VALUES (?, ?, ?)
        ''', (nom, date, heure))

        conn.commit()
        print(f"Présence enregistrée pour {nom} le {date} à {heure}")
        return True

    except Exception as e:
        print(f"Erreur lors de l'enregistrement de la présence : {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def est_present_aujourd_hui(nom, date):
    """
    Vérifie si une personne est déjà marquée présente aujourd'hui

    Args:
        nom (str): Nom de la personne
        date (str): Date au format YYYY-MM-DD

    Returns:
        bool: True si présent, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT 1 FROM presences
            WHERE nom = ? AND date = ?
            LIMIT 1
        ''', (nom, date))

        result = cursor.fetchone()
        return result is not None

    except Exception as e:
        print(f"Erreur lors de la vérification de la présence : {e}")
        return False
    finally:
        conn.close()

def obtenir_toutes_presences():
    """
    Récupère tous les enregistrements de présence

    Returns:
        list: Liste de dictionnaires contenant les enregistrements de présence
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT nom, date, heure, timestamp
            FROM presences
            ORDER BY timestamp DESC
        ''')

        results = cursor.fetchall()

        # Convertir les résultats en liste de dictionnaires
        presences = []
        for row in results:
            presence = {
                'name': row[0],
                'date': row[1],
                'time': row[2],
                'timestamp': row[3]
            }
            presences.append(presence)

        return presences

    except Exception as e:
        print(f"Erreur lors de la récupération des présences : {e}")
        return []
    finally:
        conn.close()

def obtenir_presences_par_date(date):
    """
    Récupère les enregistrements de présence pour une date spécifique

    Args:
        date (str): Date au format YYYY-MM-DD

    Returns:
        list: Liste de dictionnaires contenant les enregistrements de présence
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT nom, date, heure, timestamp
            FROM presences
            WHERE date = ?
            ORDER BY heure
        ''', (date,))

        results = cursor.fetchall()

        # Convertir les résultats en liste de dictionnaires
        presences = []
        for row in results:
            presence = {
                'name': row[0],
                'date': row[1],
                'time': row[2],
                'timestamp': row[3]
            }
            presences.append(presence)

        return presences

    except Exception as e:
        print(f"Erreur lors de la récupération des présences par date : {e}")
        return []
    finally:
        conn.close()

def obtenir_presences_par_personne(nom):
    """
    Récupère les enregistrements de présence pour une personne spécifique

    Args:
        nom (str): Nom de la personne

    Returns:
        list: Liste de dictionnaires contenant les enregistrements de présence
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT nom, date, heure, timestamp
            FROM presences
            WHERE nom = ?
            ORDER BY timestamp DESC
        ''', (nom,))

        results = cursor.fetchall()

        # Convertir les résultats en liste de dictionnaires
        presences = []
        for row in results:
            presence = {
                'name': row[0],
                'date': row[1],
                'time': row[2],
                'timestamp': row[3]
            }
            presences.append(presence)

        return presences

    except Exception as e:
        print(f"Erreur lors de la récupération des présences par personne : {e}")
        return []
    finally:
        conn.close()

def obtenir_etudiant_par_id(id_etudiant):
    """
    Récupère un étudiant par son ID

    Args:
        id_etudiant (str): ID de l'étudiant

    Returns:
        dict ou None: Informations de l'étudiant ou None si non trouvé
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id_etudiant, nom, prenom, email, telephone, date_creation
            FROM etudiants
            WHERE id_etudiant = ?
        ''', (id_etudiant,))

        result = cursor.fetchone()

        if result:
            return {
                'id_etudiant': result[0],
                'nom': result[1],
                'prenom': result[2],
                'email': result[3],
                'telephone': result[4],
                'date_creation': result[5]
            }
        return None

    except Exception as e:
        print(f"Erreur lors de la récupération de l'étudiant: {e}")
        return None
    finally:
        conn.close()

def modifier_etudiant(id_etudiant, nom, prenom, email, telephone=""):
    """
    Modifie les informations d'un étudiant

    Args:
        id_etudiant (str): ID de l'étudiant
        nom (str): Nouveau nom
        prenom (str): Nouveau prénom
        email (str): Nouvel email
        telephone (str): Nouveau téléphone (optionnel)

    Returns:
        bool: True si succès, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE etudiants
            SET nom = ?, prenom = ?, email = ?, telephone = ?
            WHERE id_etudiant = ?
        ''', (nom, prenom, email, telephone, id_etudiant))

        success = cursor.rowcount > 0
        conn.commit()

        if success:
            print(f"Étudiant {prenom} {nom} modifié avec succès")

        return success

    except Exception as e:
        print(f"Erreur lors de la modification de l'étudiant: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def supprimer_etudiant(id_etudiant):
    """
    Supprime un étudiant et toutes ses présences

    Args:
        id_etudiant (str): ID de l'étudiant

    Returns:
        bool: True si succès, False sinon
    """
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Récupérer le nom de l'étudiant avant suppression
        cursor.execute('SELECT prenom, nom FROM etudiants WHERE id_etudiant = ?', (id_etudiant,))
        result = cursor.fetchone()

        if not result:
            print(f"Étudiant avec ID {id_etudiant} non trouvé")
            return False

        prenom, nom = result
        student_name = f"{prenom} {nom}"

        # Supprimer les présences associées
        cursor.execute('DELETE FROM presences WHERE nom = ?', (student_name,))

        # Supprimer l'étudiant
        cursor.execute('DELETE FROM etudiants WHERE id_etudiant = ?', (id_etudiant,))

        success = cursor.rowcount > 0
        conn.commit()

        if success:
            print(f"Étudiant {student_name} supprimé avec succès")

        return success

    except Exception as e:
        print(f"Erreur lors de la suppression de l'étudiant: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

# Fonction d'initialisation à appeler au démarrage
if __name__ == "__main__":
    # Initialiser la base de données
    initialize_database()

    # Exemple d'utilisation
    print("Base de données SQLite initialisée avec succès!")
    print(f"Fichier de base de données : {os.path.abspath(DATABASE_FILE)}")

    # Test d'ajout d'un étudiant
    id_etudiant, mot_de_passe = ajouter_etudiant(
        nom="Test",
        prenom="Utilisateur",
        email="test@example.com",
        telephone="+33123456789"
    )

    if id_etudiant:
        print(f"Étudiant de test ajouté : ID={id_etudiant}, Mot de passe={mot_de_passe}")

        # Test de récupération des étudiants
        etudiants = obtenir_tous_etudiants()
        print(f"Nombre d'étudiants dans la base : {len(etudiants)}")

        # Test d'ajout de présence
        from datetime import datetime
        maintenant = datetime.now()
        date_str = maintenant.strftime("%Y-%m-%d")
        heure_str = maintenant.strftime("%H:%M:%S")

        ajouter_presence("Test Utilisateur", date_str, heure_str)

        # Test de vérification de présence
        present = est_present_aujourd_hui("Test Utilisateur", date_str)
        print(f"Test Utilisateur est présent aujourd'hui : {present}")
    else:
        print("Échec de l'ajout de l'étudiant de test")
