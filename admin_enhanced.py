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
    return render_template('admin/users.html', 
                         users=[], 
                         message="Page de gestion des utilisateurs en cours de développement")

@admin_enhanced_bp.route('/courses_management')
@login_required
@role_required('admin')
def courses_management():
    """Course management page"""
    return render_template('admin/courses.html', 
                         courses=[], 
                         message="Page de gestion des cours en cours de développement")

@admin_enhanced_bp.route('/system_reports')
@login_required
@role_required('admin')
def system_reports():
    """System reports page"""
    return render_template('admin/reports.html', 
                         reports=[], 
                         message="Page de rapports système en cours de développement")

@admin_enhanced_bp.route('/communication_hub')
@login_required
@role_required('admin')
def communication_hub():
    """Communication hub page"""
    return render_template('admin/messages.html', 
                         messages=[], 
                         message="Hub de communication en cours de développement")

@admin_enhanced_bp.route('/audit_trail')
@login_required
@role_required('admin')
def audit_trail():
    """Audit trail page"""
    return render_template('admin/audit.html', 
                         audit_logs=[], 
                         message="Journal d'audit en cours de développement")

@admin_enhanced_bp.route('/system_settings')
@login_required
@role_required('admin')
def system_settings():
    """System settings page"""
    return render_template('admin/settings.html', 
                         settings={}, 
                         message="Paramètres système en cours de développement")

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
