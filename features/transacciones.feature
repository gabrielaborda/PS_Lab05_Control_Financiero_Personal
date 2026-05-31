Feature: Gestión de transacciones
  Como usuario autenticado
  Quiero registrar, editar, eliminar y filtrar transacciones
  Para mantener actualizado mi historial financiero.

  Scenario: RF-10 Registro exitoso de una transacción
    Given que el usuario tiene una sesión activa y al menos una categoría creada
    When registra una transacción de tipo gasto con monto 50.00, descripción "Almuerzo", fecha de hoy y una categoría válida
    Then la transacción queda guardada y aparece en el historial

  Scenario: RF-11 Rechazo de transacción con monto menor a 0.01
    Given que el usuario está en el formulario de nueva transacción
    When ingresa el monto 0.00
    Then el sistema muestra un mensaje de error y no guarda la transacción

  Scenario: RF-12 Rechazo de transacción con descripción vacía
    Given que el usuario está en el formulario de nueva transacción
    When deja el campo descripción en blanco
    Then el sistema muestra un mensaje de error y no guarda la transacción

  Scenario: RF-13 Edición exitosa de una transacción existente
    Given que el usuario tiene una transacción registrada con monto 50.00
    When edita el monto a 75.00 y guarda los cambios
    Then la transacción se actualiza y el historial refleja el nuevo monto

  Scenario: RF-14 Eliminación exitosa de una transacción
    Given que el usuario tiene una transacción registrada
    When elimina esa transacción
    Then la transacción desaparece del historial y los totales se recalculan

  Scenario: RF-15 Filtro de transacciones por tipo
    Given que el usuario tiene transacciones de tipo ingreso y de tipo gasto registradas
    When aplica el filtro por tipo "gasto"
    Then el historial muestra únicamente las transacciones de tipo gasto

  Scenario: RF-16 Filtro de transacciones por categoría
    Given que el usuario tiene transacciones de distintas categorías registradas
    When aplica el filtro por la categoría "Alimentación"
    Then el historial muestra únicamente las transacciones de esa categoría

  Scenario: RF-17 Filtro de transacciones por rango de fechas
    Given que el usuario tiene transacciones registradas en distintas fechas
    When aplica un filtro con fecha desde "2026-01-01" hasta "2026-01-31"
    Then el historial muestra únicamente las transacciones dentro de ese rango

  Scenario: RF-18 Exportación del historial a CSV
    Given que el usuario tiene transacciones registradas y filtros aplicados
    When selecciona la opción de exportar a CSV
    Then se descarga un archivo CSV con las transacciones visibles según los filtros activos
