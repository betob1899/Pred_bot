# 🤖 Pred Bot — Bot Predictor de Tiempos para Telegram

Bot de Telegram que permite a los usuarios registrar predicciones de tiempo para eventos. Cada participante puede registrar un tiempo único por evento, con validación de conflictos por proximidad.

## ✨ Características

- **Registro conversacional** — Flujo guiado paso a paso (nombre → tiempo)
- **Validación de conflictos** — Impide registros con tiempos demasiado cercanos entre sí
- **Bloqueo por evento** — Cada usuario solo puede participar una vez por evento
- **Gestión de eventos** — El administrador puede iniciar nuevos eventos con `/nuevo_evento`
- **Base de datos persistente** — Almacenamiento con SQLite + SQLAlchemy

## 📋 Requisitos

- Python 3.10+
- Una cuenta de bot en Telegram (creada con [@BotFather](https://t.me/BotFather))

## 🚀 Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/betob1899/Pred_bot.git
cd Pred_bot
```

### 2. Instalar dependencias

```bash
pip install python-telegram-bot sqlalchemy
```

### 3. Configurar credenciales

Crea un archivo `config.py` en la raíz del proyecto con el siguiente contenido:

```python
TOKEN = "TU_TOKEN_DE_TELEGRAM"

ADMIN_ID = 123456789  # Tu Telegram ID numérico

RANGO_MINUTOS = 2  # Margen de proximidad entre tiempos
```

> ⚠️ **Importante:** `config.py` está en `.gitignore` y **no se sube al repositorio** para proteger tus credenciales.

### 4. Ejecutar el bot

```bash
python bot.py
```

## 💬 Comandos

| Comando | Descripción | Acceso |
|---------|-------------|--------|
| `/start` | Inicia el flujo de registro | Todos |
| `/cancelar` | Cancela el registro en curso | Todos |
| `/nuevo_evento` | Resetea el evento e inicia uno nuevo | Solo admin |

## 🏗️ Estructura del proyecto

```
Pred_bot/
├── bot.py          # Lógica principal del bot y handlers
├── database.py     # Modelos de base de datos y operaciones
├── config.py       # Credenciales y configuración (no incluido)
├── .gitignore      # Archivos excluidos del repositorio
└── README.md       # Este archivo
```

## 📖 ¿Cómo funciona?

1. El admin inicia un evento con `/nuevo_evento`
2. Los usuarios escriben `/start` para comenzar a registrar
3. El bot pide el **nombre** del participante
4. El bot pide el **tiempo** en formato `H:MM` (ej: `1:25`)
5. Se valida que el tiempo no esté en conflicto con otros registros
6. Se guarda el registro y el usuario queda bloqueado hasta el siguiente evento

## 📄 Licencia

Este proyecto es de uso privado.
