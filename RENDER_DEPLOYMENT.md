# 🚀 Guide de déploiement RENDER - Dépannage & Configuration

## ❌ Problème rencontré

**Erreur**: "L'application s'est arrêtée prématurément"
**Status**: 🔴 Crashed

---

## ✅ Solutions appliquées

### 1. Vérification du `requirements.txt`
```bash
✓ Flask==3.0.0
✓ Flask-SQLAlchemy==3.1.1
✓ gunicorn==21.2.0
✓ python-dotenv==1.0.0
✓ Toutes les dépendances présentes
```

### 2. Vérification du `Procfile`
```
web: gunicorn app:app
```
✓ Correct

### 3. Vérification du `runtime.txt`
```
python-3.12.10
```
✓ Version stable

---

## 🔧 Configuration RENDER - Étapes

### Étape 1: Créer une nouvelle application
1. Aller sur [render.com](https://render.com)
2. Cliquer sur **"New +" → "Web Service"**
3. Connecter votre GitHub: `https://github.com/Fanckeinstein/FRANCK`
4. Sélectionner la branche: `main`

### Étape 2: Configurer les paramètres

**Name**: `unissons-la-main` (ou autre)

**Region**: Sélectionner `Singapour` ou `Europe`

**Branch**: `main`

**Runtime**: Laisser Render détecter automatiquement (Python)

### Étape 3: Configuration BUILD

**Build Command** (IMPORTANT):
```bash
pip install -r requirements.txt
```

**Start Command** (IMPORTANT):
```bash
gunicorn app:app
```

### Étape 4: Configuration ENVIRONMENT VARIABLES

Ajouter ces variables (cliquer sur "Advanced" → "Add Environment Variable"):

```
DEBUG=False
SECRET_KEY=votre_cle_secrete_long_et_aleatoire
DATABASE_URL=sqlite:///unissons.db
VERIF_DEV_MODE=0
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.votre_cle_api_sendgrid
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxx
TWILIO_AUTH_TOKEN=token_twilio
TWILIO_WHATSAPP_FROM=whatsapp:+1415xxxxxx
```

### Étape 5: Deploy

1. Cliquer sur **"Create Web Service"**
2. Attendre que Render construise et déploie (~5 minutes)
3. Voir l'URL: `https://votre-app.onrender.com`

---

## 🔍 Dépannage - Si ça échoue encore

### Vérifier les logs

1. Aller dans votre application Render
2. Cliquer sur l'onglet **"Logs"**
3. Regarder les dernières lignes pour l'erreur

### Erreurs courantes

#### Erreur: `ModuleNotFoundError: No module named 'app'`
**Cause**: Le `Procfile` pointe vers un mauvais nom  
**Solution**: Vérifier que votre fichier principal s'appelle bien `app.py`

#### Erreur: `Address already in use`
**Cause**: Le port est mal configuré  
**Solution**: Render utilise les ports dynamiques. Ajouter ceci dans `app.py`:
```python
import os
port = int(os.getenv('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

#### Erreur: `ImportError` ou `ModuleNotFoundError`
**Cause**: Une dépendance manque  
**Solution**: Vérifier `requirements.txt` a toutes les dépendances importées dans le code

#### Erreur: `DATABASE_URL` invalide
**Cause**: SQLite ne fonctionne pas bien sur Render  
**Solution**: Configurer PostgreSQL (voir ci-dessous)

---

## 💾 Meilleure pratique: PostgreSQL

Render fournit une base de données PostgreSQL **gratuite** (limites) :

### 1. Créer une PostgreSQL Database
- Cliquer sur **"New +" → "PostgreSQL"**
- Laisser les valeurs par défaut
- Cliquer sur **"Create Database"**

### 2. Ajouter la DATABASE_URL
Render crée automatiquement la variable `DATABASE_URL` pointant vers PostgreSQL. C'est déjà configuré!

### 3. Ajouter le driver PostgreSQL
Ajouter à `requirements.txt`:
```
psycopg2-binary==2.9.9
```

---

## ✅ Checklist avant de déployer

- [ ] `requirements.txt` contient `gunicorn`
- [ ] `Procfile` exists with: `web: gunicorn app:app`
- [ ] `runtime.txt` exists with Python version
- [ ] Tous les fichiers sont sur GitHub
- [ ] Connecté à GitHub sur Render
- [ ] Build Command: `pip install -r requirements.txt`
- [ ] Start Command: `gunicorn app:app`
- [ ] Environment Variables configurées
- [ ] Port configuré dynamiquement dans Flask

---

## 📊 URL après déploiement

Une fois déployé, vous pouvez accéder à:
```
https://votre-app.onrender.com
```

---

## 🚀 Déploiement rapide

Si vous avez tout configuré:

1. Poussez vos changements sur GitHub
2. Render redéployera automatiquement
3. Attendez 2-5 minutes
4. Vérifiez les logs
5. Accédez à l'URL

---

## 📞 Si ça ne fonctionne pas

1. Regarder les **Logs** sur Render
2. Copier l'erreur exacte
3. Me la partager
4. Je corrigerai le problème

**Status**: 🟢 Prêt pour Render!

