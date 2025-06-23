#!/usr/bin/env python3
"""
Parent Dashboard Module
======================

This module provides comprehensive functionality for the parent dashboard including:
- Access to child's information (schedule, attendance, grades)
- Absence justification management
- Communication with school administration and teachers
- Notifications about child's attendance and academic performance

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
from datetime import datetime, timedelta
import uuid
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from auth_manager import login_required, role_required, get_current_user, log_audit_trail

DATABASE_FILE = "attendance.db"

# Create Blueprint for parent routes
parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_FILE)

@parent_bp.route('/dashboard')
@login_required
@role_required('parent')
def dashboard():
    """Parent dashboard main page"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])

    # Si parent_info est None, créer des informations par défaut
    if not parent_info:
        parent_info = {
            'id_parent': user['id'],
            'first_name': user.get('first_name', 'Parent'),
            'last_name': user.get('last_name', 'Utilisateur'),
            'full_name': f"{user.get('first_name', 'Parent')} {user.get('last_name', 'Utilisateur')}",
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'address': 'Non renseigné',
            'emergency_contact': user.get('phone', ''),
            'occupation': 'Non renseigné',
            'relationship_to_student': 'Parent'
        }

    # Get parent's children
    children = get_parent_children(parent_info['id_parent'])

    # Get summary information for all children
    children_summary = []
    for child in children:
        # Utiliser 'id' au lieu de 'id_student' pour la nouvelle structure
        child_id = child.get('id') or child.get('id_student')
        if child_id:
            child_summary = {
                'info': child,
                'attendance_stats': get_student_attendance_stats(child_id),
                'recent_attendance': get_student_attendance_history(child_id, limit=3),
                'pending_justifications': get_student_justifications(child_id, status='pending')
            }
            children_summary.append(child_summary)

    # Get unread messages
    unread_messages = get_parent_messages(user['id'], unread_only=True)

    return render_template('parent/dashboard.html',
                         parent=parent_info,
                         children=children_summary,
                         unread_messages=unread_messages)

@parent_bp.route('/child/<child_id>')
@login_required
@role_required('parent')
def child_details(child_id):
    """Detailed view for specific child"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])

    # Si parent_info est None, utiliser l'ID utilisateur
    if not parent_info:
        parent_id = user['id']
    else:
        parent_id = parent_info['id_parent']

    # Verify parent has access to this child
    child_info = get_child_info(child_id, parent_id)
    if not child_info:
        flash('Access denied or child not found.', 'error')
        return redirect(url_for('parent.dashboard'))

    # Get child's schedule
    child_schedule = get_student_weekly_schedule(child_id)

    # Get child's attendance history
    attendance_history = get_student_attendance_history(child_id, limit=20)

    # Get child's grades
    child_grades = get_student_grades(child_id)

    # Get attendance statistics
    attendance_stats = get_student_attendance_stats(child_id)

    return render_template('parent/child_details.html',
                         parent=parent_info,
                         child=child_info,
                         schedule=child_schedule,
                         attendance=attendance_history,
                         grades=child_grades,
                         attendance_stats=attendance_stats)

@parent_bp.route('/justification')
@login_required
@role_required('parent')
def justification():
    """Parent justification management page"""
    user = get_current_user()
    parent_id = user['id']

    # Obtenir les enfants du parent
    children = get_parent_children(parent_id)

    # Obtenir l'enfant sélectionné
    selected_child_id = request.args.get('child_id')
    if not selected_child_id and children:
        selected_child_id = children[0]['id']

    # Obtenir les justifications pour l'enfant sélectionné
    justifications = []
    if selected_child_id:
        justifications = get_child_justifications(selected_child_id)

    return render_template('parent/justification.html',
                         children=children,
                         selected_child_id=selected_child_id,
                         justifications=justifications)

@parent_bp.route('/submit_justification', methods=['POST'])
@login_required
@role_required('parent')
def submit_justification():
    """Submit absence justification for child"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])
    
    try:
        data = request.get_json()
        
        # Verify parent has access to this child
        child_info = get_child_info(data['student_id'], parent_info['id_parent'])
        if not child_info:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        justification_id = str(uuid.uuid4())
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO justifications
            (id, student_id, absence_date, reason, description, parent_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (justification_id, data['student_id'], data['absence_date'],
              data['reason'], data.get('description', ''), user['id']))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'CREATE', 'justifications', justification_id,
                       None, data)
        
        return jsonify({'success': True, 'message': 'Justification submitted successfully'})
        
    except Exception as e:
        print(f"Error submitting justification: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@parent_bp.route('/approve_justification/<justification_id>', methods=['POST'])
@login_required
@role_required('parent')
def approve_justification(justification_id):
    """Approve child's justification request"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify parent has access to this justification
        cursor.execute('''
            SELECT j.* FROM justifications j
            JOIN parent_children pc ON j.student_id = pc.child_id
            WHERE j.id = ? AND pc.parent_id = ?
        ''', (justification_id, parent_info['id_parent']))
        
        justification = cursor.fetchone()
        if not justification:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update justification status
        cursor.execute('''
            UPDATE justifications
            SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (user['id'], justification_id))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'UPDATE', 'justifications', justification_id,
                       {'status': 'pending'}, {'status': 'approved'})
        
        return jsonify({'success': True, 'message': 'Justification approved successfully'})
        
    except Exception as e:
        print(f"Error approving justification: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@parent_bp.route('/messages')
@login_required
@role_required('parent')
def messages():
    """Parent messages page"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])
    
    # Get all messages
    all_messages = get_parent_messages(user['id'])
    
    # Get teachers for messaging
    teachers = get_all_teachers()
    
    return render_template('parent/messages.html',
                         parent=parent_info,
                         messages=all_messages,
                         teachers=teachers)

@parent_bp.route('/send_message', methods=['POST'])
@login_required
@role_required('parent')
def send_message():
    """Send message to teacher or admin"""
    user = get_current_user()
    
    try:
        data = request.get_json()
        
        message_id = str(uuid.uuid4())
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO messages 
            (id_message, sender_id, recipient_id, subject, content, message_type)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (message_id, user['id'], data['recipient_id'], data['subject'], 
              data['content'], data.get('message_type', 'general')))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'CREATE', 'messages', message_id, None, data)
        
        return jsonify({'success': True, 'message': 'Message sent successfully'})
        
    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@parent_bp.route('/notifications')
