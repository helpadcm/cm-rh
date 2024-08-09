# cm-rh

Modulos referentes a Recursos humanos para CM AIrlines

## Modulo hr_contract_cm

Para la instalacion de este modulo se necesitan las siguientes dependencias

- `hr_contract`

El modulo `hr_contract_cm` realiza las siguientes modificaciones:

- Nuevos campos han sido añadidos al modelo `hr.contract` mediante herencia. Estos campos están diseñados para calcular
  beneficios adicionales que los empleados pueden obtener, tales como el bono de transporte y las horas extras. Estos
  campos se han incorporado en la vista form `hr_contract.hr_contract_view_form` bajo la sección 'CONFIGURACIÓN DE
  BONIFICACIONES QUINCENALES'.

- Se añadio un cron que actualiza los campos de los bonus utilizando la informacion de los campos del modulo de 
  studio de odoo , este cron se ejecutara de forma manual y se encuentra en la vista 
  `data/cron_update_bonus.xml` , su estado siempre sera desactivado.

para obtener mas informacion, revisar el codigo fuente en el modulo `cm_rh/hr_contract_cm`

## Modulo hr_employee_cm

Para la instalacion de este modulo se necesitan las siguientes dependencias

- `hr`

El modulo `hr_employee_cm` realiza las siguientes modificaciones:

- Se ha añadido un nuevo campo al modelo `hr.employee` mediante herencia, el cual se calcula a partir del campo
  `birthday` para determinar el próximo cumpleaños del empleado. Se han creado dos nuevos filtros centrados en este
  campo: uno para mostrar los empleados que
  cumplen años en el mes actual y otro para los que cumplen años en el próximo mes. Este campo se ha incorporado en el
  formulario `hr.view_employee_form` en la pestaña 'Información Privada', los filtros se incoporaron en view filter
  `hr.view_employee_filter`


- Se ha implementado un método que formatea el campo del número de identidad del empleado. Este método se basa en el
  estándar hondureño, donde la identidad consta de 13 dígitos numéricos.

- Se oculto la seccion de "PERMISO DE TRABAJO" en la pestaña "Informacion Privada" en el formulario de
  empleado `hr.view_employee_form`

- Se han quitado los dominios al campo "user_id" los cuales impedian asignar un "usuario de portal", el campo
  "user_id" se encuentra en la pestaña "AJUSTES DE RR.HH" en el formulario de empleado `hr.view_employee_form` ,

- Se han quitado los dominios al campo "user_id" los cuales impedian asignar un "usuario de portal", el campo 
  "user_id" se encuentra en la pestaña "AJUSTES DE RR.HH" en el formulario de empleado `hr.view_employee_form` , 
  este cambio unicamente fue realizado a nivel de vista modificando mediante herencia el archivo `hr_employee_view.xml`

  ***IMPORTANTE*** al modificar los dominios del `user_id` se esta considerando que unicamente se trabaja en base a
  una empresa, si se desea trabajar con multiples empresas este codigo no sera eficiente y se debera de modificar
  para adaptase al cambio.


- Se ha creado una accion automatizada (cron) para la creacion de usuarios de portal , el cron se ejecturada de 
  forma diaria a las 07:00 am hora hondureña , la accion creara un usuario del portal al empleado unicamente si: 
  el empleado cuenta con un correo empresarial y actualmente no cuenta con un usuario ya creado. para comprender 
  esta tarea consultar el archivo `models/hr_employee.py` en la funcion `cron_create_portal_user_to_employee` , para 
  la vista consultar el archivo `data/cron_create_portal_user_to_employee.xml`


- Se ha creado una accion automatizada(cron) para otorgar una insignia a los empleados que cumplan un año en la 
  empresa, este cron se ejecutara de forma diaira a las 07:00 am hora hondureña , la accion buscara a los empleados 
  que segun su contrato cumplan este intervalo de tiempo mayor o igual a un año y menor a dos años, para poder 
  otorgarle la insignia el empleado debera tener un usuario relacionado, ya que las insignias se otorgan al usuario 
  y no al empleado como tal. para comprender mejor la esta tarea consultar el archivo `models/hr_employee.py` en la 
  funcion `cron_award_one_year_badge`, para la vista consultar el archivo `data/cron_award_one_year_badge.xml`, para 
  consultar la creacion de la insignia consultar el archivo `data/gamification_badge_data_cm.xml`

para obtener mas informacion, revisar el codigo fuente en el modulo `cm_rh/hr_employee_cm`

