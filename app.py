from flask import Flask, render_template
from flask_login import LoginManager
from models import db, Usuario, Categoria
from auth import auth_bp
from dashboard import dashboard_bp
from transacciones import transacciones_bp


def crear_categoria_temporal(usuario):
    """Crea una categoría temporal para el usuario si no existe."""
    if not Categoria.query.filter_by(usuario_id=usuario.id, nombre="Temporal2").first():
        categoria_temp = Categoria(
            nombre="Temporal2",
            tipo="ingreso",
            icono="⏳",
            usuario_id=usuario.id
        )
        db.session.add(categoria_temp)
        db.session.commit()


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
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transacciones_bp)

    @app.route("/")
    def home():
        return render_template("index.html")

    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "message": "Aplicación funcionando correctamente"
        }

    @app.errorhandler(404)
    def pagina_no_encontrada(error):
        return render_template("error/404.html"), 404

    @app.errorhandler(500)
    def error_interno(error):
        return render_template("error/500.html"), 500

    with app.app_context():
        db.create_all()
        primer_usuario = Usuario.query.first()
        if primer_usuario:
            crear_categoria_temporal(primer_usuario)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)