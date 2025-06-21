"""
Script pour ajouter manuellement une personne dans la base de données Firebase.
"""

import firebase_config
from datetime import datetime
import sys

def add_person_to_firebase(name=None, status="présent"):
    """Ajouter manuellement une personne à Firebase
    
    Args:
        name (str, optional): Nom de la personne. Si None, demande à l'utilisateur.
        status (str, optional): Statut de présence ('présent' ou 'absent'). Par défaut 'présent'.
    """
    # Initialiser Firebase
    if not firebase_config.initialize_firebase():
        print("Échec de l'initialisation de Firebase. Vérifiez votre connexion et serviceAccountKey.json.")
        return
    
    # Si le nom n'est pas fourni, demander à l'utilisateur
    if name is None:
        name = input("Entrez le nom de la personne à ajouter : ").strip()
        if not name:
            print("Nom invalide. Opération annulée.")
            return
    
    # Obtenir la date et l'heure actuelles
    date = datetime.now().strftime("%Y-%m-%d")
    time = datetime.now().strftime("%H:%M:%S")
    
    # Vérifier si la personne est déjà présente aujourd'hui
    if firebase_config.is_present_today(name, date):
        print(f"{name} est déjà enregistré pour aujourd'hui ({date}).")
        overwrite = input("Voulez-vous mettre à jour l'enregistrement ? (o/n) : ").lower()
        if overwrite != 'o':
            print("Opération annulée.")
            return
    
    # Ajouter à Firebase
    success = firebase_config.add_attendance(name, date, time)
    
    if success:
        print(f"{name} a été ajouté avec succès à Firebase pour le {date} à {time}")
    else:
        print(f"Échec de l'ajout de {name} à Firebase")

def list_all_people():
    """Lister toutes les personnes enregistrées dans Firebase"""
    # Initialiser Firebase
    if not firebase_config.initialize_firebase():
        print("Échec de l'initialisation de Firebase.")
        return
    
    # Récupérer tous les enregistrements
    records = firebase_config.get_all_attendance()
    
    if not records:
        print("Aucun enregistrement trouvé dans Firebase.")
        return
    
    # Extraire les noms uniques
    names = set()
    for record in records:
        if 'name' in record:
            names.add(record['name'])
    
    # Afficher les noms
    print(f"\n{len(names)} personnes enregistrées dans Firebase :")
    for name in sorted(names):
        print(f"- {name}")

if __name__ == "__main__":
    print("=== AJOUT MANUEL D'UNE PERSONNE À FIREBASE ===\n")
    
    # Vérifier les arguments de ligne de commande
    if len(sys.argv) > 1:
        name = sys.argv[1]
        add_person_to_firebase(name)
    else:
        # Menu simple
        print("1. Ajouter une personne")
        print("2. Lister toutes les personnes")
        print("3. Quitter")
        
        choice = input("\nChoisissez une option (1-3) : ")
        
        if choice == "1":
            add_person_to_firebase()
        elif choice == "2":
            list_all_people()
        else:
            print("Au revoir !")
