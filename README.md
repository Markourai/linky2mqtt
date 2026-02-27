# linky2mqtt

Bridge Docker : **compteur Linky (TIC historique)** → **MQTT**

Remplace le flow Node-RED *Teleinformation Detail*.

---

## Topics MQTT publiés

Tous les topics sont publiés avec `retain=true` et uniquement si la valeur change (RBE).

| Topic                    | Description                            | Unité |
|--------------------------|----------------------------------------|-------|
| `edf/index_wh`           | Index total (somme toutes couleurs)    | Wh    |
| `edf/index_kwh`          | Index total                            | kWh   |
| `edf/index_hp_kwh`       | Index HP total (B+W+R)                 | kWh   |
| `edf/index_hc_kwh`       | Index HC total (B+W+R)                 | kWh   |
| `edf/index_hpb_kwh`      | Index HP Bleu (BBRHPJB)                | kWh   |
| `edf/index_hpw_kwh`      | Index HP Blanc (BBRHPJW)               | kWh   |
| `edf/index_hpr_kwh`      | Index HP Rouge (BBRHPJR)               | kWh   |
| `edf/index_hcb_kwh`      | Index HC Bleu (BBRHCJB)                | kWh   |
| `edf/index_hcw_kwh`      | Index HC Blanc (BBRHCJW)               | kWh   |
| `edf/index_hcr_kwh`      | Index HC Rouge (BBRHCJR)               | kWh   |
| `edf/iinst1`             | Courant instantané phase 1 (IINST)     | A     |
| `edf/iinst2`             | Courant instantané phase 2 (IINST2)    | A     |
| `edf/iinst3`             | Courant instantané phase 3 (IINST3)    | A     |
| `edf/papp`               | Puissance apparente (PAPP)             | VA    |
| `edf/pmax`               | Puissance max (PMAX)                   | VA    |
| `edf/ptec`               | Période tarifaire en cours             | texte |
| `edf/tempo_day`          | Couleur Tempo aujourd'hui              | BLUE/WHITE/RED |
| `edf/next_tempo_day`     | Couleur Tempo demain (DEMAIN)          | BLUE/WHITE/RED |

> **Note :** `edf/pinst` (puissance instantanée calculée depuis l'historique HA) n'est pas
> reproduit ici car il dépend de Home Assistant. Cette donnée peut être calculée directement
> dans HA à partir de `edf/index_wh` avec l'intégration *Utility Meter* ou un template sensor.

---

## Installation

```bash
# 1. Cloner / copier le dossier
cd linky2mqtt

# 2. Créer le fichier de configuration
cp .env.example .env
nano .env   # ajuster le port série et les paramètres MQTT

# 3. Identifier votre adaptateur USB→série si nécessaire
ls /dev/ttyUSB* /dev/ttyACM*
# Mettre à jour 'devices' dans docker-compose.yml si besoin

# 4. Lancer
docker compose up -d

# 5. Vérifier les logs
docker compose logs -f
```

---

## Accès au port série

Le conteneur accède au port série via `devices` dans `docker-compose.yml`.  
Si vous obtenez une erreur de permission, deux options :

**Option A** — ajouter l'utilisateur courant au groupe `dialout` sur l'hôte :
```bash
sudo usermod -aG dialout $USER
# puis se reconnecter
```

**Option B** — lancer le conteneur avec les droits nécessaires :
```yaml
# dans docker-compose.yml
user: root
```

---

## Structure du projet

```
linky2mqtt/
├── main.py              # Bridge principal
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example         # → copier en .env et configurer
```
