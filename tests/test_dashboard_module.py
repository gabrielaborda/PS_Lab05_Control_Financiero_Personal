from datetime import date

from tests.conftest import payload_transaccion


# Dashboard module tests

# PE: functional checks and API responses


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

#
def test_dashboard_api_resumen_con_solo_gastos(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="50.00",
            tipo="gasto",
            categoria_id=str(usuario_con_datos["categoria_gasto_id"]),
        ),
    )

    respuesta = client.get("/dashboard/api/resumen")

    assert respuesta.status_code == 200

    data = respuesta.get_json()

    assert data["gastos"] == 50.00
    assert data["ingresos"] == 0.00
    assert data["saldo"] == -50.00

def test_dashboard_api_resumen_con_solo_ingresos(client, usuario_con_datos):
    client.post(
        "/transacciones/crear",
        data=payload_transaccion(
            usuario_con_datos,
            monto="100.00",
            tipo="ingreso",
            categoria_id=str(usuario_con_datos["categoria_ingreso_id"]),
        ),
    )

    respuesta = client.get("/dashboard/api/resumen")

    assert respuesta.status_code == 200

    data = respuesta.get_json()

    assert data["ingresos"] == 100.00
    assert data["gastos"] == 0.00
    assert data["saldo"] == 100.00
    
    
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
        
def test_dashboard_reportes_carga_correctamente(
    client,
    usuario_con_datos,
):
    respuesta = client.get(
        "/dashboard/reportes"
    )

    assert respuesta.status_code == 200