#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Parcoursup-iAdmissions - Évaluation automatisée de dossiers Parcoursup BUT R&T
GitHub: github.com/MichelBaie/Parcoursup-iAdmissions
Auteur: Tristan BRINGUIER
Version : 1.0.0
Licence : MIT
"""

# pip install pdfminer.six typer rich requests

from __future__ import annotations
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import requests
import typer
from rich import print
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

__version__ = "1.0.0"

CONFIG_LM = {
    "url": "http://localhost:1234/v1/chat/completions",
    "modele": "gemma-3-27b-it-qat",
    "temperature": 0.0,
}

FICHIERS = {
    "csv": "resultats_parcoursup_evaluation.csv",
    "log": "parcoursup_erreurs.log", 
    "checkpoint": ".checkpoint_parcoursup"
}

ENTETES_CSV = [
    "nom_fichier_pdf", "numero_dossier", "note_finale_100", "type_baccalaureat",
    "portes_ouvertes", "detection_ia", "justification_note", "date_evaluation"
]

PROMPT = """**CONTEXTE PARCOURSUP-IADMISSIONS** 
Tu évalues des dossiers Parcoursup pour BUT R&T (Réseaux et Télécommunications).

**FORMAT OBLIGATOIRE** - UNE SEULE LIGNE :
`<numero_dossier>, <note_sur_100>, <type_bac>, <portes_ouvertes>, <lettre_ia>, <justification_courte>`

**CHAMPS** :
- `numero_dossier` : N° Parcoursup (ex: 123456P0) ou "INTROUVABLE"
- `note_sur_100` : Entier 0-100
- `type_bac` : "Général", "STI2D", "STL", "Autre" ou "NON_PRECISE"
- `portes_ouvertes` : "OUI" si JPO mentionnées, sinon "NON"
- `lettre_ia` : "PROBABLE_IA", "HUMAIN" ou "INCERTAIN"
- `justification_courte` : Max 60 mots

**BARÈME BUT R&T (100 points)** :
1. ADÉQUATION FORMATION (35 pts) : Compréhension réseaux/télécom, métiers tech, projet cohérent
2. MOTIVATION (25 pts) : JPO, recherches perso, engagement projets
3. PARCOURS SCOLAIRE (25 pts) : Cohérence, résultats maths/sciences
4. AVIS ÉTABLISSEMENT (15 pts) : Appréciations profs/chef

**CRITÈRES ÉLIMINATOIRES (Note = 0)** :
- Lettre hors-sujet/générique
- Aucune compréhension du BUT R&T
- Comportement problématique
- Absence totale de motivation

**DÉTECTION IA** : Style parfait = PROBABLE_IA, Personnel/erreurs = HUMAIN

