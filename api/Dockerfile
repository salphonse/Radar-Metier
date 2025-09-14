# Utilisation d'une image de base Python
FROM python:3.13-slim

# Definir le répertoire de travail à l'intérieur du conteneur
WORKDIR /app

# Copier le fichier de dépendances
COPY requirements.txt ./

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code de l'application et le modèle
COPY main.py ./
#COPY house_price_model.pkl ./

# Exposer le port par défaut
EXPOSE 8000

# Commande pour démarrer l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
