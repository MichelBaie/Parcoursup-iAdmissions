# 🎓 Parcoursup-iAdmissions

> **Évaluation automatisée de dossiers Parcoursup BUT R&T avec Intelligence Artificielle**

[![Python 3.8+](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![MIT License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Rich CLI](https://img.shields.io/badge/CLI-Rich-orange.svg)](https://github.com/Textualize/rich)

---

## 🚀 Présentation

**Parcoursup-iAdmissions** automatise l'évaluation des dossiers de candidature Parcoursup pour le **BUT Réseaux & Télécommunications** en utilisant l'IA locale via LM-Studio.

### ✨ Fonctionnalités

- 📄 **Analyse PDF automatique** - Traitement par lot de dossiers complets
- 🎯 **Notation sur 100 points** - Barème adapté aux critères BUT R&T  
- 🤖 **Détection IA** - Identification des lettres générées automatiquement
- 💾 **Points de sauvegarde** - Reprise automatique en cas d'interruption
- 📊 **Rapports détaillés** - Export CSV avec statistiques complètes
- 🎨 **Interface moderne** - CLI intuitive avec Rich

---

## 🛠️ Installation

### Prérequis
- **Python 3.8+**
- **LM-Studio** avec un modèle chargé (ex: Gemma, Llama)
- **Dossiers PDF** organisés dans un dossier

### Installation rapide
```bash
# Cloner le projet
git clone https://github.com/MichelBaie/Parcoursup-iAdmissions
cd Parcoursup-iAdmissions

# Installer les dépendances
pip install pdfminer.six typer rich requests

# Lancer LM-Studio (port 1234)
# Charger votre modèle préféré
```

---

## 🎯 Utilisation

### Commandes principales

```bash
# Évaluer tous les PDFs d'un dossier
python parcoursup.py evaluer /chemin/vers/dossiers/

# Voir le statut du traitement
python parcoursup.py statut

# Reprendre un traitement interrompu
python parcoursup.py evaluer . --force

# Mode verbose pour debugger
python parcoursup.py evaluer . --verbose
```

### Structure des fichiers
```
dossiers-parcoursup/
├── dossier_001_Jean_Dupont.pdf
├── dossier_002_Marie_Martin.pdf
└── ...
```

---

## 📊 Critères d'évaluation BUT R&T

| **Critère** | **Points** | **Détails** |
|-------------|------------|-------------|
| 🎯 **Adéquation formation** | 35 pts | Compréhension réseaux/télécom, projet cohérent |
| 💪 **Motivation** | 25 pts | Participation JPO, recherches personnelles |
| 📚 **Parcours scolaire** | 25 pts | Résultats maths/sciences, cohérence |
| 👨‍🏫 **Avis établissement** | 15 pts | Appréciations professeurs |

---

## 📈 Exemple de rapport

```csv
nom_fichier_pdf;numero_dossier;note_finale_100;type_baccalaureat;portes_ouvertes;detection_ia;justification_note
dossier_001.pdf;123456P0;78;STI2D;OUI;HUMAIN;bon candidat
dossier_002.pdf;234567P1;45;Général;NON;PROBABLE_IA;mauvais candidat
```

---

## ⚙️ Configuration

Modifiez les variables dans le code si nécessaire :

```python
CONFIG_LM = {
    "url": "http://localhost:1234/v1/chat/completions",  # URL LM-Studio
    "modele": "gemma-3-27b-it-qat",                      # Modèle à utiliser
    "temperature": 0.0,                                   # Cohérence maximale
}
```

---

## 🚨 Bonnes pratiques

- ✅ **Testez d'abord** sur quelques dossiers
- ✅ **Vérifiez LM-Studio** avant le traitement de masse
- ✅ **Sauvegardez** régulièrement le fichier CSV
- ✅ **Supervisez** les notes aberrantes

---

## 📄 Licence

MIT License - Voir [LICENSE](LICENSE) pour les détails.

---

**Développé avec passion pour démointrer la possibilité d'automatiser l'évaluation Parcoursup grâce à un modèle d'IA local**