# Pruebas black box con pytest

Estas pruebas están pensadas para el proyecto Flask de Control Financiero Personal.
Se basan en:

- Partición de equivalencia.
- Valores límite.
- Flujo funcional de transacciones, presupuesto y dashboard.

## Cómo usarlas

Copia la carpeta `tests/` dentro de la raíz del proyecto, al mismo nivel que `app.py`, `models.py` y `transacciones.py`.

Luego ejecuta:

```bash
pip install -r requirements.txt
pip install pytest
python -m pytest -q
```

## Cobertura funcional incluida

- Montos válidos e inválidos.
- Límites de monto: 0, 0.01, 999999.99 y 1000000.00.
- Descripciones vacías, de 1 carácter, 150 caracteres y 151 caracteres.
- Tipos válidos: ingreso y gasto.
- Tipo inválido.
- Categoría que no coincide con el tipo de transacción.
- Fecha actual, fecha pasada y fecha futura.
- Presupuesto por categoría: debajo del límite, en el límite y apenas por encima.
- Confirmación obligatoria cuando se supera el presupuesto.
- Verificación de que no se guarda el gasto excedido si no se confirma.
- Edición de transacción ignorando su propio monto anterior.
- Dashboard y endpoints usados por los gráficos.

## Resultado validado

En la versión revisada del proyecto, las pruebas corren con:

```text
30 passed
```
