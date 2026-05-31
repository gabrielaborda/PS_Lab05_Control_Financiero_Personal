from datetime import date, timedelta

import pytest

from models import Transaccion
from tests.conftest import payload_transaccion
from transacciones import validar_descripcion

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
#
def test_pe_descripcion_none_rechazada(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion=None,
        ),
    )

    assert respuesta.status_code == 400
    

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

#
def test_pe_categoria_inexistente_rechazada(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            categoria_id="99999",
        ),
    )

    assert respuesta.status_code == 400



def test_pe_categoria_vacia_rechazada(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            categoria_id="",
        ),
    )

    assert respuesta.status_code == 400


def test_pe_fecha_invalida_rechazada(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            fecha="2026-99-99",
        ),
    )

    assert respuesta.status_code == 400

def test_pe_eliminar_transaccion(client, usuario_con_datos):
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

    with client.application.app_context():
        t = Transaccion.query.filter_by(
            descripcion="Para eliminar"
        ).first()

        assert t is not None
        tid = t.id

    eliminar = client.post(
        f"/transacciones/{tid}/eliminar"
    )

    assert eliminar.status_code == 200
    assert eliminar.get_json()["exito"] is True
    
#
def test_pe_eliminar_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import Transaccion, db

    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    def romper():
        raise Exception("boom")

    monkeypatch.setattr(
        db.session,
        "commit",
        romper,
    )

    respuesta = client.post(
        f"/transacciones/{t.id}/eliminar"
    )

    assert respuesta.status_code == 500

    
#
def test_pe_editar_get_muestra_formulario(client, usuario_con_datos):
    resp = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    assert resp.status_code == 201

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.get(f"/transacciones/{t.id}/editar")

    assert respuesta.status_code == 200

def test_pe_editar_descripcion_vacia_rechazada(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="",
        ),
    )

    assert respuesta.status_code == 400


def test_pe_editar_monto_invalido_rechazado(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            monto="-50",
        ),
    )

    assert respuesta.status_code == 400

    
def test_pe_editar_tipo_invalido_rechazado(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            tipo="otro",
        ),
    )

    assert respuesta.status_code == 400

##

def test_pe_editar_fecha_invalida_rechazada(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            fecha="99-99-9999",
        ),
    )

    assert respuesta.status_code == 400


def test_pe_editar_categoria_inexistente_rechazada(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            categoria_id="99999",
        ),
    )

    assert respuesta.status_code == 400


def test_pe_editar_categoria_no_coincide_tipo(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            tipo="gasto",
            categoria_id=str(usuario_con_datos["categoria_ingreso_id"]),
        ),
    )

    assert respuesta.status_code == 400


def test_pe_editar_exceso_presupuesto_sin_confirmar(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="10.00",
        ),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            monto="200.00",
            tipo="gasto",
            categoria_id=str(usuario_con_datos["categoria_gasto_id"]),
        ),
    )

    assert respuesta.status_code == 409
    assert respuesta.get_json()["requiere_confirmacion"] is True


def test_pe_editar_exitoso(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Editar ok",
        ),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Editado correctamente",
            monto="15.00",
        ),
    )

    assert respuesta.status_code == 200
    assert respuesta.get_json()["exito"] is True
    
##
def test_pe_editar_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import Transaccion, db

    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    with client.application.app_context():
        t = Transaccion.query.first()

    def romper():
        raise Exception("boom")

    monkeypatch.setattr(
        db.session,
        "commit",
        romper,
    )

    respuesta = client.post(
        f"/transacciones/{t.id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Error edit",
        ),
    )

    assert respuesta.status_code == 500

def test_pe_alerta_presupuesto_excedido_sin_confirmar(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="150.00",
            tipo="gasto",
            categoria_id=str(usuario_con_datos["categoria_gasto_id"]),
        ),
    )

    assert respuesta.status_code == 409
    assert respuesta.get_json()["requiere_confirmacion"] is True


def test_pe_alerta_presupuesto_confirmada_crea_transaccion(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data={
            **payload_transaccion(
                usuario_con_datos,
                monto="150.00",
                tipo="gasto",
                categoria_id=str(usuario_con_datos["categoria_gasto_id"]),
            ),
            "confirmar_exceso": "1",
        },
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True
    
# Valida el comportamiento cuando una categoría no tiene presupuesto configurado.
def test_pe_verificar_presupuesto_sin_presupuesto_definido(
    client,
    usuario_con_datos,
):
    from models import Presupuesto, db

    with client.application.app_context():
        Presupuesto.query.delete()
        db.session.commit()

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="50.00",
            tipo="gasto",
            categoria_id=str(
                usuario_con_datos["categoria_gasto_id"]
            ),
        ),
    )

    assert respuesta.status_code == 201
#
def test_pe_crear_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import db

    def romper():
        raise Exception("boom")

    monkeypatch.setattr(
        db.session,
        "commit",
        romper,
    )

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos),
    )

    assert respuesta.status_code == 500


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
##

