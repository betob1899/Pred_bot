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
    resetear_evento
)

ESPERANDO_NOMBRE = 1
ESPERANDO_TIEMPO = 2


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


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Proceso cancelado. Escribe /start para comenzar de nuevo."
    )
    return ConversationHandler.END


def main():
    inicializar_configuracion()

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            ESPERANDO_NOMBRE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            ESPERANDO_TIEMPO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_tiempo)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("nuevo_evento", nuevo_evento))

    print("Bot iniciado. Presiona Ctrl+C para detenerlo.")
    app.run_polling()


if __name__ == "__main__":
    main()