Réponds UNIQUEMENT par la ligne de résultat."""

console = Console()

# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ══════════════════════════════════════════════════════════════════════════════

def extraire_texte_pdf(chemin_pdf: str) -> str:
    try:
        from pdfminer.high_level import extract_text
        console.print(f"[dim]📄 {Path(chemin_pdf).name}[/]", end="")
        
        texte = extract_text(chemin_pdf, laparams={'char_margin': 2.0, 'line_margin': 0.5})
        texte = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', texte)
        texte = re.sub(r'\s+', ' ', texte).strip()
        
        if len(texte) > 50000:
            texte = texte[:50000] + "\n[TRONQUÉ]"
            
        console.print(f" → [green]{len(texte)} chars[/]")
        return texte
        
    except Exception as e:
        console.print(f" → [red]Erreur: {e}[/]")
        log_erreur(f"PDF {chemin_pdf}: {e}")
        return ""

def log_erreur(msg: str):
    try:
        with open(FICHIERS["log"], "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}\n")
    except:
        pass

def appel_ia(texte: str) -> Optional[str]:
    try:
        payload = {
            "model": CONFIG_LM["modele"],
            "messages": [
                {"role": "system", "content": "Tu es Parcoursup-iAdmissions, évaluateur BUT R&T objectif."},
                {"role": "user", "content": f"{PROMPT}\n\n--- DOSSIER ---\n{texte}"}
            ],
            "temperature": CONFIG_LM["temperature"],
            "max_tokens": CONFIG_LM["max_tokens"]
        }
        
        console.print("[dim]🤖 IA...[/]", end="")
        reponse = requests.post(CONFIG_LM["url"], json=payload, timeout=CONFIG_LM["timeout"])
        reponse.raise_for_status()
        
        contenu = reponse.json()["choices"][0]["message"]["content"].strip()
        console.print(" → [green]OK[/]")
        return contenu
        
    except Exception as e:
        console.print(f" → [red]{e}[/]")
        log_erreur(f"IA: {e}")
        return None

def parser_reponse(reponse: str) -> Optional[Tuple[str, ...]]:
    if not reponse:
        return None
    
    try:
        lignes = reponse.strip().split('\n')
        ligne_result = None
        
        for ligne in lignes:
            if ',' in ligne and any(c.isdigit() for c in ligne):
                ligne_result = ligne
                break
                
        if not ligne_result:
            return None
            
        elements = [e.strip() for e in ligne_result.split(',')]
        if len(elements) < 5:
            return None
            
        numero = elements[0] or "INTROUVABLE"
        note = max(0, min(100, int(float(elements[1]))))
        bac = elements[2] or "NON_PRECISE"
        jpo = elements[3].upper() if elements[3].upper() in ["OUI", "NON"] else "NON"
        ia = elements[4] if elements[4] in ["PROBABLE_IA", "HUMAIN", "INCERTAIN"] else "INCERTAIN"
        justif = ", ".join(elements[5:])[:200] if len(elements) > 5 else "N/A"
        
        return (numero, str(note), bac, jpo, ia, justif)
        
    except Exception as e:
        log_erreur(f"Parser: {e}")
        return None

def charger_traites(csv_file: str) -> set:
    if not Path(csv_file).exists():
        return set()
        
    try:
        with open(csv_file, "r", encoding="utf-8") as f:
            return {ligne["nom_fichier_pdf"] for ligne in csv.DictReader(f, delimiter=";")}
    except Exception as e:
        console.print(f"[yellow]⚠️ Checkpoint: {e}[/]")
        return set()

def sauver(csv_file: str, data: List, entetes: bool = False):
    try:
        with open(csv_file, "w" if entetes else "a", encoding="utf-8", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            if entetes:
                writer.writerow(ENTETES_CSV)
            writer.writerow(data)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        console.print(f"[red]❌ Sauvegarde: {e}[/]")

# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

app = typer.Typer(name="parcoursup-iadmissions", help="🎓 Évaluation BUT R&T automatisée")

def banniere():
    console.print(Panel.fit(
        f"[bold blue]🎓 PARCOURSUP-IADMISSIONS[/]\n[cyan]BUT R&T v{__version__}[/]", 
        border_style="blue"
    ))

@app.command(help="🚀 Évaluer les dossiers PDF")
def evaluer(
    dossier: str = typer.Argument(".", help="📁 Dossier PDF"),
    sortie: str = typer.Option(FICHIERS["csv"], "-o", help="📊 CSV sortie"),
    verbose: bool = typer.Option(False, "-v", help="🔍 Mode détaillé"),
    force: bool = typer.Option(False, "-f", help="🔄 Recommencer")
):
    banniere()
    
    chemin = Path(dossier)
    if not chemin.exists():
        console.print(f"[red]❌ Dossier introuvable: {dossier}[/]")
        raise typer.Exit(1)
        
    pdfs = sorted(chemin.glob("*.pdf"))
    if not pdfs:
        console.print("[yellow]⚠️ Aucun PDF trouvé[/]")
        raise typer.Exit(0)
        
    if force and Path(sortie).exists():
        Path(sortie).unlink()
        
    traites = charger_traites(sortie)
    restants = [f for f in pdfs if f.name not in traites]
    
    table = Table(title="📊 BUT R&T - Statistiques")
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green", justify="right")
    table.add_row("📄 Total PDF", str(len(pdfs)))
    table.add_row("✅ Traités", str(len(traites)))
    table.add_row("🎯 Restants", str(len(restants)))
    console.print(table)
    
    if not restants:
        console.print("[green]🎉 Tout est traité ![/]")
        raise typer.Exit(0)
        
    if len(restants) > 50 and not typer.confirm(f"Traiter {len(restants)} dossiers ?"):
        raise typer.Exit(0)
        
    # Traitement principal
    creer_entetes = not Path(sortie).exists()
    erreurs = 0
    notes = []
    
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), 
                  TextColumn("{task.percentage:>3.0f}%"), TimeRemainingColumn()) as progress:
        
        task = progress.add_task("[cyan]🎓 Évaluation...", total=len(restants))
        
        for i, pdf in enumerate(restants):
            if verbose:
                console.print(f"\n[dim]{i+1}/{len(restants)}: {pdf.name}[/]")
            
            texte = extraire_texte_pdf(str(pdf))
            
            if not texte.strip():
                data = [pdf.name, "ERREUR_EXTRACTION", "0", "INCONNU", "NON", "INCERTAIN", 
                       "PDF illisible", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                erreurs += 1
            else:
                reponse = appel_ia(texte)
                result = parser_reponse(reponse) if reponse else None
                
                if result:
                    data = [pdf.name] + list(result) + [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    notes.append(int(result[1]))
                    if verbose:
                        console.print(f"[green]✅ Note: {result[1]}/100[/]")
                else:
                    data = [pdf.name, "ERREUR_IA", "0", "INCONNU", "NON", "INCERTAIN",
                           "Réponse IA invalide", datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
                    erreurs += 1
            
            sauver(sortie, data, creer_entetes)
            creer_entetes = False
            progress.advance(task)
    
    # Rapport final
    console.print(f"\n[bold green]🎉 Terminé![/]")
    final = Table(title="📈 Rapport final")
    final.add_column("Métrique", style="cyan")
    final.add_column("Valeur", style="green", justify="right")
    final.add_row("✅ Traités", str(len(restants)))
    final.add_row("❌ Erreurs", str(erreurs))
    if notes:
        final.add_row("📊 Moyenne", f"{sum(notes)/len(notes):.1f}/100")
        final.add_row("📈 Max", f"{max(notes)}/100")
        final.add_row("📉 Min", f"{min(notes)}/100")
    console.print(final)

@app.command(help="📊 Statut du traitement")
def statut(
    dossier: str = typer.Argument(".", help="📁 Dossier"),
    sortie: str = typer.Option(FICHIERS["csv"], "-o", help="📄 CSV")
):
    banniere()
    
    chemin = Path(dossier)
    pdfs = list(chemin.glob("*.pdf")) if chemin.exists() else []
    traites = charger_traites(sortie)
    
    notes = []
    erreurs = 0
    
    if Path(sortie).exists():
        try:
            with open(sortie, "r", encoding="utf-8") as f:
                for ligne in csv.DictReader(f, delimiter=";"):
                    try:
                        note = int(ligne.get("note_finale_100", "0"))
                        (notes if note > 0 else []).append(note) if note > 0 else (erreurs := erreurs + 1)
                    except:
                        erreurs += 1
        except:
            pass
    
    table = Table(title="📊 Statut Parcoursup-iAdmissions")
    table.add_column("Métrique", style="cyan")
    table.add_column("Valeur", style="green", justify="right")
    table.add_column("Détails", style="dim")
    
    total = len(pdfs)
    table.add_row("📁 Dossier", str(chemin.name), str(chemin.absolute()))
    table.add_row("📄 Total PDF", str(total), "Trouvés")
    table.add_row("✅ Traités", str(len(traites)), f"{len(traites)/total*100:.1f}%" if total else "0%")
    table.add_row("⏳ Restants", str(total - len(traites)), "À traiter")
    table.add_row("❌ Erreurs", str(erreurs), "Problèmes")
    
    if notes:
        table.add_row("📊 Moyenne", f"{sum(notes)/len(notes):.1f}/100", f"{len(notes)} notes")
        table.add_row("📈 Max", f"{max(notes)}/100", "")
        table.add_row("📉 Min", f"{min(notes)}/100", "")
    
    console.print(table)
    
    if total - len(traites) > 0:
        console.print(f"\n[yellow]💡 Commande: python parcoursup.py evaluer {dossier}[/]")

@app.command(help="🧹 Nettoyer les fichiers temporaires")
def nettoyer():
    banniere()
    
    fichiers = [FICHIERS["log"], FICHIERS["checkpoint"]]
    supprimes = 0
    
    for f in fichiers:
        if Path(f).exists():
            Path(f).unlink()
            supprimes += 1
            console.print(f"[green]🗑️  {f}[/]")
    
    console.print(f"\n[green]✅ {supprimes} fichiers supprimés[/]")

@app.command(help="ℹ️  Informations système")
def info():
    banniere()
    
    table = Table(title="🔧 Configuration système")
    table.add_column("Composant", style="cyan")
    table.add_column("Statut", style="green")
    
    # Test LM-Studio
    try:
        resp = requests.get(CONFIG_LM["url"].replace("chat/completions", "models"), timeout=5)
        lm_status = "[green]✅ Connecté[/]" if resp.status_code == 200 else "[red]❌ Erreur[/]"
    except:
        lm_status = "[red]❌ Inaccessible[/]"
    
    table.add_row("🤖 LM-Studio", lm_status)
    table.add_row("🐍 Python", f"{sys.version.split()[0]}")
    table.add_row("📦 Version", __version__)
    
    # Test dépendances
    deps = ["requests", "rich", "typer", "pdfminer.six"]
    for dep in deps:
        try:
            __import__(dep.replace(".six", ""))
            table.add_row(f"📚 {dep}", "[green]✅ OK[/]")
        except:
            table.add_row(f"📚 {dep}", "[red]❌ Manquant[/]")
    
    console.print(table)

if __name__ == "__main__":
    app()
