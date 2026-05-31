from datetime import date

from tests.conftest import payload_transaccion
from models import Categoria, Presupuesto


# Categorías module tests

# PE: equivalence partitions for category creation and budgets


def test_pe_creacion_categoria_exitosa(client, usuario_con_datos):
    respuesta = client.post(
        "/categorias/nueva",
        data={"nombre": "Alimentación", "tipo": "gasto", "icono": "🍔"},
    )

    assert respuesta.status_code in (302, 200)


def test_pe_rechazo_nombre_vacio(client, usuario_con_datos):
    respuesta = client.post(
        "/categorias/nueva",
        data={"nombre": "", "tipo": "gasto", "icono": "🍔"},
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"obligatorio" in respuesta.data.lower()


def test_pe_rechazo_nombre_muy_largo(client, usuario_con_datos):
    nombre = "x" * 51
    respuesta = client.post(
        "/categorias/nueva",
        data={"nombre": nombre, "tipo": "gasto", "icono": "🍔"},
        follow_redirects=True,
    )

    assert respuesta.status_code == 200
    assert b"no puede superar los 50 caracteres" in respuesta.data.lower()


def test_pe_creacion_presupuesto_mes_actual(client, app, usuario_con_datos):
    # Use existing gasto category from fixture
    categoria_id = usuario_con_datos["categoria_gasto_id"]

    respuesta = client.post(
        f"/categorias/presupuesto/{categoria_id}",
        data={"monto": "500.00", "mes": str(date.today().month), "anio": str(date.today().year)},
        follow_redirects=True,
    )

    assert respuesta.status_code == 200

    with app.app_context():
        p = Presupuesto.query.filter_by(usuario_id=usuario_con_datos["usuario_id"], categoria_id=categoria_id).first()
        assert p is not None
