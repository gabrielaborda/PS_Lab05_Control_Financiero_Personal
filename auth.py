from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, Usuario

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        nombre = request.form.get("nombre", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirmar_password = request.form.get("confirmar_password", "")

        if not nombre or not email or not password or not confirmar_password:
            flash("Todos los campos son obligatorios.", "danger")
            return redirect(url_for("auth.registro"))

        if password != confirmar_password:
            flash("Las contraseñas no coinciden.", "danger")
            return redirect(url_for("auth.registro"))

        usuario_existente = Usuario.query.filter_by(email=email).first()

        if usuario_existente:
            flash("Ya existe una cuenta registrada con ese correo.", "warning")
            return redirect(url_for("auth.registro"))

        nuevo_usuario = Usuario(nombre=nombre, email=email)
        nuevo_usuario.set_password(password)

        db.session.add(nuevo_usuario)
        db.session.commit()

        login_user(nuevo_usuario)

        flash("Registro exitoso. Bienvenido al sistema.", "success")
        return redirect(url_for("home"))

    return render_template("auth/registro.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Ingresa tu correo y contraseña.", "danger")
            return redirect(url_for("auth.login"))

        usuario = Usuario.query.filter_by(email=email).first()

        if not usuario or not usuario.check_password(password):
            flash("Correo o contraseña incorrectos.", "danger")
            return redirect(url_for("auth.login"))

        login_user(usuario)

        flash("Inicio de sesión correcto.", "success")
        return redirect(url_for("home"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))