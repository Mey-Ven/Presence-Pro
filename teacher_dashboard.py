#!/usr/bin/env python3
"""
Teacher Dashboard Module
=======================

This module provides comprehensive functionality for the teacher dashboard including:
- Course management (add, edit, delete courses)
- Class schedules and timetables
- Student grade management system
- Attendance records for their classes
- Course materials and announcements

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
from datetime import datetime, timedelta
import uuid
from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from auth_manager import login_required, role_required, get_current_user, log_audit_trail

DATABASE_FILE = "attendance.db"

# Create Blueprint for teacher routes
teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_FILE)

@teacher_bp.route('/dashboard')
@login_required
@role_required('teacher')
def dashboard():
    """Teacher dashboard main page"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    # Get teacher's courses
    teacher_courses = get_teacher_courses(teacher_info['id_teacher'])
    
    # Get today's schedule
    today_schedule = get_teacher_schedule(teacher_info['id_teacher'], datetime.now().strftime('%A'))
    
    # Get recent attendance for teacher's classes
    recent_attendance = get_teacher_class_attendance(teacher_info['id_teacher'], limit=10)
    
    # Get course statistics
    course_stats = get_teacher_course_stats(teacher_info['id_teacher'])
    
    return render_template('teacher/dashboard.html',
                         teacher=teacher_info,
                         courses=teacher_courses,
                         today_schedule=today_schedule,
                         recent_attendance=recent_attendance,
                         course_stats=course_stats)

