FROM python:3.14-slim

WORKDIR /app

# Dépendances système pour pyserial (accès au port série)
RUN apt-get update && apt-get install -y --no-install-recommends \
        udev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

# L'utilisateur root est nécessaire pour accéder au port série dans Docker,
# ou ajouter l'utilisateur au groupe dialout selon votre config.
CMD ["python", "-u", "main.py"]
