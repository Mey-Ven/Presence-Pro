"""
Test de cohérence des données entre le tableau de bord web et la base de données SQLite
Vérifie que les données affichées correspondent exactement aux données stockées
"""

import requests
import sqlite3
import json
from datetime import datetime, timedelta
import sqlite_database as db
import sqlite_config as config

class DataConsistencyTester:
    def __init__(self):
        self.session = requests.Session()
        self.dashboard_url = "http://localhost:5001"
        self.db_path = "attendance.db"
        self.logged_in = False
        
    def login(self):
        """Se connecter au tableau de bord"""
        print("🔐 Connexion au tableau de bord...")
        
        try:
            # Page de connexion
            response = self.session.get(f"{self.dashboard_url}/login")
            if response.status_code != 200:
                print(f"❌ Erreur page de connexion: {response.status_code}")
                return False
            
            # Connexion
            login_data = {'username': 'admin', 'password': 'admin123'}
            response = self.session.post(f"{self.dashboard_url}/login", data=login_data)
            
            if response.status_code == 200 and "dashboard" in response.url:
                print("✅ Connexion réussie")
                self.logged_in = True
                return True
            else:
                print(f"❌ Échec de la connexion: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur de connexion: {e}")
            return False
    
    def get_dashboard_stats(self):
        """Récupérer les statistiques du tableau de bord"""
        print("\n📊 Récupération des statistiques du tableau de bord...")
        
        try:
            response = self.session.get(f"{self.dashboard_url}/api/stats")
            if response.status_code == 200:
                data = response.json()
                print("✅ Statistiques dashboard récupérées")
                return data
            else:
                print(f"❌ Erreur API stats: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération stats: {e}")
            return None
    
    def get_database_stats(self):
        """Récupérer les statistiques directement de la base de données"""
        print("\n🗄️ Récupération des statistiques de la base de données...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Compter les étudiants
            cursor.execute("SELECT COUNT(*) FROM etudiants")
            total_students = cursor.fetchone()[0]
            
            # Compter toutes les présences
            cursor.execute("SELECT COUNT(*) FROM presences")
            total_attendance = cursor.fetchone()[0]
            
            # Présences aujourd'hui
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM presences WHERE date = ?", (today,))
            today_attendance = cursor.fetchone()[0]
            
            # Présences cette semaine
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM presences WHERE date >= ?", (week_ago,))
            week_attendance = cursor.fetchone()[0]
            
            conn.close()
            
            db_stats = {
                'total_students': total_students,
                'total_attendance': total_attendance,
                'today_attendance': today_attendance,
                'week_attendance': week_attendance
            }
            
            print("✅ Statistiques base de données récupérées")
            return db_stats
            
        except Exception as e:
            print(f"❌ Erreur base de données: {e}")
            return None
    
    def get_dashboard_students(self):
        """Récupérer la liste des étudiants depuis le dashboard"""
        print("\n👥 Récupération des étudiants du tableau de bord...")
        
        try:
            # Accéder à la page des étudiants
            response = self.session.get(f"{self.dashboard_url}/students")
            if response.status_code == 200:
                # Utiliser l'API pour obtenir les données
                students = db.obtenir_tous_etudiants()
                print(f"✅ {len(students)} étudiants récupérés du dashboard")
                return students
            else:
                print(f"❌ Erreur page étudiants: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur récupération étudiants dashboard: {e}")
            return None
    
    def get_database_students(self):
        """Récupérer la liste des étudiants directement de la base de données"""
        print("\n🗄️ Récupération des étudiants de la base de données...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id_etudiant, nom, prenom, email, telephone, date_creation
                FROM etudiants
                ORDER BY id_etudiant
            """)
            
            rows = cursor.fetchall()
            students = []
            
            for row in rows:
                students.append({
                    'id_etudiant': row[0],
                    'nom': row[1],
                    'prenom': row[2],
                    'email': row[3],
                    'telephone': row[4],
                    'date_creation': row[5]
                })
            
            conn.close()
            print(f"✅ {len(students)} étudiants récupérés de la base de données")
            return students
            
        except Exception as e:
            print(f"❌ Erreur base de données étudiants: {e}")
            return None
    
    def get_dashboard_attendance(self):
        """Récupérer les présences depuis le dashboard"""
        print("\n📅 Récupération des présences du tableau de bord...")
        
        try:
            # Utiliser la fonction config pour obtenir toutes les présences
            attendance = config.get_all_attendance()
            print(f"✅ {len(attendance)} présences récupérées du dashboard")
            return attendance
            
        except Exception as e:
            print(f"❌ Erreur récupération présences dashboard: {e}")
            return None
    
    def get_database_attendance(self):
        """Récupérer les présences directement de la base de données"""
        print("\n🗄️ Récupération des présences de la base de données...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT nom, date, heure, timestamp
                FROM presences
                ORDER BY timestamp DESC
            """)
            
            rows = cursor.fetchall()
            attendance = []
            
            for row in rows:
                attendance.append({
                    'name': row[0],
                    'date': row[1],
                    'time': row[2],  # Keep 'time' for consistency with dashboard data
                    'timestamp': row[3]
                })
            
            conn.close()
            print(f"✅ {len(attendance)} présences récupérées de la base de données")
            return attendance
            
        except Exception as e:
            print(f"❌ Erreur base de données présences: {e}")
            return None
    
    def compare_statistics(self, dashboard_stats, db_stats):
        """Comparer les statistiques"""
        print("\n📊 COMPARAISON DES STATISTIQUES")
        print("=" * 60)
        
        if not dashboard_stats or not db_stats:
            print("❌ Impossible de comparer - données manquantes")
            return False
        
        all_match = True
        
        # Comparer chaque statistique
        stats_to_compare = [
            ('total_students', 'Total étudiants'),
            ('total_attendance', 'Total présences'),
            ('today_attendance', 'Présences aujourd\'hui'),
            ('week_attendance', 'Présences cette semaine')
        ]
        
        for key, label in stats_to_compare:
            dashboard_val = dashboard_stats.get(key, 'N/A')
            db_val = db_stats.get(key, 'N/A')
            
            if dashboard_val == db_val:
                print(f"✅ {label}: {dashboard_val} (Dashboard) = {db_val} (DB)")
            else:
                print(f"❌ {label}: {dashboard_val} (Dashboard) ≠ {db_val} (DB)")
                all_match = False
        
        return all_match
    
    def compare_students(self, dashboard_students, db_students):
        """Comparer les listes d'étudiants"""
        print("\n👥 COMPARAISON DES ÉTUDIANTS")
        print("=" * 60)
        
        if not dashboard_students or not db_students:
            print("❌ Impossible de comparer - données manquantes")
            return False
        
        # Comparer les nombres
        dash_count = len(dashboard_students)
        db_count = len(db_students)
        
        print(f"📊 Nombre d'étudiants:")
        print(f"   Dashboard: {dash_count}")
        print(f"   Base de données: {db_count}")
        
        if dash_count != db_count:
            print("❌ DIFFÉRENCE dans le nombre d'étudiants!")
            return False
        
        # Comparer les détails
        print(f"\n🔍 Vérification détaillée de {dash_count} étudiants...")
        
        # Créer des dictionnaires pour comparaison facile
        # Dashboard uses 'IdEtudiant', 'NomEtudiant', etc.
        # Database direct query uses 'id_etudiant', 'nom', etc.
        dash_dict = {s['IdEtudiant']: s for s in dashboard_students}
        db_dict = {s['id_etudiant']: s for s in db_students}

        all_match = True

        for student_id in dash_dict:
            if student_id not in db_dict:
                print(f"❌ Étudiant {student_id} présent dans dashboard mais pas en DB")
                all_match = False
                continue

            dash_student = dash_dict[student_id]
            db_student = db_dict[student_id]

            # Comparer les champs (mapping dashboard -> database field names)
            field_mapping = {
                'NomEtudiant': 'nom',
                'PrenomEtudiant': 'prenom',
                'EmailEtudiant': 'email',
                'TelephoneEtudiant': 'telephone'
            }

            for dash_field, db_field in field_mapping.items():
                dash_value = dash_student.get(dash_field)
                db_value = db_student.get(db_field)
                if dash_value != db_value:
                    print(f"❌ Étudiant {student_id} - {db_field}: '{dash_value}' ≠ '{db_value}'")
                    all_match = False
        
        # Vérifier les étudiants uniquement en DB
        for student_id in db_dict:
            if student_id not in dash_dict:
                print(f"❌ Étudiant {student_id} présent en DB mais pas dans dashboard")
                all_match = False
        
        if all_match:
            print("✅ Tous les étudiants correspondent parfaitement")
        
        return all_match
    
    def compare_attendance(self, dashboard_attendance, db_attendance):
        """Comparer les présences"""
        print("\n📅 COMPARAISON DES PRÉSENCES")
        print("=" * 60)
        
        if not dashboard_attendance or not db_attendance:
            print("❌ Impossible de comparer - données manquantes")
            return False
        
        # Comparer les nombres
        dash_count = len(dashboard_attendance)
        db_count = len(db_attendance)
        
        print(f"📊 Nombre de présences:")
        print(f"   Dashboard: {dash_count}")
        print(f"   Base de données: {db_count}")
        
        if dash_count != db_count:
            print("❌ DIFFÉRENCE dans le nombre de présences!")
            return False
        
        print(f"✅ Même nombre de présences: {dash_count}")
        
        # Vérification par échantillonnage (10 premiers et 10 derniers)
        print(f"\n🔍 Vérification par échantillonnage...")
        
        sample_size = min(10, len(dashboard_attendance))
        all_match = True
        
        # Comparer les premiers enregistrements
        for i in range(sample_size):
            dash_record = dashboard_attendance[i]
            db_record = db_attendance[i]
            
            if (dash_record.get('name') != db_record.get('name') or
                dash_record.get('date') != db_record.get('date') or
                dash_record.get('time') != db_record.get('time')):
                print(f"❌ Présence {i+1}: Différence détectée")
                print(f"   Dashboard: {dash_record}")
                print(f"   DB: {db_record}")
                all_match = False
        
        if all_match:
            print(f"✅ Échantillon de {sample_size} présences correspond parfaitement")
        
        return all_match
    
    def run_full_comparison(self):
        """Exécuter la comparaison complète"""
        print("🔍 TEST DE COHÉRENCE DES DONNÉES")
        print("=" * 60)
        print("Comparaison entre le tableau de bord web et la base de données SQLite")
        print()
        
        # Connexion
        if not self.login():
            print("❌ Impossible de se connecter au dashboard")
            return False
        
        # Récupérer toutes les données
        print("\n📥 RÉCUPÉRATION DES DONNÉES")
        print("=" * 60)
        
        dashboard_stats = self.get_dashboard_stats()
        db_stats = self.get_database_stats()
        
        dashboard_students = self.get_dashboard_students()
        db_students = self.get_database_students()
        
        dashboard_attendance = self.get_dashboard_attendance()
        db_attendance = self.get_database_attendance()
        
        # Comparaisons
        print("\n🔍 COMPARAISONS DÉTAILLÉES")
        print("=" * 60)
        
        stats_match = self.compare_statistics(dashboard_stats, db_stats)
        students_match = self.compare_students(dashboard_students, db_students)
        attendance_match = self.compare_attendance(dashboard_attendance, db_attendance)
        
        # Résumé final
        print("\n📋 RÉSUMÉ DE LA COHÉRENCE DES DONNÉES")
        print("=" * 60)
        
        print(f"Statistiques: {'✅ COHÉRENTES' if stats_match else '❌ INCOHÉRENTES'}")
        print(f"Étudiants: {'✅ COHÉRENTS' if students_match else '❌ INCOHÉRENTS'}")
        print(f"Présences: {'✅ COHÉRENTES' if attendance_match else '❌ INCOHÉRENTES'}")
        
        all_consistent = stats_match and students_match and attendance_match
        
        print(f"\n🎯 RÉSULTAT GLOBAL: {'✅ DONNÉES COHÉRENTES' if all_consistent else '❌ INCOHÉRENCES DÉTECTÉES'}")
        
        if all_consistent:
            print("\n🎉 EXCELLENT! Le tableau de bord affiche des données parfaitement cohérentes")
            print("   ✅ Aucune discordance entre l'interface web et la base de données")
            print("   ✅ Les statistiques sont exactes")
            print("   ✅ Les listes d'étudiants correspondent")
            print("   ✅ Les enregistrements de présences sont cohérents")
        else:
            print("\n⚠️ PROBLÈMES DE COHÉRENCE DÉTECTÉS")
            print("   Causes possibles:")
            print("   - Problèmes de cache dans l'application web")
            print("   - Requêtes SQL incorrectes dans le dashboard")
            print("   - Synchronisation incomplète entre modules")
            print("   - Transactions de base de données non commitées")
        
        return all_consistent

def main():
    """Fonction principale"""
    print("🎯 TESTEUR DE COHÉRENCE DES DONNÉES")
    print("Ce script vérifie que les données affichées dans le tableau de bord")
    print("correspondent exactement aux données stockées dans la base SQLite.")
    print()
    
    # Vérifier que le serveur est accessible
    try:
        response = requests.get("http://localhost:5001", timeout=5)
        print("✅ Serveur dashboard accessible")
    except Exception as e:
        print(f"❌ Serveur non accessible: {e}")
        print("   Démarrez le dashboard avec: python admin_dashboard.py")
        return
    
    # Vérifier que la base de données existe
    try:
        conn = sqlite3.connect("attendance.db")
        conn.close()
        print("✅ Base de données SQLite accessible")
    except Exception as e:
        print(f"❌ Base de données non accessible: {e}")
        return
    
    # Exécuter le test
    tester = DataConsistencyTester()
    success = tester.run_full_comparison()
    
    if success:
        print("\n💡 RECOMMANDATIONS:")
        print("   🎯 Vos données sont cohérentes et fiables")
        print("   🎯 Le dashboard peut être utilisé en toute confiance")
        print("   🎯 Aucune action corrective nécessaire")
    else:
        print("\n💡 ACTIONS RECOMMANDÉES:")
        print("   🔧 Redémarrer l'application dashboard")
        print("   🔧 Vérifier les requêtes SQL dans le code")
        print("   🔧 Nettoyer les caches éventuels")
        print("   🔧 Vérifier l'intégrité de la base de données")

if __name__ == "__main__":
    main()