@teacher_bp.route('/courses')
@login_required
@role_required('teacher')
def courses():
    """Teacher courses management page"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    # Get all teacher's courses
    teacher_courses = get_teacher_courses(teacher_info['id_teacher'])
    
    return render_template('teacher/courses.html',
                         teacher=teacher_info,
                         courses=teacher_courses)

@teacher_bp.route('/create_course', methods=['POST'])
@login_required
@role_required('teacher')
def create_course():
    """Create new course"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    try:
        data = request.get_json()
        
        course_id = str(uuid.uuid4())
        
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO courses 
            (id_course, course_code, course_name, description, credits, teacher_id, department, semester, academic_year, max_students)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (course_id, data['course_code'], data['course_name'], data.get('description', ''),
              data.get('credits', 3), teacher_info['id_teacher'], data.get('department', ''),
              data.get('semester', ''), data.get('academic_year', ''), data.get('max_students', 30)))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'CREATE', 'courses', course_id, None, data)
        
        return jsonify({'success': True, 'message': 'Course created successfully', 'course_id': course_id})
        
    except Exception as e:
        print(f"Error creating course: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@teacher_bp.route('/update_course/<course_id>', methods=['PUT'])
@login_required
@role_required('teacher')
def update_course(course_id):
    """Update existing course"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    try:
        data = request.get_json()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify teacher owns this course
        cursor.execute('SELECT id_course FROM courses WHERE id_course = ? AND teacher_id = ?', 
                      (course_id, teacher_info['id_teacher']))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Course not found or access denied'}), 404
        
        # Get old values for audit
        cursor.execute('SELECT * FROM courses WHERE id_course = ?', (course_id,))
        old_values = dict(zip([col[0] for col in cursor.description], cursor.fetchone()))
        
        # Update course
        cursor.execute('''
            UPDATE courses 
            SET course_name = ?, description = ?, credits = ?, department = ?, 
                semester = ?, academic_year = ?, max_students = ?
            WHERE id_course = ? AND teacher_id = ?
        ''', (data['course_name'], data.get('description', ''), data.get('credits', 3),
              data.get('department', ''), data.get('semester', ''), data.get('academic_year', ''),
              data.get('max_students', 30), course_id, teacher_info['id_teacher']))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'UPDATE', 'courses', course_id, old_values, data)
        
        return jsonify({'success': True, 'message': 'Course updated successfully'})
        
    except Exception as e:
        print(f"Error updating course: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@teacher_bp.route('/delete_course/<course_id>', methods=['DELETE'])
@login_required
@role_required('teacher')
def delete_course(course_id):
    """Delete course"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify teacher owns this course
        cursor.execute('SELECT * FROM courses WHERE id_course = ? AND teacher_id = ?', 
                      (course_id, teacher_info['id_teacher']))
        course = cursor.fetchone()
        if not course:
            return jsonify({'success': False, 'message': 'Course not found or access denied'}), 404
        
        # Get old values for audit
        old_values = dict(zip([col[0] for col in cursor.description], course))
        
        # Delete course (this will cascade to schedules and enrollments)
        cursor.execute('DELETE FROM courses WHERE id_course = ? AND teacher_id = ?', 
                      (course_id, teacher_info['id_teacher']))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'DELETE', 'courses', course_id, old_values, None)
        
        return jsonify({'success': True, 'message': 'Course deleted successfully'})
        
    except Exception as e:
        print(f"Error deleting course: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@teacher_bp.route('/schedule')
@login_required
@role_required('teacher')
def schedule():
    """Teacher schedule page"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])

    # Get full weekly schedule
    weekly_schedule = get_teacher_weekly_schedule(teacher_info['id_teacher'])

    # Get current week dates
    from datetime import datetime, timedelta
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())

    dates = {
        'current_week_start': monday.strftime('%d/%m/%Y'),
        'current_week_end': (monday + timedelta(days=4)).strftime('%d/%m/%Y'),
        'monday_date': monday.strftime('%d/%m'),
        'tuesday_date': (monday + timedelta(days=1)).strftime('%d/%m'),
        'wednesday_date': (monday + timedelta(days=2)).strftime('%d/%m'),
        'thursday_date': (monday + timedelta(days=3)).strftime('%d/%m'),
        'friday_date': (monday + timedelta(days=4)).strftime('%d/%m'),
        'total_classes_week': 0  # Will be calculated from weekly_schedule
    }

    return render_template('teacher/schedule.html',
                         teacher=teacher_info,
                         weekly_schedule=weekly_schedule,
                         **dates)

@teacher_bp.route('/grades')
@login_required
@role_required('teacher')
def grades():
    """Teacher grades management page"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    # Get teacher's courses with enrolled students
    courses_with_students = get_teacher_courses_with_students(teacher_info['id_teacher'])
    
    return render_template('teacher/grades.html',
                         teacher=teacher_info,
                         courses=courses_with_students)

@teacher_bp.route('/add_grade', methods=['POST'])
@login_required
@role_required('teacher')
def add_grade():
    """Add grade for student"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])
    
    try:
        data = request.get_json()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Verify teacher owns the course
        cursor.execute('''
            SELECT e.id_enrollment FROM enrollments e
            JOIN courses c ON e.course_id = c.id_course
            WHERE e.id_enrollment = ? AND c.teacher_id = ?
        ''', (data['enrollment_id'], teacher_info['id_teacher']))
        
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Access denied'}), 403
        
        grade_id = str(uuid.uuid4())
        
        # Calculate percentage if points provided
        percentage = None
        if data.get('points_earned') and data.get('points_possible'):
            percentage = (float(data['points_earned']) / float(data['points_possible'])) * 100
        
        cursor.execute('''
            INSERT INTO grades 
            (id_grade, enrollment_id, assessment_type, assessment_name, points_earned, 
             points_possible, percentage, grade_letter, assessment_date, due_date, comments, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (grade_id, data['enrollment_id'], data['assessment_type'], data['assessment_name'],
              data.get('points_earned'), data.get('points_possible'), percentage,
              data.get('grade_letter'), data.get('assessment_date'), data.get('due_date'),
              data.get('comments'), user['id']))
        
        conn.commit()
        
        # Log audit trail
        log_audit_trail(user['id'], 'CREATE', 'grades', grade_id, None, data)
        
        return jsonify({'success': True, 'message': 'Grade added successfully'})
        
    except Exception as e:
        print(f"Error adding grade: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        conn.close()

@teacher_bp.route('/attendance')
@login_required
@role_required('teacher')
def attendance():
    """Teacher attendance view page"""
    user = get_current_user()
    teacher_info = get_teacher_info(user['id'])

    # Get attendance for teacher's classes
    class_attendance = get_teacher_class_attendance(teacher_info['id_teacher'])

    # Get teacher's courses for filtering
    teacher_courses = get_teacher_courses(teacher_info['id_teacher'])

    # Get courses with students for detailed view
    courses_with_students = get_teacher_courses_with_students(teacher_info['id_teacher'])

    # Create attendance summary
    attendance_summary = {
        'total_sessions': len(class_attendance),
        'present_count': len([a for a in class_attendance if a.get('status') == 'Present']),
        'absent_count': 0,  # Will be calculated based on expected vs actual
        'attendance_rate': 85  # Sample rate
    }

    # Get date filters from request
    from flask import request
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    return render_template('teacher/attendance.html',
                         teacher=teacher_info,
                         attendance=class_attendance,
                         courses=courses_with_students,
                         attendance_summary=attendance_summary,
                         start_date=start_date,
                         end_date=end_date)

# Helper functions

def get_teacher_info(user_id):
    """Get teacher information by user ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT t.id_teacher, t.employee_id, t.department, t.specialization, t.hire_date,
                   u.first_name, u.last_name, u.email, u.phone
            FROM teachers t
            JOIN users u ON t.user_id = u.id
            WHERE t.user_id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        if result:
            return {
                'id_teacher': result[0],
                'employee_id': result[1],
                'department': result[2],
                'specialization': result[3],
                'hire_date': result[4],
                'first_name': result[5],
                'last_name': result[6],
                'email': result[7],
                'phone': result[8],
                'full_name': f"{result[5]} {result[6]}"
            }
        return None
        
    except Exception as e:
        print(f"Error getting teacher info: {e}")
        return None
    finally:
        conn.close()

def get_teacher_courses(teacher_id):
    """Get all courses taught by teacher"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id_course, course_code, course_name, description, credits, 
                   department, semester, academic_year, max_students, is_active,
                   (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id_course AND status = 'enrolled') as enrolled_count
            FROM courses c
            WHERE teacher_id = ? AND is_active = 1
            ORDER BY course_name
        ''', (teacher_id,))
        
        results = cursor.fetchall()
        courses = []
        
        for row in results:
            courses.append({
                'id_course': row[0],
                'course_code': row[1],
                'course_name': row[2],
                'description': row[3],
                'credits': row[4],
                'department': row[5],
                'semester': row[6],
                'academic_year': row[7],
                'max_students': row[8],
                'is_active': row[9],
                'enrolled_count': row[10]
            })
        
        return courses
        
    except Exception as e:
        print(f"Error getting teacher courses: {e}")
        return []
    finally:
        conn.close()

def get_teacher_schedule(teacher_id, day_of_week=None):
    """Get teacher schedule"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        if day_of_week:
            # Convert day name to number
            day_map = {'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6, 'Sunday': 7}
            day_num = day_map.get(day_of_week, 1)
            
            cursor.execute('''
                SELECT c.course_name, c.course_code, s.start_time, s.end_time, s.classroom, s.building,
                       (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id_course AND status = 'enrolled') as student_count
                FROM courses c
                JOIN schedules s ON c.id_course = s.course_id
                WHERE c.teacher_id = ? AND s.day_of_week = ? AND c.is_active = 1
                ORDER BY s.start_time
            ''', (teacher_id, day_num))
        else:
            cursor.execute('''
                SELECT c.course_name, c.course_code, s.day_of_week, s.start_time, s.end_time, s.classroom, s.building,
                       (SELECT COUNT(*) FROM enrollments WHERE course_id = c.id_course AND status = 'enrolled') as student_count
                FROM courses c
                JOIN schedules s ON c.id_course = s.course_id
                WHERE c.teacher_id = ? AND c.is_active = 1
                ORDER BY s.day_of_week, s.start_time
            ''', (teacher_id,))
        
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
                    'student_count': row[6]
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
                    'student_count': row[7]
                })
        
        return schedule
        
    except Exception as e:
        print(f"Error getting teacher schedule: {e}")
        return []
    finally:
        conn.close()

