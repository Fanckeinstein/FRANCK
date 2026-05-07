import os
from flask import Flask
from extensions import db, login_manager


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-prod')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///unissons.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    login_manager.init_app(app)

    with app.app_context():
        from models import User
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
    
    app.register_blueprint(verification_bp, url_prefix='/verify')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(common_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(president_bp)
    app.register_blueprint(tresorier_bp)
    app.register_blueprint(secretaire_bp)

    # Register CLI commands
    @app.cli.command()
    def seed_db():
        """Seed the database with test users (president, tresorier, secretaire, members)"""
        from models import User
        
        # Create all tables first
        db.create_all()
        
        # Check if users already exist
        existing_user = db.session.query(User).first()
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
            user = User(**user_data, is_active=True)
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        print(f"✓ Database seeded with {len(users)} users")
        print("✓ Test credentials:")
        print("  - president1 / password123")
        print("  - tresorier1 / password123")
        print("  - secretaire1 / password123")

    return app


if __name__ == '__main__':
    app = create_app()
    # Pour Render: utiliser PORT ou 5000 par défaut
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
