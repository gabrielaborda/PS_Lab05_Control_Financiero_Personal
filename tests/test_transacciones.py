from datetime import date, timedelta

import pytest

from models import Transaccion
from tests.conftest import payload_transaccion


# Tests for Transacciones module

# ---------------------- AVL (Boundary Value Analysis) ----------------------


@pytest.mark.parametrize("monto", ["0.01", "999999.99"])
def test_avl_montos_borde_aceptados(client, usuario_con_datos, monto):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto=monto,
            tipo="ingreso",
            categoria_id=str(usuario_con_datos["categoria_ingreso_id"]),
        ),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


@pytest.mark.parametrize("descripcion", ["A", "x" * 150])
def test_avl_descripcion_bordes(client, usuario_con_datos, descripcion):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, descripcion=descripcion),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


@pytest.mark.parametrize("fecha", [date.today().isoformat(), (date.today() - timedelta(days=1)).isoformat()])
def test_avl_fecha_hoy_y_pasada(client, usuario_con_datos, fecha):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, fecha=fecha),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


# ---------------------- PE (Equivalence Partitioning) ----------------------


@pytest.mark.parametrize(
    "monto, status_esperado, texto_esperado",
    [
        ("0", 400, "mayor a 0"),
        ("-1", 400, "negativo"),
        ("abc", 400, "número válido"),
        ("1000000.00", 400, "límite permitido"),
    ],
)
def test_pe_montos_invalidos(client, usuario_con_datos, monto, status_esperado, texto_esperado):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto=monto),
    )

    assert respuesta.status_code == status_esperado
    assert texto_esperado in respuesta.get_json()["error"]


@pytest.mark.parametrize(
    "descripcion, status_esperado, texto_esperado",
    [
        ("", 400, "requerida"),
        ("   ", 400, "requerida"),
        ("x" * 151, 400, "150 caracteres"),
    ],
)
def test_pe_descripciones_invalidas(client, usuario_con_datos, descripcion, status_esperado, texto_esperado):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, descripcion=descripcion),
    )

    assert respuesta.status_code == status_esperado
    assert texto_esperado in respuesta.get_json()["error"]


@pytest.mark.parametrize("tipo", ["ingreso", "gasto"])
def test_pe_tipos_validos(client, usuario_con_datos, tipo):
    categoria_id = (
        usuario_con_datos["categoria_ingreso_id"]
        if tipo == "ingreso"
        else usuario_con_datos["categoria_gasto_id"]
    )

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            tipo=tipo,
            categoria_id=str(categoria_id),
        ),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


def test_pe_tipo_invalido_rechazado(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, tipo="deuda"),
    )

    assert respuesta.status_code == 400
    assert "ingreso o gasto" in respuesta.get_json()["error"]


def test_pe_categoria_no_coincide_con_tipo(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            tipo="gasto",
            categoria_id=str(usuario_con_datos["categoria_ingreso_id"]),
        ),
    )

    assert respuesta.status_code == 400
    assert "no coincide" in respuesta.get_json()["error"]


def test_pe_fecha_futura_rechazada(client, usuario_con_datos):
    manana = (date.today() + timedelta(days=1)).isoformat()

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, fecha=manana),
    )

    assert respuesta.status_code == 400
    assert "fecha futura" in respuesta.get_json()["error"]

def test_pe_eliminar_transaccion(client, usuario_con_datos):
    # crear transaccion
    resp = client.post(
        "/transacciones/crear",
        data={
            "descripcion": "Para eliminar",
            "monto": "20.00",
            "tipo": "gasto",
            "fecha": usuario_con_datos["hoy"],
            "categoria_id": str(usuario_con_datos["categoria_gasto_id"]),
        },
    )
    assert resp.status_code == 201

    # obtener id
    from models import Transaccion
    with client.application.app_context():
        t = Transaccion.query.filter_by(descripcion="Para eliminar").first()
        assert t is not None
        tid = t.id

    # eliminar
    eliminar = client.post(f"/transacciones/{tid}/eliminar")
    assert eliminar.status_code == 200
    assert eliminar.get_json().get("exito") is True


def test_pe_filtrar_transacciones_por_tipo(client, usuario_con_datos):
    # crear ingreso y gasto
    client.post(
        "/transacciones/crear",
        data={
            "descripcion": "Ingreso test",
            "monto": "150.00",
            "tipo": "ingreso",
            "fecha": usuario_con_datos["hoy"],
            "categoria_id": str(usuario_con_datos["categoria_ingreso_id"]),
        },
    )
    client.post(
        "/transacciones/crear",
        data={
            "descripcion": "Gasto test",
            "monto": "50.00",
            "tipo": "gasto",
            "fecha": usuario_con_datos["hoy"],
            "categoria_id": str(usuario_con_datos["categoria_gasto_id"]),
        },
    )

    listar = client.get("/transacciones/?tipo=gasto")
    assert listar.status_code == 200
    assert b"Gasto test" in listar.data


def test_pe_exportar_csv(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data={
            "descripcion": "Export test",
            "monto": "30.00",
            "tipo": "gasto",
            "fecha": usuario_con_datos["hoy"],
            "categoria_id": str(usuario_con_datos["categoria_gasto_id"]),
        },
    )

    resp = client.get("/transacciones/exportar-csv")
    assert resp.status_code == 200
    assert resp.headers.get("Content-Type", "").startswith("text/csv")
