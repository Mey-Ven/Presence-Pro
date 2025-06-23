#!/usr/bin/env python3
"""
Routes pour la Reconnaissance Faciale
Intègre les fonctionnalités de reconnaissance faciale avec l'interface web

Author: Facial Attendance System
Date: 2025-06-23
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash, Response
from auth_manager import login_required, role_required, get_current_user
from facial_recognition_system import facial_recognition_system
from video_streaming import get_video_streamer
import os
import json
from datetime import datetime, date
import time

# Créer le blueprint
facial_bp = Blueprint('facial', __name__, url_prefix='/facial')

@facial_bp.route('/capture/<student_id>')
@login_required
@role_required('admin', 'teacher')
def capture_student(student_id):
    """Page de capture d'images pour un étudiant"""
    user = get_current_user()
    
    # Vérifier que l'étudiant existe
    from enhanced_database import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT first_name, last_name FROM users WHERE id = ? AND role = "student"', (student_id,))
    student = cursor.fetchone()
    conn.close()
    
    if not student:
        flash('Étudiant non trouvé', 'error')
        return redirect(url_for('admin_enhanced.users'))
    
    student_info = {
        'id': student_id,
        'first_name': student[0],
        'last_name': student[1],
        'full_name': f"{student[0]} {student[1]}"
    }
    
    return render_template('facial/capture.html', student=student_info)

