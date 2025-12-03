# 🚗 Système de Gestion de Parking avec YOLO

Application de gestion de parking intelligent pour Raspberry Pi utilisant YOLOv8 pour détecter les véhicules entrants et sortants, avec interface web en temps réel.

## 📋 Fonctionnalités

- ✅ Détection automatique des véhicules avec YOLOv8
- ✅ Comptage des entrées et sorties via lignes virtuelles
- ✅ Interface web temps réel avec WebSocket
- ✅ Configuration de la capacité maximale
- ✅ Statistiques d'occupation en direct
- ✅ Indicateurs visuels (pourcentage, places disponibles)
- ✅ Historique des événements
- ✅ Design moderne avec dark mode

## 🛠️ Prérequis

### Matériel
- Raspberry Pi 4 ou 5 (recommandé)
- Caméra Raspberry Pi ou webcam USB
- Carte SD (16 GB minimum)
- Alimentation adaptée

### Logiciel
- Raspberry Pi OS (Bullseye ou plus récent)
- Python 3.9+
- Connexion Internet (pour l'installation)

## 📦 Installation

### Installation Automatique (Recommandé)

```bash
# Cloner ou télécharger le projet
cd /home/pi/rose\ parking

# Rendre le script exécutable
chmod +x install.sh

# Lancer l'installation
./install.sh
```

### Installation Manuelle

```bash
# 1. Installer les dépendances système
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv libopencv-dev python3-opencv

# 2. Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# 3. Installer les dépendances Python
pip install --upgrade pip
pip install -r requirements.txt

# 4. Le modèle YOLOv8n sera téléchargé automatiquement au premier lancement
```

## ⚙️ Configuration

### 1. Configuration de la Caméra

Éditez `config.json` pour configurer votre caméra :

```json
{
  "camera": {
    "source": 0,        // 0 pour caméra par défaut, ou chemin vers vidéo
    "width": 640,
    "height": 480,
    "fps": 10
  }
}
```

### 2. Configuration des Lignes de Comptage

Les lignes virtuelles sont définies par des ratios (0.0 à 1.0) de la hauteur de l'image :

```json
{
  "tracking": {
    "entry_line_ratio": 0.3,   // Ligne d'entrée à 30% du haut
    "exit_line_ratio": 0.7      // Ligne de sortie à 70% du haut
  }
}
```

**Important** : Ajustez ces valeurs selon l'angle de votre caméra. La logique est :
- Un véhicule franchissant la ligne d'entrée **vers le bas** = +1 entrée
- Un véhicule franchissant la ligne de sortie **vers le haut** = +1 sortie

### 3. Test de la Caméra

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Tester la caméra
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('Caméra OK' if cap.isOpened() else 'Erreur caméra')"
```

### 4. Configuration Multi-Plateforme

Le système détecte automatiquement la plateforme (Mac, Raspberry Pi, Linux) et charge la configuration appropriée depuis `config.json`.

#### Configurations Spécifiques

**Mac (Développement)** :
```json
"platform_configs": {
  "mac": {
    "camera": {
      "source": 0,          // Webcam Mac, ou chemin vers vidéo
      "width": 640,
      "height": 480,
      "fps": 10
    },
    "server": {
      "host": "127.0.0.1",  // Localhost uniquement
      "port": 5000,
      "debug": true         // Mode debug activé
    }
  }
}
```

**Raspberry Pi (Production)** :
```json
"platform_configs": {
  "raspberry_pi": {
    "camera": {
      "source": 0,          // Caméra Pi ou USB
      "width": 640,
      "height": 480,
      "fps": 10
    },
    "server": {
      "host": "0.0.0.0",    // Accessible sur le réseau
      "port": 5000,
      "debug": false
    }
  }
}
```

## 🍎 Test sur Mac

Le système peut être testé sur Mac de trois façons :

### Option 1 : Webcam Mac (Recommandé pour tests rapides)

```bash
# Dans config.json, section "mac"
"camera": {
  "source": 0,  // Utilise la webcam intégrée
  "width": 640,
  "height": 480,
  "fps": 10
}
```

Lancez simplement l'application :
```bash
python3 app.py
```

### Option 2 : Vidéo de Test (Recommandé pour tests reproductibles)

1. **Téléchargez ou créez une vidéo de test** avec du trafic de véhicules
2. **Placez la vidéo** dans le dossier du projet (ex: `test_traffic.mp4`)
3. **Modifiez config.json** :

```json
"platform_configs": {
  "mac": {
    "camera": {
      "source": "test_traffic.mp4",  // Chemin vers votre vidéo
      "width": 640,
      "height": 480,
      "fps": 10
    }
  }
}
```

La vidéo bouclera automatiquement.

### Option 3 : Mode Simulation (Sans caméra)

Pour tester l'interface sans caméra ni vidéo :

```json
{
  "simulation_mode": true
}
```

Le système générera des frames vides avec le texte "SIMULATION MODE".

### Vérifier la Détection de Plateforme

```bash
# Tester la détection
python3 platform_detector.py
```

Sortie attendue sur Mac :
```
==================================================
Platform Information:
==================================================
Platform: mac
System: Darwin
Machine: arm64 (ou x86_64)
Processor: arm (ou i386)
Python_version: 3.x.x
==================================================
```

## 🚀 Utilisation

### Démarrage Manuel

```bash
# Activer l'environnement virtuel
source venv/bin/activate

# Lancer l'application
python3 app.py
```

L'application sera accessible à : `http://<ip-raspberry-pi>:5000`

### Démarrage Automatique (Service Systemd)

Le script d'installation configure automatiquement un service systemd :

```bash
# Démarrer le service
sudo systemctl start parking

# Arrêter le service
sudo systemctl stop parking

# Redémarrer le service
sudo systemctl restart parking

# Voir les logs
sudo journalctl -u parking -f
```

## 🖥️ Interface Web

### Accès
Ouvrez un navigateur et accédez à : `http://<ip-raspberry-pi>:5000`

### Fonctionnalités
1. **Dashboard** : Vue en temps réel de l'occupation
2. **Configuration** : Modifier la capacité maximale
3. **Statistiques** : Total des entrées/sorties
4. **Réinitialisation** : Remettre le compteur à 0

### Indicateurs de Couleur
- 🟢 **Vert** : Occupation < 70%
- 🟠 **Orange** : Occupation 70-90%
- 🔴 **Rouge** : Occupation > 90%

## 🔧 Calibration

### Ajuster les Lignes de Comptage

1. Démarrez l'application en mode debug dans `app.py` :
   ```python
   CONFIG = {
       'debug_mode': True  # Activer le mode debug
   }
   ```

2. Les lignes seront visibles sur le flux vidéo
3. Ajustez `entry_line_ratio` et `exit_line_ratio` dans `config.json`
4. Redémarrez l'application

### Optimisation des Performances

Pour améliorer les performances sur Raspberry Pi :

```python
# Dans detector.py, réduire la résolution d'entrée
results = self.model.predict(
    frame,
    imgsz=320  # Réduire de 416 à 320
)
```

## 📊 API REST

### Endpoints Disponibles

#### GET `/api/stats`
Obtenir les statistiques actuelles
```json
{
  "max_capacity": 100,
  "occupied": 45,
  "available": 55,
  "occupancy_percent": 45.0,
  "total_entries": 120,
  "total_exits": 75,
  "timestamp": "2025-12-02T15:30:00"
}
```

#### GET `/api/config`
Obtenir la configuration
```json
{
  "max_capacity": 100
}
```

#### POST `/api/config`
Mettre à jour la configuration
```json
{
  "max_capacity": 150
}
```

#### POST `/api/reset`
Réinitialiser le compteur à 0

## 🐛 Dépannage

### La caméra ne fonctionne pas
```bash
# Vérifier les périphériques vidéo
ls -l /dev/video*

# Tester avec v4l2
v4l2-ctl --list-devices
```

### Erreur "No module named 'cv2'"
```bash
# Réinstaller OpenCV
pip install --force-reinstall opencv-python
```

### Performances lentes
- Réduire la résolution de la caméra dans `config.json`
- Réduire le FPS (ex: 5-8 FPS)
- Utiliser YOLOv8n (nano) au lieu de versions plus grandes
- Réduire `imgsz` dans `detector.py`

### Le comptage est imprécis
- Ajuster les positions des lignes de comptage
- Augmenter le seuil de confiance dans `detector.py`
- Vérifier l'angle de la caméra (vue en hauteur recommandée)
- S'assurer d'un bon éclairage

## 📁 Structure du Projet

```
rose parking/
├── app.py                 # Application Flask principale
├── camera.py              # Module de capture vidéo
├── detector.py            # Détection YOLO
├── tracker.py             # Tracking et comptage
├── database.py            # Gestion SQLite
├── config.json            # Configuration
├── requirements.txt       # Dépendances Python
├── install.sh            # Script d'installation
├── README.md             # Documentation
├── templates/
│   └── index.html        # Interface web
└── static/
    ├── css/
    │   └── style.css     # Styles
    └── js/
        └── app.js        # Logique frontend
```

## 🔒 Sécurité

> **⚠️ IMPORTANT** : Cette application est conçue pour un usage sur réseau local. Pour une utilisation en production :
> - Changez la clé secrète dans `app.py`
> - Ajoutez une authentification
> - Utilisez HTTPS avec un certificat SSL
> - Configurez un pare-feu

## 📝 Licence

Ce projet est fourni tel quel, sans garantie. Utilisez-le à vos propres risques.

## 🤝 Contribution

Pour signaler un bug ou suggérer une amélioration, créez une issue.

## 📞 Support

Pour toute question :
1. Vérifiez d'abord la section Dépannage
2. Consultez les logs : `sudo journalctl -u parking -f`
3. Vérifiez la configuration dans `config.json`
