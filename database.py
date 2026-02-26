from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, sessionmaker

class Base(DeclarativeBase):
    pass

class Usuario(Base):
    __tablename__ = "Participantes"  

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Integer, unique=True)

    nombre = Column(String)

    bloqueado = Column(Boolean, default=False)

class Registro(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True)

    telegram_id = Column(Integer)

    nombre_usuario = Column(String)

    tiempo_original = Column(String)

    minutos_totales = Column(Integer)

    rango_bloqueado = Column(String)

class Configuracion(Base):
    __tablename__ = "configuracion"

    id = Column(Integer, primary_key=True)

    sistema_abierto = Column(Boolean, default=True)

    numero_evento = Column(Integer, default=1)

engine = create_engine("sqlite:///bot_datos.db")

Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def inicializar_configuracion():
    session = Session()
    config = session.query(Configuracion).first()
    if not config:
        nueva_config = Configuracion()
        session.add(nueva_config)
        session.commit()
    session.close()

def obtener_configuracion():
    session = Session()
    config = session.query(Configuracion).first()
    session.close()
    return config

def obtener_o_crear_usuario(telegram_id, nombre=None):
    session = Session()
    usuario = session.query(Usuario).filter_by(telegram_id=telegram_id).first()
    if not usuario:
        usuario = Usuario(telegram_id=telegram_id, nombre=nombre)
        session.add(usuario)
        session.commit()
        session.refresh(usuario)

    session.close()
    return usuario

def usuario_esta_bloqueado(telegram_id):
    session = Session()
    usuario = session.query(Usuario).filter_by(telegram_id=telegram_id).first()
    session.close()
    if usuario:
        return usuario.bloqueado
    return False

def verificar_conflicto(minutos):
    from config import RANGO_MINUTOS
    session = Session()
    registros = session.query(Registro).all()

    # Generamos todos los minutos que ocuparía el nuevo registro
    rango_nuevo = set(range(minutos - RANGO_MINUTOS, minutos + RANGO_MINUTOS + 1))
    # set() es un conjunto, útil para comparar grupos de valores rápidamente
    # range(83, 88) genera: 83, 84, 85, 86, 87

    for registro in registros:
        # Generamos el rango del registro existente
        rango_existente = set(range(
            registro.minutos_totales - RANGO_MINUTOS,
            registro.minutos_totales + RANGO_MINUTOS + 1
        ))

        if rango_nuevo & rango_existente:

            session.close()
            return True

    session.close()
    return False

def guardar_registro(telegram_id, nombre, tiempo_original, minutos_totales, rango_bloqueado):
    session = Session()

    nuevo_registro = Registro(
        telegram_id=telegram_id,
        nombre_usuario=nombre,
        tiempo_original=tiempo_original,
        minutos_totales=minutos_totales,
        rango_bloqueado=rango_bloqueado  
    )
    session.add(nuevo_registro)

    usuario = session.query(Usuario).filter_by(telegram_id=telegram_id).first()
    if usuario:
        usuario.bloqueado = True

    session.commit()
    session.close()

def resetear_evento():
    session = Session()

    session.query(Registro).delete()

    session.query(Usuario).update({"bloqueado": False})

    config = session.query(Configuracion).first()
    if config:
        config.numero_evento += 1

    session.commit()
    session.close()

