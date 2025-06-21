"""
Système de gestion des étudiants avec entraînement facial intégré
Version améliorée qui inclut automatiquement la capture de photos et l'encodage facial
"""

import sqlite_database as db
import facial_training_module as ftm
import sys
import os

def afficher_menu():
    print("\n=== GESTION DES ÉTUDIANTS AVEC ENTRAÎNEMENT FACIAL ===")
    print("1. 🎓 Ajouter un nouvel étudiant (avec entraînement facial)")
    print("2. 👤 Ajouter un étudiant (sans entraînement facial)")
    print("3. 🔍 Vérifier si un étudiant existe")
    print("4. 📋 Lister tous les étudiants")
    print("5. 🔄 Réinitialiser le mot de passe d'un étudiant")
    print("6. 📸 Entraîner la reconnaissance faciale pour un étudiant existant")
    print("7. 🔧 Régénérer tous les encodages")
    print("8. ❌ Quitter")
    return input("Choisissez une option (1-8): ")

def ajouter_etudiant_avec_facial():
    """Ajoute un étudiant avec entraînement facial automatique"""
    print("\n=== AJOUT D'ÉTUDIANT AVEC ENTRAÎNEMENT FACIAL ===")
    
    # Collecter les informations de base
    print("📝 Collecte des informations de l'étudiant...")
    nom = input("Nom: ").strip()
    prenom = input("Prénom: ").strip()
    email = input("Email: ").strip()
    
    if not all([nom, prenom, email]):
        print("❌ Tous les champs (nom, prénom, email) sont obligatoires")
        return False
    
    # Vérifier si l'email existe déjà
    if db.etudiant_existe(email=email):
        print(f"❌ Un étudiant avec l'email {email} existe déjà!")
        return False
    
    telephone = input("Téléphone (optionnel): ").strip()
    
    print(f"\n📋 Résumé:")
    print(f"   Nom: {nom}")
    print(f"   Prénom: {prenom}")
    print(f"   Email: {email}")
    print(f"   Téléphone: {telephone if telephone else 'Non renseigné'}")
    
    confirmation = input("\n✅ Confirmer l'ajout de cet étudiant? (o/n): ").lower()
    if confirmation != 'o':
        print("❌ Ajout annulé")
        return False
    
    # Étape 1: Ajouter l'étudiant dans la base de données
    print("\n🗄️  ÉTAPE 1: Ajout dans la base de données...")
    id_etudiant, mot_de_passe = db.ajouter_etudiant(
        nom=nom,
        prenom=prenom,
        email=email,
        telephone=telephone
    )
    
    if not id_etudiant:
        print("❌ Échec de l'ajout dans la base de données")
        return False
    
    print(f"✅ Étudiant ajouté dans la base de données")
    print(f"   ID: {id_etudiant}")
    print(f"   Mot de passe: {mot_de_passe}")
    
    # Étape 2: Entraînement facial
    print(f"\n📸 ÉTAPE 2: Entraînement facial...")
    print(f"🎯 Préparation de la capture de photos pour {prenom} {nom}")
    
    # Demander confirmation pour l'entraînement facial
    facial_confirmation = input("🤔 Procéder à l'entraînement facial maintenant? (o/n): ").lower()
    if facial_confirmation != 'o':
        print("⚠️  Étudiant ajouté sans entraînement facial")
        print("💡 Vous pouvez faire l'entraînement plus tard avec l'option 6")
        return True
    
    # Initialiser le module d'entraînement facial
    trainer = ftm.FacialTrainingModule()
    
    # Lancer l'entraînement
    training_success = trainer.train_student(prenom, nom, max_photos=15)
    
    if training_success:
        print(f"\n🎉 SUCCÈS COMPLET!")
        print(f"✅ Étudiant {prenom} {nom} ajouté avec succès")
        print(f"✅ Entraînement facial terminé")
        print(f"🔍 L'étudiant peut maintenant être reconnu par le système")
        print(f"\n📊 Résumé:")
        print(f"   ID: {id_etudiant}")
        print(f"   Mot de passe: {mot_de_passe}")
        print(f"   Photos d'entraînement: Capturées")
        print(f"   Encodages: Générés")
        return True
    else:
        print(f"\n⚠️  SUCCÈS PARTIEL")
        print(f"✅ Étudiant ajouté dans la base de données")
        print(f"❌ Échec de l'entraînement facial")
        print(f"💡 Vous pouvez réessayer l'entraînement avec l'option 6")
        return True