@login_required
@role_required('parent')
def notifications():
    """Parent notifications page"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])
    
    # Get notifications
    user_notifications = get_parent_notifications(user['id'])
    
    return render_template('parent/notifications.html',
                         parent=parent_info,
                         notifications=user_notifications)

# Helper functions

def get_parent_info(user_id):
    """Get parent information by user ID"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Try parents table first (new structure)
        cursor.execute('''
            SELECT p.id_parent, p.address, p.emergency_contact, p.occupation, p.relationship_to_student,
                   u.first_name, u.last_name, u.email, u.phone
            FROM parents p
            JOIN users u ON p.user_id = u.id
            WHERE p.user_id = ?
        ''', (user_id,))

        result = cursor.fetchone()
        if result:
            return {
                'id_parent': result[0],
                'address': result[1],
                'emergency_contact': result[2],
                'occupation': result[3],
                'relationship_to_student': result[4],
                'first_name': result[5],
                'last_name': result[6],
                'email': result[7],
                'phone': result[8],
                'full_name': f"{result[5]} {result[6]}"
            }

        # Fallback to parents table (compatibility structure)
        cursor.execute('''
            SELECT p.id_parent, u.first_name, u.last_name, u.email, u.phone
            FROM parents p
            JOIN users u ON p.id_parent = u.id
            WHERE p.id_parent = ?
        ''', (user_id,))

        result = cursor.fetchone()
        if result:
            return {
                'id_parent': result[0],
                'address': 'Non renseigné',
                'emergency_contact': result[4],
                'occupation': 'Non renseigné',
                'relationship_to_student': 'Parent',
                'first_name': result[1],
                'last_name': result[2],
                'email': result[3],
                'phone': result[4],
                'full_name': f"{result[1]} {result[2]}"
            }

        # If not found in either table, create basic parent info
        cursor.execute('SELECT first_name, last_name, email, phone FROM users WHERE id = ? AND role = "parent"', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'id_parent': user_id,
                'address': 'Non renseigné',
                'emergency_contact': result[3],
                'occupation': 'Non renseigné',
                'relationship_to_student': 'Parent',
                'first_name': result[0],
                'last_name': result[1],
                'email': result[2],
                'phone': result[3],
                'full_name': f"{result[0]} {result[1]}"
            }

        return None

    except Exception as e:
        print(f"Error getting parent info: {e}")
        return None
    finally:
        conn.close()

