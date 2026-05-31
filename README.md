# Control Financiero Personal

Aplicación web para gestionar finanzas personales con registro de ingresos y gastos, categorías personalizadas, presupuestos mensuales y un dashboard de análisis.

## Integrantes
- Betanzos Rosas Taylor Anthony
- Borda Espinoza Gabriela Nayely
- Condori León Joel Isaias
- Perez Huamani Jeremy Joshua

## Instrucciones de Instalación

1. Clonar el repositorio.
2. Asegúrate de tener Python instalado.
3. Crea un entorno virtual:
   ```bash
   python -m venv venv
   ```
4. Activa el entorno virtual:
   - Windows: `.\venv\Scripts\activate`
   - Mac/Linux: `source venv/bin/activate`
5. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Cómo correr el proyecto

Ejecuta el siguiente comando en la terminal:
```bash
python app.py
```
La aplicación estará disponible en `http://127.0.0.1:5000/`.

## Descripción de Módulos

- **`app.py`**: Punto de entrada de la aplicación. Configura la base de datos y registra los blueprints. (Responsable: [ ])
- **`models.py`**: Definición de los modelos de base de datos usando SQLAlchemy (Usuario, Transacción, Categoría, Presupuesto). (Responsable: [ ])
- **`auth.py`**: Gestión de rutas de autenticación (registro, inicio de sesión, cierre de sesión) usando Flask-Login. (Responsable: [ ])
- **`templates/` y `static/`**: Archivos HTML y recursos estáticos (CSS, JS) para la interfaz de usuario. (Responsable: [ ])
