# bot.py

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

from config import TOKEN, ADMIN_ID
from database import (
    inicializar_configuracion,
    obtener_configuracion,
    obtener_o_crear_usuario,
    usuario_esta_bloqueado,
    verificar_conflicto,
    guardar_registro,
    resetear_evento,
    cerrar_evento,
    obtener_registros,
    guardar_hora_inicio,
    obtener_hora_inicio
)

ESPERANDO_NOMBRE = 1
ESPERANDO_TIEMPO = 2
ESPERANDO_HORA_INICIO = 3
ESPERANDO_HORA_FINAL = 4


def convertir_a_minutos(texto):
    try:
        partes = texto.strip().split(":")
        if len(partes) != 2:
            return None
        horas = int(partes[0])
        minutos = int(partes[1])
        if minutos < 0 or minutos > 59:
            return None
        return horas * 60 + minutos
    except ValueError:
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    config = obtener_configuracion()
    if not config.sistema_abierto:
        await update.message.reply_text(
            "El sistema esta cerrado en este momento. "
            "Espera a que el administrador abra un nuevo evento."
        )
        return ConversationHandler.END

    if usuario_esta_bloqueado(telegram_id):
        await update.message.reply_text(
            "Ya tienes un dato registrado en este evento. "
            "Espera al siguiente evento para ingresar uno nuevo."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Hola! Bienvenido al sistema de registro.\n"
        "Para comenzar, cual es tu nombre?"
    )
    return ESPERANDO_NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()

    if len(nombre) < 2:
        await update.message.reply_text(
            "Ese nombre parece muy corto. Por favor escribe tu nombre completo."
        )
        return ESPERANDO_NOMBRE

    telegram_id = update.effective_user.id
    obtener_o_crear_usuario(telegram_id, nombre)
    context.user_data["nombre"] = nombre

    await update.message.reply_text(
        f"Mucho gusto, {nombre}.\n"
        f"Ahora ingresa el tiempo en formato H:MM\n"
        f"Ejemplo: 1:25"
    )
    return ESPERANDO_TIEMPO


async def recibir_tiempo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    telegram_id = update.effective_user.id
    nombre = context.user_data.get("nombre", "Usuario")

    minutos = convertir_a_minutos(texto)

    if minutos is None:
        await update.message.reply_text(
            "El formato no es valido. Por favor usa el formato H:MM\n"
            "Ejemplo: 1:25 o 0:45"
        )
        return ESPERANDO_TIEMPO

    if verificar_conflicto(minutos):
        await update.message.reply_text(
            f"El tiempo {texto} ya esta ocupado o esta muy cerca de uno registrado.\n"
            f"Por favor intenta con otro tiempo."
        )
        return ESPERANDO_TIEMPO

    from config import RANGO_MINUTOS
    rango = []
    for i in range(-RANGO_MINUTOS, RANGO_MINUTOS + 1):
        total = minutos + i
        horas = total // 60
        mins = total % 60
        rango.append(f"{horas}:{mins:02d}")

    rango_texto = ", ".join(rango)

    guardar_registro(telegram_id, nombre, texto, minutos, rango_texto)

    await update.message.reply_text(
        f"Registro exitoso, {nombre}!\n"
        f"Tiempo registrado: {texto}\n"
        f"Rango bloqueado: {rango_texto}\n\n"
        f"Ya no podras ingresar mas datos en este evento."
    )
    return ConversationHandler.END


async def nuevo_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):
    telegram_id = update.effective_user.id

    if telegram_id != ADMIN_ID:
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return

    resetear_evento()

    config = obtener_configuracion()
    await update.message.reply_text(
        f"Nuevo evento iniciado.\n"
        f"Evento numero: {config.numero_evento}\n"
        f"Todos los usuarios pueden volver a registrar un tiempo."
    )


async def terminar_evento(update: Update, context: ContextTypes.DEFAULT_TYPE):

    telegram_id = update.effective_user.id

    if telegram_id != ADMIN_ID:
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return

    config = obtener_configuracion()
    if not config.sistema_abierto:
        await update.message.reply_text("El evento ya esta cerrado.")
        return

    cerrar_evento()

    await update.message.reply_text(
        "Evento cerrado.\n"
        "No se aceptaran mas registros hasta que se inicie un nuevo evento con /nuevo_evento."
    )


async def ver_registros(update: Update, context: ContextTypes.DEFAULT_TYPE):

    registros = obtener_registros()

    if not registros:
        await update.message.reply_text(
            "No hay tiempos registrados en este evento todavia."
        )
        return

    mensaje = "Tiempos registrados en este evento:\n\n"
    for i, registro in enumerate(registros, start=1):
        mensaje += f"{i}. Participante: {registro.nombre_usuario}\n"
        mensaje += f"   Tiempo: {registro.tiempo_original}\n"
        mensaje += f"   Rango bloqueado: {registro.rango_bloqueado}\n\n"

    await update.message.reply_text(mensaje)


