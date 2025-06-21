
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
                'message': 'Échec de l\'entraînement facial'
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
