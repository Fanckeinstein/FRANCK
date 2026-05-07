# 🚀 Déploiement sur Vincel - Guide de dépannage

## ❌ Problème: Le lien télécharge `app.py` au lieu d'afficher l'application

Cela signifie que le serveur ne sait pas comment **exécuter** votre application Flask.

---

## ✅ Solutions appliquées

### 1. **Procfile** (Créé)
```
web: gunicorn app:app
```
- Indique à Vincel comment démarrer votre application
- Utilise `gunicorn` comme serveur WSGI

### 2. **Gunicorn** (Ajouté aux requirements.txt)
- Serveur de production pour exécuter Flask
- Remplace le serveur de développement `python app.py`

### 3. **wsgi.py** (Créé)
- Point d'entrée pour les serveurs WSGI
- Configure les variables d'environnement pour la production

### 4. **runtime.txt** (Créé)
- Spécifie la version de Python (3.12.10)

---

## 📋 Checklist de déploiement

- [ ] Cloner/télécharger le repository mis à jour depuis GitHub
- [ ] Vérifier que `Procfile` existe à la racine
- [ ] Vérifier que `requirements.txt` contient `gunicorn`
- [ ] Vérifier que `.env` est configuré (ou le faire directement sur Vincel)
- [ ] Re-déployer sur Vincel

---

## 🔧 Configuration supplémentaire sur Vincel

Selon le type de Vincel, vous devrez peut-être :

### Si c'est un **VPS** ou **hébergement classique**:
1. Installer Python 3.12+
2. Exécuter : `pip install -r requirements.txt`
3. Exécuter : `gunicorn -w 4 -b 0.0.0.0:5000 app:app`

### Si c'est un **PaaS** (Heroku-like):
1. Le déploiement devrait être automatique avec `Procfile`
2. Les variables d'environnement se configurent dans le dashboard

### Si c'est de l'**hébergement partagé** (cPanel):
1. Configurer un **Python WSGI Application** 
2. Pointer vers `wsgi.py`
3. Définir le répertoire racine du projet

---

## 🌐 Configuration de l'URL

Le `.env` doit avoir la bonne `DATABASE_URL`:

```env
SECRET_KEY=votre-clé-secrète-long-et-aléatoire
DEBUG=False
DATABASE_URL=sqlite:///unissons.db
# ou pour PostgreSQL:
# DATABASE_URL=postgresql://user:password@host:port/database
```

---

## 📞 Questions pour diagnostiquer

1. **Quel type de service Vincel ?** (PaaS, VPS, Shared Hosting ?)
2. **Quelle est l'URL exacte du site ?**
3. **Comment avez-vous déployé ?** (Git push, FTP, dashboard web ?)
4. **Y a-t-il des logs d'erreur ?** (Où les consulter ?)

---

## 💡 Prochaines étapes

1. Mettez à jour votre déploiement Vincel avec les nouveaux fichiers
2. Partagez le lien et les logs d'erreur (s'il y en a)
3. Je pourrai ajuster la configuration en fonction

Le projet devrait maintenant fonctionner correctement! 🎉
