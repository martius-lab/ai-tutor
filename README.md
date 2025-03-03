# AI Tandem – Dokumentation
 
## 1. Einleitung

AITandem ist eine webbasierte Plattform, die Professoren und Universitäten dabei unterstützt, Studierenden automatisierte und KI-gestützte Übungsaufgaben bereitzustellen. Das System nutzt künstliche Intelligenz zur Bewertung und bietet personalisiertes Feedback für Studierende.

## 2. Systemübersicht

Das Projekt basiert auf dem Reflex-Framework und verwendet Python als Hauptprogrammiersprache. Daten werden in einer SQLite-Datenbank gespeichert, die bei Bedarf durch ein anderes relationales Datenbanksystem ersetzt werden kann.

### 2.1 Architektur

Frontend: Reflex (generiert UI aus Python-Code)

Backend: Python-basiert, verarbeitet Anfragen und bewertet Lösungen

Datenbank: SQLite (Standard), kann durch PostgreSQL oder MySQL ersetzt werden

KI-Module: OpenAI API ermöglicht die interaktion mit ChatGPT, aber auch andere KIs wären möglich

## 3. Installation

### 3.1 Voraussetzungen

Python ≥ 3.9

Virtuelle Umgebung (empfohlen)

Reflex Framework

Alembic für Datenbankmigrationen 

### 3.2 Einrichtung

Repository klonen:
git clone <URL-des-Repositorys>
cd aitandem

Virtuelle Umgebung erstellen & aktivieren:
python -m venv venv
source venv/bin/activate   # Linux/Mac
venv\Scripts\activate      # Windows

Abhängigkeiten installieren:

pip install -r requirements.txt

Datenbank initialisieren:

reflex db init
reflex db makemigrations
refelx db migrate 

Anwendung starten:

reflex run

## 4. Konfiguration

### 4.1 Anwendungseinstellungen

Die Konfiguration befindet sich in der Datei rxconfig.py.

Datenbank-URL: Standardmäßig sqlite:///reflex.db

App-Name: "AITandem"

### 4.2 Anpassung der KI-Module

Die KI-Komponenten zur Bewertung von Übungsaufgaben können in separaten Modulen ergänzt oder verändert werden.

## 5. Datenbankverwaltung

Das System nutzt Alembic zur Verwaltung von Schemaänderungen.

Neue Migration erstellen:

reflex db makemigrations
refelx db migrate 

## 6. Tests

Um sicherzustellen, dass das System ordnungsgemäß funktioniert, sind Tests mit pytest eingerichtet.

Tests ausführen:

pytest

## 7. Fazit

AITandem bietet eine skalierbare Lösung für die Bereitstellung interaktiver, KI-gestützter Übungsaufgaben an Hochschulen. Durch seine modulare Architektur kann es leicht erweitert und angepasst werden.