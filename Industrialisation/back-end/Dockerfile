# Image de base Python
FROM python:3.12-slim

# Installer dépendances système pour psycopg2
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copier requirements.txt
COPY requirements.txt .

# Installer dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier ton code
COPY main.py .
COPY modele_epoch4001.pkl .
COPY model.py .

# Exposer le port
EXPOSE 8000

# Commande pour lancer l’API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

#https://docs.docker.com/reference/dockerfile/#env


