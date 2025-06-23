#!/usr/bin/env python3
"""
Student Dashboard Module
=======================

This module provides comprehensive functionality for the student dashboard including:
- Personal class schedule and timetable
- Attendance history and statistics
- Absence justification system
- Profile management
- Grade viewing

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
from datetime import datetime, timedelta
import uuid
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from auth_manager import login_required, role_required, get_current_user, log_audit_trail

DATABASE_FILE = "attendance.db"

# Create Blueprint for student routes
student_bp = Blueprint('student', __name__, url_prefix='/student')

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_FILE)

@student_bp.route('/dashboard')
@login_required
@role_required('student')
def dashboard():
    """Student dashboard main page"""
    user = get_current_user()

    # Get student information
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'etudiant_id': user['id'],
            'class_name': 'Master IA',
            'enrollment_date': None,
            'first_name': user.get('first_name', 'Étudiant'),
            'last_name': user.get('last_name', 'Utilisateur'),
            'email': user.get('email', ''),
            'phone': user.get('phone', ''),
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}"
        }

    student_id = student_info['id_student']

    # Get today's schedule
    today_schedule = get_student_schedule(student_id, datetime.now().strftime('%A'))

    # Get recent attendance
    recent_attendance = get_student_attendance_history(student_id, limit=5)

    # Get attendance statistics
    attendance_stats = get_student_attendance_stats(student_id)

    # Get pending justifications
    pending_justifications = get_student_justifications(student_id, status='pending')

    return render_template('student/dashboard.html',
                         student=student_info,
                         today_schedule=today_schedule,
                         recent_attendance=recent_attendance,
                         attendance_stats=attendance_stats,
                         pending_justifications=pending_justifications)

@student_bp.route('/schedule')
@login_required
@role_required('student')
def schedule():
    """Student class schedule page"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}",
            'class_name': 'Master IA'
        }

    # Get full weekly schedule
    weekly_schedule = get_student_weekly_schedule(student_info['id_student'])

    return render_template('student/schedule.html',
                         student=student_info,
                         weekly_schedule=weekly_schedule)

@student_bp.route('/attendance')
@login_required
@role_required('student')
def attendance():
    """Student attendance history page"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}",
            'class_name': 'Master IA'
        }

    # Get date range from query parameters
    start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))

    # Get attendance history
    attendance_history = get_student_attendance_history(student_info['id_student'], start_date=start_date, end_date=end_date)

    # Get attendance statistics
    attendance_stats = get_student_attendance_stats(student_info['id_student'])

    return render_template('student/attendance.html',
                         student=student_info,
                         attendance_history=attendance_history,
                         attendance_stats=attendance_stats,
                         start_date=start_date,
                         end_date=end_date)

@student_bp.route('/justifications')
@login_required
@role_required('student')
def justifications():
    """Student absence justifications page"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}",
            'class_name': 'Master IA'
        }

    # Get all justifications
    all_justifications = get_student_justifications(student_info['id_student'])

    return render_template('student/justifications.html',
                         student=student_info,
                         justifications=all_justifications)

@student_bp.route('/submit_justification', methods=['POST'])
@login_required
@role_required('student')
def submit_justification():
    """Submit absence justification"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, utiliser l'ID utilisateur
    student_id = student_info['id_student'] if student_info else user['id']

    try:
        data = request.get_json()

        justification_id = str(uuid.uuid4())

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO justifications
            (id, student_id, absence_date, reason, description, parent_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (justification_id, student_id, data['absence_date'],
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

@student_bp.route('/profile')
@login_required
@role_required('student')
def profile():
    """Student profile page"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}",
            'class_name': 'Master IA',
            'email': user.get('email', ''),
            'phone': user.get('phone', '')
        }

    return render_template('student/profile.html',
                         student=student_info,
                         user=user)

