Feature: Gestión de cuenta de usuario
  Como usuario del sistema
  Quiero registrarme, iniciar y cerrar sesión
  Para acceder de forma segura al control financiero.

  Scenario: RF-01 Registro exitoso de nuevo usuario
    Given que el usuario no tiene una cuenta registrada
    When ingresa nombre "Juan Pérez", correo "juan@correo.com" y contraseña "123456"
    Then el sistema crea la cuenta y redirige al dashboard

  Scenario: RF-02 Rechazo de registro con correo sin @
    Given que el usuario está en el formulario de registro
    When ingresa el correo "juancorreo.com" sin el carácter @
    Then el sistema muestra un mensaje de error y no crea la cuenta

  Scenario: RF-03 Rechazo de registro con contraseña menor a 6 caracteres
    Given que el usuario está en el formulario de registro
    When ingresa la contraseña "123" con menos de 6 caracteres
    Then el sistema muestra un mensaje indicando la longitud mínima requerida y no crea la cuenta

  Scenario: RF-04 Rechazo de registro con correo ya existente
    Given que ya existe una cuenta registrada con el correo "juan@correo.com"
    When un nuevo usuario intenta registrarse con ese mismo correo
    Then el sistema muestra un mensaje de error indicando que el correo ya está en uso

  Scenario: RF-05 Rechazo de registro cuando las contraseñas no coinciden
    Given que el usuario está en el formulario de registro
    When ingresa "123456" en contraseña y "654321" en confirmar contraseña
    Then el sistema muestra un mensaje de error y no crea la cuenta

  Scenario: RF-06 Inicio de sesión exitoso
    Given que existe una cuenta con correo "juan@correo.com" y contraseña "123456"
    When el usuario ingresa esas credenciales en el formulario de login
    Then el sistema inicia la sesión y redirige al dashboard

  Scenario: RF-07 Rechazo de inicio de sesión con credenciales incorrectas
    Given que existe una cuenta con correo "juan@correo.com"
    When el usuario ingresa la contraseña incorrecta "000000"
    Then el sistema muestra un mensaje de error y no inicia la sesión

  Scenario: RF-08 Cierre de sesión exitoso
    Given que el usuario tiene una sesión activa
    When selecciona la opción de cerrar sesión
    Then el sistema cierra la sesión y redirige al login

  Scenario: RF-09 Protección de rutas para usuarios no autenticados
    Given que el usuario no ha iniciado sesión
    When intenta acceder directamente a una ruta protegida como el dashboard
    Then el sistema redirige al login sin mostrar el contenido solicitado
