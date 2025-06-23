#!/usr/bin/env python3
"""
Authentication and Role Management System
========================================

This module provides comprehensive authentication and authorization
functionality for the role-based facial recognition attendance system.

Features:
- Multi-role authentication (admin, teacher, student, parent)
- Session management with security
- Role-based access control
- Password management and security
- User profile management

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
import hashlib
import uuid
import secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import session, request, redirect, url_for, flash, jsonify
import json

DATABASE_FILE = "attendance.db"

class AuthManager:
    """Authentication and authorization manager"""
    
    def __init__(self):
        self.session_timeout = 3600  # 1 hour in seconds
    
    def get_connection(self):
        """Get database connection"""
        return sqlite3.connect(DATABASE_FILE)
    
    def hash_password(self, password):
        """Hash password with salt"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def verify_password(self, password, hashed_password):
        """Verify password against hash"""
        try:
            salt, stored_hash = hashed_password.split(':')
            password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return password_hash.hex() == stored_hash
        except:
            # Fallback for old SHA256 hashes
            return hashlib.sha256(password.encode()).hexdigest() == hashed_password
    
    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, email, password_hash, role, first_name, last_name, is_active
                FROM users 
                WHERE (username = ? OR email = ?) AND is_active = 1
            ''', (username, username))
            
            user = cursor.fetchone()
            
            if user and self.verify_password(password, user[3]):
                # Update last login
                cursor.execute('''
                    UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?
                ''', (user[0],))
                conn.commit()
                
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[4],
                    'first_name': user[5],
                    'last_name': user[6],
                    'full_name': f"{user[5]} {user[6]}"
                }
            
            return None
            
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
        finally:
            conn.close()
    
    def create_user(self, username, email, password, role, first_name, last_name, phone=None):
        """Create new user account"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Check if user exists
            cursor.execute('''
                SELECT id FROM users WHERE username = ? OR email = ?
            ''', (username, email))
            
            if cursor.fetchone():
                return False, "User already exists"
            
            # Create user
            user_id = str(uuid.uuid4())
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, role, first_name, last_name, phone)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, role, first_name, last_name, phone))
            
            conn.commit()
            return True, user_id
            
        except Exception as e:
            print(f"User creation error: {e}")
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def get_user_by_id(self, user_id):
        """Get user information by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, email, role, first_name, last_name, phone, is_active, created_at, last_login
                FROM users WHERE id = ?
            ''', (user_id,))
            
            user = cursor.fetchone()
            if user:
                return {
                    'id': user[0],
                    'username': user[1],
                    'email': user[2],
                    'role': user[3],
                    'first_name': user[4],
                    'last_name': user[5],
                    'phone': user[6],
                    'is_active': user[7],
                    'created_at': user[8],
                    'last_login': user[9],
                    'full_name': f"{user[4]} {user[5]}"
                }
            return None
            
        except Exception as e:
            print(f"Get user error: {e}")
            return None
        finally:
            conn.close()
    
    def update_user_profile(self, user_id, **kwargs):
        """Update user profile information"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Build dynamic update query
            allowed_fields = ['first_name', 'last_name', 'email', 'phone']
            updates = []
            values = []
            
            for field, value in kwargs.items():
                if field in allowed_fields and value is not None:
                    updates.append(f"{field} = ?")
                    values.append(value)
            
            if not updates:
                return False, "No valid fields to update"
            
            values.append(user_id)
            query = f"UPDATE users SET {', '.join(updates)} WHERE id = ?"
            
            cursor.execute(query, values)
            conn.commit()
            
            return True, "Profile updated successfully"
            
        except Exception as e:
            print(f"Profile update error: {e}")
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def change_password(self, user_id, old_password, new_password):
        """Change user password"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # Verify old password
            cursor.execute('SELECT password_hash FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result or not self.verify_password(old_password, result[0]):
                return False, "Current password is incorrect"
            
            # Update password
            new_hash = self.hash_password(new_password)
            cursor.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_hash, user_id))
            conn.commit()
            
            return True, "Password changed successfully"
            
        except Exception as e:
            print(f"Password change error: {e}")
            conn.rollback()
            return False, str(e)
        finally:
            conn.close()
    
    def get_users_by_role(self, role):
        """Get all users with specific role"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                SELECT id, username, email, first_name, last_name, phone, is_active, created_at, last_login
                FROM users WHERE role = ? ORDER BY last_name, first_name
            ''', (role,))
            
            users = []
            for row in cursor.fetchall():
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'first_name': row[3],
                    'last_name': row[4],
                    'phone': row[5],
                    'is_active': row[6],
                    'created_at': row[7],
                    'last_login': row[8],
                    'full_name': f"{row[3]} {row[4]}"
                })
            
            return users
            
        except Exception as e:
            print(f"Get users by role error: {e}")
            return []
        finally:
            conn.close()

# Global auth manager instance
auth_manager = AuthManager()

def login_required(f):
    """Decorator to require login for routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json:
                return jsonify({'error': 'Authentication required'}), 401
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator to require specific roles for routes"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login'))
            
            user_role = session.get('user_role')
            if user_role not in allowed_roles:
                if request.is_json:
                    return jsonify({'error': 'Insufficient permissions'}), 403
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_current_user():
    """Get current logged-in user information"""
    if 'user_id' not in session:
        return None
    
    return {
        'id': session['user_id'],
        'username': session['username'],
        'email': session['email'],
        'role': session['user_role'],
        'first_name': session['first_name'],
        'last_name': session['last_name'],
        'full_name': session['full_name']
    }

def log_audit_trail(user_id, action, table_name, record_id=None, old_values=None, new_values=None):
    """Log audit trail for important actions"""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    try:
        audit_id = str(uuid.uuid4())
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        
        cursor.execute('''
            INSERT INTO audit_trail (id_audit, user_id, action, table_name, record_id, old_values, new_values, ip_address, user_agent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (audit_id, user_id, action, table_name, record_id, 
              json.dumps(old_values) if old_values else None,
              json.dumps(new_values) if new_values else None,
              ip_address, user_agent))
        
        conn.commit()
        
    except Exception as e:
        print(f"Audit trail error: {e}")
        conn.rollback()
    finally:
        conn.close()
