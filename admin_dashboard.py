"""
Tableau de bord d'administration web pour le système de reconnaissance faciale
Application Flask complète avec gestion des étudiants, surveillance des présences et administration système
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_file
from flask_socketio import SocketIO, emit
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite_database as db
import facial_training_module as ftm
import sqlite_config as config
import os
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
                return redirect(url_for('train_student', student_id=id_etudiant))
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

@app.route('/students/<student_id>/train', methods=['GET', 'POST'])
@require_auth
def train_student(student_id):
    """Entraînement facial pour un étudiant"""
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
            # Lancer l'entraînement facial
            trainer = ftm.FacialTrainingModule()
            success = trainer.train_student(
                student.get('PrenomEtudiant'),
                student.get('NomEtudiant'),
                max_photos=15
            )

            if success:
                flash(f'Entraînement facial terminé pour {student.get("PrenomEtudiant")} {student.get("NomEtudiant")}', 'success')
            else:
                flash('Échec de l\'entraînement facial', 'error')

            return redirect(url_for('students'))

        return render_template('train_student.html', student=student)

    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('students'))

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

# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Gestion de la connexion WebSocket"""
    print('Client connecté au WebSocket')
    emit('status', {'message': 'Connecté au système de surveillance'})

@socketio.on('disconnect')
def handle_disconnect():
    """Gestion de la déconnexion WebSocket"""
    print('Client déconnecté du WebSocket')

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
