from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

cat_bp = Blueprint('categorias', __name__, url_prefix='/categorias')

# TEMPORAL: reemplazar con import de models.py cuando Dev 1 lo complete.
class CategoriaMock:
    def __init__(self, id, nombre, tipo, icono, usuario_id, presupuesto=None, gastado=0):
        self.id = id
        self.nombre = nombre
        self.tipo = tipo
        self.icono = icono
        self.usuario_id = usuario_id
        self.presupuesto = presupuesto
        self.gastado = gastado

mock_categorias = [
    CategoriaMock(1, 'Comida', 'gasto', '🍔', 1, 500.0, 600.0),
    CategoriaMock(2, 'Transporte', 'gasto', '🚗', 1, 200.0, 150.0),
    CategoriaMock(3, 'Salario', 'ingreso', '💰', 1)
]
mock_id_counter = 4

@cat_bp.route('/')
@login_required
def lista():
    categorias_usuario = [c for c in mock_categorias if c.usuario_id == current_user.id]
    return render_template('categorias/lista.html', categorias=categorias_usuario)

@cat_bp.route('/nueva', methods=['GET', 'POST'])
@login_required
def nueva():
    global mock_id_counter
    if request.method == 'POST':
        nombre = request.form.get('nombre')
        tipo = request.form.get('tipo')
        icono = request.form.get('icono')
        
        nueva_cat = CategoriaMock(mock_id_counter, nombre, tipo, icono, current_user.id)
        mock_categorias.append(nueva_cat)
        mock_id_counter += 1
        
        flash('Categoría creada exitosamente.', 'success')
        return redirect(url_for('categorias.lista'))
        
    return render_template('categorias/form.html', categoria=None)

@cat_bp.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar(id):
    categoria = next((c for c in mock_categorias if c.id == id and c.usuario_id == current_user.id), None)
    if not categoria:
        flash('Categoría no encontrada.', 'danger')
        return redirect(url_for('categorias.lista'))
        
    if request.method == 'POST':
        categoria.nombre = request.form.get('nombre')
        categoria.tipo = request.form.get('tipo')
        categoria.icono = request.form.get('icono')
        
        flash('Categoría actualizada.', 'success')
        return redirect(url_for('categorias.lista'))
        
    return render_template('categorias/form.html', categoria=categoria)

@cat_bp.route('/eliminar/<int:id>', methods=['POST'])
@login_required
def eliminar(id):
    global mock_categorias
    categoria = next((c for c in mock_categorias if c.id == id and c.usuario_id == current_user.id), None)
    if categoria:
        mock_categorias = [c for c in mock_categorias if c.id != id]
        flash('Categoría eliminada.', 'success')
    else:
        flash('Categoría no encontrada.', 'danger')
    return redirect(url_for('categorias.lista'))

@cat_bp.route('/presupuesto/<int:id>', methods=['GET', 'POST'])
@login_required
def presupuesto(id):
    categoria = next((c for c in mock_categorias if c.id == id and c.usuario_id == current_user.id), None)
    if not categoria:
        flash('Categoría no encontrada.', 'danger')
        return redirect(url_for('categorias.lista'))
        
    if request.method == 'POST':
        monto = request.form.get('monto')
        if monto:
            categoria.presupuesto = float(monto)
            flash('Presupuesto actualizado.', 'success')
            return redirect(url_for('categorias.lista'))
            
    return render_template('categorias/presupuesto.html', categoria=categoria)

@cat_bp.route('/alertas')
@login_required
def alertas():
    categorias_alertas = [
        c for c in mock_categorias 
        if c.usuario_id == current_user.id and c.tipo == 'gasto' and c.presupuesto is not None and c.gastado > c.presupuesto
    ]
    return render_template('categorias/alertas.html', categorias=categorias_alertas)
