import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
import hashlib
import uuid
import random
import string

# Initialiser Firebase (si ce n'est pas déjà fait)
try:
    firebase_admin.get_app()
except ValueError:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)

# Accéder à Firestore
db = firestore.client()

def generer_id_etudiant():
    """
    Génère un ID étudiant unique au format E-XXXX

    Returns:
        str: ID étudiant unique
    """
    # Récupérer le dernier ID utilisé
    derniers_ids = db.collection('etudiants').order_by('IdEtudiant', direction=firestore.Query.DESCENDING).limit(1).get()

    # Déterminer le prochain ID
    if len(derniers_ids) == 0:
        # Aucun étudiant dans la base, commencer à E-0001
        prochain_numero = 1
    else:
        # Extraire le numéro du dernier ID
        dernier_id = derniers_ids[0].get('IdEtudiant')
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
    Ajoute un nouvel étudiant dans la base de données Firestore

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

    # Créer le document étudiant dans la collection "etudiants"
    db.collection('etudiants').document(id_etudiant).set({
        'IdEtudiant': id_etudiant,
        'NomEtudiant': nom,
        'PrenomEtudiant': prenom,
        'EmailEtudiant': email,
        'TelephoneEtudiant': telephone,
        'MotDePasseEtudiant': mot_de_passe_hash,
        'DateCreation': firestore.SERVER_TIMESTAMP
    })

    if mot_de_passe_genere:
        print(f"Étudiant {prenom} {nom} ajouté avec succès! ID: {id_etudiant}, Mot de passe: {mot_de_passe}")
        return id_etudiant, mot_de_passe
    else:
        print(f"Étudiant {prenom} {nom} ajouté avec succès! ID: {id_etudiant}")
        return id_etudiant, None

# Fonction pour vérifier si un étudiant existe déjà
def etudiant_existe(id_etudiant=None, email=None):
    """
    Vérifie si un étudiant existe déjà par ID ou email

    Args:
        id_etudiant (str, optional): ID de l'étudiant à vérifier
        email (str, optional): Email de l'étudiant à vérifier

    Returns:
        bool: True si l'étudiant existe, False sinon
    """
    if id_etudiant:
        doc = db.collection('etudiants').document(id_etudiant).get()
        if doc.exists:
            return True

    if email:
        query = db.collection('etudiants').where('EmailEtudiant', '==', email).limit(1).get()
        return len(query) > 0

    return False

def obtenir_tous_etudiants():
    """
    Récupère tous les étudiants de la base de données Firestore

    Returns:
        list: Liste de dictionnaires contenant les informations des étudiants
    """
    try:
        # Récupérer tous les documents de la collection "etudiants"
        etudiants_ref = db.collection('etudiants').get()

        # Convertir les documents en liste de dictionnaires
        etudiants = []
        for doc in etudiants_ref:
            # Récupérer les données du document
            etudiant_data = doc.to_dict()
            # Ne pas inclure le mot de passe hashé dans les résultats
            if 'MotDePasseEtudiant' in etudiant_data:
                del etudiant_data['MotDePasseEtudiant']
            etudiants.append(etudiant_data)

        return etudiants
    except Exception as e:
        print(f"Erreur lors de la récupération des étudiants: {e}")
        return []

def reinitialiser_mot_de_passe(id_etudiant=None, email=None):
    """
    Réinitialise le mot de passe d'un étudiant

    Args:
        id_etudiant (str, optional): ID de l'étudiant
        email (str, optional): Email de l'étudiant

    Returns:
        tuple: (bool, str) - (Succès, Nouveau mot de passe)
    """
    try:
        # Vérifier si l'étudiant existe
        if not etudiant_existe(id_etudiant=id_etudiant, email=email):
            print("Étudiant non trouvé.")
            return False, None

        # Trouver l'ID de l'étudiant si on a fourni l'email
        if email and not id_etudiant:
            query = db.collection('etudiants').where('EmailEtudiant', '==', email).limit(1).get()
            if len(query) > 0:
                id_etudiant = query[0].id
            else:
                print(f"Aucun étudiant trouvé avec l'email {email}")
                return False, None

        # Générer un nouveau mot de passe
        nouveau_mot_de_passe = generer_mot_de_passe()

        # Hasher le nouveau mot de passe
        mot_de_passe_hash = hashlib.sha256(nouveau_mot_de_passe.encode()).hexdigest()

        # Mettre à jour le document dans Firestore
        db.collection('etudiants').document(id_etudiant).update({
            'MotDePasseEtudiant': mot_de_passe_hash
        })

        print(f"Mot de passe réinitialisé avec succès pour l'étudiant avec ID: {id_etudiant}")
        return True, nouveau_mot_de_passe

    except Exception as e:
        print(f"Erreur lors de la réinitialisation du mot de passe: {e}")
        return False, None
'''
# Exemple d'utilisation
if __name__ == "__main__":
    # Ajouter un nouvel étudiant avec ID et mot de passe automatiques
    id_etudiant, mot_de_passe = ajouter_etudiant(
        nom="Dupont",
        prenom="Marie",
        email="marie.dupont@example.com",
        telephone="+33612345678"
    )

    if id_etudiant:
        print(f"Informations de connexion: ID: {id_etudiant}, Mot de passe: {mot_de_passe}") '''