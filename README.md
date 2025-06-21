# 🎓 Presence Pro - Système de Reconnaissance Faciale pour Présences

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)](https://flask.palletsprojects.com/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.0+-red.svg)](https://opencv.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Un système complet de gestion des présences utilisant la reconnaissance faciale avec une interface d'administration web moderne.

## 🌟 Fonctionnalités

### 🎯 **Reconnaissance Faciale**
- Détection et reconnaissance faciale en temps réel
- Entraînement automatique avec capture de photos
- Encodage facial haute précision
- Support de multiples visages simultanément

### 🎛️ **Tableau de Bord Web**
- Interface d'administration moderne et responsive
- Gestion complète des étudiants
- Surveillance des présences en temps réel
- Statistiques et analytics avancées
- Authentification sécurisée

### 📊 **Gestion des Données**
- Base de données SQLite intégrée
- Export des données (CSV, Excel)
- Historique complet des présences
- Sauvegarde et restauration

## 🚀 Installation Rapide

### Prérequis
- Python 3.7 ou supérieur
- Caméra (webcam ou caméra USB)
- Système d'exploitation : Windows, macOS, ou Linux

### Installation Automatique
```bash
# Cloner le repository
git clone https://github.com/Mey-Ven/Presence-Pro.git
cd Presence-Pro

# Installer les dépendances automatiquement
python install_dashboard_requirements.py

# Lancer le système
python start_dashboard.py
```

### Installation Manuelle
```bash
# Créer un environnement virtuel
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# ou
.venv\Scripts\activate     # Windows

# Installer les dépendances
pip install flask flask-socketio opencv-python face-recognition pandas pillow openpyxl

# Lancer l'application
python admin_dashboard.py
```

## 🎯 Utilisation

### 1. **Accès au Tableau de Bord**
- URL : http://localhost:5001
- Utilisateur : `admin`
- Mot de passe : `admin123`

### 2. **Ajouter un Étudiant**
1. Aller dans "Gestion Étudiants" → "Ajouter Étudiant"
2. Remplir les informations (nom, prénom, email)
3. Cocher "Entraînement facial" pour la capture automatique
4. Suivre les instructions de capture de photos

### 3. **Surveillance des Présences**
1. Lancer le système de reconnaissance : `python face_recognition_attendance_improved.py`
2. Les présences apparaissent automatiquement dans le tableau de bord
3. Filtrer par date ou étudiant selon vos besoins

## 📁 Structure du Projet

```
Presence-Pro/
├── 🎛️ admin_dashboard.py              # Application web principale
├── 🚀 start_dashboard.py              # Script de lancement
├── 📦 install_dashboard_requirements.py # Installation dépendances
├── 🎯 face_recognition_attendance_improved.py # Reconnaissance faciale
├── 🗄️ sqlite_database.py              # Gestion base de données
├── 🧠 facial_training_module.py       # Module d'entraînement
├── ⚙️ sqlite_config.py                # Configuration SQLite
├── 📁 templates/                      # Templates HTML
│   ├── base.html                      # Template de base
│   ├── login.html                     # Page de connexion
│   ├── dashboard.html                 # Tableau de bord
│   ├── students.html                  # Gestion étudiants
│   ├── add_student.html               # Ajout étudiant
│   └── attendance.html                # Surveillance présences
├── 📁 dataset/                        # Images d'entraînement
├── 📁 static/                         # Ressources statiques
└── 📚 docs/                           # Documentation
```

## 🔧 Configuration

### Changer le Mot de Passe Admin
Modifiez dans `admin_dashboard.py` :
```python
ADMIN_PASSWORD_HASH = generate_password_hash("VOTRE_NOUVEAU_MOT_DE_PASSE")
```

### Configuration de la Caméra
Le système détecte automatiquement la caméra disponible. Pour forcer une caméra spécifique, modifiez l'index dans le code.

### Base de Données
- SQLite par défaut (fichier `attendance.db`)
- Sauvegarde automatique
- Migration facile vers d'autres SGBD

## 🛠️ Développement

### Architecture
- **Backend** : Flask + SocketIO
- **Frontend** : Bootstrap 5 + JavaScript
- **Base de données** : SQLite
- **IA** : OpenCV + face_recognition
- **Temps réel** : WebSockets

### Contribuer
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit vos changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

## 📋 Roadmap

- [ ] 📱 Application mobile
- [ ] 🌐 API REST complète
- [ ] 📊 Rapports PDF automatiques
- [ ] 🔔 Notifications push
- [ ] 🌍 Support multi-langues
- [ ] ☁️ Déploiement cloud
- [ ] 🔐 Authentification multi-facteurs
- [ ] 📈 Analytics avancées

## 🐛 Dépannage

### Problèmes Courants

**Caméra non détectée :**
```bash
# Vérifier les caméras disponibles
python -c "import cv2; print([i for i in range(5) if cv2.VideoCapture(i).isOpened()])"
```

**Erreur de dépendances :**
```bash
# Réinstaller les dépendances
python install_dashboard_requirements.py
```

**Port déjà utilisé :**
- Modifier le port dans `admin_dashboard.py` (ligne 456)
- Ou arrêter l'autre application utilisant le port 5001

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

## 👥 Auteurs

- **Mey-Ven** - *Développeur principal* - [GitHub](https://github.com/Mey-Ven)

## 🙏 Remerciements

- [OpenCV](https://opencv.org/) pour la vision par ordinateur
- [face_recognition](https://github.com/ageitgey/face_recognition) pour la reconnaissance faciale
- [Flask](https://flask.palletsprojects.com/) pour le framework web
- [Bootstrap](https://getbootstrap.com/) pour l'interface utilisateur

## 📞 Support

Pour toute question ou problème :
- 🐛 [Issues GitHub](https://github.com/Mey-Ven/Presence-Pro/issues)
- 📧 Email : support@presence-pro.com
- 💬 [Discussions](https://github.com/Mey-Ven/Presence-Pro/discussions)

---

⭐ **N'oubliez pas de donner une étoile au projet si vous l'aimez !** ⭐
