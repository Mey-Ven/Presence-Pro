import sqlite_database as db
import sys

def afficher_menu():
    print("\n=== GESTION DES ÉTUDIANTS (SQLite) ===")
    print("1. Ajouter un nouvel étudiant")
    print("2. Vérifier si un étudiant existe")
    print("3. Ajouter plusieurs étudiants de test")
    print("4. Lister tous les étudiants")
    print("5. Réinitialiser le mot de passe d'un étudiant")
    print("6. Quitter")
    return input("Choisissez une option (1-6): ")

def ajouter_etudiant_manuel():
    print("\n--- Ajout d'un nouvel étudiant ---")
    nom = input("Nom: ")
    prenom = input("Prénom: ")
    email = input("Email: ")
    
    # Vérifier si l'email existe déjà
    if db.etudiant_existe(email=email):
        print(f"Un étudiant avec l'email {email} existe déjà!")
        return
    
    telephone = input("Téléphone: ")
    # Laisser le mot de passe vide pour qu'il soit généré automatiquement
    mot_de_passe = None
    
    # Ajouter l'étudiant avec ID automatique et mot de passe généré
    id_etudiant, mot_de_passe_genere = db.ajouter_etudiant(
        nom=nom,
        prenom=prenom,
        email=email,
        telephone=telephone,
        mot_de_passe=mot_de_passe
    )
    
    if id_etudiant:
        print(f"Étudiant ajouté avec l'ID: {id_etudiant}")
        if mot_de_passe_genere:
            print(f"Mot de passe généré: {mot_de_passe_genere}")

def verifier_etudiant():
    print("\n--- Vérification d'un étudiant ---")
    choix = input("Vérifier par (1) ID ou (2) Email? ")
    
    if choix == "1":
        id_etudiant = input("ID Étudiant: ")
        existe = db.etudiant_existe(id_etudiant=id_etudiant)
    elif choix == "2":
        email = input("Email: ")
        existe = db.etudiant_existe(email=email)
    else:
        print("Option invalide!")
        return
    
    if existe:
        print("L'étudiant existe dans la base de données.")
    else:
        print("L'étudiant n'existe PAS dans la base de données.")

def ajouter_etudiants_test():
    etudiants = [
        {"nom": "Martin", "prenom": "Lucas", "email": "lucas.martin@example.com", "tel": "+33601020304"},
        {"nom": "Bernard", "prenom": "Emma", "email": "emma.bernard@example.com", "tel": "+33605060708"},
        {"nom": "Petit", "prenom": "Hugo", "email": "hugo.petit@example.com", "tel": "+33609101112"}
    ]
    
    for e in etudiants:
        if not db.etudiant_existe(email=e["email"]):
            # Laisser le mot de passe vide pour qu'il soit généré automatiquement
            id_etudiant, mot_de_passe = db.ajouter_etudiant(
                nom=e["nom"],
                prenom=e["prenom"],
                email=e["email"],
                telephone=e["tel"]
            )
            if id_etudiant:
                print(f"Étudiant ajouté avec l'ID: {id_etudiant}")
                if mot_de_passe:
                    print(f"Mot de passe généré: {mot_de_passe}")
        else:
            print(f"Un étudiant avec l'email {e['email']} existe déjà.")
    
    print("Ajout des étudiants de test terminé.")

def lister_etudiants():
    print("\n--- Liste de tous les étudiants ---")
    etudiants = db.obtenir_tous_etudiants()
    
    if not etudiants:
        print("Aucun étudiant trouvé dans la base de données.")
        return
    
    print(f"\n{len(etudiants)} étudiants trouvés :")
    print("-" * 60)
    print(f"{'ID':<10} {'Nom':<15} {'Prénom':<15} {'Email':<25} {'Téléphone':<15}")
    print("-" * 60)
    
    for etudiant in etudiants:
        print(f"{etudiant.get('IdEtudiant', 'N/A'):<10} "
              f"{etudiant.get('NomEtudiant', 'N/A'):<15} "
              f"{etudiant.get('PrenomEtudiant', 'N/A'):<15} "
              f"{etudiant.get('EmailEtudiant', 'N/A'):<25} "
              f"{etudiant.get('TelephoneEtudiant', 'N/A'):<15}")

def reinitialiser_mot_de_passe():
    print("\n--- Réinitialisation de mot de passe ---")
    choix = input("Réinitialiser par (1) ID ou (2) Email? ")
    
    if choix == "1":
        id_etudiant = input("ID Étudiant: ")
        email = None
    elif choix == "2":
        email = input("Email: ")
        id_etudiant = None
    else:
        print("Option invalide!")
        return
    
    # Vérifier si l'étudiant existe
    if not db.etudiant_existe(id_etudiant=id_etudiant, email=email):
        print("Étudiant non trouvé dans la base de données.")
        return
    
    # Demander confirmation
    confirmation = input("Êtes-vous sûr de vouloir réinitialiser le mot de passe? (o/n): ")
    if confirmation.lower() != 'o':
        print("Opération annulée.")
        return
    
    # Réinitialiser le mot de passe
    succes, nouveau_mot_de_passe = db.reinitialiser_mot_de_passe(id_etudiant=id_etudiant, email=email)
    
    if succes:
        print("Mot de passe réinitialisé avec succès!")
        print(f"Nouveau mot de passe: {nouveau_mot_de_passe}")
    else:
        print("Échec de la réinitialisation du mot de passe.")

if __name__ == "__main__":
    # Initialiser la base de données SQLite au démarrage
    print("Initialisation de la base de données SQLite...")
    db.initialize_database()
    
    try:
        while True:
            choix = afficher_menu()
            
            if choix == "1":
                ajouter_etudiant_manuel()
            elif choix == "2":
                verifier_etudiant()
            elif choix == "3":
                ajouter_etudiants_test()
            elif choix == "4":
                lister_etudiants()
            elif choix == "5":
                reinitialiser_mot_de_passe()
            elif choix == "6":
                print("Au revoir!")
                sys.exit(0)
            else:
                print("Option invalide! Veuillez choisir entre 1 et 6.")
    except KeyboardInterrupt:
        print("\nProgramme interrompu par l'utilisateur. Au revoir!")
        sys.exit(0)
