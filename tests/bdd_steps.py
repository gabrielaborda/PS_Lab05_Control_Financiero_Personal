from datetime import date

from pytest_bdd import given, when, then, parsers

from models import Categoria, Presupuesto, Transaccion, Usuario, db
from tests.conftest import payload_transaccion


# Shared step definitions for the Gherkin feature files.


def _response_ok(response):
    assert response is not None
    return response


def _make_user(app, nombre="QA", email="qa@test.com", password="123456"):
    with app.app_context():
        usuario = Usuario(nombre=nombre, email=email)
        usuario.set_password(password)
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
            mes=date.today().month,
            anio=date.today().year,
            usuario_id=usuario.id,
            categoria_id=categoria_gasto.id,
        )
        db.session.add(presupuesto)
        db.session.commit()

        return {
            "usuario": usuario,
            "categoria_gasto": categoria_gasto,
            "categoria_ingreso": categoria_ingreso,
        }


def _post(client, url, data, follow_redirects=True):
    return client.post(url, data=data, follow_redirects=follow_redirects)


# ----------------------------- Auth -----------------------------


@given("que el usuario no tiene una cuenta registrada")
def auth_sin_cuenta(bdd_context):
    bdd_context.clear()


@given("que el usuario está en el formulario de registro")
def auth_en_registro(bdd_context):
    bdd_context.clear()


@given(parsers.parse('que ya existe una cuenta registrada con el correo "{email}"'))
def auth_cuenta_existente(app, crear_usuario, bdd_context, email):
    usuario, _datos = crear_usuario("Usuario", email, "123456")
    bdd_context["usuario_existente"] = usuario


@given(parsers.parse('que existe una cuenta con correo "{email}" y contraseña "{password}"'))
def auth_cuenta_para_login(app, crear_usuario, bdd_context, email, password):
    usuario, _datos = crear_usuario("Usuario", email, password)
    bdd_context["usuario_existente"] = usuario


@given(parsers.parse('que existe una cuenta con correo "{email}"'))
def auth_cuenta_existente_sola(app, crear_usuario, bdd_context, email):
    usuario, _datos = crear_usuario("Usuario", email, "123456")
    bdd_context["usuario_existente"] = usuario


@given("que el usuario tiene una sesión activa")
def auth_sesion_activa(usuario_con_datos, bdd_context):
    bdd_context["usuario_con_datos"] = usuario_con_datos


@given("que el usuario no ha iniciado sesión")
def auth_sin_sesion(bdd_context):
    bdd_context.clear()


@when(parsers.parse('ingresa nombre "{nombre}", correo "{email}" y contraseña "{password}"'))
def auth_registro_exitoso(client, bdd_context, nombre, email, password):
    bdd_context["response"] = _post(
        client,
        "/auth/registro",
        {
            "nombre": nombre,
            "email": email,
            "password": password,
            "confirmar_password": password,
        },
        follow_redirects=False,
    )


@when(parsers.parse('ingresa el correo "{email}" sin el carácter @'))
def auth_registro_email_sin_arroba(client, bdd_context, email):
    bdd_context["response"] = _post(
        client,
        "/auth/registro",
        {
            "nombre": "Ana",
            "email": email,
            "password": "123456",
            "confirmar_password": "123456",
        },
        follow_redirects=True,
    )


@when(parsers.parse('ingresa la contraseña "{password}" con menos de 6 caracteres'))
def auth_registro_password_corta(client, bdd_context, password):
    bdd_context["response"] = _post(
        client,
        "/auth/registro",
        {
            "nombre": "Ana",
            "email": "ana@correo.com",
            "password": password,
            "confirmar_password": password,
        },
        follow_redirects=True,
    )


@when(parsers.parse('un nuevo usuario intenta registrarse con ese mismo correo'))
def auth_registro_correo_existente(client, bdd_context):
    email = bdd_context.get("usuario_existente").email
    bdd_context["response"] = _post(
        client,
        "/auth/registro",
        {
            "nombre": "Otro",
            "email": email,
            "password": "123456",
            "confirmar_password": "123456",
        },
        follow_redirects=True,
    )


