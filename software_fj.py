"""
Software FJ - Sistema Integral de Gestión de Clientes, Servicios y Reservas
Curso: Programación 213023 - Fase 4
Autor: [NOMBRE DEL ESTUDIANTE]

El sistema administra clientes, servicios y reservas en memoria (listas y objetos),
sin base de datos. Solo se escribe un archivo de texto plano para la auditoría de
eventos y errores: software_fj.log
"""

import logging
import os
from abc import ABC, abstractmethod
from datetime import datetime


ARCHIVO_LOG = "software_fj.log"
IVA_DEFECTO = 0.19


# ---------------------------------------------------------------------------
# 1. Auditoría: gestor de logs
# ---------------------------------------------------------------------------
class FormatoLog(logging.Formatter):
    """Formato de una línea por evento: fecha, nivel y mensaje.

    Python escribe WARNING y aquí se traduce a ADVERTENCIA para que el archivo
    quede en el mismo idioma del resto del sistema.
    """

    def format(self, registro):
        nivel_original = registro.levelname
        if registro.levelno == logging.WARNING:
            registro.levelname = "ADVERTENCIA"
        try:
            return super().format(registro)
        finally:
            registro.levelname = nivel_original


class GestorLog:
    """Único punto de escritura del archivo software_fj.log.

    Centralizar la escritura evita que cada clase abra el archivo por su cuenta
    y garantiza que todos los eventos queden con el mismo formato.
    """

    def __init__(self, ruta=ARCHIVO_LOG):
        self._ruta = ruta
        self._registrador = logging.getLogger("software_fj")
        self._registrador.setLevel(logging.INFO)
        self._registrador.propagate = False

        # Si el objeto se crea dos veces en la misma ejecución no se duplican líneas.
        for manejador in list(self._registrador.handlers):
            self._registrador.removeHandler(manejador)
            manejador.close()

        manejador = logging.FileHandler(ruta, mode="a", encoding="utf-8")
        manejador.setFormatter(
            FormatoLog(
                fmt="%(asctime)s | %(levelname)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        self._registrador.addHandler(manejador)

    @property
    def ruta(self):
        return self._ruta

    def info(self, mensaje):
        self._registrador.info(mensaje)

    def advertencia(self, mensaje):
        self._registrador.warning(mensaje)

    def error(self, mensaje):
        self._registrador.error(mensaje)

    def cerrar(self):
        for manejador in list(self._registrador.handlers):
            self._registrador.removeHandler(manejador)
            manejador.close()


# ---------------------------------------------------------------------------
# 2. Excepciones personalizadas
# ---------------------------------------------------------------------------
class ErrorSistemaFJ(Exception):
    """Excepción base de todos los errores controlados del sistema.

    Permite atrapar cualquier falla propia de Software FJ con un solo except
    sin confundirla con errores de programación (TypeError, AttributeError, etc.).
    """


class ErrorDatosInvalidos(ErrorSistemaFJ):
    """Datos vacíos, con formato incorrecto o valores negativos."""


class ErrorServicioNoDisponible(ErrorSistemaFJ):
    """El servicio está inactivo o su capacidad ya fue agotada."""


class ErrorReservaInvalida(ErrorSistemaFJ):
    """Transición de estado no permitida, duración inválida o referencias rotas."""


class ErrorCalculoCosto(ErrorSistemaFJ):
    """Inconsistencias en tarifas, descuentos o impuestos."""


# ---------------------------------------------------------------------------
# 3. Entidad base
# ---------------------------------------------------------------------------
def formatear_moneda(valor):
    """Devuelve el valor en formato de pesos colombianos: $1.234.567,89"""
    texto = f"{valor:,.2f}"
    return "$" + texto.replace(",", "_").replace(".", ",").replace("_", ".")


class EntidadBase(ABC):
    """Elemento general del sistema con identificador y fecha de creación."""

    _consecutivos = {}

    def __init__(self, prefijo):
        EntidadBase._consecutivos[prefijo] = EntidadBase._consecutivos.get(prefijo, 0) + 1
        self._identificador = f"{prefijo}-{EntidadBase._consecutivos[prefijo]:04d}"
        self._fecha_creacion = datetime.now()

    @property
    def identificador(self):
        return self._identificador

    @property
    def fecha_creacion(self):
        return self._fecha_creacion

    @abstractmethod
    def validar(self):
        """Verifica la consistencia del objeto. Devuelve True o lanza excepción."""

    @abstractmethod
    def obtener_resumen(self):
        """Devuelve una línea de texto con la información principal del objeto."""


# ---------------------------------------------------------------------------
# 4. Cliente
# ---------------------------------------------------------------------------
class Cliente(EntidadBase):
    """Cliente de Software FJ. Los datos personales quedan encapsulados."""

    def __init__(self, documento, nombre, correo, telefono):
        super().__init__("CLI")
        # Cada asignación pasa por su setter, así el objeto nunca queda mal formado.
        self.documento = documento
        self.nombre = nombre
        self.correo = correo
        self.telefono = telefono

    @property
    def documento(self):
        return self.__documento

    @documento.setter
    def documento(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if texto == "":
            raise ErrorDatosInvalidos("El documento del cliente no puede estar vacío.")
        if not texto.isdigit():
            raise ErrorDatosInvalidos(f"El documento '{texto}' debe contener solo dígitos.")
        if len(texto) < 6:
            raise ErrorDatosInvalidos(
                f"El documento '{texto}' debe tener como mínimo 6 dígitos."
            )
        self.__documento = texto

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if len(texto) < 3:
            raise ErrorDatosInvalidos("El nombre del cliente debe tener al menos 3 caracteres.")
        self.__nombre = texto

    @property
    def correo(self):
        return self.__correo

    @correo.setter
    def correo(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if texto == "":
            raise ErrorDatosInvalidos("El correo del cliente no puede estar vacío.")
        if " " in texto or "@" not in texto:
            raise ErrorDatosInvalidos(f"El correo '{texto}' no tiene un formato válido.")
        usuario, _, dominio = texto.partition("@")
        if usuario == "" or "." not in dominio or dominio.startswith(".") or dominio.endswith("."):
            raise ErrorDatosInvalidos(f"El correo '{texto}' no tiene un formato válido.")
        self.__correo = texto.lower()

    @property
    def telefono(self):
        return self.__telefono

    @telefono.setter
    def telefono(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if not texto.isdigit():
            raise ErrorDatosInvalidos(f"El teléfono '{texto}' debe contener solo dígitos.")
        if not 7 <= len(texto) <= 10:
            raise ErrorDatosInvalidos(
                f"El teléfono '{texto}' debe tener entre 7 y 10 dígitos."
            )
        self.__telefono = texto

    def validar(self):
        # Se repiten las reglas porque un objeto pudo llegar por carga masiva
        # o por un cambio posterior; validar() es la última barrera antes de usarlo.
        if len(self.documento) < 6 or not self.documento.isdigit():
            raise ErrorDatosInvalidos("El cliente no tiene un documento válido.")
        if len(self.nombre) < 3:
            raise ErrorDatosInvalidos("El cliente no tiene un nombre válido.")
        if "@" not in self.correo or "." not in self.correo:
            raise ErrorDatosInvalidos("El cliente no tiene un correo válido.")
        if not self.telefono.isdigit():
            raise ErrorDatosInvalidos("El cliente no tiene un teléfono válido.")
        return True

    def obtener_resumen(self):
        return (
            f"{self.identificador} | {self.nombre} | doc. {self.documento} | "
            f"{self.correo} | tel. {self.telefono}"
        )


# ---------------------------------------------------------------------------
# 5. Servicios
# ---------------------------------------------------------------------------
class Servicio(EntidadBase, ABC):
    """Servicio ofrecido por Software FJ.

    Define el contrato de los servicios especializados: calcular el costo,
    describirse y validar sus propios parámetros. Además concentra las
    validaciones numéricas que comparten todos los cálculos.
    """

    DESCUENTO_MAXIMO = 0.50
    IMPUESTO_MAXIMO = 0.30
    UNIDAD_COBRO = "hora"

    def __init__(self, nombre, tarifa_base, disponible=True):
        super().__init__("SRV")
        self.nombre = nombre
        self.tarifa_base = tarifa_base
        self.disponible = disponible

    @property
    def nombre(self):
        return self.__nombre

    @nombre.setter
    def nombre(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if len(texto) < 3:
            raise ErrorDatosInvalidos("El nombre del servicio debe tener al menos 3 caracteres.")
        self.__nombre = texto

    @property
    def tarifa_base(self):
        return self.__tarifa_base

    @tarifa_base.setter
    def tarifa_base(self, valor):
        if valor is None:
            raise ErrorDatosInvalidos("La tarifa base del servicio es obligatoria.")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErrorDatosInvalidos(f"La tarifa base '{valor}' debe ser un valor numérico.")
        if valor < 0:
            raise ErrorDatosInvalidos(f"La tarifa base no puede ser negativa (recibido: {valor}).")
        if valor == 0:
            raise ErrorDatosInvalidos("La tarifa base debe ser mayor que cero.")
        self.__tarifa_base = float(valor)

    @property
    def disponible(self):
        return self.__disponible

    @disponible.setter
    def disponible(self, valor):
        self.__disponible = bool(valor)

    def _verificar_duracion(self, duracion):
        """Convierte y valida la duración antes de multiplicar por la tarifa."""
        if duracion is None:
            raise ErrorCalculoCosto("La duración es obligatoria para calcular el costo.")
        if isinstance(duracion, bool) or not isinstance(duracion, (int, float)):
            raise ErrorCalculoCosto(f"La duración '{duracion}' debe ser numérica.")
        if duracion <= 0:
            raise ErrorCalculoCosto(
                f"La duración debe ser mayor que cero para calcular el costo (recibido: {duracion})."
            )
        return float(duracion)

    def _aplicar_ajustes(self, costo, descuento=None, impuesto=None):
        """Aplica descuento e impuesto sobre un costo bruto ya calculado.

        Es la parte común de la sobrecarga: los tres servicios llegan aquí con
        su costo propio y solo cambian los porcentajes recibidos.
        """
        if costo is None or costo < 0:
            raise ErrorCalculoCosto(f"El costo calculado no es válido: {costo}.")

        resultado = float(costo)

        if descuento is not None:
            if isinstance(descuento, bool) or not isinstance(descuento, (int, float)):
                raise ErrorCalculoCosto(f"El descuento '{descuento}' debe ser numérico.")
            if not 0 <= descuento <= self.DESCUENTO_MAXIMO:
                raise ErrorCalculoCosto(
                    f"El descuento {descuento:.0%} está fuera del rango permitido "
                    f"(0% - {self.DESCUENTO_MAXIMO:.0%})."
                )
            resultado = resultado * (1 - descuento)

        if impuesto is not None:
            if isinstance(impuesto, bool) or not isinstance(impuesto, (int, float)):
                raise ErrorCalculoCosto(f"El impuesto '{impuesto}' debe ser numérico.")
            if not 0 <= impuesto <= self.IMPUESTO_MAXIMO:
                raise ErrorCalculoCosto(
                    f"El impuesto {impuesto:.0%} está fuera del rango permitido "
                    f"(0% - {self.IMPUESTO_MAXIMO:.0%})."
                )
            resultado = resultado * (1 + impuesto)

        return round(resultado, 2)

    @abstractmethod
    def calcular_costo(self, duracion, descuento=None, impuesto=None):
        """Sobrecarga por argumentos opcionales.

        calcular_costo(duracion)                      -> tarifa base por duración
        calcular_costo(duracion, descuento)           -> tarifa con descuento
        calcular_costo(duracion, descuento, impuesto) -> tarifa con descuento e IVA
        """

    @abstractmethod
    def describir_servicio(self):
        """Devuelve la descripción comercial del servicio."""

    @abstractmethod
    def validar_parametros(self):
        """Valida los atributos propios de cada servicio especializado."""

    def validar(self):
        if len(self.nombre) < 3:
            raise ErrorDatosInvalidos("El servicio no tiene un nombre válido.")
        if self.tarifa_base <= 0:
            raise ErrorCalculoCosto("La tarifa base debe ser mayor que cero.")
        self.validar_parametros()
        return True

    def obtener_resumen(self):
        estado = "disponible" if self.disponible else "no disponible"
        return (
            f"{self.identificador} | {self.nombre} | {self.describir_servicio()} | "
            f"tarifa base {formatear_moneda(self.tarifa_base)} | {estado}"
        )


class ReservaSala(Servicio):
    """Alquiler de salas por hora, con recargo por aforo y equipamiento."""

    AFORO_BASE = 30
    RECARGO_AFORO = 0.15
    COSTO_EQUIPAMIENTO_HORA = 25_000
    CAPACIDAD_MAXIMA = 200

    def __init__(self, nombre, tarifa_base, capacidad=None, equipamiento=False, disponible=True):
        super().__init__(nombre, tarifa_base, disponible)
        self.capacidad = capacidad
        self.equipamiento = equipamiento
        self.validar_parametros()

    @property
    def capacidad(self):
        return self.__capacidad

    @capacidad.setter
    def capacidad(self, valor):
        if valor is None:
            raise ErrorDatosInvalidos("La sala requiere la capacidad de personas (parámetro faltante).")
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ErrorDatosInvalidos(f"La capacidad '{valor}' debe ser un número entero.")
        if valor <= 0:
            raise ErrorDatosInvalidos(f"La capacidad de la sala debe ser mayor que cero (recibido: {valor}).")
        if valor > self.CAPACIDAD_MAXIMA:
            raise ErrorDatosInvalidos(
                f"La capacidad {valor} supera el máximo permitido ({self.CAPACIDAD_MAXIMA} personas)."
            )
        self.__capacidad = valor

    @property
    def equipamiento(self):
        return self.__equipamiento

    @equipamiento.setter
    def equipamiento(self, valor):
        self.__equipamiento = bool(valor)

    def validar_parametros(self):
        if self.capacidad <= 0:
            raise ErrorDatosInvalidos("La sala debe tener una capacidad mayor que cero.")
        if self.equipamiento and self.capacidad < 5:
            raise ErrorDatosInvalidos(
                "Una sala con equipamiento audiovisual debe tener capacidad para 5 personas o más."
            )
        return True

    def calcular_costo(self, duracion, descuento=None, impuesto=None):
        horas = self._verificar_duracion(duracion)
        tarifa_hora = self.tarifa_base

        # Las salas grandes consumen más recursos de operación (aseo, vigilancia).
        if self.capacidad > self.AFORO_BASE:
            tarifa_hora *= 1 + self.RECARGO_AFORO
        if self.equipamiento:
            tarifa_hora += self.COSTO_EQUIPAMIENTO_HORA

        return self._aplicar_ajustes(tarifa_hora * horas, descuento, impuesto)

    def describir_servicio(self):
        equipo = "con equipamiento audiovisual" if self.equipamiento else "sin equipamiento"
        return f"Sala para {self.capacidad} personas, {equipo}"


class AlquilerEquipo(Servicio):
    """Alquiler de equipos por unidad y por día, con seguro opcional."""

    RECARGO_SEGURO = 0.12
    CANTIDAD_MAXIMA = 20
    UNIDAD_COBRO = "día"

    def __init__(self, nombre, tarifa_base, tipo_equipo=None, cantidad=None,
                 seguro=False, disponible=True):
        super().__init__(nombre, tarifa_base, disponible)
        self.tipo_equipo = tipo_equipo
        self.cantidad = cantidad
        self.seguro = seguro
        self.validar_parametros()

    @property
    def tipo_equipo(self):
        return self.__tipo_equipo

    @tipo_equipo.setter
    def tipo_equipo(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if texto == "":
            raise ErrorDatosInvalidos("El tipo de equipo es obligatorio (parámetro faltante).")
        self.__tipo_equipo = texto

    @property
    def cantidad(self):
        return self.__cantidad

    @cantidad.setter
    def cantidad(self, valor):
        if valor is None:
            raise ErrorDatosInvalidos("La cantidad de unidades es obligatoria (parámetro faltante).")
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ErrorDatosInvalidos(f"La cantidad '{valor}' debe ser un número entero.")
        if valor <= 0:
            raise ErrorDatosInvalidos(f"La cantidad de unidades debe ser mayor que cero (recibido: {valor}).")
        if valor > self.CANTIDAD_MAXIMA:
            raise ErrorDatosInvalidos(
                f"La cantidad {valor} supera el máximo permitido por reserva ({self.CANTIDAD_MAXIMA})."
            )
        self.__cantidad = valor

    @property
    def seguro(self):
        return self.__seguro

    @seguro.setter
    def seguro(self, valor):
        self.__seguro = bool(valor)

    def validar_parametros(self):
        if self.tipo_equipo == "":
            raise ErrorDatosInvalidos("El equipo debe tener un tipo definido.")
        if self.cantidad <= 0:
            raise ErrorDatosInvalidos("El equipo debe tener al menos una unidad.")
        return True

    def calcular_costo(self, duracion, descuento=None, impuesto=None):
        dias = self._verificar_duracion(duracion)
        costo = self.tarifa_base * self.cantidad * dias

        # El seguro cubre daños o pérdida del equipo durante el alquiler.
        if self.seguro:
            costo *= 1 + self.RECARGO_SEGURO

        return self._aplicar_ajustes(costo, descuento, impuesto)

    def describir_servicio(self):
        unidades = "unidad" if self.cantidad == 1 else "unidades"
        seguro = "con seguro" if self.seguro else "sin seguro"
        return f"{self.cantidad} {unidades} de {self.tipo_equipo.lower()}, {seguro}"


class AsesoriaEspecializada(Servicio):
    """Asesoría técnica por hora, según complejidad y modalidad."""

    FACTORES_NIVEL = {"Básico": 1.0, "Intermedio": 1.2, "Alto": 1.45}
    RECARGO_PRESENCIAL = 0.10
    MODALIDADES = ("Remota", "Presencial")

    def __init__(self, nombre, tarifa_base, especialidad=None, nivel=None,
                 modalidad=None, disponible=True):
        super().__init__(nombre, tarifa_base, disponible)
        self.especialidad = especialidad
        self.nivel = nivel
        self.modalidad = modalidad
        self.validar_parametros()

    @property
    def especialidad(self):
        return self.__especialidad

    @especialidad.setter
    def especialidad(self, valor):
        texto = "" if valor is None else str(valor).strip()
        if len(texto) < 4:
            raise ErrorDatosInvalidos("La especialidad técnica es obligatoria (parámetro faltante).")
        self.__especialidad = texto

    @property
    def nivel(self):
        return self.__nivel

    @nivel.setter
    def nivel(self, valor):
        texto = "" if valor is None else str(valor).strip().capitalize()
        if texto not in self.FACTORES_NIVEL:
            raise ErrorDatosInvalidos(
                f"El nivel de complejidad '{valor}' no es válido. "
                f"Opciones: {', '.join(self.FACTORES_NIVEL)}."
            )
        self.__nivel = texto

    @property
    def modalidad(self):
        return self.__modalidad

    @modalidad.setter
    def modalidad(self, valor):
        texto = "" if valor is None else str(valor).strip().capitalize()
        if texto not in self.MODALIDADES:
            raise ErrorDatosInvalidos(
                f"La modalidad '{valor}' no es válida. Opciones: {', '.join(self.MODALIDADES)}."
            )
        self.__modalidad = texto

    def validar_parametros(self):
        if self.especialidad == "":
            raise ErrorDatosInvalidos("La asesoría debe tener una especialidad definida.")
        if self.nivel not in self.FACTORES_NIVEL:
            raise ErrorDatosInvalidos("La asesoría debe tener un nivel de complejidad válido.")
        if self.modalidad not in self.MODALIDADES:
            raise ErrorDatosInvalidos("La asesoría debe tener una modalidad válida.")
        return True

    def calcular_costo(self, duracion, descuento=None, impuesto=None):
        horas = self._verificar_duracion(duracion)
        tarifa_hora = self.tarifa_base * self.FACTORES_NIVEL[self.nivel]

        # La asesoría presencial incluye desplazamiento del especialista.
        if self.modalidad == "Presencial":
            tarifa_hora *= 1 + self.RECARGO_PRESENCIAL

        return self._aplicar_ajustes(tarifa_hora * horas, descuento, impuesto)

    def describir_servicio(self):
        return (
            f"Asesoría en {self.especialidad.lower()}, nivel {self.nivel.lower()}, "
            f"modalidad {self.modalidad.lower()}"
        )


# ---------------------------------------------------------------------------
# 6. Reserva
# ---------------------------------------------------------------------------
class Reserva(EntidadBase):
    """Reserva de un servicio por parte de un cliente.

    El estado solo avanza por las transiciones permitidas:
    PENDIENTE -> CONFIRMADA -> PROCESADA, y PENDIENTE o CONFIRMADA -> CANCELADA.
    """

    ESTADOS = ("PENDIENTE", "CONFIRMADA", "CANCELADA", "PROCESADA")
    DURACION_MAXIMA = 720

    def __init__(self, cliente, servicio, duracion, descuento=None, impuesto=None):
        super().__init__("RES")

        if not isinstance(cliente, Cliente):
            raise ErrorReservaInvalida("La reserva necesita un cliente registrado.")
        if not isinstance(servicio, Servicio):
            raise ErrorReservaInvalida("La reserva necesita un servicio registrado.")

        self._cliente = cliente
        self._servicio = servicio
        self._duracion = None
        self.duracion = duracion
        self._descuento = descuento
        self._impuesto = impuesto
        self._estado = "PENDIENTE"
        self._costo_total = 0.0

        self.validar()
        self._costo_total = self._calcular_costo()

    @property
    def cliente(self):
        return self._cliente

    @property
    def servicio(self):
        return self._servicio

    @property
    def duracion(self):
        return self._duracion

    @duracion.setter
    def duracion(self, valor):
        if valor is None:
            raise ErrorReservaInvalida("La duración de la reserva es obligatoria.")
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ErrorReservaInvalida(f"La duración '{valor}' debe ser numérica.")
        if valor <= 0:
            raise ErrorReservaInvalida(
                f"La duración debe ser mayor que cero (recibido: {valor})."
            )
        if valor > self.DURACION_MAXIMA:
            raise ErrorReservaInvalida(
                f"La duración {valor} supera el máximo permitido ({self.DURACION_MAXIMA})."
            )
        self._duracion = float(valor)

    @property
    def estado(self):
        return self._estado

    @property
    def costo_total(self):
        return self._costo_total

    def _calcular_costo(self):
        # Polimorfismo: cada servicio resuelve su propia fórmula.
        return self._servicio.calcular_costo(
            self._duracion, self._descuento, self._impuesto
        )

    def _etiqueta_duracion(self):
        unidad = self._servicio.UNIDAD_COBRO
        return unidad if self._duracion == 1 else f"{unidad}s"

    def validar(self):
        if not self._servicio.disponible:
            raise ErrorServicioNoDisponible(
                f"El servicio '{self._servicio.nombre}' no está disponible para reservas."
            )
        self._cliente.validar()
        self._servicio.validar()
        if self._estado not in self.ESTADOS:
            raise ErrorReservaInvalida(f"El estado '{self._estado}' no es válido.")
        return True

    def confirmar(self):
        if self._estado == "CONFIRMADA":
            raise ErrorReservaInvalida(f"La reserva {self.identificador} ya está confirmada.")
        if self._estado != "PENDIENTE":
            raise ErrorReservaInvalida(
                f"La reserva {self.identificador} no puede confirmarse desde el estado {self._estado}."
            )
        self._estado = "CONFIRMADA"

    def cancelar(self):
        if self._estado == "CANCELADA":
            raise ErrorReservaInvalida(f"La reserva {self.identificador} ya estaba cancelada.")
        if self._estado == "PROCESADA":
            raise ErrorReservaInvalida(
                f"La reserva {self.identificador} ya fue procesada y no admite cancelación."
            )
        self._estado = "CANCELADA"

    def procesar(self):
        if self._estado == "PROCESADA":
            raise ErrorReservaInvalida(f"La reserva {self.identificador} ya fue procesada.")
        if self._estado != "CONFIRMADA":
            raise ErrorReservaInvalida(
                f"La reserva {self.identificador} debe confirmarse antes de procesarse "
                f"(estado actual: {self._estado})."
            )
        self._estado = "PROCESADA"

    def obtener_resumen(self):
        return (
            f"{self.identificador} | {self._cliente.nombre} | {self._servicio.nombre} | "
            f"{self._duracion:g} {self._etiqueta_duracion()} | {self._estado} | "
            f"costo {formatear_moneda(self._costo_total)}"
        )


# ---------------------------------------------------------------------------
# 7. Controlador
# ---------------------------------------------------------------------------
class GestorSoftwareFJ:
    """Controlador del sistema. Toda la información vive en listas internas."""

    def __init__(self, registro=None):
        self._clientes = []
        self._servicios = []
        self._reservas = []
        self._log = registro if registro is not None else GestorLog()

    @property
    def clientes(self):
        return list(self._clientes)

    @property
    def servicios(self):
        return list(self._servicios)

    @property
    def reservas(self):
        return list(self._reservas)

    # ------------------------------ búsquedas ------------------------------
    def _buscar_cliente(self, documento):
        texto = "" if documento is None else str(documento).strip()
        for cliente in self._clientes:
            if cliente.documento == texto:
                return cliente
        raise ErrorDatosInvalidos(
            f"No existe un cliente registrado con documento '{texto}'."
        )

    def _buscar_servicio(self, identificador):
        texto = "" if identificador is None else str(identificador).strip()
        for servicio in self._servicios:
            if servicio.identificador == texto:
                return servicio
        raise ErrorDatosInvalidos(
            f"No existe un servicio registrado con identificador '{texto}'."
        )

    # ------------------------------ clientes ------------------------------
    def registrar_cliente(self, documento, nombre, correo, telefono):
        """Registra un cliente. Usa try/except/else y conserva la excepción original."""
        try:
            cliente = Cliente(documento, nombre, correo, telefono)
            self._clientes.append(cliente)
        except ErrorDatosInvalidos as error:
            self._log.error(
                f"Cliente rechazado (documento='{documento}', nombre='{nombre}', "
                f"correo='{correo}'): {error}"
            )
            raise
        else:
            self._log.info(f"Cliente registrado: {cliente.obtener_resumen()}")
            return cliente

    # ------------------------------ servicios ------------------------------
    def crear_servicio(self, tipo, **datos):
        """Crea un servicio según su tipo. Usa try/except/finally."""
        try:
            clave = "" if tipo is None else str(tipo).strip().lower()
            if clave == "sala":
                servicio = ReservaSala(**datos)
            elif clave == "equipo":
                servicio = AlquilerEquipo(**datos)
            elif clave == "asesoria":
                servicio = AsesoriaEspecializada(**datos)
            else:
                raise ErrorDatosInvalidos(f"El tipo de servicio '{tipo}' no existe.")

            servicio.validar()
            self._servicios.append(servicio)
            return servicio

        except TypeError as error:
            # Un parámetro obligatorio ausente llega como TypeError; se traduce a
            # una excepción del dominio conservando el error original (chaining).
            mensaje = f"Faltan parámetros para crear el servicio de tipo '{tipo}': {error}"
            self._log.error(mensaje)
            raise ErrorDatosInvalidos(mensaje) from error
        except ErrorSistemaFJ as error:
            self._log.error(f"Servicio de tipo '{tipo}' rechazado: {error}")
            raise
        finally:
            self._log.info(f"Intento de creación de servicio finalizado (tipo='{tipo}').")

    def cambiar_disponibilidad(self, identificador_servicio, disponible):
        """Habilita o retira un servicio del catálogo comercial."""
        try:
            servicio = self._buscar_servicio(identificador_servicio)
            servicio.disponible = disponible
        except ErrorSistemaFJ as error:
            self._log.error(f"No se pudo cambiar la disponibilidad de '{identificador_servicio}': {error}")
            raise
        else:
            estado = "habilitado" if disponible else "fuera de servicio"
            self._log.advertencia(f"Servicio {servicio.identificador} {estado}.")
            return servicio

    # ------------------------------ reservas ------------------------------
    def crear_reserva(self, documento_cliente, identificador_servicio, duracion,
                      descuento=None, impuesto=None):
        """Crea una reserva. Combina try/except/else y encadenamiento de excepciones."""
        try:
            try:
                cliente = self._buscar_cliente(documento_cliente)
            except ErrorDatosInvalidos as error:
                raise ErrorReservaInvalida(
                    f"No se puede reservar: el cliente '{documento_cliente}' no está registrado."
                ) from error

            try:
                servicio = self._buscar_servicio(identificador_servicio)
            except ErrorDatosInvalidos as error:
                raise ErrorReservaInvalida(
                    f"No se puede reservar: el servicio '{identificador_servicio}' no existe."
                ) from error

            reserva = Reserva(cliente, servicio, duracion, descuento, impuesto)
            self._reservas.append(reserva)

        except ErrorCalculoCosto as error:
            mensaje = f"Reserva rechazada por inconsistencia en el costo: {error}"
            self._log.error(mensaje)
            raise ErrorReservaInvalida(mensaje) from error
        except (ErrorReservaInvalida, ErrorServicioNoDisponible) as error:
            self._log.advertencia(f"Reserva rechazada: {error}")
            raise
        else:
            self._log.info(
                f"Reserva creada: {reserva.obtener_resumen()} | "
                f"cliente {reserva.cliente.documento} | servicio {reserva.servicio.identificador}"
            )
            return reserva

    def confirmar_reserva(self, reserva):
        try:
            reserva.confirmar()
            self._log.info(
                f"Reserva {reserva.identificador} confirmada. "
                f"Costo total: {formatear_moneda(reserva.costo_total)}"
            )
        except ErrorReservaInvalida as error:
            self._log.advertencia(f"Confirmación rechazada: {error}")
            raise
        finally:
            self._log.info(
                f"Estado de la reserva {reserva.identificador} tras confirmación: {reserva.estado}."
            )

    def cancelar_reserva(self, reserva, motivo=""):
        try:
            reserva.cancelar()
            detalle = f" Motivo: {motivo}." if motivo else ""
            self._log.info(f"Reserva {reserva.identificador} cancelada.{detalle}")
        except ErrorReservaInvalida as error:
            self._log.advertencia(f"Cancelación rechazada: {error}")
            raise
        finally:
            self._log.info(
                f"Estado de la reserva {reserva.identificador} tras cancelación: {reserva.estado}."
            )

    def procesar_reserva(self, reserva):
        try:
            reserva.procesar()
            self._log.info(f"Reserva {reserva.identificador} procesada para facturación.")
        except ErrorReservaInvalida as error:
            self._log.advertencia(f"Procesamiento rechazado: {error}")
            raise
        finally:
            self._log.info(
                f"Estado de la reserva {reserva.identificador} tras procesamiento: {reserva.estado}."
            )

    # ------------------------------ reportes ------------------------------
    def totales_por_estado(self):
        totales = {estado: 0 for estado in Reserva.ESTADOS}
        for reserva in self._reservas:
            totales[reserva.estado] += 1
        return totales

    def ingresos_estimados(self):
        # Solo se factura lo confirmado y lo procesado; lo cancelado no genera ingreso.
        return round(
            sum(
                reserva.costo_total
                for reserva in self._reservas
                if reserva.estado in ("CONFIRMADA", "PROCESADA")
            ),
            2,
        )


# ---------------------------------------------------------------------------
# 8. Apoyo para la simulación
# ---------------------------------------------------------------------------
def ejecutar(numero, descripcion, funcion, *args, registro, **kwargs):
    """Ejecuta una operación de la simulación y continúa pase lo que pase.

    Es la red de seguridad de main(): ninguna excepción se propaga, pero todas
    quedan registradas en el archivo de logs.
    """
    print(f"\n[{numero:02d}] {descripcion}")
    try:
        resultado = funcion(*args, **kwargs)
    except ErrorSistemaFJ as error:
        print(f"     Rechazado -> {type(error).__name__}: {error}")
        registro.advertencia(f"Operación {numero:02d} rechazada: {type(error).__name__}: {error}")
        return None
    except Exception as error:  # último recurso: el programa no debe detenerse
        print(f"     Error no controlado -> {type(error).__name__}: {error}")
        registro.error(f"Operación {numero:02d} con error no controlado: {type(error).__name__}: {error}")
        return None
    else:
        # Los objetos se muestran con su resumen; así la consola queda legible.
        if hasattr(resultado, "obtener_resumen"):
            detalle = resultado.obtener_resumen()
        elif resultado is None:
            detalle = "operación completada"
        else:
            detalle = str(resultado)
        print(f"     OK -> {detalle}")
        return resultado


def demostrar_sobrecarga(servicio, duracion, registro):
    """Muestra las tres variantes de calcular_costo sobre el mismo servicio."""
    variantes = [
        ("a) tarifa base por duración", servicio.calcular_costo(duracion)),
        ("b) tarifa con descuento del 10%", servicio.calcular_costo(duracion, 0.10)),
        ("c) tarifa con descuento e IVA del 19%", servicio.calcular_costo(duracion, 0.10, IVA_DEFECTO)),
    ]
    for etiqueta, valor in variantes:
        print(f"     {etiqueta}: {formatear_moneda(valor)}")
        registro.info(
            f"Sobrecarga de costo en {servicio.identificador} - {etiqueta}: {formatear_moneda(valor)}"
        )
    return f"{len(variantes)} variantes calculadas sobre {servicio.nombre}"


def cabecera(texto):
    print("\n" + "=" * 78)
    print(texto)
    print("=" * 78)


# ---------------------------------------------------------------------------
# 9. Simulación principal
# ---------------------------------------------------------------------------
def main():
    registro = GestorLog(ARCHIVO_LOG)
    registro.info("=" * 60)
    registro.info("Inicio de la simulación de Software FJ (Fase 4).")

    cabecera("SOFTWARE FJ - GESTIÓN DE CLIENTES, SERVICIOS Y RESERVAS")
    print(f"Fecha de ejecución: {datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"Archivo de auditoría: {os.path.abspath(ARCHIVO_LOG)}")

    gestor = GestorSoftwareFJ(registro)

    # ------------------------- clientes -------------------------
    cabecera("BLOQUE 1. REGISTRO DE CLIENTES")

    cliente_laura = ejecutar(
        1, "Cliente válido: Laura Gómez",
        gestor.registrar_cliente,
        "1024567890", "Laura Gómez", "laura.gomez@correo.com", "3001234567",
        registro=registro,
    )

    cliente_carlos = ejecutar(
        2, "Cliente válido: Carlos Ramírez",
        gestor.registrar_cliente,
        "79543210", "Carlos Ramírez", "carlos.ramirez@correo.com", "3109876543",
        registro=registro,
    )

    cliente_andrea = ejecutar(
        3, "Cliente válido: Andrea Torres",
        gestor.registrar_cliente,
        "1123456789", "Andrea Torres", "andrea.torres@correo.com", "3205554433",
        registro=registro,
    )

    ejecutar(
        4, "Cliente inválido: correo sin arroba ni dominio",
        gestor.registrar_cliente,
        "1030456789", "Juan Pérez", "juan.perezcorreo.com", "3012223344",
        registro=registro,
    )

    ejecutar(
        5, "Cliente inválido: documento vacío",
        gestor.registrar_cliente,
        "", "Marta Salazar", "marta.salazar@correo.com", "3127778899",
        registro=registro,
    )

    # ------------------------- servicios -------------------------
    cabecera("BLOQUE 2. CREACIÓN DEL CATÁLOGO DE SERVICIOS")

    sala = ejecutar(
        6, "Servicio válido: sala grande con equipamiento audiovisual",
        gestor.crear_servicio, "sala",
        nombre="Sala Aurora", tarifa_base=45_000, capacidad=40, equipamiento=True,
        registro=registro,
    )

    equipo = ejecutar(
        7, "Servicio válido: alquiler de dos video beams con seguro",
        gestor.crear_servicio, "equipo",
        nombre="Alquiler de video beam", tarifa_base=38_000,
        tipo_equipo="Video beam", cantidad=2, seguro=True,
        registro=registro,
    )

    asesoria = ejecutar(
        8, "Servicio válido: asesoría presencial de nivel alto",
        gestor.crear_servicio, "asesoria",
        nombre="Asesoría en redes", tarifa_base=85_000,
        especialidad="Redes y conectividad", nivel="Alto", modalidad="Presencial",
        registro=registro,
    )

    ejecutar(
        9, "Servicio inválido: tarifa base negativa",
        gestor.crear_servicio, "sala",
        nombre="Sala subterránea", tarifa_base=-20_000, capacidad=10,
        registro=registro,
    )

    ejecutar(
        10, "Servicio inválido: parámetro faltante (capacidad de la sala)",
        gestor.crear_servicio, "sala",
        nombre="Sala sin aforo", tarifa_base=30_000, capacidad=None,
        registro=registro,
    )

    # ------------------------- sobrecarga -------------------------
    cabecera("BLOQUE 3. SOBRECARGA DEL CÁLCULO DE COSTOS")
    if sala is not None:
        ejecutar(
            11, "Tres variantes de costo para 4 horas de 'Sala Aurora'",
            demostrar_sobrecarga, sala, 4, registro,
            registro=registro,
        )

    # ------------------------- reservas -------------------------
    cabecera("BLOQUE 4. RESERVAS EXITOSAS")

    reserva_laura = None
    if cliente_laura is not None and sala is not None:
        reserva_laura = ejecutar(
            12, "Reserva de la sala por 4 horas, con descuento del 10% e IVA",
            gestor.crear_reserva,
            cliente_laura.documento, sala.identificador, 4, 0.10, IVA_DEFECTO,
            registro=registro,
        )

    if reserva_laura is not None:
        ejecutar(13, "Confirmar la reserva de Laura", gestor.confirmar_reserva,
                 reserva_laura, registro=registro)
        ejecutar(14, "Procesar la reserva de Laura", gestor.procesar_reserva,
                 reserva_laura, registro=registro)

    reserva_carlos = None
    if cliente_carlos is not None and equipo is not None:
        reserva_carlos = ejecutar(
            15, "Reserva de dos video beams por 3 días, sin descuento",
            gestor.crear_reserva,
            cliente_carlos.documento, equipo.identificador, 3,
            registro=registro,
        )

    if reserva_carlos is not None:
        ejecutar(16, "Confirmar la reserva de Carlos", gestor.confirmar_reserva,
                 reserva_carlos, registro=registro)
        ejecutar(17, "Cancelar la reserva de Carlos antes del evento",
                 gestor.cancelar_reserva, reserva_carlos,
                 "el cliente reprogramó la actividad", registro=registro)

    reserva_andrea = None
    if cliente_andrea is not None and asesoria is not None:
        reserva_andrea = ejecutar(
            18, "Reserva de asesoría por 2 horas",
            gestor.crear_reserva,
            cliente_andrea.documento, asesoria.identificador, 2,
            registro=registro,
        )

    if reserva_andrea is not None:
        ejecutar(19, "Confirmar la reserva de Andrea", gestor.confirmar_reserva,
                 reserva_andrea, registro=registro)

    # ------------------------- fallos controlados -------------------------
    cabecera("BLOQUE 5. OPERACIONES RECHAZADAS (FALLOS CONTROLADOS)")

    if sala is not None:
        ejecutar(
            20, "Retirar temporalmente la sala por mantenimiento",
            gestor.cambiar_disponibilidad, sala.identificador, False,
            registro=registro,
        )

    if cliente_andrea is not None and sala is not None:
        ejecutar(
            21, "Reserva sobre un servicio no disponible (debe fallar)",
            gestor.crear_reserva,
            cliente_andrea.documento, sala.identificador, 2,
            registro=registro,
        )

    if sala is not None:
        ejecutar(
            22, "Devolver la sala al catálogo",
            gestor.cambiar_disponibilidad, sala.identificador, True,
            registro=registro,
        )

    if cliente_laura is not None and equipo is not None:
        ejecutar(
            23, "Reserva con duración cero (debe fallar)",
            gestor.crear_reserva,
            cliente_laura.documento, equipo.identificador, 0,
            registro=registro,
        )

    if reserva_laura is not None:
        ejecutar(
            24, "Cancelar una reserva ya procesada (debe fallar)",
            gestor.cancelar_reserva, reserva_laura,
            "el cliente cambió de opinión", registro=registro,
        )

    ejecutar(
        25, "Reserva con un cliente inexistente (debe fallar)",
        gestor.crear_reserva,
        "999999999", asesoria.identificador if asesoria else "SRV-0003", 2,
        registro=registro,
    )

    if cliente_carlos is not None and asesoria is not None:
        ejecutar(
            26, "Reserva con descuento fuera de política (60%)",
            gestor.crear_reserva,
            cliente_carlos.documento, asesoria.identificador, 2, 0.60,
            registro=registro,
        )

    ejecutar(
        27, "Servicio de un tipo que no existe en el catálogo",
        gestor.crear_servicio, "transporte",
        nombre="Traslado de equipos", tarifa_base=60_000,
        registro=registro,
    )

    # ------------------------- resumen -------------------------
    cabecera("RESUMEN FINAL DEL ESTADO EN MEMORIA")

    print(f"Clientes registrados: {len(gestor.clientes)}")
    for cliente in gestor.clientes:
        print(f"  - {cliente.obtener_resumen()}")

    print(f"\nServicios en catálogo: {len(gestor.servicios)}")
    for servicio in gestor.servicios:
        print(f"  - {servicio.obtener_resumen()}")

    print(f"\nReservas registradas: {len(gestor.reservas)}")
    for reserva in gestor.reservas:
        print(f"  - {reserva.obtener_resumen()}")

    print("\nReservas por estado:")
    for estado, cantidad in gestor.totales_por_estado().items():
        print(f"  {estado}: {cantidad}")

    print(f"\nIngresos estimados (confirmadas y procesadas): {formatear_moneda(gestor.ingresos_estimados())}")
    print(f"Eventos registrados en: {ARCHIVO_LOG}")
    print("\nEl sistema terminó sin interrupciones.")

    registro.info(f"Clientes en memoria: {len(gestor.clientes)}")
    registro.info(f"Servicios en memoria: {len(gestor.servicios)}")
    registro.info(f"Reservas en memoria: {len(gestor.reservas)}")
    registro.info(f"Estados de las reservas: {gestor.totales_por_estado()}")
    registro.info(f"Ingresos estimados: {formatear_moneda(gestor.ingresos_estimados())}")
    registro.info("Fin de la simulación. El sistema terminó sin interrupciones.")
    registro.cerrar()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
