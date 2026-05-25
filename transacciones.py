from flask import Blueprint, render_template, request, jsonify, send_file
from flask_login import login_required, current_user
from models import db, Transaccion, Categoria
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation
import csv
import io
from sqlalchemy import and_, or_

transacciones_bp = Blueprint("transacciones", __name__, url_prefix="/transacciones")


# ==================== VALIDACIONES ====================

def validar_monto(monto_str):
    """
    Valida que el monto sea un número válido positivo.
    Retorna (es_valido, valor_numerico, mensaje_error)
    """
    try:
        monto = Decimal(str(monto_str).strip())
        if monto < 0:
            return False, None, "El monto no puede ser negativo"
        if monto == 0:
            return False, None, "El monto debe ser mayor a 0"
        if monto > Decimal("999999.99"):
            return False, None, "El monto excede el límite permitido"
        return True, monto, ""
    except (InvalidOperation, ValueError):
        return False, None, "El monto debe ser un número válido"


def validar_descripcion(descripcion):
    """Valida que la descripción no esté vacía y sea válida."""
    if not descripcion or not isinstance(descripcion, str):
        return False, "La descripción es requerida"
    
    descripcion = descripcion.strip()
    if len(descripcion) == 0:
        return False, "La descripción no puede estar vacía"
    if len(descripcion) > 150:
        return False, "La descripción no puede exceder 150 caracteres"
    
    return True, ""


def validar_fecha(fecha_str):
    """Valida que la fecha sea válida."""
    try:
        fecha = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        if fecha > date.today():
            return False, "No se puede ingresar una fecha futura"
        return True, fecha
    except ValueError:
        return False, "La fecha no es válida"


def validar_categoria(categoria_id, usuario_id):
    """Valida que la categoría exista y pertenezca al usuario."""
    if not categoria_id:
        return False, "La categoría es requerida"
    
    categoria = Categoria.query.filter_by(
        id=categoria_id,
        usuario_id=usuario_id
    ).first()
    
    if not categoria:
        return False, "La categoría no existe"
    
    return True, categoria


# ==================== RUTAS DE TRANSACCIONES ====================

@transacciones_bp.route("/", methods=["GET"])
@login_required
def listar_transacciones():
    """Lista todas las transacciones del usuario con filtros opcionales."""
    try:
        # Obtener parámetros de filtro
        tipo_filtro = request.args.get("tipo", "")
        fecha_inicio = request.args.get("fecha_inicio", "")
        fecha_fin = request.args.get("fecha_fin", "")
        categoria_id = request.args.get("categoria_id", "")
        pagina = request.args.get("pagina", 1, type=int)
        
        # Construir query base
        query = Transaccion.query.filter_by(usuario_id=current_user.id)
        
        # Aplicar filtros
        if tipo_filtro in ["ingreso", "gasto"]:
            query = query.filter_by(tipo=tipo_filtro)
        
        if categoria_id:
            try:
                query = query.filter_by(categoria_id=int(categoria_id))
            except ValueError:
                pass
        
        # Filtrar por rango de fechas
        if fecha_inicio:
            es_valido, fecha_obj = validar_fecha(fecha_inicio)
            if es_valido:
                query = query.filter(Transaccion.fecha >= fecha_obj)
        
        if fecha_fin:
            es_valido, fecha_obj = validar_fecha(fecha_fin)
            if es_valido:
                query = query.filter(Transaccion.fecha <= fecha_obj)
        
        # Ordenar por fecha descendente
        query = query.order_by(Transaccion.fecha.desc())
        
        # Paginar
        transacciones = query.paginate(page=pagina, per_page=10)
        
        # Obtener categorías para el formulario de filtro
        categorias = Categoria.query.filter_by(usuario_id=current_user.id).all()
        
        # Calcular totales
        todas_transacciones = query.all()
        total_ingresos = sum(
            float(t.monto) for t in todas_transacciones if t.tipo == "ingreso"
        )
        total_gastos = sum(
            float(t.monto) for t in todas_transacciones if t.tipo == "gasto"
        )
        balance = total_ingresos - total_gastos
        
        return render_template(
            "transacciones/listar.html",
            transacciones=transacciones,
            categorias=categorias,
            total_ingresos=total_ingresos,
            total_gastos=total_gastos,
            balance=balance,
            tipo_filtro=tipo_filtro,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            categoria_id=categoria_id
        )
    except Exception as e:
        return render_template(
            "error/500.html",
            error="Error al listar transacciones",
            detalles=str(e)
        ), 500