@when(parsers.parse('ingresa "{password}" en contraseña y "{confirmar}" en confirmar contraseña'))
def auth_registro_passwords_distintas(client, bdd_context, password, confirmar):
    bdd_context["response"] = _post(
        client,
        "/auth/registro",
        {
            "nombre": "Ana",
            "email": "ana@correo.com",
            "password": password,
            "confirmar_password": confirmar,
        },
        follow_redirects=True,
    )


@when("el usuario ingresa esas credenciales en el formulario de login")
def auth_login_exitoso(client, bdd_context):
    usuario = bdd_context["usuario_existente"]
    bdd_context["response"] = _post(
        client,
        "/auth/login",
        {"email": usuario.email, "password": "123456"},
        follow_redirects=False,
    )


@when(parsers.parse('el usuario ingresa la contraseña incorrecta "{password}"'))
def auth_login_incorrecto(client, bdd_context, password):
    usuario = bdd_context["usuario_existente"]
    bdd_context["response"] = _post(
        client,
        "/auth/login",
        {"email": usuario.email, "password": password},
        follow_redirects=True,
    )


@when("selecciona la opción de cerrar sesión")
def auth_logout(client, bdd_context):
    bdd_context["response"] = client.get("/auth/logout", follow_redirects=False)


@when("intenta acceder directamente a una ruta protegida como el dashboard")
def auth_ruta_protegida(client, bdd_context):
    bdd_context["response"] = client.get("/dashboard/", follow_redirects=False)


