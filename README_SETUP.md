# Unissons la Main - Guide de démarrage

## 🎯 Vue d'ensemble

**Unissons la Main** est une plateforme web de gestion de **caisse familiale solidaire**. Chaque membre cotise 1000 FCFA par mois pour créer un fonds d'urgence collectif.

## ✨ Fonctionnalités

### 👑 Rôles disponibles

1. **Président**
   - Valide ou refuse les demandes de prêt d'urgence
   - Consulte toutes les statistiques
   - Gère les rapports mensuels
   - Accède à la liste complète des membres

2. **Trésorier**
   - Enregistre et valide les cotisations
   - Gère les remboursements de prêts
   - Suit l'équilibre de la caisse
   - Consulte l'historique des transactions

3. **Secrétaire**
   - Génère les rapports mensuels
   - Exporte les données (CSV, PDF)
   - Publie les rapports du 10 du mois
   - Accède à l'historique complet

4. **Membre**
   - Consulte son historique de cotisations
   - Demande des prêts d'urgence
   - Suit le solde de la caisse
   - Voit les annonces

## 🚀 Installation

### 1. Prérequis
- Python 3.8+
- pip

### 2. Installation des dépendances

```bash
cd FRANCK
pip install -r requirements.txt
```

### 3. Configuration

Copier `.env.example` vers `.env` et adapter les paramètres :

```bash
cp .env.example .env
```

Éditer `.env` :
```env
SECRET_KEY=votre_clé_secrète
DEBUG=True
DATABASE_URL=sqlite:///unissons.db
VERIF_DEV_MODE=1
```

### 4. Initialisation de la base de données

```bash
python init_db.py
```

Cela va :
- Créer la structure de la base de données
- Créer 6 utilisateurs de test
- Générer des données d'exemple

### 5. Lancement de l'application

```bash
python app.py
```

L'application sera accessible sur : **http://127.0.0.1:5000**

## 👤 Comptes de test

| Identifiant | Mot de passe | Rôle |
|------------|------------|------|
| president1 | password123 | Président |
| tresorier1 | password123 | Trésorier |
| secretaire1 | password123 | Secrétaire |
| member1 | password123 | Membre |
| member2 | password123 | Membre |
| member3 | password123 | Membre |

## 📁 Structure du projet

```
FRANCK/
├── app.py                 # Application principale
├── models.py              # Modèles de données
├── extensions.py          # Extensions (SQLAlchemy, LoginManager)
├── init_db.py            # Script d'initialisation
├── requirements.txt      # Dépendances
├── .env                  # Configuration
│
├── routes/               # Routes par module
│   ├── auth.py          # Authentification
│   ├── common.py        # Routes communes
│   ├── member.py        # Routes membres
│   ├── president.py     # Routes président
│   ├── tresorier.py     # Routes trésorier
│   └── secretaire.py    # Routes secrétaire
│
├── templates/           # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── auth/
│   ├── member/
│   ├── president/
│   ├── tresorier/
│   └── secretaire/
│
├── static/              # Fichiers statiques
│   ├── css/
│   ├── js/
│   └── images/
│
└── verification/        # Module de vérification
    ├── routes.py
    ├── utils.py
    └── __init__.py
```

## 🔄 Flux d'utilisation

### 1. Inscription et connexion
- Accéder à `/auth/register` pour s'inscrire
- Se connecter avec `/auth/login`

### 2. Contribution mensuelle (Trésorier)
1. Aller à `/tresorier/contributions`
2. Voir la liste des cotisations en attente
3. Valider les paiements reçus
4. Enregistrer la méthode de paiement

### 3. Demande de prêt (Membre)
1. Cliquer sur "Demander un prêt" depuis le dashboard
2. Remplir le montant et la raison
3. Soumettre la demande

### 4. Approbation de prêt (Président)
1. Aller à `/president/loans`
2. Examiner les demandes
3. Approuver ou rejeter avec commentaires
4. Définir la durée de remboursement

### 5. Rapports (Secrétaire)
1. Aller à `/secretaire/monthly-report`
2. Sélectionner le mois
3. Exporter en CSV ou PDF

## 📊 Modèles de données

### User
- Authentification et profil
- Rôle (president, tresorier, secretaire, member)
- Status d'activation

### Contribution
- Cotisation mensuelle (1000 FCFA)
- Status (pending, paid, overdue)
- Validation par le trésorier

### Loan
- Demande de prêt d'urgence
- Status (pending, approved, rejected, repaid)
- Montant demandé et remboursé
- Approbation par le président

### Transaction
- Audit log de toutes les opérations
- Traçabilité complète des finances

### VerificationCode
- Codes de vérification pour inscription/réinitialisation

## 🔐 Sécurité

- Authentification avec Flask-Login
- Contrôle d'accès basé sur les rôles
- Hachage des mots de passe avec Werkzeug
- CSRF protection via Flask

## 📝 Variables d'environnement

| Variable | Description | Exemple |
|----------|-------------|---------|
| SECRET_KEY | Clé secrète Flask | dev-secret-key |
| DEBUG | Mode développement | True/False |
| DATABASE_URL | URL de la base de données | sqlite:///unissons.db |
| VERIF_DEV_MODE | Mode développement vérification | 1 |
| SMTP_HOST | Serveur SMTP | smtp.sendgrid.net |
| SMTP_PORT | Port SMTP | 587 |
| TWILIO_ACCOUNT_SID | Compte Twilio | ACxxxxxxxx |

## 🐛 Dépannage

### La base de données ne se crée pas
```bash
# Supprimer l'ancienne DB
rm unissons.db

# Réinitialiser
python init_db.py
```

### Port déjà en utilisation
Modifier le port dans `app.py` :
```python
app.run(debug=True, port=5001)
```

### Problèmes d'import
Vérifier que toutes les dépendances sont installées :
```bash
pip install -r requirements.txt --upgrade
```

## 📦 Déploiement en production

Pour un déploiement en production :

1. Installer un serveur WSGI (Gunicorn, uWSGI)
2. Configurer une base de données PostgreSQL
3. Utiliser un reverse proxy (Nginx)
4. Activer HTTPS
5. Configurer les variables d'environnement

Exemple avec Gunicorn :
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## 🤝 Contribution

Les contributions sont bienvenues ! N'hésitez pas à signaler les bugs ou proposer des améliorations.

## 📄 Licence

Projet open source pour la communauté.

---

**Support & Contact**: Pour toute question, consultez la documentation ou contactez l'équipe de développement.
