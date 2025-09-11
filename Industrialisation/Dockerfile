# Image de base Python
FROM python:3.12-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers nécessaires
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .
COPY modele_epoch4001.pkl .
COPY model.py .

# Exposer le port
EXPOSE 8000

# Commande pour lancer l’API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

#https://docs.docker.com/reference/dockerfile/#env


