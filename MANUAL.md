# Manual Rápido de Uso

## 1. Ejecutar el proyecto

1. Abrir una terminal en la carpeta del proyecto.
2. Crear el entorno virtual:
   ```bash
   python -m venv venv
   ```
3. Activar el entorno virtual:
   - Windows:
     ```powershell
     .\venv\Scripts\activate
     ```
   - Mac/Linux:
     ```bash
     source venv/bin/activate
     ```
4. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```
5. Ejecutar la aplicación:
   ```bash
   python app.py
   ```
6. Abrir el navegador en:
   ```text
   http://127.0.0.1:5000/
   ```

> La base de datos SQLite se crea automáticamente en `finanzas.db` cuando la aplicación arranca.

## 2. Módulos principales

### 2.1 Autenticación

Rutas principales:
- `/auth/registro` - Registrar nuevo usuario.
- `/auth/login` - Ingresar al sistema.
- `/auth/logout` - Cerrar sesión.

Datos válidos:
- `nombre`: texto obligatorio.
- `email`: correo electrónico obligatorio y único.
- `password`: obligatorio.
- `confirmar_password`: debe coincidir con `password`.

Restricciones:
- Todos los campos son obligatorios.
- El correo no puede estar ya registrado.
- La contraseña y su confirmación deben coincidir.

### 2.2 Dashboard

Rutas principales:
- `/dashboard/` - Vista principal de resumen mensual e histórico.
- `/dashboard/reportes` - Gráficos y reportes.

Uso:
- Solo accesible cuando el usuario está autenticado.
- Muestra ingresos, gastos, saldo histórico, transacciones recientes y alertas de presupuesto.

### 2.3 Categorías y presupuestos

Rutas principales:
- `/categorias/` - Lista de categorías del usuario.
- `/categorias/nueva` - Crear categoría.
- `/categorias/editar/<id>` - Editar categoría.
- `/categorias/eliminar/<id>` - Eliminar categoría.
- `/categorias/presupuesto/<id>` - Configurar presupuesto mensual para una categoría.
- `/categorias/alertas` - Ver categorías con gasto por encima del presupuesto.

Datos válidos por categoría:
- `nombre`: obligatorio.
- `tipo`: debe ser `ingreso` o `gasto`.
- `icono`: opcional, puede ser un emoji o un texto corto.

Restricciones de categorías:
- Las categorías pertenecen al usuario autenticado.
- Al crear o editar una categoría, se guarda el tipo elegido.
- Solo las categorías existentes del usuario pueden usarse en transacciones.

Datos válidos por presupuesto:
- `monto`: valor numérico.
- `mes`: entero entre 1 y 12.
- `anio`: año válido.

Restricciones de presupuesto:
- Un presupuesto está vinculado a una categoría, mes y año.
- El mismo usuario no puede tener dos presupuestos iguales para la misma categoría/mes/año.

### 2.4 Transacciones

Rutas principales:
- `/transacciones/` - Listar transacciones.
- `/transacciones/crear` - Crear transacción.
- `/transacciones/<id>/editar` - Editar transacción.

Filtros disponibles:
- Tipo: `ingreso` o `gasto`.
- Fecha de inicio / fecha fin.
- Categoría.
- Paginación de 10 ítems por página.

Datos válidos por transacción:
- `descripcion`: obligatorio, 1 a 150 caracteres.
- `monto`: número válido mayor a 0 y menor o igual a 999999.99.
- `tipo`: `ingreso` o `gasto`.
- `fecha`: fecha válida en formato `YYYY-MM-DD` y no puede ser futura.
- `categoria_id`: debe existir y corresponder al usuario autenticado.

Restricciones de transacciones:
- El monto no puede ser negativo ni cero.
- La categoría seleccionada debe existir y debe coincidir con el tipo de transacción.
- Las fechas no pueden ser posteriores al día actual.
- Los usuarios solo ven y modifican sus propias transacciones.

## 3. Restricciones generales del sistema

- Todas las rutas de gestión requieren inicio de sesión.
- El sistema usa `Flask-Login` para controlar el acceso.
- Los datos de usuario se guardan en una base SQLite local (`finanzas.db`).
- No se permite la creación de elementos con campos vacíos en formularios obligatorios.
- Los errores en la aplicación muestran páginas de error `404` o `500` según el problema.
- El campo `categoria_id` de una transacción puede ser `NULL` solo si no se asigna categoría, pero en la aplicación actual se debe escoger una categoría válida.

## 4. Recomendaciones de uso

1. Registra tu usuario y accede con correo y contraseña.
2. Crea categorías propias antes de registrar transacciones.
3. Define presupuestos para las categorías de gasto que quieres controlar.
4. Utiliza el dashboard para revisar alertas y saldo mensual.
5. Filtra transacciones por rango de fechas y tipo para facilitar el seguimiento.

## 5. Resumen de rutas clave

- `/` - Inicio público.
- `/auth/registro` - Registro de usuario.
- `/auth/login` - Inicio de sesión.
- `/dashboard/` - Panel principal.
- `/dashboard/reportes` - Reportes.
- `/categorias/` - Gestión de categorías.
- `/transacciones/` - Gestión y listado de transacciones.
- `/health` - Verificación de estado de la aplicación.