@transacciones_bp.route("/crear", methods=["GET", "POST"])
@login_required
def crear_transaccion():
    """Crea una nueva transacción."""
    if request.method == "POST":
        try:
            # Obtener datos
            descripcion = request.form.get("descripcion", "").strip()
            monto_str = request.form.get("monto", "").strip()
            tipo = request.form.get("tipo", "").lower()
            fecha_str = request.form.get("fecha", "")
            categoria_id = request.form.get("categoria_id", "")
            
            # Validar descripción
            es_valido, mensaje = validar_descripcion(descripcion)
            if not es_valido:
                return jsonify({"error": mensaje}), 400
            
            # Validar monto
            es_valido, monto, mensaje = validar_monto(monto_str)
            if not es_valido:
                return jsonify({"error": mensaje}), 400
            
            # Validar tipo
            if tipo not in ["ingreso", "gasto"]:
                return jsonify({"error": "El tipo debe ser ingreso o gasto"}), 400
            
            # Validar fecha
            es_valido, fecha = validar_fecha(fecha_str)
            if not es_valido:
                return jsonify({"error": fecha}), 400
            
            # Validar categoría
            es_valido, resultado = validar_categoria(categoria_id, current_user.id)
            if not es_valido:
                return jsonify({"error": resultado}), 400
            
            # Crear transacción
            nueva_transaccion = Transaccion(
                descripcion=descripcion,
                monto=monto,
                tipo=tipo,
                fecha=fecha,
                usuario_id=current_user.id,
                categoria_id=int(categoria_id)
            )
            
            db.session.add(nueva_transaccion)
            db.session.commit()
            
            return jsonify({
                "exito": True,
                "mensaje": "Transacción registrada exitosamente"
            }), 201
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al crear transacción"}), 500
    
    # GET: Mostrar formulario
    categorias = Categoria.query.filter_by(usuario_id=current_user.id).all()
    return render_template("transacciones/crear.html", categorias=categorias)


@transacciones_bp.route("/<int:id>/editar", methods=["GET", "POST"])
@login_required
def editar_transaccion(id):
    """Edita una transacción existente."""
    transaccion = Transaccion.query.filter_by(
        id=id,
        usuario_id=current_user.id
    ).first_or_404()
    
    if request.method == "POST":
        try:
            # Obtener datos
            descripcion = request.form.get("descripcion", "").strip()
            monto_str = request.form.get("monto", "").strip()
            tipo = request.form.get("tipo", "").lower()
            fecha_str = request.form.get("fecha", "")
            categoria_id = request.form.get("categoria_id", "")
            
            # Validar descripción
            es_valido, mensaje = validar_descripcion(descripcion)
            if not es_valido:
                return jsonify({"error": mensaje}), 400
            
            # Validar monto
            es_valido, monto, mensaje = validar_monto(monto_str)
            if not es_valido:
                return jsonify({"error": mensaje}), 400
            
            # Validar tipo
            if tipo not in ["ingreso", "gasto"]:
                return jsonify({"error": "El tipo debe ser ingreso o gasto"}), 400
            
            # Validar fecha
            es_valido, fecha = validar_fecha(fecha_str)
            if not es_valido:
                return jsonify({"error": fecha}), 400
            
            # Validar categoría
            es_valido, resultado = validar_categoria(categoria_id, current_user.id)
            if not es_valido:
                return jsonify({"error": resultado}), 400
            
            # Actualizar transacción
            transaccion.descripcion = descripcion
            transaccion.monto = monto
            transaccion.tipo = tipo
            transaccion.fecha = fecha
            transaccion.categoria_id = int(categoria_id)
            
            db.session.commit()
            
            return jsonify({
                "exito": True,
                "mensaje": "Transacción actualizada exitosamente"
            }), 200
            
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": "Error al actualizar transacción"}), 500
    
    # GET: Mostrar formulario
    categorias = Categoria.query.filter_by(usuario_id=current_user.id).all()
    return render_template(
        "transacciones/editar.html",
        transaccion=transaccion,
        categorias=categorias
    )


