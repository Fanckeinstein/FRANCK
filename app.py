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
    app.register_blueprint(verification_bp, url_prefix='/verify')

    @app.route('/')
    def index():
        from flask_login import current_user
        if current_user.is_authenticated:
            return f"Bienvenue {current_user.full_name}! (Rôle: {current_user.role})"
        return "Welcome to Unissons la Main"

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
