# WPP_Whatsapp

**Automatiza WhatsApp Web desde Python.**

Crea aplicaciones que reciban mensajes, lean conversaciones, trabajen con archivos
multimedia y conecten WhatsApp con clientes MCP. WPP_Whatsapp combina
[WPPConnect](https://github.com/wppconnect-team/wppconnect),
[WA-JS](https://github.com/wppconnect-team/wa-js) y Playwright, con interfaces
síncronas y soporte nativo para `asyncio`.

[English](README.md) · [العربية](README.ar.md) · **Español**

[Documentación](docs/README.md) · [PyPI](https://pypi.org/project/WPP-Whatsapp/) ·
[Versiones](https://github.com/3mora2/WPP_Whatsapp/releases) ·
[Informar de un problema](https://github.com/3mora2/WPP_Whatsapp/issues)

**En esta página**

- [Qué puedes crear](#qué-puedes-crear)
- [Instalación](#instalación)
- [Inicio rápido](#inicio-rápido-recibir-mensajes)
- [Asyncio nativo](#usar-asyncio-nativo)
- [Integración MCP](#conectar-un-cliente-mcp)
- [Sesiones y resultados de envío](#trabajar-con-sesiones-y-resultados-de-envío)
- [Documentación](#explorar-la-documentación)
- [Contribuciones y soporte](#contribuciones-y-soporte)
- [Licencia](#licencia)

## Qué puedes crear

- **Flujos de mensajes:** recibe mensajes entrantes, lee el historial de los chats,
  envía texto y responde a mensajes.
- **Integraciones multimedia:** envía imágenes y documentos, y descarga archivos
  adjuntos de los mensajes.
- **Herramientas para contactos y grupos:** consulta contactos, lista chats y
  obtén los miembros de un grupo.
- **Aplicaciones asíncronas:** utiliza servicios nativos de `asyncio` para mensajes,
  chats, eventos y más, con resultados de lectura tipados opcionales.
- **Integraciones MCP:** ofrece herramientas de WhatsApp mediante stdio o HTTP
  local, con aislamiento de cuentas, políticas de acceso, diagnósticos y seguimiento
  de los envíos.

## Instalación

Necesitas **Python 3.9 o posterior**, **Chrome o Chromium de Playwright** y una
conexión a Internet. La integración MCP opcional requiere **Python 3.10 o posterior**.

Para instalar la biblioteca de Python:

```bash
python -m pip install --upgrade WPP_Whatsapp
```

Si necesitas soporte MCP, instala el extra opcional en su lugar:

```bash
python -m pip install --upgrade "WPP_Whatsapp[mcp]"
```

Chrome es el navegador predeterminado. También puedes utilizar Chromium de
Playwright; consulta la [guía de instalación](docs/INSTALLATION.md) para configurar
el navegador y conocer el soporte opcional de FFmpeg y el extra `stealth`.

## Inicio rápido: recibir mensajes

Guarda este ejemplo como `listener.py` y ejecútalo con `python listener.py`:

```python
from threading import Event

from WPP_Whatsapp import Create


def incoming(message):
    print("ID del mensaje recibido:", message.get("id"))


with Create(session="mybot", autoClose=0) as client:
    client.onMessage(incoming)
    print("Esperando mensajes; pulsa Ctrl+C para cerrar.")
    Event().wait()
```

La primera vez, escanea el código QR que aparece en el navegador con WhatsApp
en tu teléfono. Utiliza el mismo nombre de sesión en las siguientes ejecuciones
para reutilizar el inicio de sesión guardado. El ejemplo muestra los IDs de los
mensajes entrantes y sigue escuchando hasta que pulses Ctrl+C.
Al salir del bloque `with`, se cierran los recursos del cliente y se conserva
el inicio de sesión.

`Create` gestiona el arranque y devuelve el cliente listo al entrar en el bloque
`with`. Si gestionas el arranque manualmente, utiliza `creator.start()` para
obtener ese cliente antes de registrar callbacks o llamar a sus métodos.

## Usar asyncio nativo

Elige `AsyncClient` si tu aplicación ya utiliza `asyncio`.
Este ejemplo carga un máximo de diez chats:

```python
import asyncio

from WPP_Whatsapp import AsyncClient


async def main():
    async with AsyncClient("mybot", autoClose=0) as client:
        chats = await client.chats.list_chats({"count": 10})
        print("Chats cargados:", len(chats))


asyncio.run(main())
```

Utiliza cada cliente asíncrono en el bucle de eventos que lo creó. Los servicios
nativos usan nombres de métodos en `snake_case`; los métodos directos existentes
conservan sus nombres y resultados sin procesar.
Consulta la [referencia de la API](docs/API_REFERENCE.md) para ver ejemplos de
envíos, historial y archivos multimedia, o la [guía de migración](docs/ARCHITECTURE.md)
para adaptar el código existente a los servicios nativos.

## Conectar un cliente MCP

Una vez instalado el extra `mcp`, configura tu cliente MCP para ejecutar:

```bash
wpp-whatsapp-mcp --session mybot
```

Este comando utiliza stdio. Para ejecutar un servidor HTTP local en su lugar:

```bash
wpp-whatsapp-mcp --session mybot --transport http --port 8765
```

La dirección HTTP es `http://127.0.0.1:8765/mcp`.
Cuando el servidor esté en marcha:

1. Llama a `whatsapp_connect` desde tu cliente MCP.
2. Completa el inicio de sesión de WhatsApp en el navegador.
3. Consulta `whatsapp_status` hasta que `ready` sea `true`.

Iniciar el servidor MCP por sí solo no abre WhatsApp. La versión **2.3.0** ofrece
**23 herramientas** para sesiones, chats, mensajes, búsqueda, eventos, archivos
multimedia y diagnósticos. Utiliza `--read-only` para excluir las herramientas de
envío y conciliación de resultados de envío; quedan **18 herramientas** disponibles.

La [guía de FastMCP](docs/FASTMCP.md) explica la configuración del cliente, el uso
de varias cuentas, las políticas de acceso basadas en JWT verificados y el
seguimiento de los envíos. El soporte MCP se introdujo en la versión 2.1.0 con
12 herramientas; el conjunto ampliado requiere la versión 2.2.0 o posterior.

La versión 2.3.0 vincula cada operación a su solicitud y añade eventos persistentes
opcionales, recuperación limitada, espera de entrega/lectura y límites de concurrencia.
Consulta la [guía de fiabilidad y migración](docs/RELIABILITY.md),
el [estado de publicación](CHANGELOG.md) y los ejemplos HTTP/MCP.

## Trabajar con sesiones y resultados de envío

- **Reutiliza las sesiones de forma consistente.** Cada perfil de navegador tiene
  un único propietario a la vez. Cierra el propietario actual antes de reutilizarlo;
  se rechaza `close_already_profile=True`.
- **Conserva los IDs completos.** Mantén los identificadores de mensajes exactamente
  como se reciben, incluidos los sufijos de participantes en grupos. Los números de
  teléfono sin sufijo se interpretan como números de teléfono; los LID explícitos
  utilizan `@lid`.
- **Comprueba los recibos antes de reintentar.** Los envíos realizados mediante los
  servicios con seguimiento devuelven recibos. Un ID de mensaje confirmado no
  demuestra que el destinatario haya recibido o leído el mensaje. Consulta la
  [semántica de envío](docs/ARCHITECTURE.md#sending-and-uncertain-results)
  antes de añadir reintentos automáticos.
- **Elige la versión de ejecución cuando lo necesites.** Al arrancar, la biblioteca
  normalmente busca la última versión estable de WA-JS, comprueba su caché
  verificada y recurre a los archivos incluidos si es necesario. Usa
  `wa_js_version="bundled"` para omitir la búsqueda y la descarga. WhatsApp Web
  sigue necesitando Internet. Si especificas una versión, URL o archivo, se respeta
  esa selección sin sustituirla automáticamente.
- **Revisa los ajustes opcionales.** `stealthy=True` requiere `WPP_Whatsapp[stealth]`.
  Las unidades de los tiempos de espera varían según el ajuste; consulta la
  [configuración](docs/CONFIGURATION.md).

Versiones incluidas: WPPConnect **2.3.4** y WA-JS **4.6.1**.

## Explorar la documentación

Las siguientes guías detalladas están disponibles en inglés.

| Quiero… | Empieza aquí |
| --- | --- |
| Configurar la biblioteca y el navegador | [Instalación](docs/INSTALLATION.md) |
| Abrir una sesión y leer mensajes | [Inicio rápido](docs/QUICKSTART.md) |
| Encontrar métodos y argumentos | [Referencia de la API](docs/API_REFERENCE.md) · [Firmas de los servicios](docs/API_METHODS.md) |
| Configurar perfiles y tiempos de espera | [Configuración](docs/CONFIGURATION.md) |
| Recuperar operaciones, consumir eventos persistentes y consultar métricas | [Operaciones (candidato 2.4)](docs/OPERATIONS.md) |
| Usar lecturas tipadas y operaciones multimedia con límites definidos | [Lecturas tipadas y archivos multimedia](docs/TYPED_MEDIA.md) |
| Ejecutar un ejemplo completo | [Ejemplos](examples/README.md) · [Plantillas de aplicaciones](scripts/README.md) |
| Resolver un problema | [Solución de problemas](docs/TROUBLESHOOTING.md) · [Preguntas frecuentes](docs/FAQ.md) |
| Diseñar un comportamiento fiable para la aplicación | [Buenas prácticas](docs/BEST_PRACTICES.md) · [Rendimiento](docs/PERFORMANCE.md) |

## Contribuciones y soporte

Para informar de un error, abre una [incidencia en GitHub](https://github.com/3mora2/WPP_Whatsapp/issues)
con un ejemplo mínimo que lo reproduzca y los detalles de la versión y del error,
sin datos sensibles. Para contribuir al código, empieza por la
[guía de desarrollo](docs/DEVELOPMENT.md) y la [guía de pruebas](tests/README.md).
Los cambios de cada versión se documentan en el [registro de cambios](CHANGELOG.md).

Las pruebas automatizadas de MCP utilizan operaciones de WhatsApp simuladas con
transportes MCP reales; no certifican los envíos reales ni todas las API de las
dependencias. La limitación local de la frecuencia controla el ritmo de las
operaciones y no garantiza su aceptación por la plataforma ni evita bloqueos de cuenta.

## Licencia

El proyecto de Python utiliza la licencia [MIT](LICENSE).
Las dependencias JavaScript incluidas conservan sus
[licencias originales](WPP_Whatsapp/js_lib/UPSTREAM.md).
