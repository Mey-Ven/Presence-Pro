# Système de Reconnaissance Faciale avec SQLite

Ce document explique comment utiliser la nouvelle implémentation SQLite du système de reconnaissance faciale, qui remplace Firebase pour une solution plus rapide et plus simple.

## Avantages de SQLite

- **Plus rapide** : Base de données locale, pas de latence réseau
- **Plus simple** : Aucune configuration serveur nécessaire
- **Hors ligne** : Fonctionne sans connexion internet
- **Léger** : Un seul fichier de base de données
- **Gratuit** : Aucun coût d'hébergement

## Fichiers du Système SQLite

### Nouveaux fichiers créés :

1. **`sqlite_database.py`** - Module principal de base de données SQLite
2. **`manage_students_sqlite.py`** - Interface de gestion des étudiants avec SQLite
3. **`sqlite_config.py`** - Configuration SQLite (remplace firebase_config.py)
4. **`migrate_firebase_to_sqlite.py`** - Script de migration depuis Firebase
5. **`attendance.db`** - Fichier de base de données SQLite (créé automatiquement)

## Installation et Configuration

### 1. Aucune configuration supplémentaire requise
Contrairement à Firebase, SQLite ne nécessite aucune configuration. La base de données est créée automatiquement lors du premier lancement.

### 2. Migration depuis Firebase (optionnel)
Si vous avez des données existantes dans Firebase :

```bash
python migrate_firebase_to_sqlite.py
```

**Note** : Les mots de passe seront réinitialisés à `MotDePasseTemporaire123!` car les mots de passe hashés ne peuvent pas être transférés.

## Utilisation

### Gestion des Étudiants

```bash
python manage_students_sqlite.py
```

**Menu disponible :**
1. Ajouter un nouvel étudiant
2. Vérifier si un étudiant existe
3. Ajouter plusieurs étudiants de test
4. Lister tous les étudiants
5. Réinitialiser le mot de passe d'un étudiant
6. Quitter

### Fonctionnalités

- **Ajout d'étudiants** : ID automatique au format E-XXXX, mot de passe généré automatiquement
- **Sécurité** : Mots de passe hashés avec SHA-256
- **Validation** : Vérification des emails uniques
- **Réinitialisation** : Possibilité de réinitialiser les mots de passe par ID ou email

## Structure de la Base de Données

### Table `etudiants`
```sql
CREATE TABLE etudiants (
    id_etudiant TEXT PRIMARY KEY,      -- Format E-XXXX
    nom TEXT NOT NULL,
    prenom TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    telephone TEXT,
    mot_de_passe_hash TEXT NOT NULL,   -- SHA-256 hash
    date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Table `presences`
```sql
CREATE TABLE presences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    date TEXT NOT NULL,                -- Format YYYY-MM-DD
    heure TEXT NOT NULL,               -- Format HH:MM:SS
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API du Module sqlite_database.py

### Fonctions pour les Étudiants

```python
# Initialiser la base de données
initialize_database()

# Ajouter un étudiant
id_etudiant, mot_de_passe = ajouter_etudiant(nom, prenom, email, telephone)

# Vérifier l'existence d'un étudiant
existe = etudiant_existe(id_etudiant=None, email=None)

# Récupérer tous les étudiants
etudiants = obtenir_tous_etudiants()

# Réinitialiser un mot de passe
succes, nouveau_mdp = reinitialiser_mot_de_passe(id_etudiant=None, email=None)
```

### Fonctions pour les Présences

```python
# Ajouter une présence
ajouter_presence(nom, date, heure)

# Vérifier si présent aujourd'hui
present = est_present_aujourd_hui(nom, date)

# Récupérer toutes les présences
presences = obtenir_toutes_presences()

# Récupérer par date
presences = obtenir_presences_par_date(date)

# Récupérer par personne
presences = obtenir_presences_par_personne(nom)
```

## Intégration avec le Système de Reconnaissance Faciale

Pour utiliser SQLite avec le système de reconnaissance faciale, modifiez `face_recognition_attendance_improved.py` :

1. Remplacez l'import :
```python
# Ancien
import firebase_config

# Nouveau
import sqlite_config as firebase_config
```

2. Le reste du code reste identique car `sqlite_config.py` maintient la même interface que `firebase_config.py`.

## Comparaison des Performances

| Aspect | Firebase | SQLite |
|--------|----------|--------|
| Vitesse | Dépend du réseau | Très rapide (local) |
| Configuration | Complexe | Aucune |
| Dépendances | Internet requis | Aucune |
| Coût | Limites gratuites | Gratuit |
| Sauvegarde | Automatique | Manuelle |
| Collaboration | Multi-utilisateur | Local uniquement |

## Sauvegarde et Restauration

### Sauvegarde
```bash
# Copier le fichier de base de données
cp attendance.db attendance_backup_$(date +%Y%m%d).db
```

### Restauration
```bash
# Restaurer depuis une sauvegarde
cp attendance_backup_20231201.db attendance.db
```

## Dépannage

### Problème : "Database is locked"
- Assurez-vous qu'aucun autre programme n'utilise la base de données
- Redémarrez le programme

### Problème : "No such table"
- Exécutez `python sqlite_database.py` pour initialiser la base de données

### Problème : Données manquantes après migration
- Vérifiez que la migration s'est terminée sans erreur
- Consultez les messages de la migration pour les détails

## Tests

Pour tester le système SQLite :

```bash
# Test du module de base de données
python sqlite_database.py

# Test de la configuration
python sqlite_config.py

# Test de l'interface de gestion
python manage_students_sqlite.py
```

## Migration Retour vers Firebase

Si vous souhaitez revenir à Firebase, gardez vos fichiers originaux :
- `firebase_config.py`
- `create_students_table.py`
- `manage_students.py`

Et modifiez simplement les imports dans vos scripts principaux.

## Support

Pour toute question ou problème avec l'implémentation SQLite, vérifiez :
1. Que Python 3.6+ est installé
2. Que le module `sqlite3` est disponible (inclus par défaut)
3. Que vous avez les permissions d'écriture dans le répertoire du projet
