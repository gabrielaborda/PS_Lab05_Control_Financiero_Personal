from datetime import date

import pytest

from tests.conftest import payload_transaccion


def test_registro_exitoso(client):

    response = client.post(
        "/auth/registro",
        data={
            "nombre": "Jeremy",
            "email": "jeremy@test.com",
            "password": "123456",
            "confirmar_password": "123456"
        },
        follow_redirects=True
    )

    assert response.status_code == 200


def test_registro_correo_sin_dominio(client):

    response = client.post(
        "/auth/registro",
        data={
            "nombre": "Jeremy",
            "email": "jeremy@gmail",
            "password": "123456",
            "confirmar_password": "123456"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

    assert (
        b"correo electronico valido" in response.data.lower()
        or b"correo electr\xc3\xb3nico v\xc3\xa1lido" in response.data.lower()
    )


def test_registro_passwords_diferentes(client):

    response = client.post(
        "/auth/registro",
        data={
            "nombre": "Jeremy",
            "email": "jeremy@test.com",
            "password": "123456",
            "confirmar_password": "654321"
        },
        follow_redirects=True
    )

    assert response.status_code == 200

def test_pe_registro_rechaza_correo_sin_arroba(client):
    resp = client.post(
        "/auth/registro",
        data={"nombre": "Ana", "email": "anaexample.com", "password": "123456", "confirmar_password": "123456"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert (b"correo" in resp.data.lower())


def test_avl_registro_email_tld_minimo(client):
    # email with 2-letter TLD should pass
    resp = client.post(
        "/auth/registro",
        data={"nombre": "Pepe", "email": "pepe@dom.co", "password": "123456", "confirmar_password": "123456"},
        follow_redirects=True,
    )

    assert resp.status_code == 200


def test_pe_registro_password_corta_rechazada(client):
    resp = client.post(
        "/auth/registro",
        data={"nombre": "Ana", "email": "ana@a.com", "password": "123", "confirmar_password": "123"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"longitud" in resp.data.lower() or b"contrase" in resp.data.lower()


def test_pe_login_incorrecto_no_inicia_sesion(client, crear_usuario):
    usuario, datos = crear_usuario("Tester", "t@test.com", "123456")

    resp = client.post(
        "/auth/login",
        data={"email": "t@test.com", "password": "000000"},
        follow_redirects=True,
    )

    assert resp.status_code == 200
    assert b"incorrect" in resp.data.lower() or b"contrase" in resp.data.lower()
