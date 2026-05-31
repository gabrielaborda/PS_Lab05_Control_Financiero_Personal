Feature: Gestión de categorías y presupuestos
  Como usuario autenticado
  Quiero crear, editar y eliminar categorías y presupuestos
  Para organizar mis finanzas por rubros.

  Scenario: RF-19 Creación exitosa de una categoría
    Given que el usuario tiene una sesión activa
    When crea una categoría con nombre "Alimentación", tipo "gasto" e ícono "🍔"
    Then la categoría queda guardada y aparece en el listado del usuario

  Scenario: RF-20 Rechazo de categoría con nombre vacío
    Given que el usuario está en el formulario de nueva categoría
    When deja el campo nombre en blanco
    Then el sistema muestra un mensaje de error y no guarda la categoría

  Scenario: RF-21 Rechazo de categoría con nombre mayor a 50 caracteres
    Given que el usuario está en el formulario de nueva categoría
    When ingresa un nombre de 51 caracteres
    Then el sistema muestra un mensaje de error y no guarda la categoría

  Scenario: RF-22 Edición exitosa de una categoría existente
    Given que el usuario tiene una categoría llamada "Comida"
    When edita el nombre a "Alimentación" y guarda los cambios
    Then la categoría se actualiza y el listado refleja el nuevo nombre

  Scenario: RF-23 Eliminación exitosa de una categoría
    Given que el usuario tiene una categoría registrada
    When elimina esa categoría
    Then la categoría desaparece del listado

  Scenario: RF-24 Creación exitosa de un presupuesto mensual
    Given que el usuario tiene una categoría de tipo gasto
    When asigna un presupuesto de 500.00 para el mes y año actual
    Then el presupuesto queda guardado y se muestra en el listado de categorías

  Scenario: RF-25 Rechazo de presupuesto con mes y año distinto al actual
    Given que el usuario está en el formulario de presupuesto
    When ingresa un mes y año diferente al mes y año actual
    Then el sistema muestra un mensaje de error y no guarda el presupuesto

  Scenario: RF-26 Generación de alerta por presupuesto superado
    Given que el usuario tiene una categoría de gasto con presupuesto de 100.00 para el mes actual
    When el total de gastos registrados en esa categoría supera 100.00
    Then el sistema muestra una alerta en la sección de categorías y en el dashboard
