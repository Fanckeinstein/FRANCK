# 👋 Unissons la Main

## Une plateforme de solidarité financière familiale

**Unissons la Main** est une plateforme web moderne permettant de gérer une **caisse familiale/solidaire** : cotisations mensuelles, gestion des prêts d'urgence, et transparence financière totale.

---

## 🎯 Objectif Principal

Chaque membre cotise **1000 FCFA par mois**. L'argent collecté sert à :
- Aider un membre en cas d'urgence
- Accorder des prêts temporaires
- Suivre les remboursements
- Garantir une totale transparence financière

---

## 👥 Types d'Utilisateurs

### 👑 Président
- Valider ou refuser les demandes de prêt
- Voir toutes les transactions
- Voir le solde global
- Accéder aux statistiques

### 💰 Trésorier
- Enregistrer les cotisations
- Enregistrer les dépôts Mobile Money (74471513)
- Mettre à jour la caisse
- Voir le solde total
- Confirmer les remboursements

### 📝 Secrétaire
- Générer le bilan mensuel
- Voir l'historique complet
- Publier les rapports du 10 du mois
- Exporter les données PDF/Excel

### 👥 Membres
- Voir leur propre historique
- Voir le solde global de la caisse
- Voir les cotisations effectuées
- Voir les prêts accordés
- Faire une demande de prêt
- Voir les annonces
- Voir le bilan mensuel

---

## ✨ Fonctionnalités Principales

### 1. Authentification
- Inscription avec email/numéro
- Vérification par code (email + WhatsApp)
- Mot de passe crypté
- Gestion des rôles

### 2. Gestion des Cotisations
- Enregistrement des paiements
- Statut : ✅ Payé, ⏳ En attente, ❌ Non payé
- Capture de preuves Mobile Money
- Historique des paiements

### 3. Gestion des Prêts/Urgences
- Demande de montant + justification
- Validation par Président
- Suivi du remboursement
- Historique complet

### 4. Transparence Financière
- Tous les membres voient le solde global
- Cotisations reçues visibles
- Prêts accordés visibles
- Remboursements effectués visibles
- Seuls les gestionnaires peuvent modifier

### 5. Bilan Mensuel Automatique
- Généré le 10 du mois
- Total collecté
- Total prêté
- Total remboursé
- Solde restant
- Export PDF/Excel

### 6. Notifications
- Rappel de cotisation
- Validation de prêt
- Nouveau bilan
- Retard de remboursement

### 7. Mobile Money
- Numéro officiel : **74471513**
- Capture d'écran pour preuve
- Validation par Trésorier

---

## 🛠 Technologie

### Backend
- **Flask 3.0** (Python 3.12)
- **SQLAlchemy** (ORM)
- **SQLite** (dev) / **PostgreSQL** (prod)

### Frontend (TODO)
- **React.js**
- **Tailwind CSS**

### Authentification
- Flask-Login
- Vérification par email (SMTP)
- Vérification WhatsApp (Twilio)

### Deployment
- Python 3.12+
- pip/virtualenv

---

## 🚀 Installation

### 1. Clone le repository
```bash
git clone https://github.com/Fanckeinstein/FRANCK.git
cd FRANCK
```

### 2. Crée un environnement virtuel
```bash
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

### 3. Installe les dépendances
```bash
pip install -r requirements.txt
```

### 4. Configure `.env`
```bash
cp .env.example .env
# Édite .env avec tes paramètres (SMTP, Twilio, etc.)
```

### 5. Lance le serveur
```bash
python app.py
```

Le serveur démarre sur **http://127.0.0.1:5000**

### Initialiser la base de données (contrôlé)

Par défaut l'application ne recrée pas les tables automatiquement pour éviter d'écraser des données.

Méthode 1 — Démarrage temporaire avec variable d'environnement (PowerShell):

```powershell
$env:INIT_DB='1'
python app.py
```

Méthode 2 — Commande Flask (recommandée):

Active ton environnement virtuel puis :

```powershell
$env:FLASK_APP='app.py'
flask init-db
```

La commande `flask init-db` crée les tables sans lancer le serveur.

---

## 📖 API Documentation

### Inscription
**POST** `/verify/register`

```json
{
  "username": "john_doe",
  "full_name": "John Doe",
  "email": "john@example.com",
  "phone": "+225XXXXXXXXXX",
  "password": "secure_password"
}
```

### Vérification
**POST** `/verify/verify`

```json
{
  "username": "john_doe",
  "code": "123456"
}
```

---

## 🎨 Design

### Couleurs
- 🟢 **Vert** : Solidarité
- 🔵 **Bleu** : Confiance
- ⚪ **Blanc** : Transparence

### Style
- Moderne
- Professionnel
- Familial
- Clair et simple
- **Responsive** (Mobile + Ordinateur)

---

## 📋 Roadmap

### Phase 1 (Actuelle)
- ✅ Authentification + vérification (Email + WhatsApp)
- ✅ Modèles de données
- ⏳ Gestion des cotisations
- ⏳ Gestion des prêts
- ⏳ Dashboards

### Phase 2
- Notifications
- Bilan mensuel automatique
- PDF/Excel exports
- Audit logs

### Phase 3
- Mobile app
- QR codes
- Chat/Annonces
- Signatures numériques

---

## 🔐 Sécurité

- Mots de passe hashés (Werkzeug)
- Codes de vérification temporaires (15 min)
- Gestion des rôles (RBAC)
- HTTPS recommandé en production
- Audits complets des transactions

---

## 📞 Support

Pour des questions ou des suggestions, contacte : **Franck**

---

## 📄 Licence

Ce projet est sous licence **MIT**.

---

**Ensemble, nous avançons plus loin. 🚀**
