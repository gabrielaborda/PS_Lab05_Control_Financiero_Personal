import os
from datetime import date

import pytest
from flask import Flask
from flask_login import LoginManager

from auth import auth_bp
from categorias import cat_bp
from dashboard import dashboard_bp
from models import Categoria, Presupuesto, Usuario, db
from transacciones import transacciones_bp


@pytest.fixture()
def app(tmp_path):
    """Aplicación Flask aislada para pruebas, usando una BD SQLite temporal."""

    db_path = tmp_path / "test_control_financiero.sqlite"

    app = Flask(
        __name__,
        template_folder=os.path.join(os.getcwd(), "templates"),
        static_folder=os.path.join(os.getcwd(), "static"),
    )

    app.config.update(
        TESTING=True,
        SECRET_KEY="clave-test",
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{db_path.as_posix()}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        WTF_CSRF_ENABLED=False,
    )

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(transacciones_bp)
    app.register_blueprint(cat_bp)

    @app.route("/")
    def home():
        return "OK"

    with app.app_context():
        db.create_all()

    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def usuario_con_datos(app, client):
    """Crea un usuario logueado con categorías y presupuesto para pruebas black box."""

    hoy = date.today()

    with app.app_context():
        usuario = Usuario(nombre="QA Tester", email="qa@test.com")
        usuario.set_password("123456")
        db.session.add(usuario)
        db.session.flush()

        categoria_gasto = Categoria(
            nombre="Comida",
            tipo="gasto",
            icono="🍔",
            usuario_id=usuario.id,
        )

        categoria_ingreso = Categoria(
            nombre="Sueldo",
            tipo="ingreso",
            icono="💰",
            usuario_id=usuario.id,
        )

        db.session.add_all([categoria_gasto, categoria_ingreso])
        db.session.flush()

        presupuesto = Presupuesto(
            monto_limite=100.00,
            mes=hoy.month,
            anio=hoy.year,
            usuario_id=usuario.id,
            categoria_id=categoria_gasto.id,
        )

        db.session.add(presupuesto)
        db.session.commit()

        datos = {
            "usuario_id": usuario.id,
            "categoria_gasto_id": categoria_gasto.id,
            "categoria_ingreso_id": categoria_ingreso.id,
            "hoy": hoy.isoformat(),
        }

    respuesta = client.post(
        "/auth/login",
        data={
            "email": "qa@test.com",
            "password": "123456",
        },
        follow_redirects=False,
    )

    assert respuesta.status_code == 302

    return datos


def payload_transaccion(datos, **overrides):
    """Payload válido base. Cada test cambia solo el campo que quiere evaluar."""

    payload = {
        "descripcion": "Compra de prueba",
        "monto": "10.00",
        "tipo": "gasto",
        "fecha": datos["hoy"],
        "categoria_id": str(datos["categoria_gasto_id"]),
    }

    payload.update(overrides)
    return payload