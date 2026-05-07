# 🔐 Guide de Configuration Production - SendGrid & Twilio

## 📊 État actuel de la configuration

✅ **Fichier `.env` mis à jour** avec placeholders pour:
- SendGrid (SMTP email)
- Twilio (WhatsApp)

✅ **Vérification du mode** configurée:
- `VERIF_DEV_MODE=0` = Production (envoie vraiment)
- `VERIF_DEV_MODE=1` = Dev (affiche juste les logs)

---

## 🚀 Configuration SendGrid (Emails)

### Étape 1: Créer un compte SendGrid
1. Aller sur [sendgrid.com](https://sendgrid.com)
2. S'inscrire (gratuit: 100 emails/jour)
3. Vérifier l'email de confirmation

### Étape 2: Générer une clé API
1. Aller dans **Settings → API Keys**
2. Cliquer sur **"Create API Key"**
3. Donner un nom: `Unissons la Main Production`
4. Sélectionner les permissions: **Mail Send**
5. Copier la clé (elle commence par `SG.`)

### Étape 3: Mettre à jour `.env`
```env
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.votre_vraie_cle_api_ici
SMTP_FROM="Unissons la Main <noreply@unissonslamain.org>"
```

### Étape 4: Vérifier le domaine d'envoi (optionnel mais recommandé)
1. Dans SendGrid: **Settings → Sender Authentication**
2. Cliquer sur **"Create New Sender"**
3. Vérifier le domaine ou utiliser `noreply@unissonslamain.org`

---

## 📱 Configuration Twilio (WhatsApp)

### Étape 1: Créer un compte Twilio
1. Aller sur [twilio.com](https://twilio.com)
2. S'inscrire (gratuit: $15.50 de crédit)
3. Vérifier le numéro de téléphone

### Étape 2: Configurer WhatsApp
1. Aller dans **Messaging → Try it out → Send a WhatsApp message**
2. Cliquer sur **"Get Started"**
3. Suivre les étapes:
   - Activer WhatsApp Sandbox
   - Confirmer le numéro WhatsApp test: `+14155238886`
   - Envoyer `join XXXXX` à ce numéro

### Étape 3: Obtenir les credentials
1. Aller dans **Account → API keys & tokens**
2. Copier:
   - **ACCOUNT SID** (commence par `AC`)
   - **AUTH TOKEN** (long token)
3. Aller dans **Messaging → Send a WhatsApp message**
4. Copier le **From Number** (commence par `whatsapp:+`)

### Étape 4: Mettre à jour `.env`
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=votre_token_auth_twilio_reel
TWILIO_WHATSAPP_FROM=whatsapp:+1415238886
```

---

## 🔐 Sécurité - Génération de SECRET_KEY

### Générer une clé secrète forte (32+ caractères):

```bash
# Méthode 1: Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Méthode 2: OpenSSL
openssl rand -hex 32

# Méthode 3: En ligne (moins sûr, juste pour test)
# Aller sur https://www.random.org/bytes/ et copier 32 bytes
```

### Mettre à jour `.env`:
```env
SECRET_KEY=votre_cle_de_32_caracteres_aleatoires_ici
DEBUG=False
VERIF_DEV_MODE=0
```

---

## ✅ Checklist avant production

- [ ] SendGrid configuré et clé API obtenue
- [ ] Domaine d'envoi vérifié dans SendGrid
- [ ] Twilio configuré et credentials obtenues
- [ ] WhatsApp Sandbox activé et testable
- [ ] SECRET_KEY générée aléatoirement (32+ caractères)
- [ ] DEBUG=False
- [ ] VERIF_DEV_MODE=0
- [ ] DATABASE_URL pointe vers une vraie base (PostgreSQL recommandé)
- [ ] `.env` ne contient PAS de données de développement
- [ ] `.gitignore` contient `.env` (ne pas versionner les secrets)

---

## 🧪 Tester la configuration

### Exécuter le script de test:
```bash
python test_config.py
```

### Résultat attendu:
```
✅ Email envoyé avec succès
✅ WhatsApp envoyé avec succès
```

---

## 🔍 Dépannage

### Email pas envoyé?
1. Vérifier que `VERIF_DEV_MODE=0`
2. Vérifier la clé API SendGrid dans `.env`
3. Vérifier que le domaine SMTP est correct: `smtp.sendgrid.net`
4. Regarder les logs SendGrid: **Activity Feed**

### WhatsApp pas envoyé?
1. Vérifier que `VERIF_DEV_MODE=0`
2. Vérifier les credentials Twilio
3. Vérifier que le numéro WhatsApp commence par `whatsapp:`
4. Vérifier que le numéro de destination a rejoint le Sandbox

### Erreur "authentication failed"?
1. Vérifier que `SMTP_USER=apikey` (exactement)
2. Vérifier que la clé API SendGrid est correcte
3. Vérifier qu'il n'y a pas d'espaces dans les valeurs

---

## 📧 Exemples d'emails envoyés

### Email de vérification:
```
Subject: Code de vérification Unissons la Main
From: noreply@unissonslamain.org

Votre code: 123456

Ce code expire dans 10 minutes.
```

### WhatsApp de vérification:
```
Votre code de vérification Unissons la Main: 123456
```

---

## 🎯 Flux de vérification par email/SMS

1. **Utilisateur s'inscrit** → Génère un code 6 chiffres
2. **Envoi du code** → Email via SendGrid + SMS via Twilio
3. **Utilisateur reçoit** → Code dans l'email et WhatsApp
4. **Utilisateur rentre le code** → Validé en 10 minutes
5. **Compte activé** → Accès à l'application

---

## 🚀 Après la configuration

1. Redéployer sur Vincel avec les nouvelles variables
2. Exécuter `python test_config.py` pour vérifier
3. Tester l'inscription avec un vrai numéro WhatsApp
4. Vérifier les logs de SendGrid et Twilio
5. Monitorer les rapports de livraison

---

**Status**: ✅ Prêt pour la production!

