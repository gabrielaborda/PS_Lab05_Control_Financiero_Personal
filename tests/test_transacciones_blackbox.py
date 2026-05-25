from datetime import date, timedelta

import pytest

from models import db, Categoria, Presupuesto, Transaccion, Usuario
from tests.conftest import payload_transaccion


# =========================================================
# Caja negra - Partición de equivalencia: monto
# =========================================================

@pytest.mark.parametrize(
    "monto, status_esperado, texto_esperado",
    [
        # Partición inválida: cero
        ("0", 400, "mayor a 0"),
        # Partición inválida: negativo
        ("-1", 400, "negativo"),
        # Partición inválida: no numérico
        ("abc", 400, "número válido"),
        # Partición inválida: supera máximo permitido por negocio
        ("1000000.00", 400, "límite permitido"),
    ],
)
def test_crear_transaccion_rechaza_montos_invalidos(client, usuario_con_datos, monto, status_esperado, texto_esperado):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto=monto),
    )

    assert respuesta.status_code == status_esperado
    assert texto_esperado in respuesta.get_json()["error"]


@pytest.mark.parametrize("monto", ["0.01", "999999.99"])
def test_crear_transaccion_acepta_montos_validos_en_los_bordes(client, usuario_con_datos, monto):
    # Se usa categoría de ingreso para evitar que el presupuesto de gasto interfiera con el borde superior.
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


# =========================================================
# Caja negra - Partición de equivalencia y valores límite: descripción
# =========================================================

@pytest.mark.parametrize(
    "descripcion, status_esperado, texto_esperado",
    [
        ("", 400, "requerida"),
        ("   ", 400, "requerida"),
        ("x" * 151, 400, "150 caracteres"),
    ],
)
def test_crear_transaccion_rechaza_descripciones_invalidas(client, usuario_con_datos, descripcion, status_esperado, texto_esperado):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, descripcion=descripcion),
    )

    assert respuesta.status_code == status_esperado
    assert texto_esperado in respuesta.get_json()["error"]


@pytest.mark.parametrize("descripcion", ["A", "x" * 150])
def test_crear_transaccion_acepta_descripcion_en_bordes_validos(client, usuario_con_datos, descripcion):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, descripcion=descripcion),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


# =========================================================
# Caja negra - Partición de equivalencia: tipo, categoría y fecha
# =========================================================

@pytest.mark.parametrize("tipo", ["ingreso", "gasto"])
def test_crear_transaccion_acepta_tipos_validos(client, usuario_con_datos, tipo):
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


def test_crear_transaccion_rechaza_tipo_invalido(client, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, tipo="deuda"),
    )

    assert respuesta.status_code == 400
    assert "ingreso o gasto" in respuesta.get_json()["error"]


def test_crear_transaccion_rechaza_categoria_que_no_coincide_con_tipo(client, usuario_con_datos):
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


def test_crear_transaccion_rechaza_fecha_futura(client, usuario_con_datos):
    manana = (date.today() + timedelta(days=1)).isoformat()

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, fecha=manana),
    )

    assert respuesta.status_code == 400
    assert "fecha futura" in respuesta.get_json()["error"]


@pytest.mark.parametrize("fecha", [date.today().isoformat(), (date.today() - timedelta(days=1)).isoformat()])
def test_crear_transaccion_acepta_fecha_hoy_y_pasada(client, usuario_con_datos, fecha):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, fecha=fecha),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


# =========================================================
# Caja negra - Valores límite: presupuesto por categoría
# Presupuesto configurado en fixture: S/ 100.00 para categoría Comida.
# =========================================================

@pytest.mark.parametrize(
    "monto, status_esperado, requiere_confirmacion",
    [
        # Límite inferior del borde: debajo del presupuesto
        ("99.99", 201, False),
        # En el límite exacto: todavía debería aceptar sin confirmación
        ("100.00", 201, False),
        # Apenas por encima del límite: debe pedir confirmación
        ("100.01", 409, True),
    ],
)
def test_presupuesto_valores_limite_al_crear_gasto(client, usuario_con_datos, monto, status_esperado, requiere_confirmacion):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto=monto),
    )

    assert respuesta.status_code == status_esperado
    data = respuesta.get_json()

    if requiere_confirmacion:
        assert data["requiere_confirmacion"] is True
        assert "superará el presupuesto" in data["mensaje"]
        assert data["alerta"]["limite"] == 100.00
        assert data["alerta"]["nuevo_total"] == 100.01
    else:
        assert data["exito"] is True


def test_crear_gasto_excedido_no_se_guarda_si_no_confirma(client, app, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="100.01"),
    )

    assert respuesta.status_code == 409

    with app.app_context():
        cantidad = Transaccion.query.count()

    assert cantidad == 0


