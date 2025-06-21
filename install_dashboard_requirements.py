"""
Script d'installation des dépendances pour le tableau de bord d'administration
Ce script installe automatiquement tous les packages Python nécessaires
"""

import subprocess
import sys
import os

def install_package(package):
    """Installe un package Python avec pip"""
    try:
        print(f"📦 Installation de {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} installé avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'installation de {package}: {e}")
        return False

def check_package(package):
    """Vérifie si un package est déjà installé"""
    try:
        __import__(package)
        return True
    except ImportError:
        return False

def main():
    """Fonction principale d'installation"""
    print("🚀 INSTALLATION DES DÉPENDANCES DU TABLEAU DE BORD")
    print("=" * 60)
    
    # Liste des packages requis
    packages = [
        "flask",
        "flask-socketio",
        "werkzeug",
        "pandas",
        "pillow",
        "opencv-python",
        "face-recognition",
        "openpyxl",
        "python-socketio",
        "eventlet"
    ]
    
    # Vérifier Python version
    python_version = sys.version_info
    print(f"🐍 Version Python: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 7):
        print("❌ Python 3.7 ou supérieur est requis")
        return False
    
    print("✅ Version Python compatible")
    print()
    
    # Mettre à jour pip
    print("🔄 Mise à jour de pip...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        print("✅ pip mis à jour")
    except:
        print("⚠️  Impossible de mettre à jour pip, mais on continue...")
    
    print()
    
    # Installer les packages
    installed_count = 0
    failed_packages = []
    
    for package in packages:
        # Vérifier si déjà installé
        package_name = package.split("==")[0]  # Enlever la version si spécifiée
        
        # Noms spéciaux pour certains packages
        import_names = {
            "flask-socketio": "flask_socketio",
            "opencv-python": "cv2",
            "face-recognition": "face_recognition",
            "python-socketio": "socketio",
            "pillow": "PIL"
        }
        
        import_name = import_names.get(package_name, package_name)
        
        if check_package(import_name):
            print(f"✅ {package} déjà installé")
            installed_count += 1
        else:
            if install_package(package):
                installed_count += 1
            else:
                failed_packages.append(package)
        
        print()
    
    # Résumé
    print("=" * 60)
    print("📊 RÉSUMÉ DE L'INSTALLATION")
    print("=" * 60)
    print(f"✅ Packages installés avec succès: {installed_count}/{len(packages)}")
    
    if failed_packages:
        print(f"❌ Packages échoués: {len(failed_packages)}")
        for package in failed_packages:
            print(f"   - {package}")
        print()
        print("💡 SOLUTIONS POUR LES ÉCHECS:")
        print("   1. Vérifiez votre connexion internet")
        print("   2. Essayez d'exécuter en tant qu'administrateur")
        print("   3. Installez manuellement avec: pip install <package>")
        print("   4. Vérifiez les conflits de dépendances")
    else:
        print("🎉 Toutes les dépendances ont été installées avec succès!")
    
    print()
    print("🎯 PROCHAINES ÉTAPES:")
    print("   1. Lancez le tableau de bord: python admin_dashboard.py")
    print("   2. Ouvrez votre navigateur: http://localhost:5000")
    print("   3. Connectez-vous avec: admin / admin123")
    
    # Créer un fichier de vérification
    try:
        with open("dashboard_requirements_installed.txt", "w") as f:
            f.write("Dashboard requirements installed successfully\n")
            f.write(f"Installation date: {__import__('datetime').datetime.now()}\n")
            f.write(f"Python version: {sys.version}\n")
            f.write(f"Packages installed: {installed_count}/{len(packages)}\n")
            if failed_packages:
                f.write(f"Failed packages: {', '.join(failed_packages)}\n")
        print("📝 Fichier de vérification créé: dashboard_requirements_installed.txt")
    except:
        pass
    
    return len(failed_packages) == 0

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Installation terminée avec succès!")
        sys.exit(0)
    else:
        print("\n⚠️  Installation terminée avec des erreurs")
        sys.exit(1)