def test_pe_filtrar_transacciones_por_categoria(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Filtro categoria",
        ),
    )

    categoria_id = usuario_con_datos["categoria_gasto_id"]

    respuesta = client.get(
        f"/transacciones/?categoria_id={categoria_id}"
    )

    assert respuesta.status_code == 200
    assert b"Filtro categoria" in respuesta.data


def test_pe_filtrar_categoria_id_invalido(client, usuario_con_datos):
    respuesta = client.get(
        "/transacciones/?categoria_id=abc"
    )

    assert respuesta.status_code == 200


def test_pe_filtrar_fecha_inicio_valida(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Fecha inicio",
        ),
    )

    fecha = (date.today() - timedelta(days=1)).isoformat()

    respuesta = client.get(
        f"/transacciones/?fecha_inicio={fecha}"
    )

    assert respuesta.status_code == 200


def test_pe_filtrar_fecha_fin_valida(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Fecha fin",
        ),
    )

    fecha = date.today().isoformat()

    respuesta = client.get(
        f"/transacciones/?fecha_fin={fecha}"
    )

    assert respuesta.status_code == 200
#
def test_pe_listar_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import Transaccion

    def romper(*args, **kwargs):
        raise Exception("boom")

    with client.application.app_context():
        monkeypatch.setattr(
            Transaccion.query.__class__,
            "filter_by",
            romper,
        )

    respuesta = client.get("/transacciones/")

    assert respuesta.status_code == 500
    
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

def test_pe_exportar_csv_filtrado_por_tipo(client, usuario_con_datos):
    respuesta = client.get(
        "/transacciones/exportar-csv?tipo=gasto"
    )

    assert respuesta.status_code == 200
    
def test_pe_exportar_csv_filtrado_por_categoria(client, usuario_con_datos):
    respuesta = client.get(
        f"/transacciones/exportar-csv?categoria_id={usuario_con_datos['categoria_gasto_id']}"
    )

    assert respuesta.status_code == 200
#

def test_pe_exportar_csv_categoria_id_invalido(
    client,
    usuario_con_datos,
):
    respuesta = client.get(
        "/transacciones/exportar-csv?categoria_id=abc"
    )

    assert respuesta.status_code == 200

def test_pe_exportar_csv_fecha_inicio(
    client,
    usuario_con_datos,
):
    fecha = (date.today() - timedelta(days=1)).isoformat()

    respuesta = client.get(
        f"/transacciones/exportar-csv?fecha_inicio={fecha}"
    )

    assert respuesta.status_code == 200
    
def test_pe_exportar_csv_fecha_fin(
    client,
    usuario_con_datos,
):
    fecha = date.today().isoformat()

    respuesta = client.get(
        f"/transacciones/exportar-csv?fecha_fin={fecha}"
    )

    assert respuesta.status_code == 200
    
def test_pe_exportar_csv_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import Transaccion

    def romper(*args, **kwargs):
        raise Exception("boom")

    with client.application.app_context():
        monkeypatch.setattr(
            Transaccion.query.__class__,
            "all",
            romper,
        )

    respuesta = client.get(
        "/transacciones/exportar-csv"
    )

    assert respuesta.status_code == 500

# ---------------------- API RESUMEN ----------------------

def test_pe_api_resumen_sin_transacciones(
    client,
    usuario_con_datos,
):
    respuesta = client.get(
        "/transacciones/api/resumen"
    )

    assert respuesta.status_code == 200

    data = respuesta.get_json()

    assert "total_ingresos" in data
    assert "total_gastos" in data
    assert "balance" in data

def test_pe_api_resumen_con_fecha_inicio(
    client,
    usuario_con_datos,
):
    fecha = (date.today() - timedelta(days=7)).isoformat()

    respuesta = client.get(
        f"/transacciones/api/resumen?fecha_inicio={fecha}"
    )

    assert respuesta.status_code == 200

def test_pe_api_resumen_con_fecha_fin(
    client,
    usuario_con_datos,
):
    fecha = date.today().isoformat()

    respuesta = client.get(
        f"/transacciones/api/resumen?fecha_fin={fecha}"
    )

    assert respuesta.status_code == 200

def test_pe_api_resumen_con_datos(
    client,
    usuario_con_datos,
):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="100",
            tipo="ingreso",
            categoria_id=str(
                usuario_con_datos["categoria_ingreso_id"]
            ),
        ),
    )

    respuesta = client.get(
        "/transacciones/api/resumen"
    )

    assert respuesta.status_code == 200

    data = respuesta.get_json()

    assert data["cantidad_transacciones"] >= 1

def test_pe_api_resumen_error_500(
    client,
    usuario_con_datos,
    monkeypatch,
):
    from models import Transaccion

    def romper(*args, **kwargs):
        raise Exception("boom")

    with client.application.app_context():
        monkeypatch.setattr(
            Transaccion.query.__class__,
            "filter_by",
            romper,
        )

    respuesta = client.get(
        "/transacciones/api/resumen"
    )

    assert respuesta.status_code == 500

# Se usa strip() para validar correctamente descripciones con solo espacios.
def test_pe_validar_descripcion_solo_espacios():
    valido, mensaje = validar_descripcion("     ")

    assert valido is False
    assert "vacía" in mensaje