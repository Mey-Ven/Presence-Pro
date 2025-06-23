#!/usr/bin/env python3
"""
Enhanced Admin Dashboard Module
==============================

Comprehensive admin functionality for the facial recognition attendance system.
Provides advanced user management, system monitoring, and administrative tools.

Author: Facial Attendance System
Date: 2025-06-23
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from auth_manager import login_required, role_required, get_current_user
from enhanced_database import get_connection
import uuid
import hashlib
from datetime import datetime, timedelta

# Create admin blueprint
admin_enhanced_bp = Blueprint('admin_enhanced', __name__, url_prefix='/admin')

@admin_enhanced_bp.route('/dashboard')
@login_required
@role_required('admin')
def dashboard():
    """Enhanced admin dashboard main page"""
    user = get_current_user()
    
    # Get comprehensive system statistics
    system_stats = get_system_statistics()
    
    # Get recent system activities
    recent_activities = get_recent_activities(limit=10)
    
    # Get system alerts
    system_alerts = get_system_alerts()
    
    # Get user statistics by role
    user_stats = get_user_statistics_by_role()
    
    # Ensure system_stats has required fields
    if not system_stats:
        system_stats = {}
    
    system_stats.setdefault('total_users', 0)
    system_stats.setdefault('active_courses', 0)
    system_stats.setdefault('today_attendance', 0)
    system_stats.setdefault('weekly_messages', 0)
    
    return render_template('admin/enhanced_dashboard.html',
                         admin=user,
                         system_stats=system_stats,
                         recent_activities=recent_activities,
                         system_alerts=system_alerts,
                         user_stats=user_stats)

@admin_enhanced_bp.route('/users')
@login_required
@role_required('admin')
def users():
    """User management page"""
    from enhanced_database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    # Obtenir tous les utilisateurs avec leurs informations
    cursor.execute('''
        SELECT id, username, first_name, last_name, email, phone, role, is_active, created_at
        FROM users
        ORDER BY role, last_name, first_name
    ''')

    users_data = []
    for row in cursor.fetchall():
        users_data.append({
            'id': row[0],
            'username': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'email': row[4],
            'phone': row[5],
            'role': row[6],
            'is_active': row[7],
            'created_at': row[8],
            'full_name': f"{row[2]} {row[3]}"
        })

    # Statistiques par rôle
    cursor.execute('''
        SELECT role, COUNT(*) as count,
               SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_count
        FROM users
        GROUP BY role
    ''')

    role_stats = {}
    for row in cursor.fetchall():
        role_stats[row[0]] = {
            'total': row[1],
            'active': row[2]
        }

    conn.close()

    return render_template('admin/users.html',
                         users=users_data,
                         role_stats=role_stats)

@admin_enhanced_bp.route('/courses_management')
@login_required
@role_required('admin')
def courses_management():
    """Course management page"""
    from enhanced_database import get_connection

    conn = get_connection()
    cursor = conn.cursor()

    # Obtenir tous les cours avec leurs informations
    cursor.execute('''
        SELECT id_course, course_name, course_code, credits, department, semester,
               max_students, description, created_at
        FROM courses
        ORDER BY department, course_name
    ''')

    courses_data = []
    for row in cursor.fetchall():
        course_id = row[0]

        # Compter les inscriptions
        cursor.execute('SELECT COUNT(*) FROM enrollments WHERE course_id = ?', (course_id,))
        enrolled_count = cursor.fetchone()[0] if cursor.fetchone() else 0

        courses_data.append({
            'id': row[0],
            'name': row[1],
            'code': row[2],
            'credits': row[3],
            'department': row[4],
            'semester': row[5],
            'max_students': row[6],
            'description': row[7],
            'created_at': row[8],
            'enrolled_count': enrolled_count,
            'teacher_name': "Non assigné",
            'occupancy_rate': (enrolled_count / row[6] * 100) if row[6] > 0 else 0
        })

    # Statistiques par département
    cursor.execute('''
        SELECT department, COUNT(*) as course_count
        FROM courses
        GROUP BY department
    ''')

    dept_stats = {}
    for row in cursor.fetchall():
        dept_stats[row[0]] = {
            'course_count': row[1],
            'avg_credits': 3.0
        }

    conn.close()

    return render_template('admin/courses.html',
                         courses=courses_data,
                         dept_stats=dept_stats)

@admin_enhanced_bp.route('/system_reports')
@login_required
@role_required('admin')
def system_reports():
    """System reports page"""
    from enhanced_database import get_connection
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    # Statistiques générales
    cursor.execute('SELECT COUNT(*) FROM users')
    total_users = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM courses')
    total_courses = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM presences WHERE date = ?', (datetime.now().date(),))
    today_attendance = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM messages WHERE created_at >= ?', (datetime.now() - timedelta(days=7),))
    weekly_messages = cursor.fetchone()[0]

    # Données pour les graphiques
    cursor.execute('''
        SELECT role, COUNT(*)
        FROM users
        WHERE is_active = 1
        GROUP BY role
    ''')
    user_by_role = dict(cursor.fetchall())

    cursor.execute('''
        SELECT department, COUNT(*)
        FROM courses
        GROUP BY department
    ''')
    courses_by_dept = dict(cursor.fetchall())

    conn.close()

    reports_data = {
        'summary': {
            'total_users': total_users,
            'total_courses': total_courses,
            'today_attendance': today_attendance,
            'weekly_messages': weekly_messages
        },
        'charts': {
            'user_by_role': user_by_role,
            'courses_by_dept': courses_by_dept
        }
    }

    return render_template('admin/reports.html',
                         reports=reports_data)

@admin_enhanced_bp.route('/communication_hub')
@login_required
@role_required('admin')
def communication_hub():
    """Communication hub page"""
    from enhanced_database import get_connection
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    # Obtenir les messages récents
    cursor.execute('''
        SELECT m.id, m.subject, m.content, m.sender_id, m.recipient_id, m.is_read, m.created_at,
               u1.first_name as sender_first, u1.last_name as sender_last,
               u2.first_name as recipient_first, u2.last_name as recipient_last
        FROM messages m
        JOIN users u1 ON m.sender_id = u1.id
        LEFT JOIN users u2 ON m.recipient_id = u2.id
        ORDER BY m.created_at DESC
        LIMIT 50
    ''')

    messages_data = []
    for row in cursor.fetchall():
        messages_data.append({
            'id': row[0],
            'subject': row[1],
            'content': row[2],
            'sender_id': row[3],
            'recipient_id': row[4],
            'is_read': row[5],
            'created_at': row[6],
            'sender_name': f"{row[7]} {row[8]}",
            'recipient_name': f"{row[9]} {row[10]}" if row[9] else "Diffusion générale"
        })

    # Statistiques de communication
    cursor.execute('SELECT COUNT(*) FROM messages WHERE created_at >= ?', (datetime.now() - timedelta(days=7),))
    weekly_messages = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM messages WHERE is_read = 0')
    unread_messages = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(DISTINCT sender_id) FROM messages WHERE created_at >= ?', (datetime.now() - timedelta(days=30),))
    active_senders = cursor.fetchone()[0]

    conn.close()

    communication_data = {
        'messages': messages_data,
        'stats': {
            'weekly_messages': weekly_messages,
            'unread_messages': unread_messages,
            'active_senders': active_senders
        }
    }

    return render_template('admin/messages.html',
                         communication=communication_data)

@admin_enhanced_bp.route('/audit_trail')
@login_required
@role_required('admin')
def audit_trail():
    """Audit trail page"""
    from enhanced_database import get_connection
    from datetime import datetime, timedelta

    conn = get_connection()
    cursor = conn.cursor()

    # Obtenir les logs d'audit récents
    cursor.execute('''
        SELECT a.id, a.user_id, a.action, a.table_name, a.record_id, a.old_values, a.new_values, a.created_at,
               u.first_name, u.last_name, u.role
        FROM audit_trail a
        LEFT JOIN users u ON a.user_id = u.id
        ORDER BY a.created_at DESC
        LIMIT 100
    ''')

    audit_data = []
    for row in cursor.fetchall():
        audit_data.append({
            'id': row[0],
            'user_id': row[1],
            'action': row[2],
            'table_name': row[3],
            'record_id': row[4],
            'old_values': row[5],
            'new_values': row[6],
            'created_at': row[7],
            'user_name': f"{row[8]} {row[9]}" if row[8] else "Système",
            'user_role': row[10] if row[10] else "system"
        })

    # Statistiques d'audit
    cursor.execute('SELECT COUNT(*) FROM audit_trail WHERE created_at >= ?', (datetime.now() - timedelta(days=1),))
    today_actions = cursor.fetchone()[0]

    cursor.execute('SELECT COUNT(*) FROM audit_trail WHERE created_at >= ?', (datetime.now() - timedelta(days=7),))
    weekly_actions = cursor.fetchone()[0]

    cursor.execute('SELECT action, COUNT(*) FROM audit_trail WHERE created_at >= ? GROUP BY action', (datetime.now() - timedelta(days=7),))
    action_stats = dict(cursor.fetchall())

    conn.close()

    audit_trail_data = {
        'logs': audit_data,
        'stats': {
            'today_actions': today_actions,
            'weekly_actions': weekly_actions,
            'action_stats': action_stats
        }
    }

    return render_template('admin/audit.html',
                         audit_trail=audit_trail_data)

@admin_enhanced_bp.route('/system_settings')
@login_required
@role_required('admin')
def system_settings():
    """System settings page"""
    from enhanced_database import get_connection
    import os

    # Paramètres système par défaut
    system_settings = {
        'general': {
            'institution_name': 'École Supérieure de Technologie',
            'academic_year': '2024-2025',
            'timezone': 'Europe/Paris',
            'language': 'fr'
        },
        'facial_recognition': {
            'confidence_threshold': 0.6,
            'max_distance': 0.6,
            'detection_method': 'hog',
            'auto_save_images': True
        },
        'security': {
            'session_timeout': 3600,
            'max_login_attempts': 5,
            'password_min_length': 8,
            'require_password_change': False
        },
        'notifications': {
            'email_enabled': True,
            'sms_enabled': False,
            'push_enabled': True,
            'daily_reports': True
        },
        'system': {
            'database_size': _get_database_size(),
            'total_users': _get_total_users(),
            'disk_usage': _get_disk_usage(),
            'last_backup': 'Jamais'
        }
    }

    return render_template('admin/settings.html',
                         settings=system_settings)

def _get_database_size():
    """Obtenir la taille de la base de données"""
    try:
        import os
        db_path = "attendance.db"
        if os.path.exists(db_path):
            size_bytes = os.path.getsize(db_path)
            return f"{size_bytes / 1024 / 1024:.2f} MB"
        return "0 MB"
    except:
        return "Inconnu"

def _get_total_users():
    """Obtenir le nombre total d'utilisateurs"""
    try:
        from enhanced_database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM users')
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

