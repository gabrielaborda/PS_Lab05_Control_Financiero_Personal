from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Usuario(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    categorias = db.relationship(
        "Categoria",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan"
    )

    transacciones = db.relationship(
        "Transaccion",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan"
    )

    presupuestos = db.relationship(
        "Presupuesto",
        backref="usuario",
        lazy=True,
        cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ingreso o gasto
    icono = db.Column(db.String(10), default="📌")
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)

    transacciones = db.relationship(
        "Transaccion",
        backref="categoria",
        lazy=True
    )

    presupuestos = db.relationship(
        "Presupuesto",
        backref="categoria",
        lazy=True,
        cascade="all, delete-orphan"
    )


class Transaccion(db.Model):
    __tablename__ = "transacciones"

    id = db.Column(db.Integer, primary_key=True)
    descripcion = db.Column(db.String(150), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    tipo = db.Column(db.String(20), nullable=False)  # ingreso o gasto
    fecha = db.Column(db.Date, default=date.today)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=True)

    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)


class Presupuesto(db.Model):
    __tablename__ = "presupuestos"

    id = db.Column(db.Integer, primary_key=True)
    monto_limite = db.Column(db.Numeric(10, 2), nullable=False)
    mes = db.Column(db.Integer, nullable=False)
    anio = db.Column(db.Integer, nullable=False)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id",
            "categoria_id",
            "mes",
            "anio",
            name="uq_presupuesto_categoria_mes"
        ),
    )