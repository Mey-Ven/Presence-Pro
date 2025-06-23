#!/usr/bin/env python3
"""
Role-Based Facial Recognition Attendance System
==============================================

Comprehensive web application with role-based dashboards for:
- Students: Schedule, attendance, justifications, grades
- Teachers: Course management, grades, attendance monitoring
- Parents: Child monitoring, justifications, communication
- Administrators: System-wide management and oversight

Author: Facial Attendance System
Date: 2025-06-23
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from flask_socketio import SocketIO
import os
import sys
from datetime import datetime

# Import authentication and role management
from auth_manager import auth_manager, login_required, role_required, get_current_user

# Import role-based dashboard modules
from student_dashboard import student_bp
from teacher_dashboard import teacher_bp
from parent_dashboard import parent_bp
from admin_enhanced import admin_enhanced_bp

# Import enhanced database setup
from enhanced_database import create_enhanced_tables, insert_default_admin, insert_sample_data

# Configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = 'facial_attendance_role_based_2025'
app.config['UPLOAD_FOLDER'] = 'dataset'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize SocketIO for real-time updates
socketio = SocketIO(app, cors_allowed_origins="*")

# Register blueprints for role-based dashboards
app.register_blueprint(student_bp)
app.register_blueprint(teacher_bp)
app.register_blueprint(parent_bp)
app.register_blueprint(admin_enhanced_bp)

# Initialize enhanced database
def initialize_system():
    """Initialize the enhanced database system"""
    try:
        print("🔧 Initializing enhanced database system...")
        create_enhanced_tables()
        insert_default_admin()
        insert_sample_data()
        print("✅ System initialization completed!")
    except Exception as e:
        print(f"❌ System initialization error: {e}")

@app.route('/')
def index():
    """Home page - redirect based on user role or to login"""
    if 'user_id' in session:
        user = get_current_user()
        if user:
            role = user['role']
            if role == 'admin':
                return redirect(url_for('admin_enhanced.dashboard'))
            elif role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif role == 'student':
                return redirect(url_for('student.dashboard'))
            elif role == 'parent':
                return redirect(url_for('parent.dashboard'))
    
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Universal login page for all roles"""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Authenticate user
        user = auth_manager.authenticate_user(username, password)
        
        if user:
            # Set session variables
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['email'] = user['email']
            session['user_role'] = user['role']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            session['full_name'] = user['full_name']
            
            flash(f'Welcome, {user["full_name"]}!', 'success')
            
            # Redirect based on role
            if user['role'] == 'admin':
                return redirect(url_for('admin_enhanced.dashboard'))
            elif user['role'] == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user['role'] == 'student':
                return redirect(url_for('student.dashboard'))
            elif user['role'] == 'parent':
                return redirect(url_for('parent.dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@app.route('/logout')
def logout():
    """Logout for all roles"""
    session.clear()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Generic dashboard redirect based on role"""
    user = get_current_user()
    if user:
        role = user['role']
        if role == 'admin':
            return redirect(url_for('admin_enhanced.dashboard'))
        elif role == 'teacher':
            return redirect(url_for('teacher.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
        elif role == 'parent':
            return redirect(url_for('parent.dashboard'))
    
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    """User profile page for all roles"""
    user = get_current_user()
    return render_template('common/profile.html', user=user)

@app.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    """Update user profile"""
    user = get_current_user()
    
    try:
        data = request.get_json()
        
        success, message = auth_manager.update_user_profile(
            user['id'],
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        if success:
            # Update session data
            session['first_name'] = data.get('first_name', user['first_name'])
            session['last_name'] = data.get('last_name', user['last_name'])
            session['email'] = data.get('email', user['email'])
            session['full_name'] = f"{session['first_name']} {session['last_name']}"
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Change user password"""
    user = get_current_user()
    
    try:
        data = request.get_json()
        
        success, message = auth_manager.change_password(
            user['id'],
            data['old_password'],
            data['new_password']
        )
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/notifications')
@login_required
def get_notifications():
    """Get user notifications"""
    user = get_current_user()
    
    try:
        import sqlite3
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id_notification, title, content, notification_type, is_read, 
                   action_url, created_at
            FROM notifications
            WHERE user_id = ? AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)
            ORDER BY created_at DESC
            LIMIT 10
        ''', (user['id'],))
        
        results = cursor.fetchall()
        notifications = []
        
        for row in results:
            notifications.append({
                'id': row[0],
                'title': row[1],
                'content': row[2],
                'type': row[3],
                'is_read': row[4],
                'action_url': row[5],
                'created_at': row[6]
            })
        
        return jsonify({'success': True, 'notifications': notifications})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/mark_notification_read/<notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark notification as read"""
    user = get_current_user()
    
    try:
        import sqlite3
        conn = sqlite3.connect('attendance.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE notifications 
            SET is_read = 1, read_at = CURRENT_TIMESTAMP
            WHERE id_notification = ? AND user_id = ?
        ''', (notification_id, user['id']))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Notification marked as read'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(error):
    return render_template('errors/500.html'), 500

