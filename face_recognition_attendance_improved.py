import face_recognition
import cv2
import pickle
import os
import time
import signal
import sys
from datetime import datetime
import csv
import sqlite_config as firebase_config

# Fonction pour gérer l'interruption par Ctrl+C
def signal_handler(sig, frame):
    """Gère l'interruption par Ctrl+C pour fermer proprement les ressources"""
    print("\nInterruption détectée (Ctrl+C). Fermeture en cours...")
    # Utiliser les variables globales pour nettoyer
    if 'cap' in globals() and cap is not None:
        try:
            cap.release()
            print("Caméra libérée")
        except:
            pass
    try:
        cv2.destroyAllWindows()
        print("Fenêtres fermées")
    except:
        pass
    print("Programme terminé.")
    sys.exit(0)

# Configurer le gestionnaire de signal pour Ctrl+C
signal.signal(signal.SIGINT, signal_handler)

try:
    # Charger les encodages
    print("Chargement des encodages...")
    try:
        with open("encodings.pickle", "rb") as f:
            data = pickle.load(f)
        print(f"Encodages chargés pour {len(data['names'])} personnes")

        if len(data["encodings"]) == 0:
            print("ERREUR: Aucun encodage trouvé dans le fichier encodings.pickle")
            print("Veuillez d'abord enregistrer des visages avec register_face.py")
            print("Puis générer les encodages avec encode_faces.py")
            sys.exit(1)
    except FileNotFoundError:
        print("ERREUR: Le fichier encodings.pickle n'existe pas")
        print("Veuillez d'abord enregistrer des visages avec register_face.py")
        print("Puis générer les encodages avec encode_faces.py")
        sys.exit(1)
    except (pickle.UnpicklingError, KeyError):
        print("ERREUR: Le fichier encodings.pickle est corrompu ou dans un format incorrect")
        print("Veuillez régénérer les encodages avec encode_faces.py")
        sys.exit(1)

    # Initialiser la camera
    print("Initialisation de la caméra...")

    # Essayer plusieurs indices de caméra
    camera_indices = [1, 0, 2]  # Essayer d'abord 1 (comme dans le script original), puis 0, puis 2
    cap = None

    for idx in camera_indices:
        print(f"Tentative avec la caméra {idx}...")
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            # Vérifier si la caméra fonctionne en lisant une image
            ret, test_frame = cap.read()
            if ret and test_frame is not None and test_frame.size > 0:
                print(f"Caméra {idx} connectée avec succès")
                break
            else:
                print(f"Caméra {idx} ne fournit pas d'images valides")
                cap.release()
                cap = None
        else:
            print(f"Impossible d'ouvrir la caméra {idx}")
            cap = None

    if cap is None:
        print("ERREUR: Aucune caméra disponible. Vérifiez votre connexion.")
        sys.exit(1)

    # Réduire la résolution pour améliorer les performances
    try:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        print(f"Résolution de la caméra réglée à 640x480")
    except:
        print("Impossible de régler la résolution de la caméra")

    # Initialiser Firebase
    print("Initialisation de Firebase...")
    firebase_initialized = firebase_config.initialize_firebase()

    # Gérer le fichier de présence
    attendance_file = "attendance.csv"
    present_students = set()

    try:
        # Créer le fichier de présence s'il n'existe pas
        if not os.path.exists(attendance_file):
            try:
                with open(attendance_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Nom", "Date", "Heure"])
                print("Fichier d'assiduité créé")
            except PermissionError:
                print(f"ERREUR: Impossible de créer le fichier {attendance_file}")
                print("Vérifiez que vous avez les permissions d'écriture dans ce dossier")
                sys.exit(1)

        # Vérifier si le fichier est accessible en lecture
        try:
            # Charger les présences déjà enregistrées (éviter les doublons)
            with open(attendance_file, "r") as f:
                reader = csv.reader(f)
                try:
                    next(reader)  # Skip header
                    for row in reader:
                        if row:  # Vérifier que la ligne n'est pas vide
                            present_students.add(row[0])
                except StopIteration:
                    # Fichier vide ou seulement avec l'en-tête
                    pass
            print(f"{len(present_students)} personnes déjà marquées présentes")
        except PermissionError:
            print(f"ATTENTION: Impossible de lire le fichier {attendance_file}")
            print("Le fichier est peut-être ouvert dans une autre application")
            print("Les présences ne seront pas chargées et les doublons ne seront pas évités")
            present_students = set()
    except Exception as e:
        print(f"ERREUR lors de la gestion du fichier d'assiduité: {e}")
        print("Le programme continuera mais les présences pourraient ne pas être correctement enregistrées")

    print("Appuie sur 'q' pour quitter.")

    # Variables pour le traitement des images
    last_time = time.time()
    fps_counter = 0
    fps = 0

    # Compteur d'erreurs de caméra consécutives
    camera_error_count = 0
    max_camera_errors = 5  # Nombre maximum d'erreurs avant de quitter

    # Stocker les rectangles des visages pour éviter le clignotement
    face_rectangles = []
    face_names = []

    # Créer une liste des noms d'étudiants dans le dataset (à partir des données chargées)
    student_names = set(data["names"])

    while True:
        try:
            ret, frame = cap.read()
            if not ret or frame is None or frame.size == 0:
                camera_error_count += 1
                print(f"Erreur lors de la capture d'image ({camera_error_count}/{max_camera_errors})")

                if camera_error_count >= max_camera_errors:
                    print("Trop d'erreurs de caméra consécutives. Arrêt du programme.")
                    break

                # Attendre un peu avant de réessayer
                time.sleep(1)
                continue
            else:
                # Réinitialiser le compteur d'erreurs si on a une image valide
                camera_error_count = 0
        except Exception as e:
            print(f"Erreur lors de la lecture de la caméra: {e}")
            camera_error_count += 1
            if camera_error_count >= max_camera_errors:
                print("Trop d'erreurs de caméra consécutives. Arrêt du programme.")
                break
            time.sleep(1)
            continue

        # Calculer le FPS
        fps_counter += 1
        if time.time() - last_time > 1:
            fps = fps_counter
            fps_counter = 0
            last_time = time.time()

        # Réduire la taille de l'image pour accélérer le traitement
        small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
        rgb_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

        try:
            # Utiliser le modèle HOG qui est plus rapide (par défaut)
            face_locations = face_recognition.face_locations(rgb_frame, model="hog")
            face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

            # Ajuster les coordonnées pour l'image originale
            face_locations = [(top*2, right*2, bottom*2, left*2) for top, right, bottom, left in face_locations]

            # Réinitialiser les listes de rectangles et noms
            face_rectangles = []
            face_names = []

            for face_encoding, face_location in zip(face_encodings, face_locations):
                # Utiliser une distance euclidienne pour une comparaison plus rapide
                face_distances = face_recognition.face_distance(data["encodings"], face_encoding)

                name = "Inconnu"
                if len(face_distances) > 0:
                    best_match_index = face_distances.argmin()
                    if face_distances[best_match_index] < 0.5:  # Seuil de tolérance
                        name = data["names"][best_match_index]

                        # Vérifier si le nom est dans la liste des étudiants
                        if name in student_names:
                            # Enregistrer la présence
                            if name not in present_students:
                                now = datetime.now()
                                date_str = now.strftime("%Y-%m-%d")
                                time_str = now.strftime("%H:%M:%S")

                                # Vérifier si la personne est déjà marquée présente aujourd'hui dans Firebase
                                already_present_in_firebase = False
                                if firebase_initialized:
                                    already_present_in_firebase = firebase_config.is_present_today(name, date_str)

                                # Vérifier si la personne est déjà marquée présente aujourd'hui dans le CSV
                                today_present_in_csv = False
                                try:
                                    with open(attendance_file, "r") as f:
                                        reader = csv.reader(f)
                                        next(reader)  # Skip header
                                        for row in reader:
                                            if row and row[0] == name and row[1] == date_str:
                                                today_present_in_csv = True
                                                break
                                except:
                                    pass

                                # Si la personne n'est pas déjà marquée présente
                                if not (today_present_in_csv or already_present_in_firebase):
                                    # Enregistrer dans le fichier CSV
                                    try:
                                        with open(attendance_file, "a", newline="") as f:
                                            writer = csv.writer(f)
                                            writer.writerow([name, date_str, time_str])
                                        present_students.add(name)
                                    except PermissionError:
                                        print(f"ATTENTION: Impossible d'écrire dans {attendance_file} - le fichier est peut-être ouvert dans une autre application")
                                        print(f"{name} détecté mais non enregistré dans CSV. Fermez le fichier {attendance_file} et redémarrez l'application.")
                                    except Exception as e:
                                        print(f"ERREUR lors de l'enregistrement de la présence dans CSV: {e}")

                                    # Enregistrer dans Firebase
                                    if firebase_initialized:
                                        try:
                                            firebase_config.add_attendance(name, date_str, time_str)
                                            print(f"{name} marqué présent à {time_str} et enregistré dans Firebase")
                                        except Exception as e:
                                            print(f"ERREUR lors de l'enregistrement dans Firebase: {e}")
                                            print(f"{name} détecté mais non enregistré dans Firebase en raison d'une erreur.")
                                    else:
                                        print(f"{name} marqué présent à {time_str} (Firebase non initialisé)")
                                else:
                                    if already_present_in_firebase:
                                        print(f"{name} déjà marqué présent aujourd'hui dans Firebase")
                                    else:
                                        print(f"{name} déjà marqué présent aujourd'hui dans CSV")

                # Stocker le rectangle et le nom pour l'affichage
                face_rectangles.append(face_location)
                face_names.append(name)

        except Exception as e:
            print(f"Erreur lors de la détection faciale: {e}")

        # Dessiner tous les rectangles et noms stockés
        for (top, right, bottom, left), name in zip(face_rectangles, face_names):
            # Dessiner le rectangle autour du visage
            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

            # Convertir le format du nom pour l'affichage (remplacer les underscores par des espaces)
            display_name = name.replace("_", " ")

            # Ajouter un fond noir pour le texte pour une meilleure lisibilité
            cv2.rectangle(frame, (left, top - 30), (right, top), (0, 0, 0), -1)
            cv2.putText(frame, display_name, (left + 6, top - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)

        # Afficher le FPS
        cv2.putText(frame, f"FPS: {fps}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # Afficher le nombre de personnes présentes
        cv2.putText(frame, f"Présents: {len(present_students)}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        cv2.imshow("Reconnaissance faciale - Appuie sur 'q' pour quitter", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

except Exception as e:
    print(f"Une erreur est survenue: {e}")
finally:
    # Nettoyer
    if 'cap' in locals() and cap is not None:
        cap.release()
    cv2.destroyAllWindows()
    print("Programme terminé.")
