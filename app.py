import os
import tempfile
from flask import Flask
from extensions import db, login_manager
from flask_migrate import Migrate

# Create migrate instance (initialized with app later)
migrate = Migrate()


def create_app():
    instance_dir = os.getenv('INSTANCE_PATH') or os.path.join(tempfile.gettempdir(), 'unissons_instance')
    app = Flask(__name__, instance_path=instance_dir)
    os.makedirs(app.instance_path, exist_ok=True)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///unissons.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    # Register a CLI command to initialize the database when desired.
    # Use: `flask init-db` (with FLASK_APP=app.py and activated environment)
    from flask.cli import with_appcontext
    import click

    @app.cli.command('init-db')
    @with_appcontext
    def init_db():
        """Create database tables."""
        db.create_all()
        click.echo('Initialized the database.')

    with app.app_context():
        from models import User
        # Only create tables when explicitly requested via env var.
        # Prevents accidental full DB initialization on every app start.
        if os.getenv('INIT_DB', '0') == '1':
            db.create_all()

        @login_manager.user_loader
        def load_user(user_id):
            return db.session.get(User, int(user_id))

    # Register blueprints
    from verification import bp as verification_bp
    from routes.auth import auth_bp
    from routes.common import common_bp
    from routes.member import member_bp
    from routes.president import president_bp
    from routes.tresorier import tresorier_bp
    from routes.secretaire import secretaire_bp
    from routes.admin import bp as admin_bp
    
    app.register_blueprint(verification_bp, url_prefix='/verify')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(common_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(president_bp)
    app.register_blueprint(tresorier_bp)
    app.register_blueprint(secretaire_bp)
    app.register_blueprint(admin_bp)

    # Register CLI commands
    @app.cli.command()
    def seed_db():
        """Seed the database with test users (president, tresorier, secretaire, members)"""
        from models import User as UserModel
        
        # Create all tables first
        db.create_all()
        
        # Check if users already exist
        existing_user = db.session.query(UserModel).first()
        if existing_user:
            print("✓ Database already has users, skipping seed")
            return
        
        # Create sample users
        users_data = [
            {
                'username': 'president1',
                'full_name': 'Jean Dupont',
                'email': 'president@unissonslamain.local',
                'phone': '+250789123456',
                'role': 'president'
            },
            {
                'username': 'tresorier1',
                'full_name': 'Marie Traore',
                'email': 'tresorier@unissonslamain.local',
                'phone': '+250789123457',
                'role': 'tresorier'
            },
            {
                'username': 'secretaire1',
                'full_name': 'Sophie Bernard',
                'email': 'secretaire@unissonslamain.local',
                'phone': '+250789123458',
                'role': 'secretaire'
            },
            {
                'username': 'member1',
                'full_name': 'Pierre Martin',
                'email': 'member1@unissonslamain.local',
                'phone': '+250789123459',
                'role': 'member'
            },
            {
                'username': 'member2',
                'full_name': 'Alice Johnson',
                'email': 'member2@unissonslamain.local',
                'phone': '+250789123460',
                'role': 'member'
            },
            {
                'username': 'member3',
                'full_name': 'Bob Leblanc',
                'email': 'member3@unissonslamain.local',
                'phone': '+250789123461',
                'role': 'member'
            }
        ]
        
        users = []
        for user_data in users_data:
            user = UserModel(**user_data, is_active=True)
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"✓ Database seeded with {len(users)} users")
        print("✓ Test credentials:")
        print("  - president1 / password123")
        print("  - tresorier1 / password123")
        print("  - secretaire1 / password123")
    
    @app.cli.command()
    def clear_data():
        """Clear all transactional data but keep audit logs and user accounts (admin only)"""
        from models import AuditLog, User as UserModel, Contribution, Loan, Transaction, MonthlySummary
        
        print("⚠️  Cette commande va vider les données transactionnelles (pas les utilisateurs ni l'audit log)")
        print("Les tables suivantes seront vidées:")
        print("  - contributions")
        print("  - loans")
        print("  - transactions")
        print("  - monthly_summaries")
        
        confirm = input("\nÊtes-vous sûr? (tapez 'OUI' pour confirmer): ")
        
        if confirm.upper() != 'OUI':
            print("✗ Opération annulée")
            return
        
        try:
            # Count records before deletion
            contrib_count = db.session.query(Contribution).count()
            loans_count = db.session.query(Loan).count()
            trans_count = db.session.query(Transaction).count()
            summary_count = db.session.query(MonthlySummary).count()
            total_records = contrib_count + loans_count + trans_count + summary_count
            
            # Get president user for audit log
            president = db.session.query(UserModel).filter_by(role='president').first()
            
            # Delete all transactional data
            db.session.query(Contribution).delete()
            db.session.query(Loan).delete()
            db.session.query(Transaction).delete()
            db.session.query(MonthlySummary).delete()
            
            # Create audit log entry
            audit = AuditLog(
                action='database_cleared',
                performed_by=president.id if president else 1,
                description='Nettoyage complet des données transactionnelles',
                affected_records=total_records,
                details=f'Contributions: {contrib_count}, Loans: {loans_count}, Transactions: {trans_count}, Summaries: {summary_count}'
            )
            db.session.add(audit)
            db.session.commit()
            
            print(f"\n✓ Base de données nettoyée avec succès!")
            print(f"  - {total_records} enregistrements supprimés")
            print(f"  - Utilisateurs: {db.session.query(UserModel).count()} (inchangé)")
            print(f"  - Audit logs: Mis à jour")
            print("\n✓ Vous pouvez maintenant commencer avec des données réelles")
            
        except Exception as e:
            db.session.rollback()
            print(f"✗ Erreur lors du nettoyage: {str(e)}")

    return app


if __name__ == '__main__':
    app = create_app()
    # Pour Render: utiliser PORT ou 5000 par défaut
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
