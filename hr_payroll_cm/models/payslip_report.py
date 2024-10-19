from collections import namedtuple
from dataclasses import dataclass, field
from typing import Optional

PaySlipReport = namedtuple(
    'PaySlipReport', [
        'No',
        'Fecha_de_Ingreso',
        'ID',
        'No_de_Cuenta_BAN_PAIS',
        'Nombre_de_Empleado',
        'Puesto_del_Empleado',
        'Salario_Mensual',
        'Salario_Quincenal',
        'Horas_Extras_1_25',
        'Valor_Tiempo_Extra_25',
        'Bono_de_Transporte_alimentacion_capacitacion',
        'Charter_Comisones',
        'Bono_Por_Resultado',
        'Total_Devengado',
        'ISR',
        'Rap',
        'IHSS',
        'Impto_Vecinal',
        'ELGA',
        'Prestamos_Internos',
        'Cuentas_por_Cobrar',
        'Prestamos_Rap',
        'Odontologia',
        'Optica',
        'C_Sagrada_Familia',
        'Incapacidad',
        'Otros',
        'Total_Deducciones',
        'TOTAL_NETO_A_PAGAR'
        ]
    )

ReportGroup = namedtuple(
    'ReportGroup', [
        'department',
        'total',
        'payslips'
        ]
    )


@dataclass
class PaySlipReportDataClass:
    no: Optional[int] = field(default=None)
    fecha_de_ingreso: Optional[str] = field(default=None)
    id: Optional[str] = field(default=None)
    no_de_cuenta_ban_pais: Optional[str] = field(default=None)
    nombre_de_empleado: Optional[str] = field(default=None)
    puesto_del_empleado: Optional[str] = field(default=None)
    salario_mensual: Optional[float] = field(default=None)
    salario_quincenal: Optional[float] = field(default=None)

    horas_extras_125: Optional[float] = field(default=None)
    valor_tiempo_extra_25: Optional[float] = field(default=None)
    horas_extras_150: Optional[float] = field(default=None)
    valor_tiempo_extra_50: Optional[float] = field(default=None)

    feriado_trabajado: Optional[float] = field(default=None)
    bono_de_transporte_alimentacion_capacitacion: Optional[float] = field(default=None)
    charter_comisones: Optional[float] = field(default=None)
    bono_por_resultado: Optional[float] = field(default=None)
    ajuste: Optional[float] = field(default=None)
    total_devengado: Optional[float] = field(default=None)

    isr: Optional[float] = field(default=None)
    rap: Optional[float] = field(default=None)
    ihss: Optional[float] = field(default=None)
    impto_vecinal: Optional[float] = field(default=None)
    elga: Optional[float] = field(default=None)
    prestamos_internos: Optional[float] = field(default=None)
    cuentas_por_cobrar: Optional[float] = field(default=None)
    prestamos_rap: Optional[float] = field(default=None)
    odontologia: Optional[float] = field(default=None)
    optica: Optional[float] = field(default=None)
    c_sagrada_familia: Optional[float] = field(default=None)
    incapacidad: Optional[float] = field(default=None)
    otros: Optional[float] = field(default=None)
    total_deducciones: Optional[float] = field(default=None)

    total_neto_a_pagar: Optional[float] = field(default=None)

    def update_not_none(self, other):
        for field_name in self.__annotations__:
            value = getattr(other, field_name)
            if value is not None:
                setattr(self, field_name, value)
        return self