- 2024-07-05 Se adicionó el modelo branch(sucursal) y se relacionó con el modelo hr.employee, se adicionó el campo
  branch_id en el formulario de empleado `hr.view_employee_form` para obtener mas informacion, revisar el codigo
  fuente en el modulo `cm_rh/hr_employee_cm`

## Modulo hr_payroll_cm

Para la instalacion de este modulo se necesitan las siguientes dependencias

- `hr_payroll`
- `hr_contract_cm`

El modulo `hr_payroll_cm` realiza las siguientes modificaciones:

- Se ha creado un campo computado en el modelo `hr.employee` mediante herencia que genera el codigo del empleado. Este
  valor se puede
  visualizar en el formulario `hr.view_employee_form`.


- Se han desarrollado funciones que permiten calcular el número de cuotas de manera quincenal, en lugar de
  mensual, que es el método estándar que utiliza Odoo. Para complementar esto, se ha añadido un nuevo campo al
  modelo `hr.attendance.salary` que muestra la fecha del primer pago que el empleado debe realizar. Este campo se puede
  visualizar en el formulario `hr_payroll.hr_salary_attachment_view_form`.


- Se han desarrollado dos nuevas funciones que utilizan los datos de los contratos de los empleados para calcular el
  bono de transporte y las horas extras que se deben pagar al empleado, si corresponde. Estas funciones interactúan con
  el modelo `rh_contract_cm`  y `rh_payroll` para obtener la información necesaria para realizar los cálculos. Los
  cálculos se generan en el formulario `hr_payroll.model_hr_payslip`."

para obtener mas informacion, revisar el codigo fuente en el modulo `cm_rh/hr_payroll_cm`

- 2024-06-12 Se adicionó el campo employee_no a la vista emloyee_public_form_view, en la misma posición que la vista
  privada.

## Modulo plannig_cm

Para la instalacion de este modulo se necesitan las siguientes dependencias

- `planning`
- `hr_work_entry_contract`

El modulo `planning_cm` realiza las siguientes modificaciones:

- Se extienden de hr.contract para definir métodos para procesar las entradas de trabajo y calcular las horas extras
  basándose en reglas específicas.


- Se extienden de `hr.employee` agregando nuevos metodos que se encargaran de procesar las entradas para un empleado
  durante un periodo de tiempo especifico.


- Se extienden de `hr.work.entry` para definir nuevos metodos para procesar el tipo de entrada que se esta realizando.


- Se extiende de `planning.role` para agregar nuevos campos heredados con el objetivo de crear nuevos roles

para obtener mas informacion, revisar el codigo fuente en el modulo `cm_rh/planning_cm`

## Modulo rh_attendance_cm
### Notas de Actualización - 2024-07-05

#### Nuevas Características
- Se ha añadido soporte para dispositivos de asistencia en el módulo de Recursos Humanos. Esto incluye la gestión de dispositivos de asistencia, permitiendo registrar y configurar cada dispositivo utilizado para el registro de asistencias de los empleados.
- Implementación de campos relacionados en los registros de asistencia para vincular cada marca de tiempo con un dispositivo específico y la sucursal correspondiente.

#### Mejoras
- Extensión de las vistas de asistencia para incluir el dispositivo de asistencia utilizado. Ahora es posible filtrar y agrupar las asistencias por dispositivo, facilitando la gestión y el análisis de los datos de asistencia.
- Actualización de las vistas de formulario y árbol para dispositivos de asistencia, mejorando la usabilidad y accesibilidad de la información relacionada con los dispositivos.

#### Correcciones de Errores
- Se ha corregido un error en la definición del dominio del filtro `company_filter` en la vista de búsqueda de dispositivos de asistencia. Anteriormente, se producía un error debido a la referencia incorrecta al objeto `user` en el dominio del filtro.

#### Seguridad
- Actualización de los archivos de seguridad para incluir nuevos grupos y permisos relacionados con la gestión de dispositivos de asistencia. Esto asegura que solo los usuarios autorizados puedan acceder a la información y realizar operaciones relacionadas con los dispositivos de asistencia.

#### Documentación y Ayuda
- Se ha añadido documentación detallada sobre la configuración y uso de los dispositivos de asistencia dentro del módulo de Recursos Humanos. Esto incluye guías para la configuración de dispositivos y la asignación de dispositivos a empleados.

#### Dependencias
- Este módulo requiere `hr`, `hr_attendance`, y `hr_employee_cm` para su correcto funcionamiento.

Para más detalles sobre estas actualizaciones, por favor consulte la documentación del módulo en el sistema de ayuda en línea.