def test_crear_gasto_excedido_se_guarda_cuando_confirma(client, app, usuario_con_datos):
    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="100.01",
            confirmar_exceso="1",
        ),
    )

    assert respuesta.status_code == 201
    data = respuesta.get_json()
    assert data["exito"] is True
    assert data["alerta_presupuesto"] is not None
    assert data["alerta_presupuesto"]["exceso"] == 0.01

    with app.app_context():
        cantidad = Transaccion.query.count()

    assert cantidad == 1


# =========================================================
# Caja negra - Edición de transacción y presupuesto
# =========================================================

def test_editar_gasto_no_se_cuenta_a_si_mismo_para_presupuesto(client, app, usuario_con_datos):
    crear = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="90.00"),
    )
    assert crear.status_code == 201

    with app.app_context():
        transaccion_id = Transaccion.query.first().id

    editar = client.post(
        f"/transacciones/{transaccion_id}/editar",
        data=payload_transaccion(usuario_con_datos, monto="100.00"),
    )

    assert editar.status_code == 200
    assert editar.get_json()["exito"] is True


def test_editar_gasto_pide_confirmacion_si_supera_presupuesto(client, app, usuario_con_datos):
    crear = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="90.00"),
    )
    assert crear.status_code == 201

    with app.app_context():
        transaccion_id = Transaccion.query.first().id

    editar = client.post(
        f"/transacciones/{transaccion_id}/editar",
        data=payload_transaccion(usuario_con_datos, monto="100.01"),
    )

    assert editar.status_code == 409
    data = editar.get_json()
    assert data["requiere_confirmacion"] is True
    assert data["alerta"]["nuevo_total"] == 100.01


def test_editar_gasto_excedido_se_actualiza_cuando_confirma(client, app, usuario_con_datos):
    crear = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="90.00"),
    )
    assert crear.status_code == 201

    with app.app_context():
        transaccion_id = Transaccion.query.first().id

    editar = client.post(
        f"/transacciones/{transaccion_id}/editar",
        data=payload_transaccion(
            usuario_con_datos,
            monto="100.01",
            confirmar_exceso="1",
        ),
    )

    assert editar.status_code == 200
    data = editar.get_json()
    assert data["exito"] is True
    assert data["alerta_presupuesto"] is not None

    with app.app_context():
        transaccion = Transaccion.query.get(transaccion_id)
        assert float(transaccion.monto) == 100.01


# =========================================================
# Caja negra - Dashboard y endpoints usados por gráficos
# =========================================================

def test_dashboard_carga_correctamente(client, usuario_con_datos):
    respuesta = client.get("/dashboard/")

    assert respuesta.status_code == 200
    assert b"Dashboard" in respuesta.data or b"dashboard" in respuesta.data


def test_dashboard_api_resumen_refleja_ingresos_y_gastos(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="70.00"),
    )
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            tipo="ingreso",
            categoria_id=str(usuario_con_datos["categoria_ingreso_id"]),
            monto="200.00",
        ),
    )

    respuesta = client.get("/dashboard/api/resumen")

    assert respuesta.status_code == 200
    data = respuesta.get_json()
    assert data["ingresos"] == 200.00
    assert data["gastos"] == 70.00
    assert data["saldo"] == 130.00


def test_dashboard_api_presupuestos_muestra_porcentaje_de_uso(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="80.00"),
    )

    respuesta = client.get("/dashboard/api/presupuestos")

    assert respuesta.status_code == 200
    data = respuesta.get_json()
    assert len(data) == 1
    assert data[0]["categoria"] == "Comida"
    assert data[0]["limite"] == 100.00
    assert data[0]["gastado"] == 80.00
    assert data[0]["porcentaje"] == 80.0


def test_formulario_crear_contiene_modal_de_confirmacion(client, usuario_con_datos):
    respuesta = client.get("/transacciones/crear")

    assert respuesta.status_code == 200
    assert "Presupuesto excedido" in respuesta.get_data(as_text=True)
    assert "¿Está seguro de hacer el gasto en esa categoría?" in respuesta.get_data(as_text=True)
# =========================================================
# Caja negra adicional - Seguridad, sesiones y casos vacíos
# =========================================================

def test_dashboard_redirige_a_login_si_no_hay_sesion(client):
    respuesta = client.get("/dashboard/")

    assert respuesta.status_code == 302
    assert "/auth/login" in respuesta.headers["Location"]


def test_crear_transaccion_redirige_a_login_si_no_hay_sesion(client):
    respuesta = client.get("/transacciones/crear")

    assert respuesta.status_code == 302
    assert "/auth/login" in respuesta.headers["Location"]