def get_teacher_weekly_schedule(teacher_id):
    """Get teacher's full weekly schedule organized by day"""
    schedule = get_teacher_schedule(teacher_id)
    
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

def get_teacher_courses_with_students(teacher_id):
    """Get teacher's courses with enrolled students"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT c.id_course, c.course_name, c.course_code,
                   e.id_enrollment, e.student_id,
                   u.first_name, u.last_name, se.class_name
            FROM courses c
            LEFT JOIN enrollments e ON c.id_course = e.course_id AND e.status = 'enrolled'
            LEFT JOIN students_extended se ON e.student_id = se.id_student
            LEFT JOIN users u ON se.user_id = u.id
            WHERE c.teacher_id = ? AND c.is_active = 1
            ORDER BY c.course_name, u.last_name, u.first_name
        ''', (teacher_id,))
        
        results = cursor.fetchall()
        courses = {}
        
        for row in results:
            course_id = row[0]
            if course_id not in courses:
                courses[course_id] = {
                    'id_course': row[0],
                    'course_name': row[1],
                    'course_code': row[2],
                    'students': []
                }
            
            if row[3]:  # If enrollment exists
                courses[course_id]['students'].append({
                    'enrollment_id': row[3],
                    'student_id': row[4],
                    'first_name': row[5],
                    'last_name': row[6],
                    'class_name': row[7],
                    'full_name': f"{row[5]} {row[6]}"
                })
        
        return list(courses.values())
        
    except Exception as e:
        print(f"Error getting courses with students: {e}")
        return []
    finally:
        conn.close()

def get_teacher_class_attendance(teacher_id, limit=None):
    """Get attendance records for teacher's classes"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Get students enrolled in teacher's courses
        cursor.execute('''
            SELECT DISTINCT e.prenom || ' ' || e.nom as student_name
            FROM courses c
            JOIN enrollments en ON c.id_course = en.course_id
            JOIN students_extended se ON en.student_id = se.id_student
            JOIN etudiants e ON se.etudiant_id = e.id_etudiant
            WHERE c.teacher_id = ? AND en.status = 'enrolled'
        ''', (teacher_id,))
        
        student_names = [row[0] for row in cursor.fetchall()]
        
        if not student_names:
            return []
        
        # Get attendance for these students
        placeholders = ','.join(['?' for _ in student_names])
        query = f'''
            SELECT nom, date, heure, timestamp
            FROM presences
            WHERE nom IN ({placeholders})
            ORDER BY timestamp DESC
        '''
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, student_names)
        results = cursor.fetchall()
        
        attendance = []
        for row in results:
            attendance.append({
                'student_name': row[0],
                'date': row[1],
                'time': row[2],
                'timestamp': row[3],
                'status': 'Present'
            })
        
        return attendance
        
    except Exception as e:
        print(f"Error getting class attendance: {e}")
        return []
    finally:
        conn.close()

def get_teacher_course_stats(teacher_id):
    """Get statistics for teacher's courses"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('''
            SELECT
                COUNT(*) as total_courses,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active_courses,
                (SELECT COUNT(*) FROM enrollments e JOIN courses c ON e.course_id = c.id_course
                 WHERE c.teacher_id = ? AND e.status = 'enrolled') as total_students
            FROM courses
            WHERE teacher_id = ?
        ''', (teacher_id, teacher_id))

        result = cursor.fetchone()

        if result:
            return {
                'total_courses': result[0],
                'active_courses': result[1],
                'total_students': result[2]
            }

        return {}

    except Exception as e:
        print(f"Error getting course stats: {e}")
        return {}
    finally:
        conn.close()
