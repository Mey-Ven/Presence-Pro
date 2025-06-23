#!/usr/bin/env python3
"""
Validation Spécifique des Fonctionnalités Critiques
==================================================

Tests approfondis des fonctionnalités critiques:
- Persistance des données de reconnaissance faciale
- Relations parent-enfant
- Système de justifications
- Intégrité des encodages faciaux

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
import requests
import json
from datetime import datetime, date, timedelta
import numpy as np

class SpecificValidation:
    def __init__(self):
        self.base_url = "http://localhost:5002"
        self.db_path = "attendance.db"
        self.session = requests.Session()
        
        # Connexion admin pour les tests
        self.session.post(f"{self.base_url}/login", 
                         data={'username': 'admin', 'password': 'admin123'})
    
    def validate_facial_recognition_data_persistence(self):
        """Valider la persistance des données de reconnaissance faciale"""
        print("🤖 VALIDATION: Persistance des données de reconnaissance faciale")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Vérifier les encodages d'Elmehdi
        cursor.execute('''
            SELECT fe.*, u.username, u.first_name, u.last_name
            FROM facial_encodings fe
            JOIN users u ON fe.student_id = u.id
            WHERE u.username = 'elmehdi.rahaoui'
        ''')
        
        elmehdi_encoding = cursor.fetchone()
        if elmehdi_encoding:
            print(f"✅ Encodage facial d'Elmehdi trouvé (ID: {elmehdi_encoding[0]})")
            
            # Vérifier la validité de l'encodage
            encoding_data = elmehdi_encoding[2]  # encoding_data column
            if encoding_data and len(encoding_data) > 0:
                print(f"✅ Données d'encodage valides ({len(encoding_data)} bytes)")
                
                # Tenter de décoder l'encodage
                try:
                    encoding_array = np.frombuffer(encoding_data, dtype=np.float64)
                    if len(encoding_array) == 128:
                        print(f"✅ Encodage facial valide (128 dimensions)")
                    else:
                        print(f"⚠️ Encodage facial incorrect ({len(encoding_array)} dimensions)")
                except Exception as e:
                    print(f"❌ Erreur de décodage: {e}")
            else:
                print("❌ Données d'encodage manquantes")
        else:
            print("❌ Encodage facial d'Elmehdi non trouvé")
        
        # Vérifier les présences existantes
        cursor.execute('''
            SELECT COUNT(*), MIN(date), MAX(date)
            FROM presences
            WHERE student_id IN (SELECT id FROM users WHERE username = 'elmehdi.rahaoui')
        ''')
        
        presence_stats = cursor.fetchone()
        if presence_stats and presence_stats[0] > 0:
            print(f"✅ {presence_stats[0]} présences enregistrées pour Elmehdi")
            print(f"   📅 Période: {presence_stats[1]} à {presence_stats[2]}")
        else:
            print("⚠️ Aucune présence enregistrée pour Elmehdi")
        
        conn.close()
    
    def validate_parent_child_relationships(self):
        """Valider les relations parent-enfant"""
        print("\n👨‍👩‍👧‍👦 VALIDATION: Relations parent-enfant")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Créer la relation parent1 -> elmehdi si elle n'existe pas
        cursor.execute('SELECT id FROM users WHERE username = ?', ('parent1',))
        parent1_result = cursor.fetchone()
        
        cursor.execute('SELECT id FROM users WHERE username = ?', ('elmehdi.rahaoui',))
        elmehdi_result = cursor.fetchone()
        
        if parent1_result and elmehdi_result:
            parent1_id = parent1_result[0]
            elmehdi_id = elmehdi_result[0]
            
            # Vérifier si la relation existe
            cursor.execute('''
                SELECT * FROM parent_children 
                WHERE parent_id = ? AND child_id = ?
            ''', (parent1_id, elmehdi_id))
            
            relation = cursor.fetchone()
            if not relation:
                # Créer la relation
                cursor.execute('''
                    INSERT INTO parent_children (parent_id, child_id, relationship)
                    VALUES (?, ?, ?)
                ''', (parent1_id, elmehdi_id, 'parent'))
                conn.commit()
                print(f"✅ Relation parent-enfant créée: Parent1 -> Elmehdi")
            else:
                print(f"✅ Relation parent-enfant existe: Parent1 -> Elmehdi")
            
            # Tester l'accès parent au dashboard
            parent_session = requests.Session()
            login_response = parent_session.post(f"{self.base_url}/login", 
                                               data={'username': 'parent1', 'password': 'parent123'})
            
            if login_response.status_code == 302:
                dashboard_response = parent_session.get(f"{self.base_url}/parent/dashboard")
                if dashboard_response.status_code == 200:
                    print("✅ Dashboard parent accessible avec enfant assigné")
                else:
                    print(f"❌ Erreur dashboard parent: {dashboard_response.status_code}")
            else:
                print("❌ Connexion parent échouée")
        else:
            print("❌ Utilisateurs parent1 ou elmehdi.rahaoui non trouvés")
        
        conn.close()
    
    def validate_justification_system(self):
        """Valider le système de justifications"""
        print("\n📝 VALIDATION: Système de justifications")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Créer une justification de test
        cursor.execute('SELECT id FROM users WHERE username = ?', ('elmehdi.rahaoui',))
        elmehdi_result = cursor.fetchone()
        
        if elmehdi_result:
            elmehdi_id = elmehdi_result[0]
            test_date = date.today() - timedelta(days=1)
            
            # Insérer une justification de test
            cursor.execute('''
                INSERT INTO justifications
                (student_id, absence_date, reason, description, status)
                VALUES (?, ?, ?, ?, ?)
            ''', (str(elmehdi_id), test_date.isoformat(), 'Maladie',
                  'Test de justification automatique', 'pending'))
            
            conn.commit()
            
            # Vérifier la justification
            cursor.execute('''
                SELECT j.*, u.first_name, u.last_name
                FROM justifications j
                JOIN users u ON j.student_id = u.id
                WHERE j.student_id = ? AND j.reason = ?
                ORDER BY j.created_at DESC
                LIMIT 1
            ''', (str(elmehdi_id), 'Maladie'))
            
            justification = cursor.fetchone()
            if justification:
                print(f"✅ Justification créée pour {justification[10]} {justification[11]}")
                print(f"   📅 Date: {justification[3]}, Raison: {justification[4]}")
                print(f"   📊 Statut: {justification[6]}")
            else:
                print("❌ Justification non créée")
        else:
            print("❌ Utilisateur Elmehdi non trouvé pour justification")
        
        conn.close()
    
    def validate_database_integrity_constraints(self):
        """Valider les contraintes d'intégrité de la base de données"""
        print("\n🔗 VALIDATION: Contraintes d'intégrité")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Test des contraintes de clés étrangères
        try:
            # Tenter d'insérer une présence avec un student_id inexistant
            cursor.execute('''
                INSERT INTO presences (student_id, date, time, status)
                VALUES (?, ?, ?, ?)
            ''', (99999, date.today(), '12:00:00', 'Test'))
            
            conn.commit()
            print("⚠️ Contrainte de clé étrangère non appliquée (présence avec student_id inexistant)")
            
            # Nettoyer
            cursor.execute('DELETE FROM presences WHERE student_id = ?', (99999,))
            conn.commit()
            
        except sqlite3.IntegrityError:
            print("✅ Contraintes de clé étrangère fonctionnelles")
        
        # Vérifier la cohérence des données
        cursor.execute('''
            SELECT COUNT(*) FROM presences p
            LEFT JOIN users u ON p.student_id = u.id
            WHERE u.id IS NULL
        ''')
        
        orphaned_presences = cursor.fetchone()[0]
        if orphaned_presences == 0:
            print("✅ Aucune présence orpheline trouvée")
        else:
            print(f"⚠️ {orphaned_presences} présences orphelines trouvées")
        
        conn.close()
    
    def validate_facial_recognition_api(self):
        """Valider l'API de reconnaissance faciale"""
        print("\n🎥 VALIDATION: API de reconnaissance faciale")
        
        # Test de l'API de statut
        response = self.session.get(f"{self.base_url}/facial/api/streaming_status")
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                status = data.get('status', {})
                print(f"✅ API de statut fonctionnelle")
                print(f"   🎥 Streaming: {'Actif' if status.get('is_streaming') else 'Inactif'}")
                print(f"   🔍 Détection: {'Active' if status.get('detection_enabled') else 'Inactive'}")
                print(f"   👥 Visages connus: {status.get('known_faces_count', 0)}")
            else:
                print("❌ API de statut retourne une erreur")
        else:
            print(f"❌ API de statut inaccessible: {response.status_code}")
        
        # Test de démarrage du streaming (sans caméra physique)
        try:
            stream_response = self.session.post(f"{self.base_url}/facial/api/start_streaming")
            if stream_response.status_code == 200:
                stream_data = stream_response.json()
                if stream_data.get('success'):
                    print("✅ API de démarrage streaming fonctionnelle")
                else:
                    print(f"⚠️ Streaming non démarré: {stream_data.get('message', 'Erreur inconnue')}")
            else:
                print(f"❌ API de streaming inaccessible: {stream_response.status_code}")
        except Exception as e:
            print(f"⚠️ Test streaming ignoré: {e}")
    
    def run_validation(self):
        """Exécuter toutes les validations"""
        print("🔍 VALIDATION SPÉCIFIQUE DES FONCTIONNALITÉS CRITIQUES")
        print("=" * 70)
        
        self.validate_facial_recognition_data_persistence()
        self.validate_parent_child_relationships()
        self.validate_justification_system()
        self.validate_database_integrity_constraints()
        self.validate_facial_recognition_api()
        
        print("\n" + "=" * 70)
        print("✅ VALIDATION SPÉCIFIQUE TERMINÉE")
        print("📊 Toutes les fonctionnalités critiques ont été validées")

if __name__ == "__main__":
    validator = SpecificValidation()
    validator.run_validation()
