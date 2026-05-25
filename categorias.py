from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Categoria, Presupuesto, Transaccion
from sqlalchemy import func, extract
from datetime import date

cat_bp = Blueprint('categorias', __name__, url_prefix='/categorias')

@cat_bp.route('/')
@login_required
def lista():
    categorias_usuario = Categoria.query.filter_by(usuario_id=current_user.id).all()
    
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    for c in categorias_usuario:
        presupuesto = Presupuesto.query.filter_by(
            usuario_id=current_user.id,
            categoria_id=c.id,
            mes=mes_actual,
            anio=anio_actual
        ).first()
        
        c.presupuesto = presupuesto.monto_limite if presupuesto else None
        
    return render_template('categorias/lista.html', categorias=categorias_usuario)

@cat_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo')
        icono = request.form.get('icono')
        
        nueva_cat = Categoria(
            nombre=nombre, 
            tipo=tipo, 
            icono=icono, 
            usuario_id=current_user.id
        )
        db.session.add(nueva_cat)
        db.session.commit()
        
        flash('Categoría creada exitosamente.', 'success')
        return redirect(url_for('categorias.lista'))
        
    return render_template('categorias/form.html', categoria=None)

@cat_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    categoria = Categoria.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
        
    if request.method == 'POST':
        categoria.nombre = request.form.get('nombre')
        categoria.tipo = request.form.get('tipo')
        categoria.icono = request.form.get('icono')
        
        db.session.commit()
        
        flash('Categoría actualizada.', 'success')
        return redirect(url_for('categorias.lista'))
        
    return render_template('categorias/form.html', categoria=categoria)

@cat_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    categoria = Categoria.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    db.session.delete(categoria)
    db.session.commit()
    flash('Categoría eliminada.', 'success')
    return redirect(url_for('categorias.lista'))

@cat_bp.route('/presupuesto/<int:id>', methods=['GET', 'POST'])
@login_required
def presupuesto(id):
    categoria = Categoria.query.filter_by(id=id, usuario_id=current_user.id).first_or_404()
    
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    presupuesto_actual = Presupuesto.query.filter_by(
        usuario_id=current_user.id,
        categoria_id=categoria.id,
        mes=mes_actual,
        anio=anio_actual
    ).first()
    
    categoria.presupuesto = presupuesto_actual.monto_limite if presupuesto_actual else None
        
    if request.method == 'POST':
        monto = request.form.get('monto')
        mes = request.form.get('mes', mes_actual, type=int)
        anio = request.form.get('anio', anio_actual, type=int)
        
        if monto:
            p = Presupuesto.query.filter_by(
                usuario_id=current_user.id,
                categoria_id=categoria.id,
                mes=mes,
                anio=anio
            ).first()
            
            if p:
                p.monto_limite = float(monto)
            else:
                p = Presupuesto(
                    monto_limite=float(monto),
                    mes=mes,
                    anio=anio,
                    usuario_id=current_user.id,
                    categoria_id=categoria.id
                )
                db.session.add(p)
                
            db.session.commit()
            flash('Presupuesto actualizado.', 'success')
            return redirect(url_for('categorias.lista'))
            
    return render_template('categorias/presupuesto.html', categoria=categoria)

@cat_bp.route('/alertas')
@login_required
def alertas():
    hoy = date.today()
    mes_actual = hoy.month
    anio_actual = hoy.year
    
    categorias_alertas = []
    
    presupuestos = Presupuesto.query.filter_by(
        usuario_id=current_user.id,
        mes=mes_actual,
        anio=anio_actual
    ).all()
    
    for p in presupuestos:
        if p.categoria and p.categoria.tipo == 'gasto':
            gastado = db.session.query(func.sum(Transaccion.monto)).filter(
                Transaccion.usuario_id == current_user.id,
                Transaccion.categoria_id == p.categoria_id,
                Transaccion.tipo == 'gasto',
                extract('month', Transaccion.fecha) == mes_actual,
                extract('year', Transaccion.fecha) == anio_actual
            ).scalar()
            
            gastado = float(gastado) if gastado else 0.0
            limite = float(p.monto_limite)
            
            if gastado > limite:
                cat = p.categoria
                cat.presupuesto = limite
                cat.gastado = gastado
                categorias_alertas.append(cat)

    return render_template('categorias/alertas.html', categorias=categorias_alertas)