@facial_bp.route('/api/capture/<student_id>', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_capture_student(student_id):
    """API pour capturer des images d'un étudiant"""
    try:
        data = request.get_json()
        num_images = data.get('num_images', 5)
        
        success, message = facial_recognition_system.capture_student_image(student_id, num_images)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/train/<student_id>', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_train_student(student_id):
    """API pour entraîner les encodages faciaux d'un étudiant"""
    try:
        success, message = facial_recognition_system.train_student_encodings(student_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/recognition')
@login_required
@role_required('admin', 'teacher')
def recognition_control():
    """Page de contrôle de la reconnaissance faciale"""
    user = get_current_user()
    
    # Obtenir l'état actuel du système
    is_running = facial_recognition_system.is_running
    current_session = facial_recognition_system.current_session_id
    
    # Obtenir les présences d'aujourd'hui
    today_attendance = facial_recognition_system.get_today_attendance()
    
    return render_template('facial/recognition.html', 
                         is_running=is_running,
                         current_session=current_session,
                         today_attendance=today_attendance)

@facial_bp.route('/api/start_recognition', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_start_recognition():
    """API pour démarrer la reconnaissance faciale"""
    try:
        user = get_current_user()
        data = request.get_json()
        
        session_name = data.get('session_name', f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        course_id = data.get('course_id')
        
        success, message = facial_recognition_system.start_recognition_session(
            session_name=session_name,
            course_id=course_id,
            created_by=user['id']
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/stop_recognition', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_stop_recognition():
    """API pour arrêter la reconnaissance faciale"""
    try:
        success, message = facial_recognition_system.stop_recognition_session()
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/recognition_status')
@login_required
def api_recognition_status():
    """API pour obtenir l'état de la reconnaissance faciale"""
    try:
        status = {
            'is_running': facial_recognition_system.is_running,
            'current_session_id': facial_recognition_system.current_session_id,
            'known_faces_count': len(facial_recognition_system.known_face_encodings),
            'today_attendance_count': len(facial_recognition_system.get_today_attendance())
        }
        
        return jsonify({'success': True, 'status': status})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500



@facial_bp.route('/students')
@login_required
@role_required('admin', 'teacher')
def students_management():
    """Page de gestion des étudiants pour la reconnaissance faciale"""
    from enhanced_database import get_connection
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Obtenir tous les étudiants avec leur statut d'encodage
    cursor.execute('''
        SELECT u.id, u.first_name, u.last_name, u.email,
               (SELECT COUNT(*) FROM facial_encodings WHERE student_id = u.id) as has_encoding
        FROM users u
        WHERE u.role = 'student' AND u.is_active = 1
        ORDER BY u.last_name, u.first_name
    ''')
    
    students = []
    for row in cursor.fetchall():
        students.append({
            'id': row[0],
            'first_name': row[1],
            'last_name': row[2],
            'email': row[3],
            'full_name': f"{row[1]} {row[2]}",
            'has_encoding': row[4] > 0,
            'encoding_count': row[4]
        })
    
    conn.close()
    
    return render_template('facial/students.html', students=students)

@facial_bp.route('/api/reload_encodings', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_reload_encodings():
    """API pour recharger les encodages faciaux"""
    try:
        facial_recognition_system.load_encodings()
        count = len(facial_recognition_system.known_face_encodings)
        
        return jsonify({
            'success': True, 
            'message': f'{count} encodages rechargés avec succès',
            'count': count
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/delete_encoding/<student_id>', methods=['DELETE'])
@login_required
@role_required('admin', 'teacher')
def api_delete_encoding(student_id):
    """API pour supprimer l'encodage facial d'un étudiant"""
    try:
        from enhanced_database import get_connection
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Supprimer l'encodage de la base de données
        cursor.execute('DELETE FROM facial_encodings WHERE student_id = ?', (student_id,))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        # Recharger les encodages
        facial_recognition_system.load_encodings()
        
        if deleted_count > 0:
            return jsonify({'success': True, 'message': 'Encodage supprimé avec succès'})
        else:
            return jsonify({'success': False, 'message': 'Aucun encodage trouvé pour cet étudiant'}), 404
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/attendance_history')
@login_required
def attendance_history():
    """Page d'historique des présences par reconnaissance faciale"""
    from enhanced_database import get_connection
    
    # Obtenir les paramètres de filtre
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')
    student_id = request.args.get('student_id', '')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Construire la requête avec filtres
    query = '''
        SELECT p.*, u.first_name, u.last_name
        FROM presences p
        JOIN users u ON p.student_id = u.id
        WHERE 1=1
    '''
    params = []
    
    if start_date:
        query += ' AND p.date >= ?'
        params.append(start_date)
    
    if end_date:
        query += ' AND p.date <= ?'
        params.append(end_date)
    
    if student_id:
        query += ' AND p.student_id = ?'
        params.append(student_id)
    
    query += ' ORDER BY p.date DESC, p.time DESC LIMIT 100'
    
    cursor.execute(query, params)
    
    attendance_records = []
    for row in cursor.fetchall():
        attendance_records.append({
            'id': row[0],
            'student_id': row[1],
            'course_id': row[2],
            'date': row[3],
            'time': row[4],
            'status': row[5],
            'confidence': row[6],
            'created_at': row[7],
            'student_name': f"{row[8]} {row[9]}"
        })
    
    # Obtenir la liste des étudiants pour le filtre
    cursor.execute('''
        SELECT id, first_name, last_name
        FROM users
        WHERE role = 'student' AND is_active = 1
        ORDER BY last_name, first_name
    ''')
    
    students = []
    for row in cursor.fetchall():
        students.append({
            'id': row[0],
            'full_name': f"{row[1]} {row[2]}"
        })
    
    conn.close()
    
    return render_template('facial/attendance_history.html',
                         attendance_records=attendance_records,
                         students=students,
                         start_date=start_date,
                         end_date=end_date,
                         selected_student_id=student_id)

@facial_bp.route('/api/camera_test')
@login_required
@role_required('admin', 'teacher')
def api_camera_test():
    """API pour tester l'accès à la caméra"""
    try:
        import cv2
        camera = cv2.VideoCapture(0)

        if camera.isOpened():
            ret, frame = camera.read()
            camera.release()

            if ret:
                return jsonify({'success': True, 'message': 'Caméra accessible et fonctionnelle'})
            else:
                return jsonify({'success': False, 'message': 'Caméra accessible mais aucune image captée'})
        else:
            return jsonify({'success': False, 'message': 'Impossible d\'accéder à la caméra'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Erreur de caméra: {str(e)}'})

@facial_bp.route('/api/start_streaming', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_start_streaming():
    """API pour démarrer le streaming vidéo"""
    try:
        streamer = get_video_streamer(facial_recognition_system)
        success, message = streamer.start_streaming()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/stop_streaming', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_stop_streaming():
    """API pour arrêter le streaming vidéo"""
    try:
        streamer = get_video_streamer(facial_recognition_system)
        success, message = streamer.stop_streaming()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/enable_detection', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_enable_detection():
    """API pour activer la détection faciale"""
    try:
        streamer = get_video_streamer(facial_recognition_system)
        success, message = streamer.enable_detection()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/disable_detection', methods=['POST'])
@login_required
@role_required('admin', 'teacher')
def api_disable_detection():
    """API pour désactiver la détection faciale"""
    try:
        streamer = get_video_streamer(facial_recognition_system)
        success, message = streamer.disable_detection()

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/video_feed')
@login_required
@role_required('admin', 'teacher')
def video_feed():
    """Stream vidéo en temps réel"""
    def generate_frames():
        streamer = get_video_streamer(facial_recognition_system)

        while True:
            frame_base64 = streamer.get_current_frame_base64()

            if frame_base64:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' +
                       base64.b64decode(frame_base64) + b'\r\n')
            else:
                # Frame par défaut si pas de caméra
                yield (b'--frame\r\n'
                       b'Content-Type: text/plain\r\n\r\n'
                       b'No camera feed available\r\n')

            time.sleep(0.033)  # ~30 FPS

    return Response(generate_frames(),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

@facial_bp.route('/api/streaming_status')
@login_required
@role_required('admin', 'teacher')
def api_streaming_status():
    """API pour obtenir l'état du streaming avec statistiques complètes"""
    try:
        streamer = get_video_streamer(facial_recognition_system)
        status = streamer.get_detection_info()

        # Ajouter les statistiques de présence
        conn = get_connection()
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT COUNT(*) FROM presences
            WHERE date = ?
        ''', (today,))
        today_count = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM presences')
        total_count = cursor.fetchone()[0]

        # Ajouter les informations supplémentaires
        status.update({
            'today_attendance_count': today_count,
            'total_detections': total_count,
            'camera_index': 0,  # Caméra par défaut (FaceTime HD)
            'known_faces_count': len(facial_recognition_system.known_face_encodings),
            'system_ready': len(facial_recognition_system.known_face_encodings) > 0
        })

        conn.close()

        return jsonify({'success': True, 'status': status})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@facial_bp.route('/api/today_attendance_live')
@login_required
@role_required('admin', 'teacher')
def api_today_attendance_live():
    """API pour obtenir les présences d'aujourd'hui"""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        today = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            SELECT p.time, u.first_name, u.last_name, p.detection_confidence, p.status
            FROM presences p
            JOIN users u ON p.student_id = u.id
            WHERE p.date = ?
            ORDER BY p.time DESC
        ''', (today,))

        results = cursor.fetchall()
        attendance = []

        for row in results:
            attendance.append({
                'time': row[0],
                'student_name': f"{row[1]} {row[2]}",
                'confidence': row[3],
                'status': row[4]
            })

        conn.close()

        return jsonify({
            'success': True,
            'attendance': attendance,
            'count': len(attendance)
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
