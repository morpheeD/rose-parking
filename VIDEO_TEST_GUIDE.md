# 🎬 Guide : Vidéo de Test pour le Système de Parking

## ✅ Vidéo Générée

Une vidéo de test a été créée : `test_traffic.mp4`

**Caractéristiques** :
- ⏱️ Durée : 60 secondes (boucle automatique)
- 📐 Résolution : 640x480
- 🚗 ~19 véhicules simulés
- ➡️ Entrées (ligne verte à 30%)
- ⬅️ Sorties (ligne rouge à 70%)

## 🚀 Utilisation

### Option 1 : Lancer directement (Recommandé)

La configuration est déjà prête pour Mac :

```bash
cd "/Users/morphee/rose parking"
source venv/bin/activate
python3 app.py
```

Puis ouvrez : **http://localhost:5000**

### Option 2 : Régénérer une nouvelle vidéo

Pour créer une vidéo plus longue ou avec plus de véhicules :

```bash
# Vidéo de 120 secondes
python3 generate_test_video.py 120 test_traffic.mp4

# Modifier le nombre de véhicules par minute dans generate_test_video.py
# Ligne 162: vehicles_per_minute=20  (augmentez ce nombre)
```

## 🎮 Ce que vous verrez

1. **Vidéo en boucle** avec des voitures simulées
2. **Détection YOLO** des rectangles (voitures)
3. **Comptage automatique** :
   - Voiture traverse ligne verte (haut→bas) = +1 entrée
   - Voiture traverse ligne rouge (bas→haut) = +1 sortie
4. **Interface web** mise à jour en temps réel

## 🔄 Basculer entre modes

### Utiliser la webcam à la place

Modifiez `config.json` :
```json
"platform_configs": {
  "mac": {
    "camera": {
      "source": 0  // 0 = webcam
    }
  }
}
```

### Utiliser le mode simulation

Modifiez `config.json` :
```json
{
  "simulation_mode": true
}
```

## 📊 Tester le Système

1. **Lancez l'application** : `python3 app.py`
2. **Ouvrez l'interface** : http://localhost:5000
3. **Observez** :
   - Compteur d'occupation
   - Total entrées/sorties
   - Pourcentage d'occupation
   - Historique des événements

## 🛠️ Personnalisation

### Ajuster les lignes de détection

Dans `config.json` :
```json
"tracking": {
  "entry_line_ratio": 0.3,  // 0.0 = haut, 1.0 = bas
  "exit_line_ratio": 0.7
}
```

### Modifier la capacité maximale

Via l'interface web ou dans la base de données :
```bash
sqlite3 parking.db "UPDATE config SET value='50' WHERE key='max_capacity';"
```

## 🎯 Prochaines Étapes

Pour déployer sur Raspberry Pi :
1. Copiez le projet sur le Pi
2. Lancez `./install.sh`
3. Le système détectera automatiquement le Pi
4. Utilisera la caméra Pi (source: 0)
5. Serveur accessible sur le réseau (0.0.0.0:5000)
6. url de video test : https://youtu.be/ymuYdUT5p7Q?si=yV8KA2vSRSEMgCM9