def ajouter_etudiant_sans_facial():
    """Ajoute un étudiant sans entraînement facial"""
    print("\n=== AJOUT D'ÉTUDIANT (SANS ENTRAÎNEMENT FACIAL) ===")
    
    nom = input("Nom: ").strip()
    prenom = input("Prénom: ").strip()
    email = input("Email: ").strip()
    
    if not all([nom, prenom, email]):
        print("❌ Tous les champs (nom, prénom, email) sont obligatoires")
        return
    
    # Vérifier si l'email existe déjà
    if db.etudiant_existe(email=email):
        print(f"❌ Un étudiant avec l'email {email} existe déjà!")
        return
    
    telephone = input("Téléphone (optionnel): ").strip()
    
    # Ajouter l'étudiant
    id_etudiant, mot_de_passe = db.ajouter_etudiant(
        nom=nom,
        prenom=prenom,
        email=email,
        telephone=telephone
    )
    
    if id_etudiant:
        print(f"✅ Étudiant ajouté avec succès!")
        print(f"   ID: {id_etudiant}")
        print(f"   Mot de passe: {mot_de_passe}")
        print(f"💡 Pour ajouter l'entraînement facial, utilisez l'option 6")
    else:
        print("❌ Échec de l'ajout de l'étudiant")

def verifier_etudiant():
    """Vérifie si un étudiant existe"""
    print("\n=== VÉRIFICATION D'ÉTUDIANT ===")
    choix = input("Vérifier par (1) ID ou (2) Email? ")
    
    if choix == "1":
        id_etudiant = input("ID Étudiant: ").strip()
        existe = db.etudiant_existe(id_etudiant=id_etudiant)
    elif choix == "2":
        email = input("Email: ").strip()
        existe = db.etudiant_existe(email=email)
    else:
        print("❌ Option invalide!")
        return
    
    if existe:
        print("✅ L'étudiant existe dans la base de données")
    else:
        print("❌ L'étudiant n'existe PAS dans la base de données")

def lister_etudiants():
    """Liste tous les étudiants"""
    print("\n=== LISTE DE TOUS LES ÉTUDIANTS ===")
    etudiants = db.obtenir_tous_etudiants()
    
    if not etudiants:
        print("❌ Aucun étudiant trouvé dans la base de données")
        return
    
    print(f"\n📊 {len(etudiants)} étudiants trouvés:")
    print("-" * 80)
    print(f"{'ID':<10} {'Nom':<15} {'Prénom':<15} {'Email':<25} {'Téléphone':<15}")
    print("-" * 80)
    
    for etudiant in etudiants:
        print(f"{etudiant.get('IdEtudiant', 'N/A'):<10} "
              f"{etudiant.get('NomEtudiant', 'N/A'):<15} "
              f"{etudiant.get('PrenomEtudiant', 'N/A'):<15} "
              f"{etudiant.get('EmailEtudiant', 'N/A'):<25} "
              f"{etudiant.get('TelephoneEtudiant', 'N/A'):<15}")

def reinitialiser_mot_de_passe():
    """Réinitialise le mot de passe d'un étudiant"""
    print("\n=== RÉINITIALISATION DE MOT DE PASSE ===")
    choix = input("Réinitialiser par (1) ID ou (2) Email? ")
    
    if choix == "1":
        id_etudiant = input("ID Étudiant: ").strip()
        email = None
    elif choix == "2":
        email = input("Email: ").strip()
        id_etudiant = None
    else:
        print("❌ Option invalide!")
        return
    
    # Vérifier si l'étudiant existe
    if not db.etudiant_existe(id_etudiant=id_etudiant, email=email):
        print("❌ Étudiant non trouvé dans la base de données")
        return
    
    # Demander confirmation
    confirmation = input("✅ Êtes-vous sûr de vouloir réinitialiser le mot de passe? (o/n): ").lower()
    if confirmation != 'o':
        print("❌ Opération annulée")
        return
    
    # Réinitialiser le mot de passe
    succes, nouveau_mot_de_passe = db.reinitialiser_mot_de_passe(id_etudiant=id_etudiant, email=email)
    
    if succes:
        print("✅ Mot de passe réinitialisé avec succès!")
        print(f"🔑 Nouveau mot de passe: {nouveau_mot_de_passe}")
    else:
        print("❌ Échec de la réinitialisation du mot de passe")