def get_parent_children(parent_id):
    """Get all children for a parent"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Essayer d'abord avec la nouvelle table parent_children
        cursor.execute('''
            SELECT u.id, u.first_name, u.last_name, u.email, u.role
            FROM parent_children pc
            JOIN users u ON pc.child_id = u.id
            WHERE pc.parent_id = ? AND u.is_active = 1
            ORDER BY u.first_name, u.last_name
        ''', (parent_id,))

        results = cursor.fetchall()
        children = []

        for row in results:
            children.append({
                'id': row[0],
                'first_name': row[1],
                'last_name': row[2],
                'email': row[3],
                'role': row[4],
                'full_name': f"{row[1]} {row[2]}",
                'class_name': 'Master IA'  # Valeur par défaut
            })

        # Si aucun enfant trouvé, essayer l'ancienne structure
        if not children:
            cursor.execute('''
                SELECT se.id_student, se.etudiant_id, se.class_name, se.enrollment_date,
                       u.first_name, u.last_name, u.email,
                       e.nom, e.prenom
                FROM students_extended se
                JOIN users u ON se.user_id = u.id
                LEFT JOIN etudiants e ON se.etudiant_id = e.id_etudiant
                WHERE se.parent_id = ? AND se.status = 'active'
                ORDER BY u.first_name, u.last_name
            ''', (parent_id,))

            results = cursor.fetchall()

            for row in results:
                children.append({
                    'id': row[0],
                    'id_student': row[0],
                    'etudiant_id': row[1],
                    'class_name': row[2],
                    'enrollment_date': row[3],
                    'first_name': row[4],
                    'last_name': row[5],
                    'email': row[6],
                    'full_name': f"{row[4]} {row[5]}"
                })

        return children

    except Exception as e:
        print(f"Error getting parent children: {e}")
        return []
    finally:
        conn.close()

def get_child_justifications(child_id):
    """Get justifications for a specific child"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT id, student_id, absence_date, reason, description, status, created_at
            FROM justifications
            WHERE student_id = ?
            ORDER BY created_at DESC
        ''', (child_id,))

        results = cursor.fetchall()
        justifications = []

        for row in results:
            justifications.append({
                'id': row[0],
                'student_id': row[1],
                'absence_date': row[2],
                'reason': row[3],
                'description': row[4],
                'status': row[5],
                'created_at': row[6]
            })

        return justifications

    except Exception as e:
        print(f"Error getting child justifications: {e}")
        return []
    finally:
        conn.close()

def get_child_info(child_id, parent_id):
    """Get child information with parent verification"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT se.id_student, se.etudiant_id, se.class_name, se.enrollment_date,
                   u.first_name, u.last_name, u.email, u.phone
            FROM students_extended se
            JOIN users u ON se.user_id = u.id
            WHERE se.id_student = ? AND se.parent_id = ?
        ''', (child_id, parent_id))
        
        result = cursor.fetchone()
        if result:
            return {
                'id_student': result[0],
                'etudiant_id': result[1],
                'class_name': result[2],
                'enrollment_date': result[3],
                'first_name': result[4],
                'last_name': result[5],
                'email': result[6],
                'phone': result[7],
                'full_name': f"{result[4]} {result[5]}"
            }
        return None
        
    except Exception as e:
        print(f"Error getting child info: {e}")
        return None
    finally:
        conn.close()

def get_parent_messages(user_id, unread_only=False):
    """Get messages for parent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        query = '''
            SELECT m.id_message, m.subject, m.content, m.message_type, m.is_read, 
                   m.is_urgent, m.sent_at, m.read_at,
                   u.first_name || ' ' || u.last_name as sender_name
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.recipient_id = ?
        '''
        
        if unread_only:
            query += ' AND m.is_read = 0'
        
        query += ' ORDER BY m.sent_at DESC'
        
        cursor.execute(query, (user_id,))
        results = cursor.fetchall()
        
        messages = []
        for row in results:
            messages.append({
                'id_message': row[0],
                'subject': row[1],
                'content': row[2],
                'message_type': row[3],
                'is_read': row[4],
                'is_urgent': row[5],
                'sent_at': row[6],
                'read_at': row[7],
                'sender_name': row[8]
            })
        
        return messages
        
    except Exception as e:
        print(f"Error getting parent messages: {e}")
        return []
    finally:
        conn.close()

def get_all_teachers():
    """Get all teachers for messaging"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT u.id, u.first_name || ' ' || u.last_name as full_name, t.department
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE u.is_active = 1
            ORDER BY u.last_name, u.first_name
        ''')
        
        results = cursor.fetchall()
        teachers = []
        
        for row in results:
            teachers.append({
                'id': row[0],
                'full_name': row[1],
                'department': row[2]
            })
        
        return teachers
        
    except Exception as e:
        print(f"Error getting teachers: {e}")
        return []
    finally:
        conn.close()

def get_parent_notifications(user_id):
    """Get notifications for parent"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id_notification, title, content, notification_type, is_read, 
                   action_url, created_at, expires_at
            FROM notifications
            WHERE user_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        notifications = []
        
        for row in results:
            notifications.append({
                'id_notification': row[0],
                'title': row[1],
                'content': row[2],
                'notification_type': row[3],
                'is_read': row[4],
                'action_url': row[5],
                'created_at': row[6],
                'expires_at': row[7]
            })
        
        return notifications
        
    except Exception as e:
        print(f"Error getting parent notifications: {e}")
        return []
    finally:
        conn.close()

# Import helper functions from student_dashboard
def get_student_attendance_stats(student_id):
    """Get attendance statistics for a student"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get attendance statistics directly by student_id
        cursor.execute('''
            SELECT
                COUNT(*) as total_days,
                COUNT(DISTINCT date) as unique_days,
                MIN(date) as first_attendance,
                MAX(date) as last_attendance
            FROM presences
            WHERE student_id = ?
        ''', (student_id,))

        result = cursor.fetchone()
        if result:
            total_days = result[0] or 0
            unique_days = result[1] or 0

            # Calculate attendance rate (assuming 30 days in a month)
            expected_days = 30
            attendance_rate = (unique_days / expected_days * 100) if expected_days > 0 else 0

            return {
                'total_days': total_days,
                'unique_days': unique_days,
                'attendance_rate': round(attendance_rate, 1),
                'first_attendance': result[2],
                'last_attendance': result[3]
            }

        return {
            'total_days': 0,
            'unique_days': 0,
            'attendance_rate': 0,
            'first_attendance': None,
            'last_attendance': None
        }

    except Exception as e:
        print(f"Error getting student attendance stats: {e}")
        return {
            'total_days': 0,
            'unique_days': 0,
            'attendance_rate': 0,
            'first_attendance': None,
            'last_attendance': None
        }
    finally:
        conn.close()

def get_student_attendance_history(student_id, limit=10):
    """Get attendance history for a student"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT date, time, status, detection_confidence
            FROM presences
            WHERE student_id = ?
            ORDER BY date DESC, time DESC
            LIMIT ?
        ''', (student_id, limit))

        results = cursor.fetchall()
        attendance = []

        for row in results:
            attendance.append({
                'date': row[0],
                'time': row[1],
                'status': row[2],
                'detection_confidence': row[3]
            })

        return attendance

    except Exception as e:
        print(f"Error getting student attendance history: {e}")
        return []
    finally:
        conn.close()

