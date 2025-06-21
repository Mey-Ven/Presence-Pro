"""
Script pour visualiser les enregistrements de présence stockés dans SQLite
Version SQLite de view_attendance.py
"""

import sqlite_config as config
import sys
from datetime import datetime

def display_attendance(attendance_list):
    """
    Affiche une liste d'enregistrements de présence
    
    Args:
        attendance_list (list): Liste des enregistrements de présence
    """
    if not attendance_list:
        print("Aucun enregistrement de présence trouvé.")
        return
    
    print(f"\n{len(attendance_list)} enregistrements trouvés :")
    print("-" * 80)
    print(f"{'Nom':<25} {'Date':<12} {'Heure':<10} {'Timestamp':<20}")
    print("-" * 80)
    
    for record in attendance_list:
        name = record.get('name', 'N/A')
        date = record.get('date', 'N/A')
        time = record.get('time', 'N/A')
        timestamp = record.get('timestamp', 'N/A')
        
        # Formater le timestamp si disponible
        if timestamp and timestamp != 'N/A':
            try:
                # Essayer de parser et reformater le timestamp
                if isinstance(timestamp, str):
                    # Si c'est déjà une chaîne, l'utiliser telle quelle
                    formatted_timestamp = timestamp[:19]  # Prendre les 19 premiers caractères
                else:
                    formatted_timestamp = str(timestamp)[:19]
            except:
                formatted_timestamp = str(timestamp)[:19]
        else:
            formatted_timestamp = 'N/A'
        
        print(f"{name:<25} {date:<12} {time:<10} {formatted_timestamp:<20}")

def show_statistics(attendance_list):
    """
    Affiche des statistiques sur les enregistrements de présence
    
    Args:
        attendance_list (list): Liste des enregistrements de présence
    """
    if not attendance_list:
        return
    
    print(f"\n=== STATISTIQUES ===")
    
    # Compter les personnes uniques
    unique_names = set()
    dates = set()
    
    for record in attendance_list:
        if 'name' in record:
            unique_names.add(record['name'])
        if 'date' in record:
            dates.add(record['date'])
    
    print(f"Nombre total d'enregistrements : {len(attendance_list)}")
    print(f"Nombre de personnes uniques : {len(unique_names)}")
    print(f"Nombre de dates différentes : {len(dates)}")
    
    if unique_names:
        print(f"\nPersonnes enregistrées :")
        for name in sorted(unique_names):
            # Compter les présences pour cette personne
            count = sum(1 for record in attendance_list if record.get('name') == name)
            print(f"  - {name} : {count} présence(s)")
    
    if dates:
        print(f"\nDates avec des présences :")
        for date in sorted(dates):
            # Compter les présences pour cette date
            count = sum(1 for record in attendance_list if record.get('date') == date)
            print(f"  - {date} : {count} présence(s)")

def main():
    """Fonction principale"""
    print("=== VISUALISEUR DE PRÉSENCES SQLite ===")
    
    # Initialiser SQLite
    if not config.initialize_sqlite():
        print("Échec de l'initialisation de SQLite. Sortie.")
        sys.exit(1)
    
    # Analyser les arguments de ligne de commande
    if len(sys.argv) == 1:
        # Aucun argument, afficher tous les enregistrements
        print("\nAffichage de tous les enregistrements de présence :")
        attendance_list = config.get_all_attendance()
        display_attendance(attendance_list)
        show_statistics(attendance_list)
    
    elif len(sys.argv) == 2 and sys.argv[1] == "today":
        # Afficher les enregistrements d'aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        print(f"\nAffichage des enregistrements de présence pour aujourd'hui ({today}) :")
        attendance_list = config.get_attendance_by_date(today)
        display_attendance(attendance_list)
        show_statistics(attendance_list)
    
    elif len(sys.argv) == 2 and sys.argv[1] == "stats":
        # Afficher seulement les statistiques
        print("\nAffichage des statistiques de présence :")
        attendance_list = config.get_all_attendance()
        show_statistics(attendance_list)
    
    elif len(sys.argv) == 3 and sys.argv[1] == "date":
        # Afficher les enregistrements pour une date spécifique
        date = sys.argv[2]
        print(f"\nAffichage des enregistrements de présence pour {date} :")
        attendance_list = config.get_attendance_by_date(date)
        display_attendance(attendance_list)
        show_statistics(attendance_list)
    
    elif len(sys.argv) == 3 and sys.argv[1] == "person":
        # Afficher les enregistrements pour une personne spécifique
        name = sys.argv[2]
        print(f"\nAffichage des enregistrements de présence pour {name} :")
        attendance_list = config.get_attendance_by_person(name)
        display_attendance(attendance_list)
        show_statistics(attendance_list)
    
    else:
        # Afficher l'aide
        print("\nUtilisation :")
        print(f"  {sys.argv[0]}                    # Affiche tous les enregistrements")
        print(f"  {sys.argv[0]} today              # Affiche les enregistrements d'aujourd'hui")
        print(f"  {sys.argv[0]} stats              # Affiche seulement les statistiques")
        print(f"  {sys.argv[0]} date YYYY-MM-DD    # Affiche les enregistrements pour une date")
        print(f"  {sys.argv[0]} person NOM         # Affiche les enregistrements pour une personne")
        print("\nExemples :")
        print(f"  python {sys.argv[0]} today")
        print(f"  python {sys.argv[0]} date 2023-12-01")
        print(f"  python {sys.argv[0]} person 'Marie Dupont'")
        sys.exit(1)

if __name__ == "__main__":
    main()