def entrainer_etudiant_existant():
    """Entraîne la reconnaissance faciale pour un étudiant existant"""
    print("\n=== ENTRAÎNEMENT FACIAL POUR ÉTUDIANT EXISTANT ===")
    
    # Lister les étudiants pour aider l'utilisateur
    etudiants = db.obtenir_tous_etudiants()
    if not etudiants:
        print("❌ Aucun étudiant dans la base de données")
        return
    
    print(f"📋 Étudiants disponibles:")
    for i, etudiant in enumerate(etudiants[:10], 1):  # Afficher les 10 premiers
        print(f"   {i}. {etudiant.get('PrenomEtudiant')} {etudiant.get('NomEtudiant')} ({etudiant.get('IdEtudiant')})")
    
    if len(etudiants) > 10:
        print(f"   ... et {len(etudiants) - 10} autres")
    
    # Demander l'ID ou l'email
    choix = input("\nSélectionner par (1) ID ou (2) Email? ")
    
    if choix == "1":
        id_etudiant = input("ID Étudiant: ").strip()
        # Trouver l'étudiant par ID
        etudiant_trouve = None
        for etudiant in etudiants:
            if etudiant.get('IdEtudiant') == id_etudiant:
                etudiant_trouve = etudiant
                break
    elif choix == "2":
        email = input("Email: ").strip()
        # Trouver l'étudiant par email
        etudiant_trouve = None
        for etudiant in etudiants:
            if etudiant.get('EmailEtudiant') == email:
                etudiant_trouve = etudiant
                break
    else:
        print("❌ Option invalide!")
        return
    
    if not etudiant_trouve:
        print("❌ Étudiant non trouvé")
        return
    
    prenom = etudiant_trouve.get('PrenomEtudiant')
    nom = etudiant_trouve.get('NomEtudiant')
    
    print(f"\n🎯 Étudiant sélectionné: {prenom} {nom}")
    
    confirmation = input("🤔 Procéder à l'entraînement facial? (o/n): ").lower()
    if confirmation != 'o':
        print("❌ Entraînement annulé")
        return
    
    # Initialiser le module d'entraînement
    trainer = ftm.FacialTrainingModule()
    
    # Lancer l'entraînement
    training_success = trainer.train_student(prenom, nom, max_photos=15)
    
    if training_success:
        print(f"🎉 Entraînement facial terminé avec succès pour {prenom} {nom}!")
    else:
        print(f"❌ Échec de l'entraînement facial pour {prenom} {nom}")

def regenerer_encodages():
    """Régénère tous les encodages"""
    print("\n=== RÉGÉNÉRATION DES ENCODAGES ===")
    
    # Vérifier s'il y a des images dans le dataset
    dataset_folder = "dataset"
    if not os.path.exists(dataset_folder):
        print("❌ Dossier dataset non trouvé")
        return
    
    image_files = [f for f in os.listdir(dataset_folder) if f.endswith(('.jpg', '.jpeg', '.png'))]
    if not image_files:
        print("❌ Aucune image trouvée dans le dataset")
        return
    
    print(f"📁 {len(image_files)} images trouvées dans le dataset")
    
    confirmation = input("🤔 Régénérer tous les encodages? (o/n): ").lower()
    if confirmation != 'o':
        print("❌ Opération annulée")
        return
    
    # Initialiser le module et régénérer
    trainer = ftm.FacialTrainingModule()
    success = trainer.generate_encodings()
    
    if success:
        print("✅ Encodages régénérés avec succès!")
    else:
        print("❌ Échec de la régénération des encodages")

def main():
    """Fonction principale"""
    # Initialiser la base de données SQLite au démarrage
    print("🔧 Initialisation de la base de données SQLite...")
    db.initialize_database()
    
    try:
        while True:
            choix = afficher_menu()
            
            if choix == "1":
                ajouter_etudiant_avec_facial()
            elif choix == "2":
                ajouter_etudiant_sans_facial()
            elif choix == "3":
                verifier_etudiant()
            elif choix == "4":
                lister_etudiants()
            elif choix == "5":
                reinitialiser_mot_de_passe()
            elif choix == "6":
                entrainer_etudiant_existant()
            elif choix == "7":
                regenerer_encodages()
            elif choix == "8":
                print("👋 Au revoir!")
                sys.exit(0)
            else:
                print("❌ Option invalide! Veuillez choisir entre 1 et 8")
                
    except KeyboardInterrupt:
        print("\n\n🛑 Programme interrompu par l'utilisateur. Au revoir!")
        sys.exit(0)

if __name__ == "__main__":
    main()
