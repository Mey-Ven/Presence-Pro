"""
Script pour corriger tous les problèmes de reconnaissance faciale
"""

import os
import pickle
import cv2
import face_recognition
import numpy as np
from pathlib import Path
import shutil

def fix_encodings_file():
    """Crée un fichier d'encodages vide si nécessaire"""
    print("🧠 CORRECTION DU FICHIER D'ENCODAGES")
    print("=" * 50)
    
    encodings_files = ["encodings.pickle", "face_encodings.pkl", "known_faces.pkl"]
    
    # Vérifier si un fichier d'encodages existe
    existing_file = None
    for file in encodings_files:
        if os.path.exists(file):
            existing_file = file
            break
    
    if existing_file:
        print(f"✅ Fichier d'encodages trouvé: {existing_file}")
        
        # Vérifier le contenu
        try:
            with open(existing_file, "rb") as f:
                data = pickle.load(f)
                encodings_count = len(data.get("encodings", []))
                names_count = len(data.get("names", []))
                print(f"   📊 {encodings_count} encodages, {names_count} noms")
                
                if encodings_count == 0:
                    print("   ⚠️ Fichier vide, création d'un nouveau fichier")
                    create_empty_encodings()
                else:
                    print("   ✅ Fichier valide")
                    
        except Exception as e:
            print(f"   ❌ Fichier corrompu: {e}")
            print("   🔧 Création d'un nouveau fichier")
            create_empty_encodings()
    else:
        print("❌ Aucun fichier d'encodages trouvé")
        print("🔧 Création d'un fichier d'encodages vide")
        create_empty_encodings()

def create_empty_encodings():
    """Crée un fichier d'encodages vide"""
    try:
        data = {
            "encodings": [],
            "names": []
        }
        
        with open("encodings.pickle", "wb") as f:
            pickle.dump(data, f)
        
        print("✅ Fichier encodings.pickle créé")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création fichier: {e}")
        return False

def test_face_recognition_library():
    """Test de la bibliothèque face_recognition"""
    print("\n🔍 TEST DE LA BIBLIOTHÈQUE FACE_RECOGNITION")
    print("=" * 50)
    
    try:
        # Test d'importation
        import face_recognition
        print("✅ Bibliothèque face_recognition importée")
        
        # Test avec une image de test simple
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        test_image[25:75, 25:75] = [255, 255, 255]  # Carré blanc
        
        # Test de détection de visages
        face_locations = face_recognition.face_locations(test_image)
        print(f"✅ Détection de visages: {len(face_locations)} visages trouvés")
        
        # Test d'encodage (même sans visage détecté)
        try:
            face_encodings = face_recognition.face_encodings(test_image)
            print(f"✅ Encodage facial: {len(face_encodings)} encodages générés")
        except Exception as e:
            print(f"⚠️ Encodage facial: {e}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Erreur d'importation: {e}")
        print("💡 Installez face_recognition: pip install face_recognition")
        return False
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        return False

def test_camera_functionality():
    """Test de la fonctionnalité caméra"""
    print("\n📷 TEST DE LA FONCTIONNALITÉ CAMÉRA")
    print("=" * 50)
    
    try:
        # Test d'ouverture de la caméra
        cap = cv2.VideoCapture(0)
        
        if not cap.isOpened():
            print("❌ Impossible d'ouvrir la caméra")
            return False
        
        print("✅ Caméra ouverte")
        
        # Test de capture
        ret, frame = cap.read()
        
        if ret and frame is not None:
            print(f"✅ Capture réussie: {frame.shape}")
            
            # Test de détection de visages sur une vraie image
            try:
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                face_locations = face_recognition.face_locations(rgb_frame)
                print(f"✅ Détection sur image réelle: {len(face_locations)} visages")
                
                if len(face_locations) > 0:
                    face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                    print(f"✅ Encodages générés: {len(face_encodings)}")
                else:
                    print("ℹ️ Aucun visage détecté (normal si personne devant la caméra)")
                    
            except Exception as e:
                print(f"❌ Erreur détection: {e}")
        else:
            print("❌ Échec de capture")
            cap.release()
            return False
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ Erreur caméra: {e}")
        return False

def fix_dataset_structure():
    """Corrige la structure du dossier dataset"""
    print("\n📁 CORRECTION DE LA STRUCTURE DATASET")
    print("=" * 50)
    
    dataset_path = Path("dataset")
    
    try:
        # Créer le dossier dataset s'il n'existe pas
        dataset_path.mkdir(exist_ok=True)
        print("✅ Dossier dataset vérifié")
        
        # Vérifier les permissions
        if os.access(dataset_path, os.W_OK):
            print("✅ Permissions d'écriture OK")
        else:
            print("❌ Pas de permissions d'écriture")
            return False
        
        # Créer un fichier de test
        test_file = dataset_path / "test.txt"
        try:
            with open(test_file, "w") as f:
                f.write("test")
            test_file.unlink()  # Supprimer le fichier de test
            print("✅ Test d'écriture réussi")
        except Exception as e:
            print(f"❌ Erreur test d'écriture: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur structure dataset: {e}")
        return False

