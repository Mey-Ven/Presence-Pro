"""
Script pour vérifier les noms encodés dans le système de reconnaissance faciale.
"""

import pickle
import os

def check_encodings():
    """Vérifier les noms encodés dans le fichier encodings.pickle"""
    try:
        # Vérifier si le fichier existe
        if not os.path.exists("encodings.pickle"):
            print("ERREUR: Le fichier encodings.pickle n'existe pas.")
            return
        
        # Charger les encodages
        with open("encodings.pickle", "rb") as f:
            data = pickle.load(f)
        
        # Vérifier la structure des données
        if "names" not in data or "encodings" not in data:
            print("ERREUR: Le fichier encodings.pickle a une structure incorrecte.")
            return
        
        # Afficher tous les noms uniques
        unique_names = set(data["names"])
        print("\nPersonnes enregistrées dans le système :")
        print("======================================")
        for name in sorted(unique_names):
            # Compter combien de fois chaque nom apparaît (nombre d'images)
            count = data["names"].count(name)
            print(f"- {name} ({count} images)")
        
        print(f"\nTotal : {len(unique_names)} personnes")
        print(f"Total d'encodages : {len(data['encodings'])} images")
        
        # Vérifier spécifiquement pour Elmehdi Rahaoui
        variations = ["elmehdi_rahaoui", "Elmehdi_Rahaoui", "elmehdi rahaoui", "Elmehdi Rahaoui"]
        found = False
        for var in variations:
            if var in data["names"]:
                found = True
                print(f"\nElmehdi Rahaoui est présent sous la forme '{var}'")
                break
        
        if not found:
            print("\nElmehdi Rahaoui n'est PAS présent dans les encodages.")
            print("Vous devrez peut-être l'enregistrer avec register_face.py")
        
    except Exception as e:
        print(f"Erreur lors de la vérification des encodages : {e}")

def check_dataset():
    """Vérifier les images dans le dossier dataset"""
    try:
        # Vérifier si le dossier existe
        if not os.path.exists("dataset"):
            print("ERREUR: Le dossier dataset n'existe pas.")
            return
        
        # Lister tous les fichiers
        files = os.listdir("dataset")
        image_files = [f for f in files if f.endswith(('.jpg', '.jpeg', '.png'))]
        
        if not image_files:
            print("Aucune image trouvée dans le dossier dataset.")
            return
        
        # Regrouper par nom
        names = {}
        for img in image_files:
            # Supposer que le format est nom_prenom_X.jpg
            parts = img.split('_')
            if len(parts) >= 2:
                name = '_'.join(parts[:-1])  # Tout sauf le dernier élément (numéro)
                if name in names:
                    names[name] += 1
                else:
                    names[name] = 1
        
        print("\nImages dans le dossier dataset :")
        print("==============================")
        for name, count in sorted(names.items()):
            print(f"- {name} : {count} images")
        
        # Vérifier spécifiquement pour Elmehdi Rahaoui
        elmehdi_files = [f for f in image_files if "elmehdi" in f.lower() and "rahaoui" in f.lower()]
        if elmehdi_files:
            print(f"\nTrouvé {len(elmehdi_files)} images pour Elmehdi Rahaoui dans dataset :")
            for f in elmehdi_files[:5]:  # Afficher les 5 premiers fichiers
                print(f"- {f}")
            if len(elmehdi_files) > 5:
                print(f"... et {len(elmehdi_files) - 5} autres")
        else:
            print("\nAucune image pour Elmehdi Rahaoui trouvée dans le dossier dataset.")
        
    except Exception as e:
        print(f"Erreur lors de la vérification du dossier dataset : {e}")

if __name__ == "__main__":
    print("=== VÉRIFICATION DES ENCODAGES ET IMAGES ===")
    check_encodings()
    check_dataset()
    print("\nSi Elmehdi Rahaoui n'est pas présent dans les encodages mais que ses images sont dans dataset,")
    print("exécutez 'python encode_faces.py' pour mettre à jour les encodages.")
    print("\nSi ses images ne sont pas dans dataset, utilisez 'python register_face.py' pour l'enregistrer.")
