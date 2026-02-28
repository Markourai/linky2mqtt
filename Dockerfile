FROM python:3.14-slim

WORKDIR /app

# Créer le groupe dialout avec le GID 20 (standard Linux) s'il n'existe pas,
# puis créer un utilisateur applicatif membre de ce groupe.
# Cela permet d'accéder à /dev/ttyUSB* sans être root.
RUN groupadd -g 20 dialout 2>/dev/null || true && \
    useradd -m -u 1001 -G dialout appuser
# Dépendances système pour pyserial (accès au port série)
RUN apt-get update && apt-get install -y --no-install-recommends \
        udev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

USER appuser
# L'utilisateur root est nécessaire pour accéder au port série dans Docker,
# ou ajouter l'utilisateur au groupe dialout selon votre config.
CMD ["python", "-u", "main.py"]
