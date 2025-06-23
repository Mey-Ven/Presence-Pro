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
    
    # Get parent's children
    children = get_parent_children(parent_info['id_parent'])
    
    # Get summary information for all children
    children_summary = []
    for child in children:
        child_summary = {
            'info': child,
            'attendance_stats': get_student_attendance_stats(child['id_student']),
            'recent_attendance': get_student_attendance_history(child['id_student'], limit=3),
            'pending_justifications': get_student_justifications(child['id_student'], status='pending')
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
    
    # Verify parent has access to this child
    child_info = get_child_info(child_id, parent_info['id_parent'])
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

@parent_bp.route('/justifications')
@login_required
@role_required('parent')
def justifications():
    """Parent justifications management page"""
    user = get_current_user()
    parent_info = get_parent_info(user['id'])
    
    # Get all children
    children = get_parent_children(parent_info['id_parent'])
    
    # Get justifications for all children
    all_justifications = []
    for child in children:
        child_justifications = get_student_justifications(child['id_student'])
        for justification in child_justifications:
            justification['child_name'] = child['full_name']
            justification['child_id'] = child['id_student']
        all_justifications.extend(child_justifications)
    
    # Sort by submission date
    all_justifications.sort(key=lambda x: x['submitted_at'], reverse=True)
    
    return render_template('parent/justifications.html',
                         parent=parent_info,
                         children=children,
                         justifications=all_justifications)

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
            INSERT INTO absence_justifications 
            (id_justification, student_id, absence_date, reason, description, submitted_by)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (justification_id, data['student_id'], data['absence_date'], 
              data['reason'], data.get('description', ''), user['id']))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'CREATE', 'absence_justifications', justification_id, 
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
            SELECT aj.*, se.id_student FROM absence_justifications aj
            JOIN students_extended se ON aj.student_id = se.id_student
            WHERE aj.id_justification = ? AND se.parent_id = ?
        ''', (justification_id, parent_info['id_parent']))
        
        justification = cursor.fetchone()
        if not justification:
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        # Update justification status
        cursor.execute('''
            UPDATE absence_justifications 
            SET status = 'approved', reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP,
                review_comments = 'Approved by parent'
            WHERE id_justification = ?
        ''', (user['id'], justification_id))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'UPDATE', 'absence_justifications', justification_id, 
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
        children = []
        
        for row in results:
            children.append({
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
from student_dashboard import (
    get_student_attendance_history,
    get_student_attendance_stats,
    get_student_justifications,
    get_student_weekly_schedule,
    get_student_grades
)