# Context processors for templates
@app.context_processor
def inject_user():
    """Inject current user into all templates"""
    return dict(current_user=get_current_user())

@app.context_processor
def inject_navigation():
    """Inject navigation items based on user role"""
    user = get_current_user()
    if not user:
        return dict(navigation=[])
    
    role = user['role']
    navigation = []
    
    if role == 'admin':
        navigation = [
            {'name': 'Dashboard', 'url': url_for('admin_enhanced.dashboard'), 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Users', 'url': url_for('admin_enhanced.users'), 'icon': 'fas fa-users'},
            {'name': 'Courses', 'url': url_for('admin_enhanced.courses_management'), 'icon': 'fas fa-book'},
            {'name': 'Reports', 'url': url_for('admin_enhanced.system_reports'), 'icon': 'fas fa-chart-bar'},
            {'name': 'Messages', 'url': url_for('admin_enhanced.communication_hub'), 'icon': 'fas fa-envelope'},
            {'name': 'Audit', 'url': url_for('admin_enhanced.audit_trail'), 'icon': 'fas fa-history'},
            {'name': 'Settings', 'url': url_for('admin_enhanced.system_settings'), 'icon': 'fas fa-cog'}
        ]
    elif role == 'teacher':
        navigation = [
            {'name': 'Dashboard', 'url': url_for('teacher.dashboard'), 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Courses', 'url': url_for('teacher.courses'), 'icon': 'fas fa-book'},
            {'name': 'Schedule', 'url': url_for('teacher.schedule'), 'icon': 'fas fa-calendar'},
            {'name': 'Grades', 'url': url_for('teacher.grades'), 'icon': 'fas fa-graduation-cap'},
            {'name': 'Attendance', 'url': url_for('teacher.attendance'), 'icon': 'fas fa-check-circle'}
        ]
    elif role == 'student':
        navigation = [
            {'name': 'Dashboard', 'url': url_for('student.dashboard'), 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Schedule', 'url': url_for('student.schedule'), 'icon': 'fas fa-calendar'},
            {'name': 'Attendance', 'url': url_for('student.attendance'), 'icon': 'fas fa-check-circle'},
            {'name': 'Grades', 'url': url_for('student.grades'), 'icon': 'fas fa-graduation-cap'},
            {'name': 'Justifications', 'url': url_for('student.justifications'), 'icon': 'fas fa-file-alt'}
        ]
    elif role == 'parent':
        navigation = [
            {'name': 'Dashboard', 'url': url_for('parent.dashboard'), 'icon': 'fas fa-tachometer-alt'},
            {'name': 'Children', 'url': url_for('parent.dashboard'), 'icon': 'fas fa-child'},
            {'name': 'Justifications', 'url': url_for('parent.justifications'), 'icon': 'fas fa-file-alt'},
            {'name': 'Messages', 'url': url_for('parent.messages'), 'icon': 'fas fa-envelope'},
            {'name': 'Notifications', 'url': url_for('parent.notifications'), 'icon': 'fas fa-bell'}
        ]
    
    return dict(navigation=navigation)

if __name__ == '__main__':
    # Initialize system on startup
    initialize_system()
    
    print("🚀 Starting Role-Based Facial Recognition Attendance System...")
    print("📊 Available dashboards:")
    print("   👨‍💼 Admin: http://localhost:5002/admin/dashboard")
    print("   👨‍🏫 Teacher: http://localhost:5002/teacher/dashboard")
    print("   👨‍🎓 Student: http://localhost:5002/student/dashboard")
    print("   👨‍👩‍👧‍👦 Parent: http://localhost:5002/parent/dashboard")
    print("🔐 Default admin login: admin / admin123")
    
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5002, debug=True)
