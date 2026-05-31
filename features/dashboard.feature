Feature: Dashboard financiero
  Como usuario autenticado
  Quiero ver indicadores, gráficos y alertas
  Para analizar mi estado financiero mensual.

  Scenario: RF-27 Visualización del saldo del mes actual
    Given que el usuario tiene ingresos por 5000.00 y gastos por 1500.00 registrados en el mes actual
    When accede al dashboard
    Then el sistema muestra un saldo de 3500.00 para el mes actual

  Scenario: RF-28 Visualización de totales de ingresos y gastos por separado
    Given que el usuario tiene ingresos por 5000.00 y gastos por 1500.00 en el mes actual
    When accede al dashboard
    Then el sistema muestra 5000.00 como total de ingresos y 1500.00 como total de gastos de forma separada

  Scenario: RF-29 Visualización de últimas transacciones
    Given que el usuario tiene transacciones registradas en distintas fechas
    When accede al dashboard
    Then el sistema muestra las transacciones más recientes en orden cronológico descendente

  Scenario: RF-30 Visualización de gráfico de distribución por categoría
    Given que el usuario tiene transacciones de distintas categorías en el mes actual
    When accede al dashboard
    Then el sistema muestra un gráfico que refleja los montos reales por categoría del mes en curso

  Scenario: RF-31 Visualización de gráfico comparativo de los últimos 6 meses
    Given que el usuario tiene transacciones registradas en los últimos 6 meses
    When accede al dashboard
    Then el sistema muestra un gráfico con los ingresos y gastos reales de cada mes en orden cronológico

  Scenario: RF-32 Visualización del avance porcentual de presupuestos
    Given que el usuario tiene un presupuesto de 200.00 en la categoría "Transporte" y ha gastado 150.00 en esa categoría este mes
    When accede al dashboard
    Then el sistema muestra un avance del 75% para el presupuesto de "Transporte"
