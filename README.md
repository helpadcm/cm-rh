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
  este cambio unicamente fue realizado a nivel de vista modificando mediante herencia el archivo `hr_employee_view.xml`

  ***IMPORTANTE*** al modificar los dominios del `user_id` se esta considerando que unicamente se trabaja en base a
  una empresa, si se desea trabajar con multiples empresas este codigo no sera eficiente y se debera de modificar
  para adaptase al cambio.

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
