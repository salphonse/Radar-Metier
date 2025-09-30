
#Image de base Python slim
FROM python:3.12-slim

# Empêche Python d’écrire des fichiers .pyc
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

#Définir répertoire de travail à l'intérieur du conteneur
WORKDIR /app


#Copier le fichiers de dépendances
COPY requirements.txt ./


#Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

#Copier le code de l'application et le modèle dans le conteneur
COPY main.py ./


#Expose le port par défaut de FastAPI
EXPOSE 8000

#Commande pour démarrer l'application avec Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

