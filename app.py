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

    return app


if __name__ == '__main__':
    app = create_app()
    # Pour Render: utiliser PORT ou 5000 par défaut
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug, host='0.0.0.0', port=port)
