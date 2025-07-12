# Projet Géolocalisation avec Neo4j, Python et React

## 📝 Description
Ce projet est une application de géolocalisation qui permet de rechercher des lieux (cafés, restaurants, etc.) à proximité, calculer des itinéraires, et visualiser les résultats sur une interface web.  
La base de données utilise Neo4j pour stocker et interroger les données sous forme de graphes. Le backend est en Python (Flask/FastAPI) et le frontend en React.

## 🚀 Fonctionnalités principales
- Recherche de lieux par type et proximité
- Calcul d’itinéraires optimisés entre deux points
- Affichage interactif des résultats sur la carte
- Gestion des données dans Neo4j avec requêtes Cypher personnalisées

## 🛠️ Technologies utilisées
- Base de données : Neo4j (graph database)
- Backend : Python avec Flask 
- Frontend : React.js
- API géolocalisation : OpenStreetMap / OSRM 

## 📋 Prérequis
- Neo4j Community/Enterprise installé
- Python 3.x installé
- Node.js et npm installés

## ⚙️ Installation et lancement

#### Pour importer les données :

### 1. Importer la base Neo4j

Nous utilisons un script Python (`backend/import_places.py`) qui interroge l’API OpenStreetMap via la bibliothèque `overpy` pour récupérer des lieux (cafés, pharmacies, écoles, restaurants) dans une zone administrative (exemple : Rabat).  

Le script calcule le centre géographique des objets `way` et insère les données dans la base Neo4j en créant des nœuds `Place` avec leurs propriétés (`name`, `type`, `latitude`, `longitude`).

```bash
cd backend
pip install -r requirements.txt
python import_places.py


2. Lancer le backend Python
cd backend
pip install -r requirements.txt
python app.py


3. Lancer le frontend React
cd frontend
npm install
npm start
