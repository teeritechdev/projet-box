# 🚀 GUIDE COMPLET DE DÉPLOIEMENT DJANGO EN PRODUCTION DE A À Z
> **Environnement cible** : VPS Ubuntu (ex: Contabo), Python 3.12, Nginx, Gunicorn, Systemd, SSL Certbot & GitHub.
> **Exemple de domaine** : `mma.teeritech.bf` | **IP VPS** : `167.86.109.31`

---

## 📌 RÉSUMÉ DE L'ARCHITECTURE DE PRODUCTION

```
[ Navigateur Client ] ──(HTTPS:443 / Port 80)──> [ Serveur Nginx ]
                                                       │ (Proxy Pass 127.0.0.1:8001)
                                                       ▼
                                             [ Gunicorn Service ]
                                                       │
                                                       ▼
                                            [ Application Django ]
```

---

## 🛠️ ÉTAPE 0 : PRÉPARATION DU PROJET EN LOCAL (Sur votre PC)

Avant de toucher au serveur VPS, s'assurer que le projet local contient les fichiers de production :

### 1. `requirements.txt`
Contient la liste de tous les paquets Python requis.
```txt
Django>=5.0,<6.2
pillow>=10.0.0
gunicorn>=26.2.0
whitenoise>=6.12.0
psycopg2-binary>=2.9.0
asgiref>=3.7.0
sqlparse>=0.4.0
tzdata
```

### 2. `Procfile`
Indique la commande d'exécution du serveur Gunicorn.
```procfile
web: gunicorn configuration.wsgi:application --bind 0.0.0.0:$PORT
```

### 3. `configuration/settings.py` (Configuration Statiques & Sécurité)
```python
# Activer WhiteNoise pour les fichiers statiques (CSS, JS, Images UI)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware', # juste sous SecurityMiddleware
    ...
]

# Gestion des statiques
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'statiques']
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Hôtes autorisés et sécurité
ALLOWED_HOSTS = ['*']
X_FRAME_OPTIONS = 'SAMEORIGIN'
```

### 4. Pousser tout le code sur GitHub
```bash
git add .
git commit -m "Préparation déploiement production"
git push origin main
```

---

## 🟢 ÉTAPE 1 : CONNEXION AU VPS & CLONAGE DU PROJET

1. Connectez-vous à votre VPS Ubuntu via votre terminal :
   ```bash
   ssh root@167.86.109.31
   ```

2. Configurez l'authentification Git par jeton (PAT) pour ne plus jamais ressaisir de mot de passe :
   ```bash
   cd /var/www
   git clone https://ghp_VOTRE_TOKEN_GITHUB@github.com/votre-compte/votre-projet.git projet-box
   cd projet-box
   ```

---

## 🔵 ÉTAPE 2 : ENVIRONNEMENT VIRTUEL & DÉPENDANCES PYTHON

1. Installez les paquets système Python requis :
   ```bash
   apt update && apt install -y python3-venv python3-pip
   ```

2. Créez et activez l'environnement virtuel Python (`venv`) :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Installez toutes les dépendances Python du projet :
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

---

## 🟡 ÉTAPE 3 : BASE DE DONNÉES & FICHIERS STATIQUES

1. Créez le dossier statique et appliquez les migrations de la base de données :
   ```bash
   mkdir -p /var/www/projet-box/statiques
   python manage.py makemigrations
   python manage.py migrate
   ```

2. Rassemblez tous les fichiers statiques (CSS, JS, images) dans le dossier de production `staticfiles` :
   ```bash
   python manage.py collectstatic --noinput
   ```

---

## 🟠 ÉTAPE 4 : CRÉATION DU SERVICE SYSTEMD (GUNICORN EN ARRIÈRE-PLAN)

Gunicorn gère les requêtes Django en tâche de fond de manière autonome.

1. Créez le fichier de service système :
   ```bash
   nano /etc/systemd/system/projet-box.service
   ```

2. Collez la configuration suivante :
   ```ini
   [Unit]
   Description=Gunicorn Daemon pour projet-box (JAES 2026)
   After=network.target

   [Service]
   User=root
   WorkingDirectory=/var/www/projet-box
   ExecStart=/var/www/projet-box/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8001 configuration.wsgi:application

   [Install]
   WantedBy=multi-user.target
   ```
   *(Sauvegardez avec `Ctrl+O`, `Entrée`, puis `Ctrl+X`)*.

3. Démarrez et activez le service au démarrage du serveur :
   ```bash
   systemctl daemon-reload
   systemctl start projet-box
   systemctl enable projet-box
   ```

