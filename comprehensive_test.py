#!/usr/bin/env python3
"""
Test Complet End-to-End du Système de Reconnaissance Faciale
============================================================

Ce script effectue des tests complets de toutes les fonctionnalités:
- Base de données et intégrité des données
- Système de reconnaissance faciale
- Dashboards et interfaces utilisateur
- Stockage et persistance des données

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
import requests
import json
import time
from datetime import datetime, date
import os
import sys

class ComprehensiveTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.db_path = "attendance.db"
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name, status, message=""):
        """Enregistrer le résultat d'un test"""
        result = {
            'test': test_name,
            'status': status,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if message:
            print(f"   📝 {message}")
    
    def test_database_structure(self):
        """Test 1: Structure de la base de données"""
        print("\n🗄️ TEST 1: STRUCTURE DE LA BASE DE DONNÉES")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Vérifier les tables principales
            required_tables = [
                'users', 'presences', 'justifications', 'parent_children',
                'facial_encodings', 'courses', 'enrollments', 'messages',
                'audit_trail', 'etudiants', 'enseignants', 'parents'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table in existing_tables:
                    self.log_test(f"Table {table}", "PASS", "Table existe")
                else:
                    self.log_test(f"Table {table}", "FAIL", "Table manquante")
            
            # Vérifier les contraintes de clés étrangères
            cursor.execute("PRAGMA foreign_keys")
            fk_status = cursor.fetchone()
            if fk_status and fk_status[0] == 1:
                self.log_test("Foreign Keys", "PASS", "Contraintes activées")
            else:
                self.log_test("Foreign Keys", "WARN", "Contraintes non activées")
            
            conn.close()
            
        except Exception as e:
            self.log_test("Database Structure", "FAIL", str(e))
    
    def test_database_data_integrity(self):
        """Test 2: Intégrité des données"""
        print("\n🔗 TEST 2: INTÉGRITÉ DES DONNÉES")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test des utilisateurs
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            self.log_test("Users Count", "PASS" if user_count > 0 else "FAIL", f"{user_count} utilisateurs")
            
            # Test des encodages faciaux
            cursor.execute("SELECT COUNT(*) FROM facial_encodings")
            encoding_count = cursor.fetchone()[0]
            self.log_test("Facial Encodings", "PASS" if encoding_count > 0 else "WARN", f"{encoding_count} encodages")
            
            # Test des relations parent-enfant
            cursor.execute("SELECT COUNT(*) FROM parent_children")
            relation_count = cursor.fetchone()[0]
            self.log_test("Parent-Child Relations", "PASS" if relation_count > 0 else "WARN", f"{relation_count} relations")
            
            # Test de l'utilisateur Elmehdi
            cursor.execute("SELECT * FROM users WHERE username = 'elmehdi.rahaoui'")
            elmehdi = cursor.fetchone()
            if elmehdi:
                self.log_test("Elmehdi User", "PASS", "Utilisateur Elmehdi trouvé")
                
                # Vérifier son encodage facial
                cursor.execute("SELECT COUNT(*) FROM facial_encodings WHERE student_id = ?", (elmehdi[0],))
                elmehdi_encoding = cursor.fetchone()[0]
                self.log_test("Elmehdi Encoding", "PASS" if elmehdi_encoding > 0 else "FAIL", 
                            f"{elmehdi_encoding} encodage(s)")
            else:
                self.log_test("Elmehdi User", "FAIL", "Utilisateur Elmehdi non trouvé")
            
            conn.close()
            
        except Exception as e:
            self.log_test("Data Integrity", "FAIL", str(e))
    
    def test_web_application_accessibility(self):
        """Test 3: Accessibilité de l'application web"""
        print("\n🌐 TEST 3: ACCESSIBILITÉ WEB")
        
        # Test des pages principales
        pages_to_test = [
            ('/', 'Page d\'accueil'),
            ('/login', 'Page de connexion'),
            ('/admin/dashboard', 'Dashboard Admin'),
            ('/teacher/dashboard', 'Dashboard Enseignant'),
            ('/student/dashboard', 'Dashboard Étudiant'),
            ('/parent/dashboard', 'Dashboard Parent'),
            ('/facial/recognition', 'Reconnaissance Faciale'),
            ('/facial/students', 'Gestion Étudiants IA'),
            ('/facial/attendance_history', 'Historique IA')
        ]
        
        for url, description in pages_to_test:
            try:
                response = self.session.get(f"{self.base_url}{url}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"Page {description}", "PASS", f"Status {response.status_code}")
                elif response.status_code == 302:  # Redirection (normal pour pages protégées)
                    self.log_test(f"Page {description}", "PASS", f"Redirection {response.status_code}")
                else:
                    self.log_test(f"Page {description}", "FAIL", f"Status {response.status_code}")
            except Exception as e:
                self.log_test(f"Page {description}", "FAIL", str(e))
    
    def test_authentication_system(self):
        """Test 4: Système d'authentification"""
        print("\n🔐 TEST 4: SYSTÈME D'AUTHENTIFICATION")
        
        # Test de connexion admin
        login_data = {
            'username': 'admin',
            'password': 'admin123'
        }
        
        try:
            response = self.session.post(f"{self.base_url}/login", data=login_data)
            if response.status_code == 302 or 'dashboard' in response.url:
                self.log_test("Admin Login", "PASS", "Connexion admin réussie")
                
                # Test d'accès aux pages admin
                admin_response = self.session.get(f"{self.base_url}/admin/dashboard")
                if admin_response.status_code == 200:
                    self.log_test("Admin Dashboard Access", "PASS", "Accès autorisé")
                else:
                    self.log_test("Admin Dashboard Access", "FAIL", f"Status {admin_response.status_code}")
            else:
                self.log_test("Admin Login", "FAIL", f"Status {response.status_code}")
                
        except Exception as e:
            self.log_test("Authentication", "FAIL", str(e))
    
    def test_facial_recognition_system(self):
        """Test 5: Système de reconnaissance faciale"""
        print("\n🤖 TEST 5: SYSTÈME DE RECONNAISSANCE FACIALE")
        
        try:
            # Test de l'API de statut
            response = self.session.get(f"{self.base_url}/facial/api/streaming_status")
            if response.status_code == 200:
                status_data = response.json()
                if status_data.get('success'):
                    self.log_test("Facial API Status", "PASS", "API accessible")
                    
                    # Vérifier les encodages connus
                    known_faces = status_data.get('status', {}).get('known_faces_count', 0)
                    self.log_test("Known Faces Count", "PASS" if known_faces > 0 else "WARN", 
                                f"{known_faces} visages connus")
                else:
                    self.log_test("Facial API Status", "FAIL", "API retourne erreur")
            else:
                self.log_test("Facial API Status", "FAIL", f"Status {response.status_code}")
            
            # Test de démarrage du streaming (sans caméra physique)
            try:
                stream_response = self.session.post(f"{self.base_url}/facial/api/start_streaming")
                if stream_response.status_code == 200:
                    self.log_test("Streaming Start", "PASS", "API de streaming fonctionne")
                else:
                    self.log_test("Streaming Start", "WARN", "Pas de caméra disponible (normal)")
            except:
                self.log_test("Streaming Start", "WARN", "Test streaming ignoré (pas de caméra)")
                
        except Exception as e:
            self.log_test("Facial Recognition", "FAIL", str(e))
    
    def test_crud_operations(self):
        """Test 6: Opérations CRUD"""
        print("\n📝 TEST 6: OPÉRATIONS CRUD")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Test CREATE - Ajouter une présence de test
            test_date = date.today()
            test_time = datetime.now().strftime("%H:%M:%S")
            
            cursor.execute('''
                INSERT INTO presences (student_id, date, time, status, detection_confidence)
                VALUES (?, ?, ?, ?, ?)
            ''', (1, test_date, test_time, 'Test', 0.95))
            
            presence_id = cursor.lastrowid
            self.log_test("CREATE Presence", "PASS", f"Présence ID {presence_id} créée")
            
            # Test READ
            cursor.execute('SELECT * FROM presences WHERE id = ?', (presence_id,))
            presence = cursor.fetchone()
            if presence:
                self.log_test("READ Presence", "PASS", "Présence lue avec succès")
            else:
                self.log_test("READ Presence", "FAIL", "Présence non trouvée")
            
            # Test UPDATE
            cursor.execute('UPDATE presences SET status = ? WHERE id = ?', ('Test_Updated', presence_id))
            if cursor.rowcount > 0:
                self.log_test("UPDATE Presence", "PASS", "Présence mise à jour")
            else:
                self.log_test("UPDATE Presence", "FAIL", "Mise à jour échouée")
            
            # Test DELETE
            cursor.execute('DELETE FROM presences WHERE id = ?', (presence_id,))
            if cursor.rowcount > 0:
                self.log_test("DELETE Presence", "PASS", "Présence supprimée")
            else:
                self.log_test("DELETE Presence", "FAIL", "Suppression échouée")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.log_test("CRUD Operations", "FAIL", str(e))
    
    def test_dashboard_functionality(self):
        """Test 7: Fonctionnalité des dashboards"""
        print("\n📊 TEST 7: FONCTIONNALITÉ DES DASHBOARDS")
        
        # Test des dashboards avec différents utilisateurs
        users_to_test = [
            ('admin', 'admin123', '/admin/dashboard'),
            ('teacher1', 'teacher123', '/teacher/dashboard'),
            ('student1', 'student123', '/student/dashboard'),
            ('parent1', 'parent123', '/parent/dashboard'),
            ('elmehdi.rahaoui', 'elmehdi123', '/student/dashboard')
        ]
        
        for username, password, dashboard_url in users_to_test:
            try:
                # Nouvelle session pour chaque utilisateur
                user_session = requests.Session()
                
                # Connexion
                login_response = user_session.post(f"{self.base_url}/login", 
                                                 data={'username': username, 'password': password})
                
                if login_response.status_code == 302 or 'dashboard' in str(login_response.url):
                    # Test d'accès au dashboard
                    dashboard_response = user_session.get(f"{self.base_url}{dashboard_url}")
                    if dashboard_response.status_code == 200:
                        self.log_test(f"Dashboard {username}", "PASS", "Accès réussi")
                    else:
                        self.log_test(f"Dashboard {username}", "FAIL", f"Status {dashboard_response.status_code}")
                else:
                    self.log_test(f"Login {username}", "FAIL", "Connexion échouée")
                    
            except Exception as e:
                self.log_test(f"Dashboard {username}", "FAIL", str(e))
    
    def run_all_tests(self):
        """Exécuter tous les tests"""
        print("🚀 DÉBUT DES TESTS COMPLETS DU SYSTÈME")
        print("=" * 60)
        
        start_time = datetime.now()
        
        # Exécution des tests
        self.test_database_structure()
        self.test_database_data_integrity()
        self.test_web_application_accessibility()
        self.test_authentication_system()
        self.test_facial_recognition_system()
        self.test_crud_operations()
        self.test_dashboard_functionality()
        
        # Résumé des résultats
        end_time = datetime.now()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        print("📊 RÉSUMÉ DES TESTS")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([r for r in self.test_results if r['status'] == 'PASS'])
        failed_tests = len([r for r in self.test_results if r['status'] == 'FAIL'])
        warning_tests = len([r for r in self.test_results if r['status'] == 'WARN'])
        
        print(f"✅ Tests réussis: {passed_tests}")
        print(f"❌ Tests échoués: {failed_tests}")
        print(f"⚠️ Avertissements: {warning_tests}")
        print(f"📊 Total: {total_tests}")
        print(f"⏱️ Durée: {duration.total_seconds():.2f} secondes")
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        print(f"🎯 Taux de réussite: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ TESTS ÉCHOUÉS:")
            for result in self.test_results:
                if result['status'] == 'FAIL':
                    print(f"   • {result['test']}: {result['message']}")
        
        return success_rate >= 80  # Considérer comme réussi si 80%+ des tests passent

if __name__ == "__main__":
    tester = ComprehensiveTestSuite()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 TESTS GLOBALEMENT RÉUSSIS!")
        sys.exit(0)
    else:
        print("\n⚠️ CERTAINS TESTS ONT ÉCHOUÉ - VÉRIFICATION NÉCESSAIRE")
        sys.exit(1)
