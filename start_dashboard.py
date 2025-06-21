"""
Script de lancement du tableau de bord d'administration
Ce script vérifie les dépendances et lance le tableau de bord
"""

import sys
import os
import subprocess
import time

def check_dependencies():
    """Vérifie si toutes les dépendances sont installées"""
    required_packages = [
        ("flask", "Flask"),
        ("flask_socketio", "Flask-SocketIO"),
        ("cv2", "OpenCV"),
        ("face_recognition", "Face Recognition"),
        ("PIL", "Pillow"),
        ("pandas", "Pandas")
    ]
    
    missing_packages = []
    
    for import_name, display_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {display_name}")
        except ImportError:
            print(f"❌ {display_name} - MANQUANT")
            missing_packages.append(display_name)
    
    return missing_packages

def check_files():
    """Vérifie si tous les fichiers nécessaires sont présents"""
    required_files = [
        "admin_dashboard.py",
        "sqlite_database.py",
        "facial_training_module.py",
        "sqlite_config.py",
        "templates/base.html",
        "templates/login.html",
        "templates/dashboard.html",
        "templates/students.html",
        "templates/add_student.html",
        "templates/attendance.html"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MANQUANT")
            missing_files.append(file_path)
    
    return missing_files

def create_directories():
    """Crée les dossiers nécessaires"""
    directories = [
        "templates",
        "static/css",
        "static/js",
        "static/images",
        "dataset"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Dossier créé: {directory}")
        else:
            print(f"✅ Dossier existant: {directory}")

def initialize_database():
    """Initialise la base de données SQLite"""
    try:
        import sqlite_database as db
        db.initialize_database()
        print("✅ Base de données SQLite initialisée")
        return True
    except Exception as e:
        print(f"❌ Erreur d'initialisation de la base de données: {e}")
        return False

def launch_dashboard():
    """Lance le tableau de bord"""
    try:
        print("\n🚀 Lancement du tableau de bord...")
        print("📱 URL: http://localhost:5001")
        print("👤 Utilisateur: admin")
        print("🔑 Mot de passe: admin123")
        print("\n⏳ Démarrage en cours...")
        
        # Lancer le tableau de bord
        subprocess.run([sys.executable, "admin_dashboard.py"])
        
    except KeyboardInterrupt:
        print("\n🛑 Arrêt du tableau de bord demandé par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur lors du lancement: {e}")

def main():
    """Fonction principale"""
    print("🎛️  TABLEAU DE BORD D'ADMINISTRATION")
    print("🎓 Système de Reconnaissance Faciale")
    print("=" * 50)
    
    # Vérifier les dossiers
    print("\n📁 Vérification des dossiers...")
    create_directories()
    
    # Vérifier les fichiers
    print("\n📄 Vérification des fichiers...")
    missing_files = check_files()
    
    if missing_files:
        print(f"\n❌ {len(missing_files)} fichiers manquants:")
        for file in missing_files:
            print(f"   - {file}")
        print("\n💡 Assurez-vous que tous les fichiers du tableau de bord sont présents")
        return False
    
    # Vérifier les dépendances
    print("\n📦 Vérification des dépendances...")
    missing_packages = check_dependencies()
    
    if missing_packages:
        print(f"\n❌ {len(missing_packages)} packages manquants:")
        for package in missing_packages:
            print(f"   - {package}")
        
        print("\n💡 Pour installer les dépendances, exécutez:")
        print("   python install_dashboard_requirements.py")
        
        response = input("\n🤔 Voulez-vous installer automatiquement les dépendances? (o/n): ")
        if response.lower() == 'o':
            print("\n📦 Installation des dépendances...")
            try:
                subprocess.run([sys.executable, "install_dashboard_requirements.py"])
                print("\n🔄 Redémarrage de la vérification...")
                time.sleep(2)
                return main()  # Relancer la vérification
            except Exception as e:
                print(f"❌ Erreur lors de l'installation: {e}")
                return False
        else:
            return False
    
    # Initialiser la base de données
    print("\n🗄️  Initialisation de la base de données...")
    if not initialize_database():
        return False
    
    # Tout est prêt, lancer le tableau de bord
    print("\n✅ Toutes les vérifications sont passées!")
    print("🎉 Le système est prêt à être lancé")
    
    response = input("\n🚀 Lancer le tableau de bord maintenant? (o/n): ")
    if response.lower() == 'o':
        launch_dashboard()
    else:
        print("\n💡 Pour lancer manuellement:")
        print("   python admin_dashboard.py")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if not success:
            print("\n❌ Échec du lancement du tableau de bord")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Arrêt demandé par l'utilisateur")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)