def create_training_api_routes():
    """Crée un fichier avec les routes API manquantes pour l'entraînement"""
    print("\n🛠️ CRÉATION DES ROUTES API D'ENTRAÎNEMENT")
    print("=" * 50)
    
    api_code = '''
# Routes API à ajouter dans admin_dashboard.py

@app.route('/api/training/capture-photo', methods=['POST'])
@require_auth
def api_capture_photo():
    """Capture une photo pour l'entraînement facial"""
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'message': 'Aucune photo fournie'})
        
        photo = request.files['photo']
        student_id = request.form.get('student_id')
        photo_index = request.form.get('photo_index', '0')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'ID étudiant manquant'})
        
        # Créer le dossier pour l'étudiant
        student_folder = os.path.join('dataset', student_id)
        os.makedirs(student_folder, exist_ok=True)
        
        # Sauvegarder la photo
        filename = f'photo_{photo_index}.jpg'
        photo_path = os.path.join(student_folder, filename)
        photo.save(photo_path)
        
        return jsonify({
            'success': True, 
            'message': 'Photo sauvegardée',
            'photo_path': photo_path
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/training/complete', methods=['POST'])
@require_auth
def api_complete_training():
    """Finalise l'entraînement facial et génère les encodages"""
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        
        if not student_id:
            return jsonify({'success': False, 'message': 'ID étudiant manquant'})
        
        # Obtenir les informations de l'étudiant
        student = db.obtenir_etudiant_par_id(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Étudiant non trouvé'})
        
        # Lancer l'entraînement facial
        trainer = ftm.FacialTrainingModule()
        prenom = student.get('PrenomEtudiant', '')
        nom = student.get('NomEtudiant', '')
        
        success = trainer.train_student(prenom, nom, max_photos=15)
        
        if success:
            # Recharger les encodages dans le contrôleur
            recognition_controller = get_recognition_controller()
            recognition_controller.reload_encodings()
            
            return jsonify({
                'success': True, 
                'message': 'Entraînement terminé avec succès'
            })
        else:
            return jsonify({
                'success': False, 
                'message': 'Échec de l\\'entraînement facial'
            })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/train-student/<student_id>')
@require_auth
def train_student_page(student_id):
    """Page d'entraînement facial pour un étudiant"""
    try:
        student = db.obtenir_etudiant_par_id(student_id)
        if not student:
            flash('Étudiant non trouvé', 'error')
            return redirect(url_for('students'))
        
        return render_template('train_student.html', student=student)
        
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('students'))
'''
    
    try:
        with open("training_api_routes.py", "w", encoding="utf-8") as f:
            f.write(api_code)
        
        print("✅ Fichier training_api_routes.py créé")
        print("💡 Copiez ce code dans admin_dashboard.py")
        return True
        
    except Exception as e:
        print(f"❌ Erreur création routes: {e}")
        return False

def run_comprehensive_fix():
    """Exécute toutes les corrections"""
    print("🔧 CORRECTION COMPLÈTE DU SYSTÈME DE RECONNAISSANCE FACIALE")
    print("=" * 80)
    
    fixes = [
        ("Fichier d'encodages", fix_encodings_file),
        ("Bibliothèque face_recognition", test_face_recognition_library),
        ("Fonctionnalité caméra", test_camera_functionality),
        ("Structure dataset", fix_dataset_structure),
        ("Routes API d'entraînement", create_training_api_routes)
    ]
    
    results = {}
    
    for fix_name, fix_function in fixes:
        try:
            results[fix_name] = fix_function()
        except Exception as e:
            print(f"❌ Erreur dans {fix_name}: {e}")
            results[fix_name] = False
    
    # Résumé
    print("\n" + "=" * 80)
    print("📋 RÉSUMÉ DES CORRECTIONS")
    print("=" * 80)
    
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    for fix_name, success in results.items():
        status = "✅ CORRIGÉ" if success else "❌ ÉCHEC"
        print(f"{fix_name}: {status}")
    
    print(f"\n🎯 RÉSULTAT: {success_count}/{total_count} corrections réussies")
    
    if success_count == total_count:
        print("\n🎉 TOUTES LES CORRECTIONS APPLIQUÉES!")
        print("💡 Prochaines étapes:")
        print("   1. Exécutez le script de réinitialisation: python reset_system_complete.py")
        print("   2. Ajoutez les routes API dans admin_dashboard.py")
        print("   3. Redémarrez le serveur")
        print("   4. Testez l'entraînement facial")
    else:
        print("\n⚠️ CERTAINES CORRECTIONS ONT ÉCHOUÉ")
        print("💡 Vérifiez les erreurs ci-dessus et relancez le script")

if __name__ == "__main__":
    run_comprehensive_fix()
