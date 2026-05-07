#!/usr/bin/env python
"""
Script de test pour vérifier que SendGrid et Twilio sont correctement configurés
"""
import os
from dotenv import load_dotenv
from verification.utils import send_email, send_whatsapp, generate_code

# Charger les variables d'environnement
load_dotenv()

def test_configuration():
    print("=" * 60)
    print("🔧 TEST DE CONFIGURATION - SENDGRID & TWILIO")
    print("=" * 60)
    
    # Afficher la configuration (masquer les clés sensibles)
    smtp_host = os.getenv('SMTP_HOST', '')
    smtp_port = os.getenv('SMTP_PORT', '')
    smtp_user = os.getenv('SMTP_USER', '')
    twilio_account = os.getenv('TWILIO_ACCOUNT_SID', '')[:8] + '...'
    verif_mode = os.getenv('VERIF_DEV_MODE', '1')
    debug = os.getenv('DEBUG', 'True')
    
    print(f"\n📋 Configuration actuelle:")
    print(f"   DEBUG:                    {debug}")
    print(f"   VERIF_DEV_MODE:           {verif_mode} (0=Production, 1=Dev)")
    print(f"   SMTP_HOST:                {smtp_host}")
    print(f"   SMTP_PORT:                {smtp_port}")
    print(f"   SMTP_USER:                {smtp_user}")
    print(f"   TWILIO_ACCOUNT_SID:       {twilio_account if twilio_account != '...' else 'Non configuré'}")
    
    # Test 1: Vérifier les variables
    print(f"\n✅ Étape 1: Vérifier les variables d'environnement")
    
    if not os.getenv('SECRET_KEY') or os.getenv('SECRET_KEY') == 'dev-secret-key-change-in-prod':
        print("   ⚠️  SECRET_KEY n'est pas configurée (placeholder)")
    else:
        print("   ✓ SECRET_KEY configurée")
    
    if os.getenv('DEBUG') == 'False':
        print("   ✓ DEBUG=False (Mode production)")
    else:
        print("   ⚠️  DEBUG=True (Mode développement)")
    
    # Test 2: Test email
    print(f"\n✅ Étape 2: Tester SendGrid")
    code = generate_code()
    test_email = "test@example.com"
    
    print(f"   Envoi d'un code de vérification de test...")
    email_result = send_email(
        test_email,
        f"Code de vérification Unissons la Main: {code}",
        f"Votre code: {code}\n\nCe code expire dans 10 minutes."
    )
    
    if email_result:
        print(f"   ✓ Email envoyé avec succès (ou mode dev activé)")
    else:
        print(f"   ✗ Erreur lors de l'envoi de l'email")
    
    # Test 3: Test WhatsApp
    print(f"\n✅ Étape 3: Tester Twilio/WhatsApp")
    test_phone = "+250789123456"
    
    print(f"   Envoi d'un message WhatsApp de test...")
    whatsapp_result = send_whatsapp(
        test_phone,
        f"Votre code de vérification Unissons la Main: {code}"
    )
    
    if whatsapp_result:
        print(f"   ✓ WhatsApp envoyé avec succès (ou mode dev activé)")
    else:
        print(f"   ✗ Erreur lors de l'envoi du WhatsApp")
    
    # Recommandations
    print(f"\n📝 Recommandations pour la production:")
    print(f"   1. Générer une SECRET_KEY forte (32+ caractères aléatoires)")
    print(f"   2. Remplacer les clés d'API SendGrid et Twilio")
    print(f"   3. Mettre DEBUG=False")
    print(f"   4. Mettre VERIF_DEV_MODE=0")
    print(f"   5. Configurer le DATABASE_URL approprié (PostgreSQL recommandé)")
    
    # Exemple de génération de clé
    print(f"\n🔑 Génération d'une clé secrète:")
    import secrets
    new_key = secrets.token_urlsafe(32)
    print(f"   SECRET_KEY={new_key}")
    
    print(f"\n" + "=" * 60)
    print("✨ Configuration testée!")
    print("=" * 60)

if __name__ == '__main__':
    test_configuration()