def get_student_justifications(student_id, status=None):
    """Get justifications for a student"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = '''
            SELECT id, absence_date, reason, description, status,
                   created_at, reviewed_at, ''
            FROM justifications
            WHERE student_id = ?
        '''

        params = [student_id]

        if status:
            query += ' AND status = ?'
            params.append(status)

        query += ' ORDER BY created_at DESC'

        cursor.execute(query, params)
        results = cursor.fetchall()

        justifications = []
        for row in results:
            justifications.append({
                'id': row[0],
                'absence_date': row[1],
                'reason': row[2],
                'description': row[3],
                'status': row[4],
                'created_at': row[5],
                'reviewed_at': row[6],
                'review_comments': row[7] if row[7] else ''
            })

        return justifications

    except Exception as e:
        print(f"Error getting student justifications: {e}")
        return []
    finally:
        conn.close()

def get_student_grades(student_id):
    """Get grades for a student"""
    # Retourner des données d'exemple pour l'instant
    return [
        {
            'course_name': 'Intelligence Artificielle',
            'assessment_name': 'Examen Final',
            'grade_letter': 'A',
            'points_earned': 85,
            'points_possible': 100,
            'percentage': 85,
            'assessment_date': '2024-12-15'
        },
        {
            'course_name': 'Machine Learning',
            'assessment_name': 'Projet',
            'grade_letter': 'B+',
            'points_earned': 78,
            'points_possible': 100,
            'percentage': 78,
            'assessment_date': '2024-12-10'
        }
    ]

def get_student_weekly_schedule(student_id):
    """Get weekly schedule for a student"""
    # Retourner un emploi du temps d'exemple
    return {
        'lundi': [
            {
                'subject_name': 'Intelligence Artificielle',
                'teacher_name': 'Dr. Martin',
                'start_time': '08:00',
                'end_time': '10:00',
                'room': 'Salle 101'
            },
            {
                'subject_name': 'Machine Learning',
                'teacher_name': 'Prof. Dubois',
                'start_time': '10:30',
                'end_time': '12:30',
                'room': 'Salle 102'
            }
        ],
        'mardi': [
            {
                'subject_name': 'Deep Learning',
                'teacher_name': 'Dr. Bernard',
                'start_time': '09:00',
                'end_time': '11:00',
                'room': 'Salle 103'
            }
        ],
        'mercredi': [],
        'jeudi': [
            {
                'subject_name': 'Projet IA',
                'teacher_name': 'Prof. Laurent',
                'start_time': '14:00',
                'end_time': '17:00',
                'room': 'Lab IA'
            }
        ],
        'vendredi': [
            {
                'subject_name': 'Séminaire',
                'teacher_name': 'Dr. Martin',
                'start_time': '10:00',
                'end_time': '12:00',
                'room': 'Amphithéâtre'
            }
        ]
    }