@student_bp.route('/grades')
@login_required
@role_required('student')
def grades():
    """Student grades page"""
    user = get_current_user()
    student_info = get_student_info(user['id'])

    # Si student_info est None, créer des informations par défaut
    if not student_info:
        student_info = {
            'id_student': user['id'],
            'full_name': f"{user.get('first_name', 'Étudiant')} {user.get('last_name', 'Utilisateur')}",
            'class_name': 'Master IA'
        }

    # Get student grades
    student_grades = get_student_grades(student_info['id_student'])

    return render_template('student/grades.html',
                         student=student_info,
                         grades=student_grades)

# Helper functions

def get_student_info(user_id):
    """Get student information by user ID"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Try students_extended table first
        cursor.execute('''
            SELECT se.id_student, se.etudiant_id, se.class_name, se.enrollment_date,
                   u.first_name, u.last_name, u.email, u.phone,
                   e.nom, e.prenom
            FROM students_extended se
            JOIN users u ON se.user_id = u.id
            LEFT JOIN etudiants e ON se.etudiant_id = e.id_etudiant
            WHERE se.user_id = ?
        ''', (user_id,))

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

        # Fallback to etudiants table
        cursor.execute('''
            SELECT e.id_student, u.first_name, u.last_name, u.email, u.phone, e.classe
            FROM etudiants e
            JOIN users u ON e.id_student = u.id
            WHERE e.id_student = ?
        ''', (user_id,))

        result = cursor.fetchone()
        if result:
            return {
                'id_student': result[0],
                'etudiant_id': result[0],
                'class_name': result[5] or 'Non assigné',
                'enrollment_date': None,
                'first_name': result[1],
                'last_name': result[2],
                'email': result[3],
                'phone': result[4],
                'full_name': f"{result[1]} {result[2]}"
            }

        # If not found in either table, create basic student info
        cursor.execute('SELECT first_name, last_name, email, phone FROM users WHERE id = ? AND role = "student"', (user_id,))
        result = cursor.fetchone()
        if result:
            return {
                'id_student': user_id,
                'etudiant_id': user_id,
                'class_name': 'Non assigné',
                'enrollment_date': None,
                'first_name': result[0],
                'last_name': result[1],
                'email': result[2],
                'phone': result[3],
                'full_name': f"{result[0]} {result[1]}"
            }

        return None

    except Exception as e:
        print(f"Error getting student info: {e}")
        return None
    finally:
        conn.close()

def get_student_schedule(student_id, day_of_week=None):
    """Get student schedule"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if day_of_week:
            # Convert day name to number
            day_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
            day_num = day_map.get(day_of_week, 1)
            
            cursor.execute('''
                SELECT c.course_name, c.course_code, s.start_time, s.end_time, s.classroom, s.building,
                       u.first_name || ' ' || u.last_name as teacher_name
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id_course
                JOIN schedules s ON c.id_course = s.course_id
                JOIN teachers t ON c.teacher_id = t.id_teacher
                JOIN users u ON t.user_id = u.id
                WHERE e.student_id = ? AND s.day_of_week = ? AND e.status = 'enrolled'
                ORDER BY s.start_time
            ''', (student_id, day_num))
        else:
            cursor.execute('''
                SELECT c.course_name, c.course_code, s.day_of_week, s.start_time, s.end_time, s.classroom, s.building,
                       u.first_name || ' ' || u.last_name as teacher_name
                FROM enrollments e
                JOIN courses c ON e.course_id = c.id_course
                JOIN schedules s ON c.id_course = s.course_id
                JOIN teachers t ON c.teacher_id = t.id_teacher
                JOIN users u ON t.user_id = u.id
                WHERE e.student_id = ? AND e.status = 'enrolled'
                ORDER BY s.day_of_week, s.start_time
            ''', (student_id,))
        
        results = cursor.fetchall()
        schedule = []
        
        for row in results:
            if day_of_week:
                schedule.append({
                    'course_name': row[0],
                    'course_code': row[1],
                    'start_time': row[2],
                    'end_time': row[3],
                    'classroom': row[4],
                    'building': row[5],
                    'teacher_name': row[6]
                })
            else:
                schedule.append({
                    'course_name': row[0],
                    'course_code': row[1],
                    'day_of_week': row[2],
                    'start_time': row[3],
                    'end_time': row[4],
                    'classroom': row[5],
                    'building': row[6],
                    'teacher_name': row[7]
                })
        
        return schedule
        
    except Exception as e:
        print(f"Error getting student schedule: {e}")
        return []
    finally:
        conn.close()