def test_dashboard_api_resumen_sin_transacciones_devuelve_ceros(client, usuario_con_datos):
    respuesta = client.get("/dashboard/api/resumen")

    assert respuesta.status_code == 200

    data = respuesta.get_json()
    assert data["ingresos"] == 0.0
    assert data["gastos"] == 0.0
    assert data["saldo"] == 0.0
    assert data["por_categoria"] == []


def test_dashboard_api_mensual_devuelve_seis_meses(client, usuario_con_datos):
    respuesta = client.get("/dashboard/api/mensual")

    assert respuesta.status_code == 200

    data = respuesta.get_json()
    assert len(data) == 6

    for item in data:
        assert "mes" in item
        assert "ingresos" in item
        assert "gastos" in item


def test_presupuesto_de_mes_anterior_no_bloquea_gasto_actual(client, app, usuario_con_datos):
    hoy = date.today()

    if hoy.month == 1:
        mes_anterior = 12
        anio_anterior = hoy.year - 1
    else:
        mes_anterior = hoy.month - 1
        anio_anterior = hoy.year

    with app.app_context():
        categoria = Categoria(
            nombre="Transporte",
            tipo="gasto",
            icono="🚌",
            usuario_id=usuario_con_datos["usuario_id"],
        )
        db.session.add(categoria)
        db.session.flush()

        presupuesto_anterior = Presupuesto(
            monto_limite=100.00,
            mes=mes_anterior,
            anio=anio_anterior,
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=categoria.id,
        )
        db.session.add(presupuesto_anterior)
        db.session.commit()

        categoria_id = categoria.id

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            descripcion="Gasto actual transporte",
            monto="150.00",
            tipo="gasto",
            categoria_id=str(categoria_id),
        ),
    )

    assert respuesta.status_code == 201
    assert respuesta.get_json()["exito"] is True


def test_crear_transaccion_rechaza_categoria_de_otro_usuario(client, app, usuario_con_datos):
    with app.app_context():
        otro_usuario = Usuario(nombre="Otro Usuario", email="otro@test.com")
        otro_usuario.set_password("123456")
        db.session.add(otro_usuario)
        db.session.flush()

        categoria_ajena = Categoria(
            nombre="Categoría ajena",
            tipo="gasto",
            icono="🚫",
            usuario_id=otro_usuario.id,
        )
        db.session.add(categoria_ajena)
        db.session.commit()

        categoria_ajena_id = categoria_ajena.id

    respuesta = client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            categoria_id=str(categoria_ajena_id),
        ),
    )

    assert respuesta.status_code == 400
    assert "categoría no existe" in respuesta.get_json()["error"].lower()


def test_editar_transaccion_rechaza_monto_cero(client, app, usuario_con_datos):
    crear = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="50.00"),
    )

    assert crear.status_code == 201

    with app.app_context():
        transaccion_id = Transaccion.query.first().id

    respuesta = client.post(
        f"/transacciones/{transaccion_id}/editar",
        data=payload_transaccion(usuario_con_datos, monto="0"),
    )

    assert respuesta.status_code == 400
    assert "mayor a 0" in respuesta.get_json()["error"]


def test_eliminar_transaccion_propia_la_elimina_correctamente(client, app, usuario_con_datos):
    crear = client.post(
        "/transacciones/crear",
        data=payload_transaccion(usuario_con_datos, monto="25.00"),
    )

    assert crear.status_code == 201

    with app.app_context():
        transaccion_id = Transaccion.query.first().id

    respuesta = client.post(f"/transacciones/{transaccion_id}/eliminar")

    assert respuesta.status_code == 200
    assert respuesta.get_json()["exito"] is True

    with app.app_context():
        cantidad = Transaccion.query.count()

    assert cantidad == 0


def test_eliminar_transaccion_de_otro_usuario_no_debe_permitirse(client, app, usuario_con_datos):
    with app.app_context():
        otro_usuario = Usuario(nombre="Usuario Ajeno", email="ajeno@test.com")
        otro_usuario.set_password("123456")
        db.session.add(otro_usuario)
        db.session.flush()

        categoria_ajena = Categoria(
            nombre="Ajena",
            tipo="gasto",
            icono="🚫",
            usuario_id=otro_usuario.id,
        )
        db.session.add(categoria_ajena)
        db.session.flush()

        transaccion_ajena = Transaccion(
            descripcion="Gasto de otro usuario",
            monto=30.00,
            tipo="gasto",
            fecha=date.today(),
            usuario_id=otro_usuario.id,
            categoria_id=categoria_ajena.id,
        )
        db.session.add(transaccion_ajena)
        db.session.commit()

        transaccion_ajena_id = transaccion_ajena.id

    respuesta = client.post(f"/transacciones/{transaccion_ajena_id}/eliminar")

    assert respuesta.status_code != 200

    with app.app_context():
        transaccion = db.session.get(Transaccion, transaccion_ajena_id)

    assert transaccion is not None