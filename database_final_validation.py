#!/usr/bin/env python3
"""
Validation Finale de la Base de Données
=======================================

Validation complète de l'état de la base de données après tous les tests

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
from datetime import datetime

def validate_database_final_state():
    """Validation finale de l'état de la base de données"""
    print("🗄️ VALIDATION FINALE DE LA BASE DE DONNÉES")
    print("=" * 60)
    
    conn = sqlite3.connect("attendance.db")
    cursor = conn.cursor()
    
    # 1. Compter les enregistrements dans chaque table
    tables = [
        'users', 'presences', 'justifications', 'parent_children',
        'facial_encodings', 'courses', 'enrollments', 'messages',
        'audit_trail', 'etudiants', 'enseignants', 'parents'
    ]
    
    print("📊 NOMBRE D'ENREGISTREMENTS PAR TABLE:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table:20}: {count:4} enregistrements")
        except Exception as e:
            print(f"   {table:20}: ❌ Erreur - {e}")
    
    print("\n👥 UTILISATEURS DÉTAILLÉS:")
    cursor.execute('''
        SELECT id, username, first_name, last_name, role, is_active
        FROM users
        ORDER BY role, username
    ''')
    
    for user in cursor.fetchall():
        status = "✅ Actif" if user[5] else "❌ Inactif"
        print(f"   {user[1]:20} | {user[2]} {user[3]:15} | {user[4]:10} | {status}")
    
    print("\n🤖 ENCODAGES FACIAUX:")
    cursor.execute('''
        SELECT fe.id, u.username, u.first_name, u.last_name, fe.image_path
        FROM facial_encodings fe
        JOIN users u ON fe.student_id = u.id
    ''')
    
    for encoding in cursor.fetchall():
        print(f"   ID {encoding[0]:2} | {encoding[1]:20} | {encoding[2]} {encoding[3]:15} | {encoding[4]}")
    
    print("\n📅 PRÉSENCES RÉCENTES:")
    cursor.execute('''
        SELECT p.date, p.time, u.first_name, u.last_name, p.status, p.detection_confidence
        FROM presences p
        JOIN users u ON p.student_id = u.id
        ORDER BY p.date DESC, p.time DESC
        LIMIT 10
    ''')
    
    for presence in cursor.fetchall():
        confidence = f"{presence[5]:.1%}" if presence[5] else "N/A"
        print(f"   {presence[0]} {presence[1]} | {presence[2]} {presence[3]:15} | {presence[4]:10} | {confidence}")
    
    print("\n📝 JUSTIFICATIONS:")
    cursor.execute('''
        SELECT j.id, u.first_name, u.last_name, j.absence_date, j.reason, j.status
        FROM justifications j
        JOIN users u ON j.student_id = u.id
        ORDER BY j.created_at DESC
    ''')
    
    for justification in cursor.fetchall():
        print(f"   ID {justification[0]:2} | {justification[1]} {justification[2]:15} | {justification[3]} | {justification[4]:15} | {justification[5]}")
    
    print("\n👨‍👩‍👧‍👦 RELATIONS PARENT-ENFANT:")
    cursor.execute('''
        SELECT 
            up.first_name || ' ' || up.last_name as parent_name,
            uc.first_name || ' ' || uc.last_name as child_name,
            pc.relationship
        FROM parent_children pc
        JOIN users up ON pc.parent_id = up.id
        JOIN users uc ON pc.child_id = uc.id
    ''')
    
    for relation in cursor.fetchall():
        print(f"   {relation[0]:20} -> {relation[1]:20} ({relation[2]})")
    
    print("\n📊 STATISTIQUES GÉNÉRALES:")
    
    # Utilisateurs actifs par rôle
    cursor.execute('''
        SELECT role, COUNT(*) as count
        FROM users
        WHERE is_active = 1
        GROUP BY role
    ''')
    
    print("   Utilisateurs actifs par rôle:")
    for role_stat in cursor.fetchall():
        print(f"     {role_stat[0]:15}: {role_stat[1]} utilisateurs")
    
    # Présences par jour (derniers 7 jours)
    cursor.execute('''
        SELECT date, COUNT(*) as count
        FROM presences
        WHERE date >= date('now', '-7 days')
        GROUP BY date
        ORDER BY date DESC
    ''')
    
    print("   Présences par jour (7 derniers jours):")
    for day_stat in cursor.fetchall():
        print(f"     {day_stat[0]}: {day_stat[1]} présences")
    
    # Justifications par statut
    cursor.execute('''
        SELECT status, COUNT(*) as count
        FROM justifications
        GROUP BY status
    ''')
    
    print("   Justifications par statut:")
    for status_stat in cursor.fetchall():
        print(f"     {status_stat[0]:15}: {status_stat[1]} justifications")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ VALIDATION FINALE TERMINÉE")
    print(f"📅 Date de validation: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    validate_database_final_state()
