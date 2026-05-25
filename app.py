from flask import Flask, render_template
from flask_login import LoginManager
from models import db, Usuario
from auth import auth_bp


def create_app():
    app = Flask(__name__)

    app.config["SECRET_KEY"] = "clave-secreta-desarrollo"
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///finanzas.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message = "Debes iniciar sesión para acceder a esta sección."
    login_manager.login_message_category = "warning"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return Usuario.query.get(int(user_id))

    app.register_blueprint(auth_bp)

    @app.route("/")
    def home():
        return render_template("index.html")

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)