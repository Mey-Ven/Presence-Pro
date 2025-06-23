#!/usr/bin/env python3
"""
Enhanced Database Schema for Role-Based Facial Recognition Attendance System
===========================================================================

This module extends the existing database with comprehensive tables for:
- Multi-role user management (admin, teacher, student, parent)
- Course and schedule management
- Grade management system
- Absence justification system
- Messaging and notification system
- Audit trail functionality

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
import hashlib
import uuid
from datetime import datetime
import os

DATABASE_FILE = "attendance.db"

def get_connection():
    """Get database connection"""
    return sqlite3.connect(DATABASE_FILE)

def create_enhanced_tables():
    """Create all enhanced tables for role-based system"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Enhanced Users table (unified authentication)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'teacher', 'student', 'parent')),
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                phone TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                profile_image TEXT
            )
        ''')
        
        # Teachers table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                id_teacher TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                employee_id TEXT UNIQUE,
                department TEXT,
                specialization TEXT,
                hire_date DATE,
                salary DECIMAL(10,2),
                office_location TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Parents table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parents (
                id_parent TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                address TEXT,
                emergency_contact TEXT,
                occupation TEXT,
                relationship_to_student TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Enhanced Students table (link to existing etudiants)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS students_extended (
                id_student TEXT PRIMARY KEY,
                user_id TEXT,
                etudiant_id TEXT,
                parent_id TEXT,
                class_name TEXT,
                enrollment_date DATE,
                graduation_date DATE,
                status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'graduated', 'transferred')),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (etudiant_id) REFERENCES etudiants(id_etudiant),
                FOREIGN KEY (parent_id) REFERENCES parents(id_parent)
            )
        ''')
        
        # Courses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                id_course TEXT PRIMARY KEY,
                course_code TEXT UNIQUE NOT NULL,
                course_name TEXT NOT NULL,
                description TEXT,
                credits INTEGER DEFAULT 3,
                teacher_id TEXT,
                department TEXT,
                semester TEXT,
                academic_year TEXT,
                max_students INTEGER DEFAULT 30,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (teacher_id) REFERENCES teachers(id_teacher)
            )
        ''')
        
        # Class Schedules table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS schedules (
                id_schedule TEXT PRIMARY KEY,
                course_id TEXT NOT NULL,
                day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 1 AND 7),
                start_time TIME NOT NULL,
                end_time TIME NOT NULL,
                classroom TEXT,
                building TEXT,
                effective_date DATE,
                expiry_date DATE,
                FOREIGN KEY (course_id) REFERENCES courses(id_course) ON DELETE CASCADE
            )
        ''')
        
        # Student Course Enrollments
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                id_enrollment TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                course_id TEXT NOT NULL,
                enrollment_date DATE DEFAULT (date('now')),
                status TEXT DEFAULT 'enrolled' CHECK (status IN ('enrolled', 'dropped', 'completed')),
                final_grade DECIMAL(5,2),
                FOREIGN KEY (student_id) REFERENCES students_extended(id_student) ON DELETE CASCADE,
                FOREIGN KEY (course_id) REFERENCES courses(id_course) ON DELETE CASCADE,
                UNIQUE(student_id, course_id)
            )
        ''')
        
        # Grades table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                id_grade TEXT PRIMARY KEY,
                enrollment_id TEXT NOT NULL,
                assessment_type TEXT NOT NULL CHECK (assessment_type IN ('quiz', 'exam', 'assignment', 'project', 'participation')),
                assessment_name TEXT NOT NULL,
                points_earned DECIMAL(5,2),
                points_possible DECIMAL(5,2),
                percentage DECIMAL(5,2),
                grade_letter TEXT,
                assessment_date DATE,
                due_date DATE,
                comments TEXT,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(id_enrollment) ON DELETE CASCADE,
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')
        
        # Absence Justifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS absence_justifications (
                id_justification TEXT PRIMARY KEY,
                student_id TEXT NOT NULL,
                absence_date DATE NOT NULL,
                reason TEXT NOT NULL,
                description TEXT,
                supporting_document TEXT,
                submitted_by TEXT NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
                reviewed_by TEXT,
                reviewed_at TIMESTAMP,
                review_comments TEXT,
                FOREIGN KEY (student_id) REFERENCES students_extended(id_student) ON DELETE CASCADE,
                FOREIGN KEY (submitted_by) REFERENCES users(id),
                FOREIGN KEY (reviewed_by) REFERENCES users(id)
            )
        ''')
        
        # Messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id_message TEXT PRIMARY KEY,
                sender_id TEXT NOT NULL,
                recipient_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'general' CHECK (message_type IN ('general', 'attendance', 'grade', 'announcement', 'alert')),
                is_read BOOLEAN DEFAULT 0,
                is_urgent BOOLEAN DEFAULT 0,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                read_at TIMESTAMP,
                parent_message_id TEXT,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (recipient_id) REFERENCES users(id),
                FOREIGN KEY (parent_message_id) REFERENCES messages(id_message)
            )
        ''')
        
        # Notifications table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id_notification TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                notification_type TEXT DEFAULT 'info' CHECK (notification_type IN ('info', 'warning', 'error', 'success')),
                is_read BOOLEAN DEFAULT 0,
                action_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Audit Trail table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_trail (
                id_audit TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                action TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id TEXT,
                old_values TEXT,
                new_values TEXT,
                ip_address TEXT,
                user_agent TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        
        # System Settings table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                setting_type TEXT DEFAULT 'string' CHECK (setting_type IN ('string', 'integer', 'boolean', 'json')),
                description TEXT,
                is_public BOOLEAN DEFAULT 0,
                updated_by TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (updated_by) REFERENCES users(id)
            )
        ''')
        
        # Create presences table for facial recognition attendance
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS presences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                course_id TEXT,
                date DATE NOT NULL,
                time TIME NOT NULL,
                status TEXT DEFAULT 'Present',
                detection_confidence REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (course_id) REFERENCES courses(id_course)
            )
        ''')

        # Create etudiants table for compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS etudiants (
                id_student TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                classe TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_student) REFERENCES users(id)
            )
        ''')

        # Create enseignants table for compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enseignants (
                id_teacher TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                department TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_teacher) REFERENCES users(id)
            )
        ''')

        # Create parents table for compatibility
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS parents (
                id_parent TEXT PRIMARY KEY,
                nom TEXT NOT NULL,
                prenom TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (id_parent) REFERENCES users(id)
            )
        ''')

        # Create facial_encodings table for face recognition
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facial_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT NOT NULL,
                encoding_data BLOB NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        ''')

        # Create attendance_sessions table for tracking recognition sessions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_name TEXT NOT NULL,
                course_id TEXT,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                status TEXT DEFAULT 'active',
                created_by TEXT,
                FOREIGN KEY (course_id) REFERENCES courses(id_course),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        ''')

        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_schedules_day_time ON schedules(day_of_week, start_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_grades_enrollment ON grades(enrollment_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_recipient ON messages(recipient_id, is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_audit_user_date ON audit_trail(user_id, created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_presences_student_date ON presences(student_id, date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_facial_encodings_student ON facial_encodings(student_id)')
        
        conn.commit()
        print("✅ Enhanced database tables created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating enhanced tables: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

def insert_default_admin():
    """Insert default admin user if not exists"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Check if admin exists
        cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
        if cursor.fetchone():
            print("✅ Admin user already exists")
            return
        
        # Create default admin
        admin_id = str(uuid.uuid4())
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()
        
        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (admin_id, 'admin', 'admin@school.com', password_hash, 'admin', 'System', 'Administrator', '+1234567890'))
        
        # Create default teacher
        teacher_id = str(uuid.uuid4())
        teacher_password_hash = hashlib.sha256("teacher123".encode()).hexdigest()

        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_id, 'teacher1', 'teacher1@school.com', teacher_password_hash, 'teacher', 'Jean', 'Dupont', '+1234567891'))

        # Create default student
        student_id = str(uuid.uuid4())
        student_password_hash = hashlib.sha256("student123".encode()).hexdigest()

        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (student_id, 'student1', 'student1@school.com', student_password_hash, 'student', 'Marie', 'Martin', '+1234567892'))

        # Create default parent
        parent_id = str(uuid.uuid4())
        parent_password_hash = hashlib.sha256("parent123".encode()).hexdigest()

        cursor.execute('''
            INSERT INTO users (id, username, email, password_hash, role, first_name, last_name, phone)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (parent_id, 'parent1', 'parent1@school.com', parent_password_hash, 'parent', 'Pierre', 'Durand', '+1234567893'))

        # Insert corresponding records in compatibility tables
        cursor.execute('''
            INSERT OR IGNORE INTO enseignants (id_teacher, nom, prenom, email, phone, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (teacher_id, 'Dupont', 'Jean', 'teacher1@school.com', '+1234567891', 'Mathématiques'))

        cursor.execute('''
            INSERT OR IGNORE INTO etudiants (id_student, nom, prenom, email, phone, classe)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (student_id, 'Martin', 'Marie', 'student1@school.com', '+1234567892', 'Terminale S'))

        cursor.execute('''
            INSERT OR IGNORE INTO parents (id_parent, nom, prenom, email, phone)
            VALUES (?, ?, ?, ?, ?)
        ''', (parent_id, 'Durand', 'Pierre', 'parent1@school.com', '+1234567893'))

        conn.commit()
        print("✅ Default users created:")
        print("   Admin: admin / admin123")
        print("   Teacher: teacher1 / teacher123")
        print("   Student: student1 / student123")
        print("   Parent: parent1 / parent123")
        
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        conn.rollback()
    finally:
        conn.close()

def insert_sample_data():
    """Insert sample data for testing"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Sample teacher
        teacher_user_id = str(uuid.uuid4())
        teacher_id = str(uuid.uuid4())
        password_hash = hashlib.sha256("teacher123".encode()).hexdigest()
        
        cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, email, password_hash, role, first_name, last_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (teacher_user_id, 'teacher1', 'teacher@school.com', password_hash, 'teacher', 'John', 'Smith'))
        
        cursor.execute('''
            INSERT OR IGNORE INTO teachers (id_teacher, user_id, employee_id, department, specialization)
            VALUES (?, ?, ?, ?, ?)
        ''', (teacher_id, teacher_user_id, 'T001', 'Computer Science', 'Programming'))
        
        # Sample course
        course_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR IGNORE INTO courses (id_course, course_code, course_name, description, teacher_id, department)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (course_id, 'CS101', 'Introduction to Programming', 'Basic programming concepts', teacher_id, 'Computer Science'))
        
        # Sample schedule
        schedule_id = str(uuid.uuid4())
        cursor.execute('''
            INSERT OR IGNORE INTO schedules (id_schedule, course_id, day_of_week, start_time, end_time, classroom)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (schedule_id, course_id, 1, '09:00', '10:30', 'Room 101'))
        
        conn.commit()
        print("✅ Sample data inserted successfully!")
        
    except Exception as e:
        print(f"❌ Error inserting sample data: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("🔧 Setting up enhanced database schema...")
    create_enhanced_tables()
    insert_default_admin()
    insert_sample_data()
    print("🎉 Enhanced database setup completed!")
