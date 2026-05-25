from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import db, Transaccion, Categoria, Presupuesto
from sqlalchemy import func, extract
from datetime import date
from decimal import Decimal

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


# ─────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────

def _to_float(value):
    """Convierte Decimal / None a float de forma segura."""
    if value is None:
        return 0.0
    return float(value)


def _resumen_mes(usuario_id, mes, anio):
    """Devuelve (total_ingresos, total_gastos, saldo) para un mes dado."""
    def total_tipo(tipo):
        resultado = (
            db.session.query(func.sum(Transaccion.monto))
            .filter(
                Transaccion.usuario_id == usuario_id,
                Transaccion.tipo == tipo,
                extract("month", Transaccion.fecha) == mes,
                extract("year", Transaccion.fecha) == anio,
            )
            .scalar()
        )
        return _to_float(resultado)

    ingresos = total_tipo("ingreso")
    gastos = total_tipo("gasto")
    return ingresos, gastos, ingresos - gastos


# ─────────────────────────────────────────────
#  Rutas HTML
# ─────────────────────────────────────────────

@dashboard_bp.route("/")
@login_required
def index():
    """Página principal del dashboard."""
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year

    ingresos_mes, gastos_mes, saldo_mes = _resumen_mes(
        current_user.id, mes_actual, anio_actual
    )

    # Saldo total histórico
    total_ingresos_hist = _to_float(
        db.session.query(func.sum(Transaccion.monto))
        .filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.tipo == "ingreso",
        )
        .scalar()
    )
    total_gastos_hist = _to_float(
        db.session.query(func.sum(Transaccion.monto))
        .filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.tipo == "gasto",
        )
        .scalar()
    )
    saldo_total = total_ingresos_hist - total_gastos_hist

    # Últimas 8 transacciones
    ultimas = (
        Transaccion.query.filter_by(usuario_id=current_user.id)
        .order_by(Transaccion.fecha.desc(), Transaccion.fecha_creacion.desc())
        .limit(8)
        .all()
    )

    # Alertas de presupuesto: categorías que superaron su límite este mes
    alertas = []
    presupuestos = Presupuesto.query.filter_by(
        usuario_id=current_user.id,
        mes=mes_actual,
        anio=anio_actual,
    ).all()

    for p in presupuestos:
        gastado = _to_float(
            db.session.query(func.sum(Transaccion.monto))
            .filter(
                Transaccion.usuario_id == current_user.id,
                Transaccion.categoria_id == p.categoria_id,
                Transaccion.tipo == "gasto",
                extract("month", Transaccion.fecha) == mes_actual,
                extract("year", Transaccion.fecha) == anio_actual,
            )
            .scalar()
        )
        limite = _to_float(p.monto_limite)
        porcentaje = round((gastado / limite * 100) if limite > 0 else 0, 1)
        if porcentaje >= 80:
            alertas.append(
                {
                    "categoria": p.categoria.nombre if p.categoria else "—",
                    "icono": p.categoria.icono if p.categoria else "📌",
                    "gastado": gastado,
                    "limite": limite,
                    "porcentaje": porcentaje,
                    "superado": gastado > limite,
                }
            )

    return render_template(
        "dashboard/index.html",
        ingresos_mes=ingresos_mes,
        gastos_mes=gastos_mes,
        saldo_mes=saldo_mes,
        saldo_total=saldo_total,
        ultimas=ultimas,
        alertas=alertas,
        mes_nombre=hoy.strftime("%B %Y"),
    )


@dashboard_bp.route("/reportes")
@login_required
def reportes():
    """Página de reportes con gráficos."""
    return render_template("dashboard/reportes.html")


# ─────────────────────────────────────────────
#  Endpoints JSON para Chart.js
# ─────────────────────────────────────────────

@dashboard_bp.route("/api/resumen")
@login_required
def api_resumen():
    """
    Resumen del mes actual + desglose por categoría.
    Usado por los gráficos de dona y barras del dashboard.
    """
    hoy = date.today()
    mes = hoy.month
    anio = hoy.year

    ingresos, gastos, saldo = _resumen_mes(current_user.id, mes, anio)

    # Gastos por categoría (mes actual)
    por_categoria = (
        db.session.query(
            Categoria.nombre,
            Categoria.icono,
            func.sum(Transaccion.monto).label("total"),
        )
        .join(Transaccion, Transaccion.categoria_id == Categoria.id)
        .filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.tipo == "gasto",
            extract("month", Transaccion.fecha) == mes,
            extract("year", Transaccion.fecha) == anio,
        )
        .group_by(Categoria.id)
        .order_by(func.sum(Transaccion.monto).desc())
        .all()
    )

    categorias_data = [
        {
            "nombre": row.nombre,
            "icono": row.icono,
            "total": _to_float(row.total),
        }
        for row in por_categoria
    ]

    return jsonify(
        {
            "ingresos": ingresos,
            "gastos": gastos,
            "saldo": saldo,
            "por_categoria": categorias_data,
        }
    )


@dashboard_bp.route("/api/mensual")
@login_required
def api_mensual():
    """
    Ingresos y gastos de los últimos 6 meses.
    Usado por el gráfico de líneas / barras agrupadas.
    """
    hoy = date.today()
    resultados = []

    for i in range(5, -1, -1):
        # Retroceder i meses desde hoy
        mes = ((hoy.month - 1 - i) % 12) + 1
        anio = hoy.year + ((hoy.month - 1 - i) // 12)

        ingresos, gastos, _ = _resumen_mes(current_user.id, mes, anio)
        etiqueta = date(anio, mes, 1).strftime("%b %Y")

        resultados.append(
            {
                "mes": etiqueta,
                "ingresos": ingresos,
                "gastos": gastos,
            }
        )

    return jsonify(resultados)


@dashboard_bp.route("/api/presupuestos")
@login_required
def api_presupuestos():
    """
    Estado de presupuestos del mes actual.
    Usado por el gráfico de barras horizontales de presupuestos.
    """
    hoy = date.today()
    mes = hoy.month
    anio = hoy.year

    presupuestos = Presupuesto.query.filter_by(
        usuario_id=current_user.id,
        mes=mes,
        anio=anio,
    ).all()

    data = []
    for p in presupuestos:
        gastado = _to_float(
            db.session.query(func.sum(Transaccion.monto))
            .filter(
                Transaccion.usuario_id == current_user.id,
                Transaccion.categoria_id == p.categoria_id,
                Transaccion.tipo == "gasto",
                extract("month", Transaccion.fecha) == mes,
                extract("year", Transaccion.fecha) == anio,
            )
            .scalar()
        )
        limite = _to_float(p.monto_limite)
        data.append(
            {
                "categoria": p.categoria.nombre if p.categoria else "—",
                "icono": p.categoria.icono if p.categoria else "📌",
                "gastado": gastado,
                "limite": limite,
                "porcentaje": round((gastado / limite * 100) if limite > 0 else 0, 1),
            }
        )

    return jsonify(data)
