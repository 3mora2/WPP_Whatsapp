# WPP_Whatsapp

Automatización de WhatsApp Web para Python mediante WPPConnect, WA-JS y Playwright.

[English](README.md) · [Documentación](docs/README.md) ·
[PyPI](https://pypi.org/project/WPP-Whatsapp/) · [Cambios](CHANGELOG.md)

## Instalación

La biblioteca principal admite Python **3.9+**. La integración FastMCP requiere
Python **3.10+**. Chrome es el navegador predeterminado.

```bash
python -m pip install --upgrade WPP_Whatsapp
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
```

El segundo comando añade FastMCP. Desde el código fuente:
`python -m pip install -e ".[mcp,dev]"`.
Consulta [instalación](docs/INSTALLATION.md) para Chromium, FFmpeg y stealth.

## Cliente síncrono

`Create` es una fábrica; `start()` o su gestor de contexto devuelve el cliente.
Los callbacks se registran en ese cliente con `onMessage`; `on_message` también
existe como alias en la API plana.

```python
from threading import Event
from WPP_Whatsapp import Create

with Create(session="mybot", autoClose=0) as client:
    def incoming(message):
        print("ID recibido:", message.get("id"))

    client.onMessage(incoming)
    Event().wait()
```

Escanea el QR en el navegador. El perfil se conserva para la próxima ejecución.
Al salir del contexto se cierran los recursos; no se cierra la sesión de WhatsApp.

## Cliente asyncio

```python
import asyncio
from WPP_Whatsapp import AsyncClient

async def main():
    async with AsyncClient("mybot", autoClose=0) as client:
        chats = await client.chats.list_chats({"count": 10})
        print("Chats:", len(chats))

asyncio.run(main())
```

Los servicios nativos usan snake_case. Las llamadas planas existentes conservan
sus nombres y resultados. Los envíos mediante servicios devuelven recibos;
un ID confirmado no demuestra entrega ni lectura por el destinatario.

## Servidor FastMCP

```bash
wpp-whatsapp-mcp --session mybot
wpp-whatsapp-mcp --session mybot --transport http --port 8765
```

Elige stdio o HTTP local (`http://127.0.0.1:8765/mcp`). Llama a
`whatsapp_connect`, inicia sesión en el navegador y consulta `whatsapp_status`
hasta que esté listo. La versión 2.2.0 incluye 21 herramientas (16 con
`--read-only`), cuentas aisladas, permisos JWT, eventos, búsqueda y archivos.
Estas mejoras están disponibles desde 2.2.0; la versión 2.1.0 tiene
las 12 herramientas originales. Consulta también las [lecturas tipadas y archivos](docs/TYPED_MEDIA.md).
Consulta la [guía FastMCP](docs/FASTMCP.md).

## Compatibilidad y ayuda

- Un perfil de navegador tiene un único propietario; no se admite
  `close_already_profile=True`.
- `stealthy=True` requiere `WPP_Whatsapp[stealth]`.
- `wa_js_version="bundled"` evita descargar WA-JS; WhatsApp Web necesita Internet.
- Conserva los IDs completos de mensajes de grupo, incluido el participante.
- Los límites locales de envío no garantizan aceptación ni evitan bloqueos.

Consulta [inicio rápido](docs/QUICKSTART.md), [API](docs/API_REFERENCE.md),
[configuración](docs/CONFIGURATION.md), [migración](docs/ARCHITECTURE.md),
[ejemplos](examples/README.md) y [solución de problemas](docs/TROUBLESHOOTING.md).
Las pruebas MCP usan operaciones WhatsApp simuladas; no certifican envíos reales.

Licencia Python: [MIT](LICENSE). Las dependencias JavaScript mantienen sus
[licencias originales](WPP_Whatsapp/js_lib/UPSTREAM.md).