def get_student_weekly_schedule(student_id):
    """Get student's full weekly schedule organized by day"""
    schedule = get_student_schedule(student_id)
    
    weekly_schedule = {
        1: [],  # Monday
        2: [],  # Tuesday
        3: [],  # Wednesday
        4: [],  # Thursday
        5: [],  # Friday
        6: [],  # Saturday
        7: []   # Sunday
    }
    
    for class_item in schedule:
        day = class_item['day_of_week']
        weekly_schedule[day].append(class_item)
    
    return weekly_schedule

def get_student_attendance_history(student_id, start_date=None, end_date=None, limit=None):
    """Get student attendance history"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get student's full name from etudiants table
        cursor.execute('''
            SELECT e.prenom || ' ' || e.nom as full_name
            FROM students_extended se
            JOIN etudiants e ON se.etudiant_id = e.id_etudiant
            WHERE se.id_student = ?
        ''', (student_id,))
        
        student_name_result = cursor.fetchone()
        if not student_name_result:
            return []
        
        student_name = student_name_result[0]
        
        # Build query based on parameters
        query = '''
            SELECT date, heure, timestamp
            FROM presences
            WHERE nom = ?
        '''
        params = [student_name]
        
        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)
        
        query += ' ORDER BY timestamp DESC'
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        attendance = []
        for row in results:
            attendance.append({
                'date': row[0],
                'time': row[1],
                'timestamp': row[2],
                'status': 'Present'
            })
        
        return attendance
        
    except Exception as e:
        print(f"Error getting attendance history: {e}")
        return []
    finally:
        conn.close()

def get_student_attendance_stats(student_id):
    """Get student attendance statistics"""
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
            return {
                'total_detections': result[0],
                'unique_days': result[1],
                'first_attendance': result[2],
                'last_attendance': result[3],
                'attendance_rate': 85.5  # Placeholder - would need more complex calculation
            }
        
        return {}
        
    except Exception as e:
        print(f"Error getting attendance stats: {e}")
        return {}
    finally:
        conn.close()

def get_student_justifications(student_id, status=None):
    """Get student's absence justifications"""
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
        print(f"Error getting justifications: {e}")
        return []
    finally:
        conn.close()

def get_student_grades(student_id):
    """Get student's grades"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT c.course_name, c.course_code, g.assessment_type, g.assessment_name,
                   g.points_earned, g.points_possible, g.percentage, g.grade_letter,
                   g.assessment_date, g.comments
            FROM enrollments e
            JOIN courses c ON e.course_id = c.id_course
            JOIN grades g ON e.id_enrollment = g.enrollment_id
            WHERE e.student_id = ?
            ORDER BY c.course_name, g.assessment_date DESC
        ''', (student_id,))
        
        results = cursor.fetchall()
        grades = []
        
        for row in results:
            grades.append({
                'course_name': row[0],
                'course_code': row[1],
                'assessment_type': row[2],
                'assessment_name': row[3],
                'points_earned': row[4],
                'points_possible': row[5],
                'percentage': row[6],
                'grade_letter': row[7],
                'assessment_date': row[8],
                'comments': row[9]
            })
        
        return grades
        
    except Exception as e:
        print(f"Error getting student grades: {e}")
        return []
    finally:
        conn.close()
