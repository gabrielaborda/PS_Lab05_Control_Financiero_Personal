import os
import sys
from datetime import date

# Ensure project root is on sys.path so test imports (e.g. `from auth import ...`)
# work when pytest is run from a virtualenv or different working directory.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import pytest
from flask import Flask
from flask_login import LoginManager

pytest_plugins = ["tests.bdd_steps"]

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


@pytest.fixture()
def payload_base():

    def _payload(datos, **overrides):

        payload = {
            "descripcion": "Compra de prueba",
            "monto": "10.00",
            "tipo": "gasto",
            "fecha": datos["hoy"],
            "categoria_id": str(datos["categoria_gasto_id"]),
        }

        payload.update(overrides)

        return payload

    return _payload


def payload_transaccion(datos, **overrides):
    """Compatibility helper: return a transaction payload dict.

    Many tests import `payload_transaccion` directly; provide this
    function for backward compatibility.
    """
    payload = {
        "descripcion": "Compra de prueba",
        "monto": "10.00",
        "tipo": "gasto",
        "fecha": datos["hoy"],
        "categoria_id": str(datos["categoria_gasto_id"]),
    }

    payload.update(overrides)
    return payload


@pytest.fixture()
def crear_usuario(app):
    """Factory to create a user directly in the database for tests.

    Returns a function `crear(nombre, email, password)` that creates and
    commits a `Usuario` and default categories, then returns the user
    instance and a dict similar to `usuario_con_datos`.
    """

    def _crear(nombre, email, password):
        from models import Usuario, Categoria, Presupuesto, db

        with app.app_context():
            usuario = Usuario(nombre=nombre, email=email)
            usuario.set_password(password)
            db.session.add(usuario)
            db.session.flush()

            # crear categorías por defecto
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

            db.session.commit()

            datos = {
                "usuario_id": usuario.id,
                "categoria_gasto_id": categoria_gasto.id,
                "categoria_ingreso_id": categoria_ingreso.id,
                "hoy": date.today().isoformat(),
            }

            return usuario, datos

    return _crear


@pytest.fixture()
def login_user(client):
    """Helper to log a user in via the `client`. Returns a function
    `login(email, password)` that posts to `/auth/login` and asserts
    successful redirect.
    """

    def _login(email, password):
        resp = client.post(
            "/auth/login",
            data={"email": email, "password": password},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        return resp

    return _login


@pytest.fixture()
def crear_categoria(app):
    def _crear(usuario_id, nombre="Test", tipo="gasto", icono="📌"):
        from models import Categoria, db

        with app.app_context():
            c = Categoria(nombre=nombre, tipo=tipo, icono=icono, usuario_id=usuario_id)
            db.session.add(c)
            db.session.commit()
            return c.id

    return _crear


@pytest.fixture()
def bdd_context():
    """Shared mutable context for BDD step definitions."""

    return {}


@pytest.fixture()
def crear_transaccion_db(app):
    def _crear(usuario_id, categoria_id, monto="10.00", descripcion="t", tipo="gasto", fecha=None):
        from models import Transaccion, db
        from datetime import date

        with app.app_context():
            fecha = fecha or date.today()
            t = Transaccion(
                descripcion=descripcion,
                monto=monto,
                tipo=tipo,
                fecha=fecha,
                usuario_id=usuario_id,
                categoria_id=categoria_id,
            )
            db.session.add(t)
            db.session.commit()
            return t

    return _crear