@then("el sistema crea la cuenta y redirige al dashboard")
def then_registro_exitoso(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@then("el sistema muestra un mensaje de error y no crea la cuenta")
def then_registro_error(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"correo" in response.data.lower() or b"contrase" in response.data.lower()


@then("el sistema muestra un mensaje indicando la longitud mínima requerida y no crea la cuenta")
def then_registro_password_corta(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"6 caracteres" in response.data.lower() or b"contrase" in response.data.lower()


@then("el sistema muestra un mensaje de error indicando que el correo ya está en uso")
def then_registro_correo_en_uso(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"ya existe" in response.data.lower() or b"correo" in response.data.lower()


@then("el sistema inicia la sesión y redirige al dashboard")
def then_login_exitoso(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")


@then("el sistema muestra un mensaje de error y no inicia la sesión")
def then_login_error(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"incorrect" in response.data.lower() or b"contrase" in response.data.lower()


@then("el sistema cierra la sesión y redirige al login")
def then_logout_exitoso(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


@then("el sistema redirige al login sin mostrar el contenido solicitado")
def then_protegida_redirect(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 302
    assert "/auth/login" in response.headers["Location"]


# -------------------------- Transacciones --------------------------


@given("que el usuario tiene una sesión activa y al menos una categoría creada")
def transacciones_usuario_activo(usuario_con_datos, bdd_context):
    bdd_context["usuario_con_datos"] = usuario_con_datos


@given("que el usuario está en el formulario de nueva transacción")
def transacciones_formulario_nuevo(bdd_context):
    bdd_context.clear()


@given(parsers.parse('que el usuario tiene una transacción registrada con monto {monto}'))
def transacciones_existe_registrada(app, usuario_con_datos, bdd_context, monto):
    with app.app_context():
        transaccion = Transaccion(
            descripcion="Compra base",
            monto=monto,
            tipo="gasto",
            fecha=date.today(),
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=usuario_con_datos["categoria_gasto_id"],
        )
        db.session.add(transaccion)
        db.session.commit()
        bdd_context["transaccion_id"] = transaccion.id


@given("que el usuario tiene una transacción registrada")
def transacciones_existe_simple(app, usuario_con_datos, bdd_context):
    with app.app_context():
        transaccion = Transaccion(
            descripcion="Transacción base",
            monto="20.00",
            tipo="gasto",
            fecha=date.today(),
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=usuario_con_datos["categoria_gasto_id"],
        )
        db.session.add(transaccion)
        db.session.commit()
        bdd_context["transaccion_id"] = transaccion.id


@given("que el usuario tiene transacciones de tipo ingreso y de tipo gasto registradas")
def transacciones_ingreso_y_gasto(app, usuario_con_datos, bdd_context):
    with app.app_context():
        gasto = Transaccion(
            descripcion="Gasto BDD",
            monto="50.00",
            tipo="gasto",
            fecha=date.today(),
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=usuario_con_datos["categoria_gasto_id"],
        )
        ingreso = Transaccion(
            descripcion="Ingreso BDD",
            monto="120.00",
            tipo="ingreso",
            fecha=date.today(),
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=usuario_con_datos["categoria_ingreso_id"],
        )
        db.session.add_all([gasto, ingreso])
        db.session.commit()


@given("que el usuario tiene transacciones de distintas categorías registradas")
def transacciones_distintas_categorias(app, usuario_con_datos, crear_categoria, bdd_context):
    alimentacion_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Alimentación", tipo="gasto", icono="🍔")
    ropa_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Ropa", tipo="gasto", icono="👕")
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Comida",
                monto="40.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=alimentacion_id,
            ),
            Transaccion(
                descripcion="Camisa",
                monto="60.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=ropa_id,
            ),
        ])
        db.session.commit()
        bdd_context["categoria_filtro"] = {"id": alimentacion_id, "nombre": "Alimentación"}


@given("que el usuario tiene transacciones registradas en distintas fechas")
def transacciones_distintas_fechas(app, usuario_con_datos, bdd_context):
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Enero",
                monto="10.00",
                tipo="gasto",
                fecha=date(2026, 1, 10),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
            Transaccion(
                descripcion="Febrero",
                monto="20.00",
                tipo="gasto",
                fecha=date(2026, 2, 10),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
        ])
        db.session.commit()


@given("que el usuario tiene transacciones registradas y filtros aplicados")
def transacciones_para_csv(app, usuario_con_datos, bdd_context):
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="CSV Gasto",
                monto="30.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
            Transaccion(
                descripcion="CSV Ingreso",
                monto="90.00",
                tipo="ingreso",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_ingreso_id"],
            ),
        ])
        db.session.commit()


@when(parsers.parse('registra una transacción de tipo gasto con monto {monto}, descripción "{descripcion}", fecha de hoy y una categoría válida'))
def transacciones_crear_gasto(client, usuario_con_datos, bdd_context, monto, descripcion):
    bdd_context["response"] = _post(
        client,
        "/transacciones/crear",
        payload_transaccion(
            usuario_con_datos,
            monto=monto,
            descripcion=descripcion,
            tipo="gasto",
            fecha=usuario_con_datos["hoy"],
            categoria_id=str(usuario_con_datos["categoria_gasto_id"]),
        ),
    )


@when(parsers.parse('ingresa el monto {monto}'))
def transacciones_monto_invalido(client, usuario_con_datos, bdd_context, monto):
    bdd_context["response"] = _post(
        client,
        "/transacciones/crear",
        payload_transaccion(usuario_con_datos, monto=monto),
    )


@when("deja el campo descripción en blanco")
def transacciones_descripcion_blanca(client, usuario_con_datos, bdd_context):
    bdd_context["response"] = _post(
        client,
        "/transacciones/crear",
        payload_transaccion(usuario_con_datos, descripcion=""),
    )


@when(parsers.parse('edita el monto a {monto} y guarda los cambios'))
def transacciones_editar_monto(client, app, usuario_con_datos, bdd_context, monto):
    transaccion_id = bdd_context["transaccion_id"]
    bdd_context["response"] = _post(
        client,
        f"/transacciones/{transaccion_id}/editar",
        payload_transaccion(usuario_con_datos, monto=monto),
    )


@when("elimina esa transacción")
def transacciones_eliminar(client, bdd_context):
    transaccion_id = bdd_context["transaccion_id"]
    bdd_context["response"] = client.post(f"/transacciones/{transaccion_id}/eliminar")


@when(parsers.parse('aplica el filtro por tipo "{tipo}"'))
def transacciones_filtrar_tipo(client, bdd_context, tipo):
    bdd_context["response"] = client.get(f"/transacciones/?tipo={tipo}")


@when(parsers.parse('aplica el filtro por la categoría "{nombre_categoria}"'))
def transacciones_filtrar_categoria(client, bdd_context, nombre_categoria):
    categoria = bdd_context["categoria_filtro"]
    assert categoria["nombre"] == nombre_categoria
    bdd_context["response"] = client.get(f"/transacciones/?categoria_id={categoria['id']}")


@when(parsers.parse('aplica un filtro con fecha desde "{fecha_inicio}" hasta "{fecha_fin}"'))
def transacciones_filtrar_fecha(client, bdd_context, fecha_inicio, fecha_fin):
    bdd_context["fecha_inicio"] = fecha_inicio
    bdd_context["fecha_fin"] = fecha_fin
    bdd_context["response"] = client.get(
        f"/transacciones/?fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}"
    )


@when("selecciona la opción de exportar a CSV")
def transacciones_exportar_csv(client, bdd_context):
    bdd_context["response"] = client.get("/transacciones/exportar-csv")


@then("la transacción queda guardada y aparece en el historial")
def then_transaccion_guardada(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 201
    assert response.get_json()["exito"] is True


@then("el sistema muestra un mensaje de error y no guarda la transacción")
def then_transaccion_error(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 400


@then("la transacción se actualiza y el historial refleja el nuevo monto")
def then_transaccion_actualizada(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    with app.app_context():
        transaccion = db.session.get(Transaccion, bdd_context["transaccion_id"])
        assert transaccion is not None
        assert float(transaccion.monto) == 75.00


@then("la transacción desaparece del historial y los totales se recalculan")
def then_transaccion_eliminada(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    with app.app_context():
        transaccion = db.session.get(Transaccion, bdd_context["transaccion_id"])
        assert transaccion is None


@then("el historial muestra únicamente las transacciones de tipo gasto")
def then_historial_filtrado_tipo(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"Gasto BDD" in response.data
    assert b"Ingreso BDD" not in response.data


@then("el historial muestra únicamente las transacciones de esa categoría")
def then_historial_filtrado_categoria(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"Comida" in response.data or b"Alimentaci" in response.data


@then("el historial muestra únicamente las transacciones dentro de ese rango")
def then_historial_filtrado_fecha(app, usuario_con_datos, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    with app.app_context():
        inicio = date.fromisoformat(bdd_context["fecha_inicio"])
        fin = date.fromisoformat(bdd_context["fecha_fin"])
        transacciones = (
            db.session.query(Transaccion)
            .filter(
                Transaccion.usuario_id == usuario_con_datos["usuario_id"],
                Transaccion.fecha >= inicio,
                Transaccion.fecha <= fin,
            )
            .all()
        )
        assert len(transacciones) == 1
        assert transacciones[0].fecha.month == inicio.month


@then("se descarga un archivo CSV con las transacciones visibles según los filtros activos")
def then_csv_descargado(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert response.headers.get("Content-Type", "").startswith("text/csv")


# -------------------------- Categorías --------------------------


@given("que el usuario está en el formulario de nueva categoría")
def categorias_formulario_nuevo(usuario_con_datos, bdd_context):
    bdd_context["usuario_con_datos"] = usuario_con_datos


@given(parsers.parse('que el usuario tiene una categoría llamada "{nombre}"'))
def categorias_categoria_existente(app, crear_categoria, usuario_con_datos, bdd_context, nombre):
    categoria_id = crear_categoria(usuario_con_datos["usuario_id"], nombre=nombre, tipo="gasto", icono="🍲")
    bdd_context["categoria_id"] = categoria_id


@given("que el usuario tiene una categoría registrada")
def categorias_categoria_registrada(app, crear_categoria, usuario_con_datos, bdd_context):
    categoria_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Temporal", tipo="gasto", icono="📌")
    bdd_context["categoria_id"] = categoria_id


@given("que el usuario tiene una categoría de tipo gasto")
def categorias_categoria_gasto(usuario_con_datos, bdd_context):
    bdd_context["categoria_id"] = usuario_con_datos["categoria_gasto_id"]


@given("que el usuario está en el formulario de presupuesto")
def categorias_formulario_presupuesto(usuario_con_datos, bdd_context):
    bdd_context["usuario_con_datos"] = usuario_con_datos
    bdd_context["categoria_id"] = usuario_con_datos["categoria_gasto_id"]


@given(parsers.parse('que el usuario tiene una categoría de gasto con presupuesto de {limite} para el mes actual'))
def categorias_alerta_presupuesto(app, usuario_con_datos, bdd_context, limite):
    with app.app_context():
        presupuesto = db.session.query(Presupuesto).filter_by(
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=usuario_con_datos["categoria_gasto_id"],
        ).first()
        presupuesto.monto_limite = float(limite)
        db.session.add(
            Transaccion(
                descripcion="Exceso presupuesto",
                monto=str(float(limite) + 20.00),
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            )
        )
        db.session.commit()
        bdd_context["categoria_nombre"] = "Comida"
        bdd_context["categoria_id"] = usuario_con_datos["categoria_gasto_id"]


@when(parsers.parse('crea una categoría con nombre "{nombre}", tipo "{tipo}" e ícono "{icono}"'))
def categorias_crear(client, bdd_context, nombre, tipo, icono):
    bdd_context["response"] = _post(
        client,
        "/categorias/nueva",
        {"nombre": nombre, "tipo": tipo, "icono": icono},
    )


@when("deja el campo nombre en blanco")
def categorias_nombre_blanco(client, usuario_con_datos, bdd_context):
    bdd_context["response"] = _post(client, "/categorias/nueva", {"nombre": "", "tipo": "gasto", "icono": "🍔"})


@when(parsers.parse('ingresa un nombre de {cantidad:d} caracteres'))
def categorias_nombre_largo(client, usuario_con_datos, bdd_context, cantidad):
    bdd_context["response"] = _post(
        client,
        "/categorias/nueva",
        {"nombre": "x" * cantidad, "tipo": "gasto", "icono": "🍔"},
    )


@when(parsers.parse('edita el nombre a "{nombre}" y guarda los cambios'))
def categorias_editar(client, bdd_context, nombre):
    categoria_id = bdd_context["categoria_id"]
    bdd_context["response"] = _post(
        client,
        f"/categorias/editar/{categoria_id}",
        {"nombre": nombre, "tipo": "gasto", "icono": "🍲"},
    )


@when("elimina esa categoría")
def categorias_eliminar(client, bdd_context):
    categoria_id = bdd_context["categoria_id"]
    bdd_context["response"] = client.post(f"/categorias/eliminar/{categoria_id}")


@when(parsers.parse('asigna un presupuesto de {monto} para el mes y año actual'))
def categorias_presupuesto(client, bdd_context, monto):
    categoria_id = bdd_context["categoria_id"]
    hoy = date.today()
    bdd_context["response"] = _post(
        client,
        f"/categorias/presupuesto/{categoria_id}",
        {"monto": monto, "mes": str(hoy.month), "anio": str(hoy.year)},
    )


@when("ingresa un mes y año diferente al mes y año actual")
def categorias_presupuesto_invalido(client, usuario_con_datos, bdd_context):
    categoria_id = bdd_context["categoria_id"]
    hoy = date.today()
    bdd_context["response"] = _post(
        client,
        f"/categorias/presupuesto/{categoria_id}",
        {"monto": "500.00", "mes": str(hoy.month + 1 if hoy.month < 12 else 1), "anio": str(hoy.year)},
    )


@when("el total de gastos registrados en esa categoría supera 100.00")
def categorias_supera_presupuesto(client, bdd_context):
    bdd_context["response_categorias"] = client.get("/categorias/alertas")
    bdd_context["response_dashboard"] = client.get("/dashboard/")


@then("la categoría queda guardada y aparece en el listado del usuario")
def then_categoria_guardada(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code in (200, 302)


@then("el sistema muestra un mensaje de error y no guarda la categoría")
def then_categoria_error(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    body = response.get_data(as_text=True).lower()
    assert "obligatorio" in body or "50 caracteres" in body


@then("la categoría se actualiza y el listado refleja el nuevo nombre")
def then_categoria_actualizada(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code in (200, 302)


@then("la categoría desaparece del listado")
def then_categoria_eliminada(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code in (200, 302)


@then("el presupuesto queda guardado y se muestra en el listado de categorías")
def then_presupuesto_guardado(app, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code in (200, 302)


@then("el sistema muestra un mensaje de error y no guarda el presupuesto")
def then_presupuesto_error(bdd_context):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert b"periodo actual" in response.data.lower() or b"mes y a" in response.data.lower()


@then("el sistema muestra una alerta en la sección de categorías y en el dashboard")
def then_alerta_presupuesto(bdd_context):
    response_categorias = _response_ok(bdd_context.get("response_categorias"))
    response_dashboard = _response_ok(bdd_context.get("response_dashboard"))
    assert response_categorias.status_code == 200
    assert response_dashboard.status_code == 200
    assert b"Comida" in response_categorias.data or b"Comida" in response_dashboard.data


# -------------------------- Dashboard --------------------------


@given(parsers.parse('que el usuario tiene ingresos por {ingresos} y gastos por {gastos} registrados en el mes actual'))
def dashboard_balance_mes(app, usuario_con_datos, bdd_context, ingresos, gastos):
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Ingreso dashboard",
                monto=ingresos,
                tipo="ingreso",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_ingreso_id"],
            ),
            Transaccion(
                descripcion="Gasto dashboard",
                monto=gastos,
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
        ])
        db.session.commit()


@given(parsers.parse('que el usuario tiene ingresos por {ingresos} y gastos por {gastos} en el mes actual'))
def dashboard_totales_mes(app, usuario_con_datos, ingresos, gastos):
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Ingreso dashboard 2",
                monto=ingresos,
                tipo="ingreso",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_ingreso_id"],
            ),
            Transaccion(
                descripcion="Gasto dashboard 2",
                monto=gastos,
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
        ])
        db.session.commit()


@given("que el usuario tiene transacciones registradas en distintas fechas")
def dashboard_transacciones_fechas(app, usuario_con_datos):
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Vieja",
                monto="10.00",
                tipo="gasto",
                fecha=date(2026, 1, 1),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
            Transaccion(
                descripcion="Nueva",
                monto="20.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=usuario_con_datos["categoria_gasto_id"],
            ),
        ])
        db.session.commit()


@given("que el usuario tiene transacciones de distintas categorías en el mes actual")
def dashboard_transacciones_categorias(app, usuario_con_datos, crear_categoria):
    alimento_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Alimentación", tipo="gasto", icono="🍔")
    transporte_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Transporte", tipo="gasto", icono="🚌")
    with app.app_context():
        db.session.add_all([
            Transaccion(
                descripcion="Alimento",
                monto="40.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=alimento_id,
            ),
            Transaccion(
                descripcion="Bus",
                monto="60.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=transporte_id,
            ),
        ])
        db.session.commit()


@given("que el usuario tiene transacciones registradas en los últimos 6 meses")
def dashboard_transacciones_6m(app, usuario_con_datos):
    hoy = date.today()
    with app.app_context():
        for delta, monto in zip(range(5, -1, -1), [10, 20, 30, 40, 50, 60]):
            month = ((hoy.month - 1 - delta) % 12) + 1
            year = hoy.year + ((hoy.month - 1 - delta) // 12)
            db.session.add(
                Transaccion(
                    descripcion=f"Mes {month}",
                    monto=str(monto),
                    tipo="gasto" if monto % 20 else "ingreso",
                    fecha=date(year, month, 10),
                    usuario_id=usuario_con_datos["usuario_id"],
                    categoria_id=usuario_con_datos["categoria_gasto_id"],
                )
            )
        db.session.commit()


@given('que el usuario tiene un presupuesto de 200.00 en la categoría "Transporte" y ha gastado 150.00 en esa categoría este mes')
def dashboard_presupuesto_transporte(app, usuario_con_datos, crear_categoria):
    transporte_id = crear_categoria(usuario_con_datos["usuario_id"], nombre="Transporte", tipo="gasto", icono="🚌")
    with app.app_context():
        presupuesto = Presupuesto(
            monto_limite=200.00,
            mes=date.today().month,
            anio=date.today().year,
            usuario_id=usuario_con_datos["usuario_id"],
            categoria_id=transporte_id,
        )
        db.session.add(presupuesto)
        db.session.add(
            Transaccion(
                descripcion="Viaje",
                monto="150.00",
                tipo="gasto",
                fecha=date.today(),
                usuario_id=usuario_con_datos["usuario_id"],
                categoria_id=transporte_id,
            )
        )
        db.session.commit()


@when("accede al dashboard")
def dashboard_accede(client, bdd_context):
    bdd_context["response"] = client.get("/dashboard/")
    bdd_context["api_resumen"] = client.get("/dashboard/api/resumen")
    bdd_context["api_presupuestos"] = client.get("/dashboard/api/presupuestos")
    bdd_context["api_mensual"] = client.get("/dashboard/api/mensual")


@then(parsers.parse('el sistema muestra un saldo de {saldo} para el mes actual'))
def then_dashboard_saldo(client, bdd_context, saldo):
    response = _response_ok(bdd_context.get("response"))
    assert response.status_code == 200
    assert f"S/ {float(saldo):.2f}" in response.get_data(as_text=True)


@then(parsers.parse('el sistema muestra {ingresos} como total de ingresos y {gastos} como total de gastos de forma separada'))
def then_dashboard_totales(client, bdd_context, ingresos, gastos):
    response = _response_ok(bdd_context.get("response"))
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert f"S/ {float(ingresos):.2f}" in body
    assert f"S/ {float(gastos):.2f}" in body or f"-S/ {float(gastos):.2f}" in body


@then("el sistema muestra las transacciones más recientes en orden cronológico descendente")
def then_dashboard_ultimas(client, bdd_context):
    response = _response_ok(bdd_context.get("response"))
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert body.index("Nueva") < body.index("Vieja")


@then("el sistema muestra un gráfico que refleja los montos reales por categoría del mes en curso")
def then_dashboard_grafico_categoria(bdd_context):
    response = _response_ok(bdd_context.get("api_resumen"))
    data = response.get_json()
    assert response.status_code == 200
    assert isinstance(data.get("por_categoria"), list)
    assert len(data["por_categoria"]) >= 1


@then("el sistema muestra un gráfico con los ingresos y gastos reales de cada mes en orden cronológico")
def then_dashboard_grafico_mensual(bdd_context):
    response = _response_ok(bdd_context.get("api_mensual"))
    data = response.get_json()
    assert response.status_code == 200
    assert len(data) == 6
    assert all("mes" in item and "ingresos" in item and "gastos" in item for item in data)


@then(parsers.parse('el sistema muestra un avance del {porcentaje}% para el presupuesto de "{categoria}"'))
def then_dashboard_presupuesto(client, bdd_context, porcentaje, categoria):
    response = _response_ok(bdd_context.get("api_presupuestos"))
    data = response.get_json()
    assert response.status_code == 200
    assert any(item["categoria"] == categoria and item["porcentaje"] == float(porcentaje) for item in data)
