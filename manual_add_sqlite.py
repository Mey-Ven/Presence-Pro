"""
Script pour ajouter manuellement des présences dans SQLite
Version SQLite de manual_add.py
"""

import sqlite_config as config
from datetime import datetime

def add_person_to_sqlite(name=None, status="présent"):
    """
    Ajouter manuellement une personne à SQLite
    
    Args:
        name (str, optional): Nom de la personne. Si None, demande à l'utilisateur.
        status (str, optional): Statut de présence ('présent' ou 'absent'). Par défaut 'présent'.
    """
    # Initialiser SQLite
    if not config.initialize_sqlite():
        print("Échec de l'initialisation de SQLite. Vérifiez la base de données.")
        return
    
    # Si le nom n'est pas fourni, demander à l'utilisateur
    if name is None:
        name = input("Entrez le nom de la personne à ajouter : ").strip()
        if not name:
            print("Nom invalide. Opération annulée.")
            return
    
    # Obtenir la date et l'heure actuelles
    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    
    # Vérifier si la personne est déjà présente aujourd'hui
    if config.is_present_today(name, date):
        print(f"{name} est déjà enregistré pour aujourd'hui ({date}).")
        overwrite = input("Voulez-vous ajouter un nouvel enregistrement quand même ? (o/n) : ").lower()
        if overwrite != 'o':
            print("Opération annulée.")
            return
    
    # Ajouter à SQLite
    success = config.add_attendance(name, date, time)
    
    if success:
        print(f"{name} a été ajouté avec succès à SQLite pour le {date} à {time}")
    else:
        print(f"Échec de l'ajout de {name} à SQLite")

def list_all_people():
    """Lister toutes les personnes enregistrées dans SQLite"""
    # Initialiser SQLite
    if not config.initialize_sqlite():
        print("Échec de l'initialisation de SQLite.")
        return
    
    # Récupérer tous les enregistrements
    records = config.get_all_attendance()
    
    if not records:
        print("Aucun enregistrement trouvé dans SQLite.")
        return
    
    # Extraire les noms uniques
    names = set()
    for record in records:
        if 'name' in record:
            names.add(record['name'])
    
    # Afficher les noms
    print(f"\n{len(names)} personnes enregistrées dans SQLite :")
    for name in sorted(names):
        # Compter les présences pour cette personne
        person_records = config.get_attendance_by_person(name)
        count = len(person_records)
        print(f"- {name} ({count} présence(s))")

def list_today_attendance():
    """Lister les présences d'aujourd'hui"""
    # Initialiser SQLite
    if not config.initialize_sqlite():
        print("Échec de l'initialisation de SQLite.")
        return
    
    # Obtenir la date d'aujourd'hui
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Récupérer les enregistrements d'aujourd'hui
    records = config.get_attendance_by_date(today)
    
    if not records:
        print(f"Aucune présence enregistrée pour aujourd'hui ({today}).")
        return
    
    print(f"\nPrésences pour aujourd'hui ({today}) :")
    print("-" * 50)
    print(f"{'Nom':<25} {'Heure':<15}")
    print("-" * 50)
    
    for record in records:
        name = record.get('name', 'N/A')
        time = record.get('time', 'N/A')
        print(f"{name:<25} {time:<15}")

def add_multiple_people():
    """Ajouter plusieurs personnes en une fois"""
    print("\n=== Ajout de plusieurs personnes ===")
    print("Entrez les noms des personnes (une par ligne).")
    print("Tapez 'fin' pour terminer.")
    
    names = []
    while True:
        name = input("Nom de la personne : ").strip()
        if name.lower() == 'fin':
            break
        if name:
            names.append(name)
        else:
            print("Nom vide ignoré.")
    
    if not names:
        print("Aucun nom saisi. Opération annulée.")
        return
    
    print(f"\nAjout de {len(names)} personnes...")
    
    success_count = 0
    for name in names:
        print(f"Ajout de {name}...")
        
        # Obtenir la date et l'heure actuelles
        now = datetime.now()
        date = now.strftime("%Y-%m-%d")
        time = now.strftime("%H:%M:%S")
        
        # Ajouter à SQLite
        success = config.add_attendance(name, date, time)
        
        if success:
            success_count += 1
            print(f"  ✓ {name} ajouté avec succès")
        else:
            print(f"  ✗ Échec de l'ajout de {name}")
    
    print(f"\nRésumé : {success_count}/{len(names)} personnes ajoutées avec succès.")

def interactive_menu():
    """Menu interactif pour la gestion des présences"""
    while True:
        print("\n=== GESTION MANUELLE DES PRÉSENCES (SQLite) ===")
        print("1. Ajouter une personne")
        print("2. Lister toutes les personnes enregistrées")
        print("3. Voir les présences d'aujourd'hui")
        print("4. Ajouter plusieurs personnes")
        print("5. Voir les statistiques")
        print("6. Quitter")
        
        choice = input("\nChoisissez une option (1-6) : ").strip()
        
        if choice == "1":
            add_person_to_sqlite()
        
        elif choice == "2":
            list_all_people()
        
        elif choice == "3":
            list_today_attendance()
        
        elif choice == "4":
            add_multiple_people()
        
        elif choice == "5":
            # Afficher les statistiques en utilisant le visualiseur
            print("\n=== STATISTIQUES ===")
            records = config.get_all_attendance()
            
            if not records:
                print("Aucun enregistrement trouvé.")
                continue
            
            # Statistiques générales
            unique_names = set(record.get('name') for record in records if 'name' in record)
            unique_dates = set(record.get('date') for record in records if 'date' in record)
            
            print(f"Nombre total d'enregistrements : {len(records)}")
            print(f"Nombre de personnes uniques : {len(unique_names)}")
            print(f"Nombre de dates différentes : {len(unique_dates)}")
            
            # Présences par personne
            if unique_names:
                print(f"\nPrésences par personne :")
                for name in sorted(unique_names):
                    person_records = config.get_attendance_by_person(name)
                    print(f"  - {name} : {len(person_records)} présence(s)")
        
        elif choice == "6":
            print("Au revoir !")
            break
        
        else:
            print("Option invalide. Veuillez choisir entre 1 et 6.")

def main():
    """Fonction principale"""
    import sys
    
    if len(sys.argv) == 1:
        # Mode interactif
        interactive_menu()
    
    elif len(sys.argv) == 2:
        if sys.argv[1] == "list":
            list_all_people()
        elif sys.argv[1] == "today":
            list_today_attendance()
        elif sys.argv[1] == "interactive":
            interactive_menu()
        else:
            # Ajouter une personne avec le nom fourni
            add_person_to_sqlite(sys.argv[1])
    
    else:
        print("Utilisation :")
        print(f"  {sys.argv[0]}                    # Mode interactif")
        print(f"  {sys.argv[0]} interactive        # Mode interactif")
        print(f"  {sys.argv[0]} list               # Lister toutes les personnes")
        print(f"  {sys.argv[0]} today              # Voir les présences d'aujourd'hui")
        print(f"  {sys.argv[0]} 'Nom Personne'     # Ajouter une personne spécifique")
        print("\nExemples :")
        print(f"  python {sys.argv[0]}")
        print(f"  python {sys.argv[0]} list")
        print(f"  python {sys.argv[0]} 'Marie Dupont'")

if __name__ == "__main__":
    main()