@transacciones_bp.route("/<int:id>/eliminar", methods=["POST"])
@login_required
def eliminar_transaccion(id):
    """Elimina una transacción."""
    try:
        transaccion = Transaccion.query.filter_by(
            id=id,
            usuario_id=current_user.id
        ).first_or_404()
        
        db.session.delete(transaccion)
        db.session.commit()
        
        return jsonify({
            "exito": True,
            "mensaje": "Transacción eliminada exitosamente"
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Error al eliminar transacción"}), 500


# ==================== EXPORTACIÓN ====================

@transacciones_bp.route("/exportar-csv", methods=["GET"])
@login_required
def exportar_csv():
    """Exporta las transacciones a CSV con filtros opcionales."""
    try:
        # Obtener parámetros de filtro (mismos que en listar)
        tipo_filtro = request.args.get("tipo", "")
        fecha_inicio = request.args.get("fecha_inicio", "")
        fecha_fin = request.args.get("fecha_fin", "")
        categoria_id = request.args.get("categoria_id", "")
        
        # Construir query
        query = Transaccion.query.filter_by(usuario_id=current_user.id)
        
        # Aplicar filtros
        if tipo_filtro in ["ingreso", "gasto"]:
            query = query.filter_by(tipo=tipo_filtro)
        
        if categoria_id:
            try:
                query = query.filter_by(categoria_id=int(categoria_id))
            except ValueError:
                pass
        
        if fecha_inicio:
            es_valido, fecha_obj = validar_fecha(fecha_inicio)
            if es_valido:
                query = query.filter(Transaccion.fecha >= fecha_obj)
        
        if fecha_fin:
            es_valido, fecha_obj = validar_fecha(fecha_fin)
            if es_valido:
                query = query.filter(Transaccion.fecha <= fecha_obj)
        
        transacciones = query.order_by(Transaccion.fecha.desc()).all()
        
        # Crear CSV
        output = io.StringIO()
        writer = csv.writer(output, delimiter=",", quoting=csv.QUOTE_ALL)
        
        # Encabezados
        writer.writerow([
            "ID",
            "Fecha",
            "Descripción",
            "Categoría",
            "Tipo",
            "Monto",
            "Fecha de Creación"
        ])
        
        # Datos
        for t in transacciones:
            categoria_nombre = t.categoria.nombre if t.categoria else "Sin categoría"
            writer.writerow([
                t.id,
                t.fecha.strftime("%Y-%m-%d"),
                t.descripcion,
                categoria_nombre,
                t.tipo.upper(),
                f"{t.monto:.2f}",
                t.fecha_creacion.strftime("%Y-%m-%d %H:%M:%S")
            ])
        
        # Crear archivo para descargar
        output.seek(0)
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode("utf-8"))
        bytes_output.seek(0)
        
        fecha_export = datetime.now().strftime("%Y%m%d_%H%M%S")
        nombre_archivo = f"transacciones_{fecha_export}.csv"
        
        return send_file(
            bytes_output,
            mimetype="text/csv",
            as_attachment=True,
            download_name=nombre_archivo
        )
        
    except Exception as e:
        return jsonify({"error": "Error al exportar CSV"}), 500


@transacciones_bp.route("/api/resumen", methods=["GET"])
@login_required
def obtener_resumen():
    """Obtiene un resumen de ingresos, gastos y balance."""
    try:
        # Parámetros opcionales para filtrar
        fecha_inicio = request.args.get("fecha_inicio", "")
        fecha_fin = request.args.get("fecha_fin", "")
        
        query = Transaccion.query.filter_by(usuario_id=current_user.id)
        
        if fecha_inicio:
            es_valido, fecha_obj = validar_fecha(fecha_inicio)
            if es_valido:
                query = query.filter(Transaccion.fecha >= fecha_obj)
        
        if fecha_fin:
            es_valido, fecha_obj = validar_fecha(fecha_fin)
            if es_valido:
                query = query.filter(Transaccion.fecha <= fecha_obj)
        
        transacciones = query.all()
        
        total_ingresos = sum(
            float(t.monto) for t in transacciones if t.tipo == "ingreso"
        )
        total_gastos = sum(
            float(t.monto) for t in transacciones if t.tipo == "gasto"
        )
        balance = total_ingresos - total_gastos
        
        return jsonify({
            "total_ingresos": round(total_ingresos, 2),
            "total_gastos": round(total_gastos, 2),
            "balance": round(balance, 2),
            "cantidad_transacciones": len(transacciones)
        }), 200
        
    except Exception as e:
        return jsonify({"error": "Error al obtener resumen"}), 500
