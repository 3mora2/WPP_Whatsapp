# WPP_Whatsapp
<p align="center">
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="PyPI Version" src="https://img.shields.io/pypi/v/WPP_Whatsapp.svg?maxAge=86400" /></a>
  <a href="https://pypi.org/project/WPP-Whatsapp"><img alt="View" src="https://static.pepy.tech/personalized-badge/WPP_Whatsapp?period=total&units=international_system&left_text=Downloads"/></a>
  <a href="https://github.com/3mora2/WPP_Whatsapp/actions"><img alt="GitHub Actions" src="https://github.com/3mora2/WPP_Whatsapp/actions/workflows/python-publish.yml/badge.svg" /></a>
  <a href="https://python.org"><img alt="Python Version" src="https://img.shields.io/badge/python-3.9+-blue.svg" /></a>
</p>

**WPP_Whatsapp** es una potente librería de Python construida sobre [WPPConnect](https://github.com/wppconnect-team/wppconnect), que lleva la automatización de WhatsApp Web a los desarrolladores de Python.

> 💡 **¿Buscas algo más?** Echa un vistazo a [neonize](https://github.com/krypton-byte/neonize) - Una potente librería de Python construida sobre **Whatsmeow**, que permite una automatización de WhatsApp fluida con rendimiento de grado empresarial.

📚 **¿Buscas la documentación?** Consulta nuestra [Documentación Completa](docs/README.md)

---

## ✨ Características

| Característica | Estado |
|----------------|--------|
| Actualización automática de QR | ✅ |
| Enviar **texto, imágenes, videos, audio, documentos** | ✅ |
| Obtener **contactos, chats, grupos, miembros de grupo** | ✅ |
| Enviar contactos, stickers, ubicaciones | ✅ |
| Soporte para múltiples sesiones | ✅ |
| Reenviar mensajes | ✅ |
| Recibir mensajes con Callbacks | ✅ |
| Gestión de grupos | ✅ |
| Funciones de Business | ✅ |
| Limitación de tasa (Rate Limiting) | ✅ |

---

## 🚀 Inicio Rápido

### Instalación

**Usando pip:**
```bash
pip install wpp-whatsapp
```

**Usando uv (Recomendado):**
```bash
uv add wpp-whatsapp
```

### Tu primer Bot (2 minutos)

```python
from WPP_Whatsapp import Create

# Crear e iniciar cliente
creator = Create(session="mybot")

client = creator.start()
# Definir manejador de mensajes
def on_message(msg):
    if msg.get('body') and not msg.get('isGroupMsg'):
        # Respuesta automática
        client.sendText(msg.get('from'), "¡Gracias por tu mensaje! 🤖")

# Registrar manejador
client.on_message(on_message)

# Iniciar bot
print("¡Bot iniciado! Escanea el código QR...")
client.start()
```

**¡Eso es todo!** ¡Tu bot de WhatsApp ya está funcionando! 🎉

---

## 📚 Documentación

Hemos creado una documentación exhaustiva para ayudarte:

- 📘 **[Guía de Inicio Rápido](docs/QUICKSTART.md)** - Empieza en 5 minutos
- 📖 **[Referencia de la API](docs/API_REFERENCE.md)** - Documentación completa de métodos
- 🔧 **[Solución de Problemas](docs/TROUBLESHOOTING.md)** - Problemas comunes y soluciones
- 💡 **[Ejemplos](examples/README.md)** - Ejemplos de código para cada caso de uso
- ⚡ **[Ejemplos Avanzados](scripts/README.md)** - Patrones y características avanzadas

**Empieza aquí:** [Índice de Documentación Completa](docs/README.md)

---

## 💡 Ejemplos

### Enviar Mensajes

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()
# Enviar texto
client.sendText("1234567890@c.us", "¡Hola!")

# Enviar imagen
client.sendImage("1234567890@c.us", "image.jpg", "¡Bello atardecer!")

# Enviar archivo
client.sendFile("1234567890@c.us", "document.pdf", "Aquí tienes el documento")

# Enviar ubicación
client.sendLocation("1234567890@c.us", 40.7128, -74.0060, title="Nueva York")
```

### Recibir Mensajes

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()

def on_message(message):
    # Ignorar mensajes de grupo
    if message.get('isGroupMsg'):
        return
    
    # Procesar mensaje
    chat_id = message.get('from')
    text = message.get('body')
    
    if 'hola' in text.lower():
        client.sendText(chat_id, "¡Hola! 👋")

client.on_message(on_message)
client.start()
```

### Gestión de Grupos

```python
from WPP_Whatsapp import Create

creator = Create(session="test")
client = creator.start()

# Crear grupo
group = client.createGroup("Mi Grupo", ["123@c.us", "456@c.us"])

# Añadir participante
client.addParticipant(group['gid'], "789@c.us")

# Enviar mensaje al grupo
client.sendText(group['gid'], "¡Hola a todos!")
```

### Más Ejemplos

- 📂 **[Ejemplos Básicos](examples/README.md)** - Funcionalidades principales
- ⚡ **[Ejemplos Avanzados](scripts/README.md)** - Patrones complejos
- 🗂️ **[Archivo](archive/examples/README.md)** - Ejemplos adicionales

---

## 🎯 Casos de Uso

WPP_Whatsapp puede usarse para:

- 🤖 **Chatbots** - Automatización de servicio al cliente
- 📢 **Difusión** - Mensajería masiva segura con limitación de tasa
- 👥 **Gestión de Grupos** - Administración automatizada de grupos
- 📊 **Analítica** - Seguimiento de mensajes y estadísticas
- 🔄 **Integración** - Conectar WhatsApp con otros servicios
- 📱 **Auto-respuestas** - Sistemas de respuesta inteligentes

---

## ⚠️ Notas Importantes

### Limitación de Tasa (Rate Limiting)
Usa siempre la limitación de tasa para operaciones masivas para evitar baneos:
```python
import time

contacts = ["123@c.us", "456@c.us"]
for contact in contacts:
    client.sendText(contact, "Hola")
    time.sleep(2)  # Retraso de 2 segundos
```

### Buenas Prácticas
- ✅ Maneja los errores con elegancia
- ✅ Usa nombres de sesión únicos
- ✅ Implementa lógica de reconexión
- ✅ Prueba primero con grupos pequeños
- ✅ Respeta los términos de servicio de WhatsApp

---

## 🆘 ¿Necesitas Ayuda?

### Documentación
- 📚 [Documentación Completa](docs/README.md)
- 🚀 [Guía de Inicio Rápido](docs/QUICKSTART.md)
- 🔧 [Solución de Problemas](docs/TROUBLESHOOTING.md)

### Comunidad
- 💬 [Discusiones de GitHub](https://github.com/3mora2/WPP_Whatsapp/discussions)
- 🐛 [Reportar Problemas](https://github.com/3mora2/WPP_Whatsapp/issues)
- 💡 [Solicitud de Funciones](https://github.com/3mora2/WPP_Whatsapp/issues)

---

## 📦 Estructura del Proyecto

```
WPP_Whatsapp/
├── WPP_Whatsapp/      # Paquete principal
├── docs/              # Documentación
├── examples/          # Ejemplos básicos
├── scripts/           # Ejemplos avanzados
├── archive/           # Ejemplos adicionales
├── tests/             # Suite de pruebas
├── README.md          # Este archivo
├── pyproject.toml     # Configuración del proyecto
└── CHANGELOG.md       # Historial de versiones
```

---

## 🤝 Contribución

¡Bienvenidas las contribuciones! Aquí tienes cómo puedes ayudar:

- 📝 Mejorar la documentación
- 🐛 Reportar errores
- 💡 Sugerir funciones
- 🔧 Enviar pull requests
- 📚 Añadir ejemplos

Consulta la [Guía de Contribución](docs/README.md#-contributing) para más detalles.

---

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

---

## 🙏 Agradecimientos

- Construido sobre [WPPConnect](https://github.com/wppconnect-team/wppconnect)
- Impulsado por [Playwright](https://playwright.dev/)

---

**Hecho con ❤️ por [Ammar Alkotb](https://github.com/3mora2)**

**¡Feliz Programación! 🎉**