4. Vérifiez que le service fonctionne (statut vert `active (running)`) :
   ```bash
   systemctl status projet-box
   ```

---

## 🌐 ÉTAPE 5 : CONFIGURATION DU SERVEUR WEB NGINX

Nginx réceptionne le trafic web sur le port 80/443, gère le cache/statiques et transmet le reste à Gunicorn.

1. Créez le fichier de configuration Nginx pour votre domaine :
   ```bash
   nano /etc/nginx/sites-available/projet-box
   ```

2. Collez la configuration suivante :
   ```nginx
   server {
       listen 80;
       server_name mma.teeritech.bf 167.86.109.31;

       client_max_body_size 20M;

       location /static/ {
           alias /var/www/projet-box/staticfiles/;
       }

       location /media/ {
           alias /var/www/projet-box/media/;
       }

       location / {
           proxy_pass http://127.0.0.1:8001;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # Support Streaming Temps Réel (SSE / WebSockets) pour l'écran TV broadcast
           proxy_buffering off;
           proxy_cache off;
           proxy_read_timeout 86400s;
       }
   }
   ```
   *(Sauvegardez avec `Ctrl+O`, `Entrée`, puis `Ctrl+X`)*.

3. Activez le site et relancez Nginx :
   ```bash
   ln -s /etc/nginx/sites-available/projet-box /etc/nginx/sites-enabled/
   nginx -t
   systemctl restart nginx
   ```

---

## 🌐 ÉTAPE 6 : POINTEUR DNS (CHEZ VOTRE FOURNISSEUR DE DOMAINE)

Connectez-vous au panneau d'administration de votre nom de domaine (`teeritech.bf`) :
1. Allez dans **Zone DNS / DNS Records**.
2. Ajoutez un enregistrement de **Type A** :
   * **Host / Nom** : `mma` (pour cibler `mma.teeritech.bf`)
   * **Type** : `A`
   * **Valeur / Cible IP** : `167.86.109.31`
   * **TTL** : Automatique (3600)

---

## 🔒 ÉTAPE 7 : ACTIVATION DE SÉCURITÉ HTTPS (SSL CERTBOT GRATUIT)

Une fois le pointeur DNS propagé, activez le cadenas HTTPS sécurisé 🔒 :

1. Installez Certbot pour Nginx :
   ```bash
   apt update && apt install -y certbot python3-certbot-nginx
   ```

2. Obtenez et installez le certificat SSL automatiquement :
   ```bash
   certbot --nginx -d mma.teeritech.bf
   ```

3. Certbot modifie automatiquement Nginx pour rediriger tout le trafic en `HTTPS://` sécurisé !

---

## 🔄 ÉTAPE 8 : SCRIPT DE MISE À JOUR AUTOMATIQUE (MISE À JOUR EN 2 SECONDES)

Sur votre VPS dans le dossier du projet (`/var/www/projet-box`), créez le fichier `update.sh` :

1. Ouvrez l'éditeur :
   ```bash
   nano update.sh
   ```

2. Ajoutez ce script d'automatisation :
   ```bash
   #!/bin/bash
   echo "🔄 Récupération des nouveautés depuis GitHub..."
   git pull origin main
   source venv/bin/activate
   pip install -r requirements.txt
   python manage.py migrate
   python manage.py collectstatic --noinput
   sudo systemctl restart projet-box
   echo "✅ Déploiement mis à jour avec succès sur https://mma.teeritech.bf !"
   ```

3. Rendez le script exécutable :
   ```bash
   chmod +x update.sh
   ```

### 💡 Workflow quotidien de travail :
1. Vous apportez des modifications sur votre PC local.
2. Vous faites `git commit` et `git push origin main`.
3. Sur votre VPS Contabo, vous tapez simplement :
   ```bash
   ./update.sh
   ```
4. Votre application web en ligne est mise à jour instantanément !

---

## 🛠️ AIDE-MÉMOIRE DES COMMANDES UTILES EN PRODUCTION

| Action | Commande Linux / Terminal |
|---|---|
| **Voir le statut du serveur Python** | `systemctl status projet-box` |
| **Redémarrer le serveur Python** | `systemctl restart projet-box` |
| **Voir les erreurs/logs en direct** | `journalctl -u projet-box -f` |
| **Redémarrer le serveur Web Nginx** | `systemctl restart nginx` |
| **Tester la syntaxe Nginx** | `nginx -t` |
| **Lancer la mise à jour du site** | `./update.sh` |