def _get_disk_usage():
    """Obtenir l'utilisation du disque"""
    try:
        import shutil
        total, used, free = shutil.disk_usage(".")
        used_gb = used / (1024**3)
        total_gb = total / (1024**3)
        return f"{used_gb:.1f} GB / {total_gb:.1f} GB"
    except:
        return "Inconnu"

# Helper functions

def get_system_statistics():
    """Get comprehensive system statistics"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        stats = {}
        
        # User counts by role
        cursor.execute('SELECT role, COUNT(*) FROM users GROUP BY role')
        user_counts = dict(cursor.fetchall())
        stats['users'] = user_counts
        
        # Total users
        cursor.execute('SELECT COUNT(*) FROM users')
        stats['total_users'] = cursor.fetchone()[0]
        
        # Course statistics
        cursor.execute('SELECT COUNT(*) FROM courses')
        stats['active_courses'] = cursor.fetchone()[0]
        
        # Today's attendance
        cursor.execute('SELECT COUNT(*) FROM presences WHERE date = date("now")')
        stats['today_attendance'] = cursor.fetchone()[0]
        
        # Weekly messages
        cursor.execute('SELECT COUNT(*) FROM messages WHERE sent_at >= date("now", "-7 days")')
        stats['weekly_messages'] = cursor.fetchone()[0]
        
        return stats
        
    except Exception as e:
        print(f"Error getting system statistics: {e}")
        return {'total_users': 0, 'active_courses': 0, 'today_attendance': 0, 'weekly_messages': 0}
    finally:
        conn.close()

def get_recent_activities(limit=10):
    """Get recent system activities"""
    # Return sample activities for now
    return [
        {
            'action': 'CREATE',
            'table_name': 'users',
            'record_id': 'sample',
            'created_at': '2025-06-23 10:00:00',
            'user_name': 'Admin'
        }
    ]

def get_system_alerts():
    """Get system alerts"""
    # Return sample alerts for now
    return []

def get_user_statistics_by_role():
    """Get user statistics by role"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT role, COUNT(*) as total,
                   SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active
            FROM users
            GROUP BY role
        ''')
        
        results = cursor.fetchall()
        stats = {}
        
        for row in results:
            stats[row[0]] = {
                'total': row[1],
                'active': row[2],
                'active_this_week': row[2]  # Simplified for now
            }
        
        return stats
        
    except Exception as e:
        print(f"Error getting user statistics: {e}")
        return {}
    finally:
        conn.close()
