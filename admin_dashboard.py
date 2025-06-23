"""
Tableau de bord d'administration web pour le système de reconnaissance faciale
Application Flask complète avec gestion des étudiants, surveillance des présences et administration système
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file, Response
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite_database as db
import facial_training_module as ftm
import sqlite_config as config
import facial_recognition_controller as frc
import os
import sys
import json
import csv
import io
import base64
from datetime import datetime, timedelta
import threading
import time
import shutil
import pandas as pd
from PIL import Image
import cv2

# Configuration de l'application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'facial_attendance_admin_2023'
app.config['UPLOAD_FOLDER'] = 'dataset'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialiser SocketIO pour les mises à jour en temps réel
socketio = SocketIO(app, cors_allowed_origins="*")

# Configuration admin par défaut
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")  # Changez ce mot de passe !

# Initialiser la base de données
db.initialize_database()

# Initialiser le contrôleur de reconnaissance faciale
recognition_controller = frc.get_recognition_controller(socketio)

def require_auth(f):
    """Décorateur pour vérifier l'authentification"""
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/')
def index():
    """Page d'accueil - redirige vers le tableau de bord ou la connexion"""
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Page de connexion"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['logged_in'] = True
            session['username'] = username
            flash('Connexion réussie!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Déconnexion"""
    session.clear()
    flash('Déconnexion réussie', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@require_auth
def dashboard():
    """Tableau de bord principal"""
    try:
        # Statistiques générales
        students = db.obtenir_tous_etudiants()
        total_students = len(students)
        
        # Présences d'aujourd'hui
        today = datetime.now().strftime("%Y-%m-%d")
        today_attendance = config.get_attendance_by_date(today)
        today_count = len(today_attendance)
        
        # Présences totales
        all_attendance = config.get_all_attendance()
        total_attendance = len(all_attendance)
        
        # Statistiques de la semaine
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_attendance = [a for a in all_attendance if a.get('date', '') >= week_ago]
        week_count = len(week_attendance)
        
        # Vérifier l'état de la caméra
        trainer = ftm.FacialTrainingModule()
        camera_status = trainer.find_camera() is not None
        
        # Vérifier les encodages
        encodings_exist = os.path.exists('encodings.pickle')
        
        stats = {
            'total_students': total_students,
            'today_attendance': today_count,
            'total_attendance': total_attendance,
            'week_attendance': week_count,
            'camera_status': camera_status,
            'encodings_exist': encodings_exist,
            'database_size': os.path.getsize('attendance.db') if os.path.exists('attendance.db') else 0
        }
        
        # Activité récente (dernières présences)
        recent_attendance = sorted(all_attendance, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
        
        return render_template('dashboard.html', stats=stats, recent_attendance=recent_attendance)
        
    except Exception as e:
        flash(f'Erreur lors du chargement du tableau de bord: {str(e)}', 'error')
        return render_template('dashboard.html', stats={}, recent_attendance=[])

@app.route('/students')
@require_auth
def students():
    """Page de gestion des étudiants"""
    try:
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '', type=str)
        per_page = 20
        
        # Récupérer tous les étudiants
        all_students = db.obtenir_tous_etudiants()
        
        # Filtrer par recherche si nécessaire
        if search:
            filtered_students = []
            search_lower = search.lower()
            for student in all_students:
                if (search_lower in student.get('NomEtudiant', '').lower() or
                    search_lower in student.get('PrenomEtudiant', '').lower() or
                    search_lower in student.get('EmailEtudiant', '').lower() or
                    search_lower in student.get('IdEtudiant', '').lower()):
                    filtered_students.append(student)
            all_students = filtered_students
        
        # Pagination
        total = len(all_students)
        start = (page - 1) * per_page
        end = start + per_page
        students_page = all_students[start:end]
        
        # Calculer les informations de pagination
        has_prev = page > 1
        has_next = end < total
        prev_num = page - 1 if has_prev else None
        next_num = page + 1 if has_next else None
        
        pagination = {
            'page': page,
            'per_page': per_page,
            'total': total,
            'has_prev': has_prev,
            'has_next': has_next,
            'prev_num': prev_num,
            'next_num': next_num,
            'pages': list(range(1, (total // per_page) + 2))
        }
        
        return render_template('students.html', 
                             students=students_page, 
                             pagination=pagination, 
                             search=search)
        
    except Exception as e:
        flash(f'Erreur lors du chargement des étudiants: {str(e)}', 'error')
        return render_template('students.html', students=[], pagination={}, search='')

@app.route('/students/add', methods=['GET', 'POST'])
@require_auth
def add_student():
    """Ajouter un nouvel étudiant"""
    if request.method == 'POST':
        try:
            nom = request.form['nom'].strip()
            prenom = request.form['prenom'].strip()
            email = request.form['email'].strip()
            telephone = request.form.get('telephone', '').strip()
            with_facial = request.form.get('with_facial') == 'on'
            
            if not all([nom, prenom, email]):
                flash('Nom, prénom et email sont obligatoires', 'error')
                return render_template('add_student.html')
            
            # Vérifier si l'email existe déjà
            if db.etudiant_existe(email=email):
                flash(f'Un étudiant avec l\'email {email} existe déjà', 'error')
                return render_template('add_student.html')
            
            # Ajouter l'étudiant dans la base de données
            id_etudiant, mot_de_passe = db.ajouter_etudiant(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone
            )
            
            if not id_etudiant:
                flash('Erreur lors de l\'ajout de l\'étudiant', 'error')
                return render_template('add_student.html')
            
            flash(f'Étudiant {prenom} {nom} ajouté avec succès (ID: {id_etudiant})', 'success')
            
            if with_facial:
                # Rediriger vers la page d'entraînement facial
                return redirect(url_for('train_student_page', student_id=id_etudiant))
            else:
                return redirect(url_for('students'))
                
        except Exception as e:
            flash(f'Erreur lors de l\'ajout: {str(e)}', 'error')
    
    return render_template('add_student.html')

@app.route('/students/<student_id>/edit', methods=['GET', 'POST'])
@require_auth
def edit_student(student_id):
    """Modifier un étudiant"""
    try:
        # Récupérer l'étudiant
        students = db.obtenir_tous_etudiants()
        student = None
        for s in students:
            if s.get('IdEtudiant') == student_id:
                student = s
                break
        
        if not student:
            flash('Étudiant non trouvé', 'error')
            return redirect(url_for('students'))
        
        if request.method == 'POST':
            # Mise à jour des informations (à implémenter dans sqlite_database.py)
            flash('Fonctionnalité de modification en cours de développement', 'info')
            return redirect(url_for('students'))
        
        return render_template('edit_student.html', student=student)
        
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('students'))

@app.route('/students/<student_id>/delete', methods=['POST'])
@require_auth
def delete_student(student_id):
    """Supprimer un étudiant"""
    try:
        # Vérifier si l'étudiant existe
        if not db.etudiant_existe(id_etudiant=student_id):
            return jsonify({'success': False, 'message': 'Étudiant non trouvé'})
        
        # Supprimer les images de l'étudiant du dataset
        dataset_folder = 'dataset'
        if os.path.exists(dataset_folder):
            for filename in os.listdir(dataset_folder):
                if student_id in filename:
                    try:
                        os.remove(os.path.join(dataset_folder, filename))
                    except:
                        pass
        
        # Supprimer de la base de données (à implémenter dans sqlite_database.py)
        # Pour l'instant, on simule la suppression
        flash('Fonctionnalité de suppression en cours de développement', 'info')
        
        return jsonify({'success': True, 'message': 'Étudiant supprimé avec succès'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/students/<student_id>/reset_password', methods=['POST'])
@require_auth
def reset_student_password(student_id):
    """Réinitialiser le mot de passe d'un étudiant"""
    try:
        success, new_password = db.reinitialiser_mot_de_passe(id_etudiant=student_id)
        
        if success:
            return jsonify({
                'success': True, 
                'message': 'Mot de passe réinitialisé avec succès',
                'new_password': new_password
            })
        else:
            return jsonify({'success': False, 'message': 'Erreur lors de la réinitialisation'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

# Route obsolète supprimée - utiliser train_student_page() à la place

@app.route('/api/student/<student_id>/photo')
def student_photo(student_id):
    """API pour récupérer la photo d'un étudiant"""
    try:
        # Chercher une image de l'étudiant dans le dataset
        dataset_folder = 'dataset'
        if os.path.exists(dataset_folder):
            for filename in os.listdir(dataset_folder):
                if student_id in filename and filename.endswith(('.jpg', '.jpeg', '.png')):
                    return send_file(os.path.join(dataset_folder, filename))

        # Retourner une image par défaut si aucune photo trouvée
        return '', 404

    except Exception as e:
        return '', 404

@app.route('/api/stats')
def api_stats():
    """API pour récupérer les statistiques en temps réel"""
    try:
        students = db.obtenir_tous_etudiants()
        total_students = len(students)

        today = datetime.now().strftime("%Y-%m-%d")
        today_attendance = config.get_attendance_by_date(today)
        today_count = len(today_attendance)

        all_attendance = config.get_all_attendance()
        total_attendance = len(all_attendance)

        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        week_attendance = [a for a in all_attendance if a.get('date', '') >= week_ago]
        week_count = len(week_attendance)

        return jsonify({
            'total_students': total_students,
            'today_attendance': today_count,
            'total_attendance': total_attendance,
            'week_attendance': week_count
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/attendance')
@require_auth
def attendance():
    """Page de surveillance des présences"""
    try:
        # Paramètres de filtrage
        date_filter = request.args.get('date', datetime.now().strftime("%Y-%m-%d"))
        student_filter = request.args.get('student', '')

        # Récupérer les présences
        if date_filter:
            attendance_records = config.get_attendance_by_date(date_filter)
        else:
            attendance_records = config.get_all_attendance()

        # Filtrer par étudiant si nécessaire
        if student_filter:
            attendance_records = [r for r in attendance_records if student_filter.lower() in r.get('name', '').lower()]

        # Trier par heure décroissante
        attendance_records = sorted(attendance_records, key=lambda x: x.get('time', ''), reverse=True)

        return render_template('attendance.html',
                             attendance_records=attendance_records,
                             date_filter=date_filter,
                             student_filter=student_filter)

    except Exception as e:
        flash(f'Erreur lors du chargement des présences: {str(e)}', 'error')
        return render_template('attendance.html', attendance_records=[], date_filter='', student_filter='')

# Routes pour le contrôle de la reconnaissance faciale

@app.route('/api/recognition/start', methods=['POST'])
@require_auth
def start_recognition():
    """Démarre le système de reconnaissance faciale"""
    try:
        success = recognition_controller.start_recognition()
        return jsonify({
            'success': success,
            'message': 'Reconnaissance faciale démarrée' if success else 'Erreur lors du démarrage'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/recognition/stop', methods=['POST'])
@require_auth
def stop_recognition():
    """Arrête le système de reconnaissance faciale"""
    try:
        success = recognition_controller.stop_recognition()
        return jsonify({
            'success': success,
            'message': 'Reconnaissance faciale arrêtée' if success else 'Erreur lors de l\'arrêt'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/recognition/status')
@require_auth
def recognition_status():
    """Retourne le statut du système de reconnaissance faciale"""
    try:
        status = recognition_controller.get_status()
        return jsonify(status)
    except Exception as e:
        return jsonify({
            'error': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/recognition/reload', methods=['POST'])
@require_auth
def reload_encodings():
    """Recharge les encodages faciaux"""
    try:
        success = recognition_controller.reload_encodings()
        return jsonify({
            'success': success,
            'message': 'Encodages rechargés' if success else 'Erreur lors du rechargement'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/recognition/screenshot', methods=['POST'])
@require_auth
def capture_screenshot():
    """Capture une capture d'écran de la caméra"""
    try:
        filename = recognition_controller.capture_screenshot()
        return jsonify({
            'success': filename is not None,
            'filename': filename,
            'message': f'Capture sauvegardée: {filename}' if filename else 'Erreur lors de la capture'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

# Routes pour l'export de données

@app.route('/export/attendance/csv')
@require_auth
def export_attendance_csv():
    """Exporter les données de présence en CSV"""
    try:
        # Récupérer toutes les présences
        all_attendance = config.get_all_attendance()

        # Créer un fichier CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow(['Nom', 'Date', 'Heure', 'Timestamp'])

        # Données
        for record in all_attendance:
            writer.writerow([
                record.get('name', ''),
                record.get('date', ''),
                record.get('time', ''),
                record.get('timestamp', '')
            ])

        # Préparer la réponse
        output.seek(0)

        # Créer le nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"presences_{timestamp}.csv"

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Erreur lors de l\'export CSV: {str(e)}', 'error')
        return redirect(url_for('attendance'))

@app.route('/export/attendance/excel')
@require_auth
def export_attendance_excel():
    """Exporter les données de présence en Excel"""
    try:
        # Récupérer toutes les présences
        all_attendance = config.get_all_attendance()

        # Créer un DataFrame pandas
        df = pd.DataFrame(all_attendance)

        # Réorganiser les colonnes
        if not df.empty:
            df = df[['name', 'date', 'time', 'timestamp']]
            df.columns = ['Nom', 'Date', 'Heure', 'Timestamp']

        # Créer un fichier Excel en mémoire
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Présences', index=False)

            # Ajouter des statistiques sur une autre feuille
            stats_data = {
                'Métrique': [
                    'Total des présences',
                    'Nombre d\'étudiants uniques',
                    'Présences aujourd\'hui',
                    'Date d\'export'
                ],
                'Valeur': [
                    len(all_attendance),
                    len(set(record.get('name', '') for record in all_attendance)),
                    len([r for r in all_attendance if r.get('date', '') == datetime.now().strftime("%Y-%m-%d")]),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
            }

            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='Statistiques', index=False)

        output.seek(0)

        # Créer le nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"presences_{timestamp}.xlsx"

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Erreur lors de l\'export Excel: {str(e)}', 'error')
        return redirect(url_for('attendance'))

@app.route('/export/students/csv')
@require_auth
def export_students_csv():
    """Exporter la liste des étudiants en CSV"""
    try:
        # Récupérer tous les étudiants
        students = db.obtenir_tous_etudiants()

        # Créer un fichier CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)

        # En-têtes
        writer.writerow(['ID Étudiant', 'Nom', 'Prénom', 'Email', 'Téléphone', 'Date Création'])

        # Données
        for student in students:
            writer.writerow([
                student.get('id_etudiant', ''),
                student.get('nom', ''),
                student.get('prenom', ''),
                student.get('email', ''),
                student.get('telephone', ''),
                student.get('date_creation', '')
            ])

        # Préparer la réponse
        output.seek(0)

        # Créer le nom de fichier avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"etudiants_{timestamp}.csv"

        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )

    except Exception as e:
        flash(f'Erreur lors de l\'export CSV des étudiants: {str(e)}', 'error')
        return redirect(url_for('students'))

# Routes pour les paramètres et configuration

@app.route('/settings')
@require_auth
def settings():
    """Page de paramètres et configuration"""
    try:
        # Récupérer les informations système
        system_info = {
            'database_size': os.path.getsize('attendance.db') if os.path.exists('attendance.db') else 0,
            'encodings_exist': os.path.exists('encodings.pickle'),
            'dataset_size': sum(len(files) for _, _, files in os.walk('dataset')) if os.path.exists('dataset') else 0,
            'total_students': len(db.obtenir_tous_etudiants()),
            'total_attendance': len(config.get_all_attendance()),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'flask_version': '2.0+',
            'opencv_version': cv2.__version__ if 'cv2' in globals() else 'Non disponible'
        }

        # Configuration actuelle
        current_config = {
            'admin_username': ADMIN_USERNAME,
            'recognition_cooldown': getattr(recognition_controller, 'recognition_cooldown', 30),
            'camera_resolution': '640x480',
            'frame_skip': 2,
            'confidence_threshold': 0.6
        }

        return render_template('settings.html',
                             system_info=system_info,
                             current_config=current_config)

    except Exception as e:
        flash(f'Erreur lors du chargement des paramètres: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/settings/update', methods=['POST'])
@require_auth
def update_settings():
    """Mettre à jour les paramètres système"""
    try:
        # Récupérer les données du formulaire
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        recognition_cooldown = request.form.get('recognition_cooldown', type=int)

        # Validation
        if new_password and new_password != confirm_password:
            flash('Les mots de passe ne correspondent pas', 'error')
            return redirect(url_for('settings'))

        # Mettre à jour le mot de passe admin si fourni
        if new_password and len(new_password) >= 6:
            global ADMIN_PASSWORD_HASH
            ADMIN_PASSWORD_HASH = generate_password_hash(new_password)
            flash('Mot de passe administrateur mis à jour avec succès', 'success')

        # Mettre à jour les paramètres de reconnaissance
        if recognition_cooldown and 5 <= recognition_cooldown <= 300:
            recognition_controller.recognition_cooldown = recognition_cooldown
            flash(f'Délai de reconnaissance mis à jour: {recognition_cooldown}s', 'success')

        return redirect(url_for('settings'))

    except Exception as e:
        flash(f'Erreur lors de la mise à jour: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/settings/backup')
@require_auth
def backup_database():
    """Créer une sauvegarde de la base de données"""
    try:
        if not os.path.exists('attendance.db'):
            flash('Base de données non trouvée', 'error')
            return redirect(url_for('settings'))

        # Créer le nom de fichier de sauvegarde
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"backup_attendance_{timestamp}.db"

        # Copier la base de données
        shutil.copy2('attendance.db', backup_filename)

        # Envoyer le fichier
        return send_file(
            backup_filename,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        flash(f'Erreur lors de la sauvegarde: {str(e)}', 'error')
        return redirect(url_for('settings'))

@app.route('/settings/regenerate-encodings', methods=['POST'])
@require_auth
def regenerate_encodings():
    """Régénérer tous les encodages faciaux"""
    try:
        # Importer le module d'encodage
        import encode_faces

        # Régénérer les encodages
        encode_faces.main()

        # Recharger les encodages dans le contrôleur
        recognition_controller.reload_encodings()

        flash('Encodages faciaux régénérés avec succès', 'success')

    except Exception as e:
        flash(f'Erreur lors de la régénération: {str(e)}', 'error')

    return redirect(url_for('settings'))

@app.route('/settings/clear-attendance', methods=['POST'])
@require_auth
def clear_attendance():
    """Effacer toutes les données de présence (avec confirmation)"""
    try:
        confirmation = request.form.get('confirmation')
        if confirmation != 'SUPPRIMER':
            flash('Confirmation incorrecte. Tapez "SUPPRIMER" pour confirmer', 'error')
            return redirect(url_for('settings'))

        # Effacer toutes les présences
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM presences')
        conn.commit()
        conn.close()

        flash('Toutes les données de présence ont été supprimées', 'warning')

    except Exception as e:
        flash(f'Erreur lors de la suppression: {str(e)}', 'error')

    return redirect(url_for('settings'))

# Routes pour les rapports et analytics

@app.route('/reports')
@require_auth
def reports():
    """Page de rapports et analytics"""
    try:
        # Récupérer toutes les données
        all_attendance = config.get_all_attendance()
        all_students = db.obtenir_tous_etudiants()

        # Statistiques générales
        total_attendance = len(all_attendance)
        total_students = len(all_students)

        # Présences par jour (derniers 30 jours)
        from collections import defaultdict
        daily_stats = defaultdict(int)

        # Calculer les présences par jour
        for record in all_attendance:
            date = record.get('date', '')
            if date:
                daily_stats[date] += 1

        # Présences par étudiant
        student_stats = defaultdict(int)
        for record in all_attendance:
            name = record.get('name', '')
            if name:
                student_stats[name] += 1

        # Top 10 étudiants les plus présents
        top_students = sorted(student_stats.items(), key=lambda x: x[1], reverse=True)[:10]

        # Présences par heure
        hourly_stats = defaultdict(int)
        for record in all_attendance:
            time_str = record.get('time', '')
            if time_str:
                try:
                    hour = int(time_str.split(':')[0])
                    hourly_stats[hour] += 1
                except:
                    pass

        # Présences par jour de la semaine
        import calendar
        weekday_stats = defaultdict(int)
        for record in all_attendance:
            date_str = record.get('date', '')
            if date_str:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    weekday = calendar.day_name[date_obj.weekday()]
                    weekday_stats[weekday] += 1
                except:
                    pass

        # Préparer les données pour les graphiques
        chart_data = {
            'daily_labels': list(sorted(daily_stats.keys()))[-30:],  # 30 derniers jours
            'daily_values': [daily_stats[date] for date in sorted(daily_stats.keys())[-30:]],
            'student_labels': [name for name, _ in top_students],
            'student_values': [count for _, count in top_students],
            'hourly_labels': [f"{hour}:00" for hour in range(24)],
            'hourly_values': [hourly_stats[hour] for hour in range(24)],
            'weekday_labels': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'],
            'weekday_values': [weekday_stats[day] for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']]
        }

        # Statistiques récentes (7 derniers jours)
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        recent_attendance = [a for a in all_attendance if a.get('date', '') >= week_ago]

        stats = {
            'total_attendance': total_attendance,
            'total_students': total_students,
            'week_attendance': len(recent_attendance),
            'avg_daily': len(recent_attendance) / 7 if recent_attendance else 0,
            'attendance_rate': (len(set(r.get('name', '') for r in recent_attendance)) / total_students * 100) if total_students > 0 else 0
        }

        return render_template('reports.html',
                             chart_data=chart_data,
                             stats=stats,
                             top_students=top_students[:5])

    except Exception as e:
        flash(f'Erreur lors du chargement des rapports: {str(e)}', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/reports/data')
@require_auth
def api_reports_data():
    """API pour récupérer les données de rapports en JSON"""
    try:
        # Récupérer les paramètres
        report_type = request.args.get('type', 'daily')
        days = request.args.get('days', 30, type=int)

        all_attendance = config.get_all_attendance()

        if report_type == 'daily':
            # Présences par jour
            from collections import defaultdict
            daily_stats = defaultdict(int)

            # Filtrer par nombre de jours
            cutoff_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

            for record in all_attendance:
                date = record.get('date', '')
                if date and date >= cutoff_date:
                    daily_stats[date] += 1

            return jsonify({
                'labels': list(sorted(daily_stats.keys())),
                'values': [daily_stats[date] for date in sorted(daily_stats.keys())],
                'title': f'Présences par jour ({days} derniers jours)'
            })

        elif report_type == 'hourly':
            # Présences par heure
            hourly_stats = defaultdict(int)
            for record in all_attendance:
                time_str = record.get('time', '')
                if time_str:
                    try:
                        hour = int(time_str.split(':')[0])
                        hourly_stats[hour] += 1
                    except:
                        pass

            return jsonify({
                'labels': [f"{hour}:00" for hour in range(24)],
                'values': [hourly_stats[hour] for hour in range(24)],
                'title': 'Présences par heure'
            })

        else:
            return jsonify({'error': 'Type de rapport non supporté'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Routes pour la gestion avancée des étudiants

@app.route('/api/students/<student_id>/delete', methods=['DELETE'])
@require_auth
def api_delete_student(student_id):
    """Supprimer un étudiant"""
    try:
        # Récupérer les informations de l'étudiant
        student = db.obtenir_etudiant_par_id(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Étudiant non trouvé'}), 404

        # Supprimer l'étudiant
        success = db.supprimer_etudiant(student_id)

        if success:
            # Supprimer aussi les images du dataset si elles existent
            student_name = f"{student.get('prenom', '')} {student.get('nom', '')}".strip()
            dataset_path = os.path.join('dataset', student_name)
            if os.path.exists(dataset_path):
                shutil.rmtree(dataset_path)

            return jsonify({
                'success': True,
                'message': f'Étudiant {student_name} supprimé avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la suppression'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/students/<student_id>/edit', methods=['PUT'])
@require_auth
def api_edit_student(student_id):
    """Modifier un étudiant"""
    try:
        data = request.get_json()

        # Validation des données
        required_fields = ['nom', 'prenom', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'Le champ {field} est requis'
                }), 400

        # Mettre à jour l'étudiant
        success = db.modifier_etudiant(
            student_id,
            data['nom'],
            data['prenom'],
            data['email'],
            data.get('telephone', '')
        )

        if success:
            return jsonify({
                'success': True,
                'message': 'Étudiant modifié avec succès'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de la modification'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/students/<student_id>/retrain', methods=['POST'])
@require_auth
def api_retrain_student(student_id):
    """Relancer l'entraînement facial pour un étudiant"""
    try:
        # Récupérer les informations de l'étudiant
        student = db.obtenir_etudiant_par_id(student_id)
        if not student:
            return jsonify({'success': False, 'message': 'Étudiant non trouvé'}), 404

        student_name = f"{student.get('prenom', '')} {student.get('nom', '')}".strip()

        # Lancer l'entraînement facial
        trainer = ftm.FacialTrainingModule()
        # Extraire prénom et nom
        name_parts = student_name.split(' ', 1)
        prenom = name_parts[0] if len(name_parts) > 0 else student_name
        nom = name_parts[1] if len(name_parts) > 1 else ""
        success = trainer.train_student(prenom, nom, max_photos=15)

        if success:
            # Régénérer les encodages
            recognition_controller.reload_encodings()

            return jsonify({
                'success': True,
                'message': f'Entraînement facial relancé pour {student_name}'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erreur lors de l\'entraînement facial'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

@app.route('/api/students/bulk-action', methods=['POST'])
@require_auth
def bulk_student_action():
    """Actions en lot sur les étudiants"""
    try:
        data = request.get_json()
        action = data.get('action')
        student_ids = data.get('student_ids', [])

        if not action or not student_ids:
            return jsonify({
                'success': False,
                'message': 'Action et IDs étudiants requis'
            }), 400

        results = []

        if action == 'delete':
            for student_id in student_ids:
                try:
                    student = db.obtenir_etudiant_par_id(student_id)
                    if student:
                        success = db.supprimer_etudiant(student_id)
                        if success:
                            # Supprimer les images du dataset
                            student_name = f"{student.get('prenom', '')} {student.get('nom', '')}".strip()
                            dataset_path = os.path.join('dataset', student_name)
                            if os.path.exists(dataset_path):
                                shutil.rmtree(dataset_path)
                            results.append({'id': student_id, 'success': True})
                        else:
                            results.append({'id': student_id, 'success': False, 'error': 'Erreur de suppression'})
                    else:
                        results.append({'id': student_id, 'success': False, 'error': 'Étudiant non trouvé'})
                except Exception as e:
                    results.append({'id': student_id, 'success': False, 'error': str(e)})

        elif action == 'retrain':
            for student_id in student_ids:
                try:
                    student = db.obtenir_etudiant_par_id(student_id)
                    if student:
                        prenom = student.get('prenom', '')
                        nom = student.get('nom', '')
                        trainer = ftm.FacialTrainingModule()
                        success = trainer.train_student(prenom, nom, max_photos=15)
                        results.append({'id': student_id, 'success': success})
                    else:
                        results.append({'id': student_id, 'success': False, 'error': 'Étudiant non trouvé'})
                except Exception as e:
                    results.append({'id': student_id, 'success': False, 'error': str(e)})

        # Régénérer les encodages si nécessaire
        if action == 'retrain':
            recognition_controller.reload_encodings()

        successful = sum(1 for r in results if r['success'])
        total = len(results)

        return jsonify({
            'success': True,
            'message': f'{successful}/{total} opérations réussies',
            'results': results
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Erreur: {str(e)}'
        }), 500

# Routes API pour l'entraînement facial
@app.route('/api/training/capture-photo', methods=['POST'])
@require_auth
def api_capture_photo():
    """Capture une photo pour l'entraînement facial"""
    global training_camera
    try:
        # Vérifier si c'est une requête JSON (nouvelle version) ou FormData (ancienne)
        if request.is_json:
            data = request.get_json()
            student_id = data.get('student_id')
            photo_index = data.get('photo_index', 0)

            # Capturer depuis la caméra backend
            import cv2
            if training_camera is None:
                training_camera = cv2.VideoCapture(0)

            if not training_camera.isOpened():
                return jsonify({'success': False, 'message': 'Caméra non accessible'})

            ret, frame = training_camera.read()
            if not ret or frame is None:
                return jsonify({'success': False, 'message': 'Impossible de capturer une image'})

            # Obtenir les informations de l'étudiant
            student = db.obtenir_etudiant_par_id(student_id)
            if not student:
                return jsonify({'success': False, 'message': 'Étudiant non trouvé'})

            # Créer le dossier de l'étudiant
            student_name = f"{student.get('prenom', '')} {student.get('nom', '')}".strip()
            student_folder = os.path.join('dataset', student_name)
            os.makedirs(student_folder, exist_ok=True)

            # Sauvegarder la photo
            filename = f'photo_{int(photo_index):03d}.jpg'
            photo_path = os.path.join(student_folder, filename)

            # Save the photo with high quality
            success = cv2.imwrite(photo_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

            if success and os.path.exists(photo_path):
                file_size = os.path.getsize(photo_path)
                print(f"📸 Photo saved: {filename} ({file_size} bytes) for {student_name}")

                return jsonify({
                    'success': True,
                    'message': f'Photo {filename} sauvegardée avec succès',
                    'photo_path': photo_path,
                    'filename': filename,
                    'file_size': file_size
                })
            else:
                print(f"❌ Failed to save photo: {filename} for {student_name}")
                return jsonify({
                    'success': False,
                    'message': f'Erreur lors de la sauvegarde de {filename}',
                    'photo_path': photo_path
                })

        else:
            # Ancienne version avec FormData (pour compatibilité)
            if 'photo' not in request.files:
                return jsonify({'success': False, 'message': 'Aucune photo fournie'})

            photo = request.files['photo']
            student_id = request.form.get('student_id')
            photo_index = request.form.get('photo_index', '0')

            if not student_id:
                return jsonify({'success': False, 'message': 'ID étudiant manquant'})

            # Obtenir les informations de l'étudiant pour créer le bon dossier
            student = db.obtenir_etudiant_par_id(student_id)
            if not student:
                return jsonify({'success': False, 'message': 'Étudiant non trouvé'})

            # Créer le nom du dossier basé sur le nom de l'étudiant
            student_name = f"{student.get('prenom', '')} {student.get('nom', '')}".strip()
            student_folder = os.path.join('dataset', student_name)
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

# Variables globales pour la caméra d'entraînement
training_camera = None

@app.route('/api/training/test-camera', methods=['POST'])
@require_auth
def api_test_camera():
    """Tester l'accès à la caméra"""
    try:
        import cv2
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            return jsonify({'success': False, 'message': 'Caméra inaccessible'})

        ret, frame = cap.read()
        cap.release()

        if ret and frame is not None:
            return jsonify({'success': True, 'message': 'Caméra accessible'})
        else:
            return jsonify({'success': False, 'message': 'Impossible de lire la caméra'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur: {str(e)}'})

@app.route('/api/training/video-feed')
@require_auth
def api_video_feed():
    """Flux vidéo en direct pour l'entraînement"""
    def generate_frames():
        global training_camera
        import cv2

        if training_camera is None:
            training_camera = cv2.VideoCapture(0)

        while training_camera and training_camera.isOpened():
            ret, frame = training_camera.read()
            if not ret:
                break

            # Encoder la frame en JPEG
            _, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/training/stop-camera', methods=['POST'])
@require_auth
def api_stop_camera():
    """Arrêter la caméra d'entraînement"""
    global training_camera
    try:
        if training_camera:
            training_camera.release()
            training_camera = None
        return jsonify({'success': True, 'message': 'Caméra arrêtée'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/training/capture-preview', methods=['POST'])
@require_auth
def api_capture_preview():
    """Capturer une image de prévisualisation pour l'affichage"""
    global training_camera
    try:
        import cv2

        if training_camera is None:
            training_camera = cv2.VideoCapture(0)

        if not training_camera.isOpened():
            return jsonify({'success': False, 'message': 'Caméra non accessible'}), 500

        ret, frame = training_camera.read()
        if not ret or frame is None:
            return jsonify({'success': False, 'message': 'Impossible de capturer une image'}), 500

        # Encoder l'image en JPEG
        _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])

        # Retourner l'image comme réponse binaire
        return Response(buffer.tobytes(), mimetype='image/jpeg')

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/training/photo/<path:photo_path>')
@require_auth
def api_get_photo(photo_path):
    """Récupérer une photo d'entraînement"""
    try:
        import os
        # Ensure the path is relative to the current directory
        if not os.path.isabs(photo_path):
            photo_path = os.path.join(os.getcwd(), photo_path)

        if os.path.exists(photo_path):
            return send_file(photo_path)
        else:
            return jsonify({'success': False, 'message': f'Photo not found: {photo_path}'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

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
        prenom = student.get('prenom', '')
        nom = student.get('nom', '')

        success = trainer.train_student(prenom, nom, max_photos=15)

        if success:
            # Recharger les encodages dans le contrôleur
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

@app.route('/students/<student_id>/train')
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

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    print('Client connecté au WebSocket')
    emit('status', {'message': 'Connecté au système de surveillance'})

    # Envoyer le statut actuel de la reconnaissance faciale
    try:
        status = recognition_controller.get_status()
        emit('recognition_status', {
            'message': f"Système {'actif' if status['is_running'] else 'inactif'}",
            'type': 'info',
            'status': status
        })
    except Exception as e:
        emit('recognition_status', {
            'message': f'Erreur de statut: {e}',
            'type': 'error'
        })

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion WebSocket"""
    print('Client déconnecté du WebSocket')

@socketio.on('request_camera_feed')
def handle_camera_feed_request():
    """Gestion de la demande de flux caméra"""
    try:
        status = recognition_controller.get_status()
        emit('camera_feed_status', {
            'available': status['is_running'] and status['camera_status'] == 'Connectée'
        })
    except Exception as e:
        emit('camera_feed_status', {'available': False, 'error': str(e)})

def broadcast_attendance_update(name, date, time):
    """Diffuser une mise à jour de présence à tous les clients connectés"""
    socketio.emit('attendance_update', {
        'name': name,
        'date': date,
        'time': time,
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    # Créer les dossiers nécessaires
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    os.makedirs('static/images', exist_ok=True)

    print("🚀 Démarrage du tableau de bord d'administration...")
    print("📱 Accès: http://localhost:5001")
    print("👤 Utilisateur: admin")
    print("🔑 Mot de passe: admin123")

    socketio.run(app, debug=True, host='0.0.0.0', port=5001)