async def iniciar_tiempo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Solo el administrador puede usar este comando.
    Le pide una hora de referencia y la guarda en la base de datos.
    """
    telegram_id = update.effective_user.id

    if telegram_id != ADMIN_ID:
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return ConversationHandler.END

    await update.message.reply_text(
        "Ingresa la hora de inicio en formato H:MM\n"
        "Ejemplo: 14:30"
    )
    return ESPERANDO_HORA_INICIO


async def recibir_hora_inicio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe la hora de inicio que ingresa el administrador y la guarda.
    """
    texto = update.message.text.strip()
    minutos = convertir_a_minutos(texto)

    if minutos is None:
        await update.message.reply_text(
            "El formato no es valido. Por favor usa el formato H:MM\n"
            "Ejemplo: 14:30"
        )
        return ESPERANDO_HORA_INICIO

    guardar_hora_inicio(texto)

    await update.message.reply_text(
        f"Hora de inicio guardada: {texto}\n"
        f"Ya puedes usar /tiempo_transcurrido o /tiempo_entre."
    )
    return ConversationHandler.END


async def tiempo_transcurrido(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Disponible para todos los usuarios.
    Calcula cuanto tiempo ha pasado desde la hora de inicio guardada.
    """
    hora_inicio = obtener_hora_inicio()

    if not hora_inicio:
        await update.message.reply_text(
            "El administrador aun no ha registrado una hora de inicio."
        )
        return

    minutos_inicio = convertir_a_minutos(hora_inicio)

    # Obtenemos la hora actual del sistema
    from datetime import datetime
    ahora = datetime.now()
    minutos_ahora = ahora.hour * 60 + ahora.minute
    # datetime.now() devuelve la hora actual del servidor
    # .hour y .minute extraen las partes que necesitamos

    diferencia = minutos_ahora - minutos_inicio

    if diferencia < 0:
        # Esto pasa si la hora de inicio es mayor a la hora actual
        await update.message.reply_text(
            "La hora actual es menor a la hora de inicio registrada.\n"
            "Verifica que la hora de inicio sea correcta."
        )
        return

    horas = diferencia // 60
    minutos = diferencia % 60

    await update.message.reply_text(
        f"Hora de inicio: {hora_inicio}\n"
        f"Hora actual: {ahora.hour}:{ahora.minute:02d}\n"
        f"Tiempo transcurrido: {horas} horas con {minutos} minutos"
    )


async def tiempo_entre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Solo el administrador puede usar este comando.
    Pide una hora final y calcula el tiempo entre la hora de inicio y esa hora.
    """
    telegram_id = update.effective_user.id

    if telegram_id != ADMIN_ID:
        await update.message.reply_text("No tienes permisos para usar este comando.")
        return ConversationHandler.END

    hora_inicio = obtener_hora_inicio()

    if not hora_inicio:
        await update.message.reply_text(
            "Primero debes registrar una hora de inicio con /iniciar_tiempo."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"Hora de inicio registrada: {hora_inicio}\n"
        f"Ingresa la hora final en formato H:MM\n"
        f"Ejemplo: 16:45"
    )
    return ESPERANDO_HORA_FINAL


async def recibir_hora_final(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Recibe la hora final y calcula la diferencia con la hora de inicio.
    """
    texto = update.message.text.strip()
    minutos_final = convertir_a_minutos(texto)

    if minutos_final is None:
        await update.message.reply_text(
            "El formato no es valido. Por favor usa el formato H:MM\n"
            "Ejemplo: 16:45"
        )
        return ESPERANDO_HORA_FINAL

    hora_inicio = obtener_hora_inicio()
    minutos_inicio = convertir_a_minutos(hora_inicio)

    diferencia = minutos_final - minutos_inicio

    if diferencia < 0:
        await update.message.reply_text(
            "La hora final no puede ser menor a la hora de inicio.\n"
            "Intenta de nuevo con una hora mayor."
        )
        return ESPERANDO_HORA_FINAL

    horas = diferencia // 60
    minutos = diferencia % 60

    await update.message.reply_text(
        f"Hora de inicio: {hora_inicio}\n"
        f"Hora final: {texto}\n"
        f"Tiempo transcurrido: {horas} horas con {minutos} minutos"
    )
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Proceso cancelado. Escribe /start para comenzar de nuevo."
    )
    return ConversationHandler.END


def main():
    inicializar_configuracion()

    app = Application.builder().token(TOKEN).build()

    # Flujo de registro de participantes
    conv_registro = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ESPERANDO_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            ESPERANDO_TIEMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tiempo)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Flujo para guardar hora de inicio
    conv_hora_inicio = ConversationHandler(
        entry_points=[CommandHandler("iniciar_tiempo", iniciar_tiempo)],
        states={
            ESPERANDO_HORA_INICIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_inicio)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Flujo para calcular tiempo entre dos horas
    conv_tiempo_entre = ConversationHandler(
        entry_points=[CommandHandler("tiempo_entre", tiempo_entre)],
        states={
            ESPERANDO_HORA_FINAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_hora_final)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    # Registramos cada flujo por separado
    app.add_handler(conv_registro)
    app.add_handler(conv_hora_inicio)
    app.add_handler(conv_tiempo_entre)

    # Comandos simples que no necesitan flujo de conversación
    app.add_handler(CommandHandler("nuevo_evento", nuevo_evento))
    app.add_handler(CommandHandler("terminar_evento", terminar_evento))
    app.add_handler(CommandHandler("ver_registros", ver_registros))
    app.add_handler(CommandHandler("tiempo_transcurrido", tiempo_transcurrido))

    print("Bot iniciado. Presiona Ctrl+C para detenerlo.")
    app.run_polling()


if __name__ == "__main__":
    main()
