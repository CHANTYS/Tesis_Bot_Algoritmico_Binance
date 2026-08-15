================================================================================
  INSTRUCTIVO DE PUESTA EN MARCHA
  Sistema de Trading Algorítmico — TFG Rojo Santiago
  Universidad Nacional de La Rioja | Licenciatura en Sistemas de Información
================================================================================

  Repositorio: https://github.com/CHANTYS/Tesis_Bot_Algoritmico_Binance
  Rama: Stable
  Lenguaje: Python 3.x
  Entorno de operación: Binance TESTNET (sin capital real)

================================================================================
  ÍNDICE
================================================================================

  1.  Requisitos previos
  2.  Descarga del código fuente
  3.  Creación del entorno virtual e instalación de dependencias
  4.  Configuración del archivo .env
  5.  Configuración del Bot de Telegram
  6.  Obtención de credenciales Binance Testnet
  7.  Verificación de dependencias
  8.  Puesta en marcha del orquestador (manager.py)
  9.  Ejecución de backtesting
  10. Ejecución de motores en vivo
  11. Estructura de archivos de persistencia
  12. Visualización de resultados
  13. Solución de problemas frecuentes
  14. Consideraciones de seguridad

================================================================================
  1. REQUISITOS PREVIOS
================================================================================

  Antes de comenzar, asegúrese de contar con:

  - Python 3.10 o superior instalado
    Verificación:
      python --version
      python3 --version

  - pip (gestor de paquetes de Python)
    Verificación:
      pip --version

  - git (control de versiones)
    Verificación:
      git --version

  - Conexión a internet (para descargar klines de Binance y enviar
    mensajes vía Telegram)

  - Sistema operativo: Linux, macOS o Windows
    Nota: En Windows, usar "python" en lugar de "python3"

  - Cuenta de Telegram (para interactuar con el bot)

  - Cuenta en Binance Testnet: https://testnet.binancefuture.com

================================================================================
  2. DESCARGA DEL CÓDIGO FUENTE
================================================================================

  Paso 1: Clonar el repositorio desde la rama Stable.

    git clone -b Stable https://github.com/CHANTYS/Tesis_Bot_Algoritmico_Binance.git
    cd Tesis_Bot_Algoritmico_Binance

  Paso 2: Verificar la estructura de archivos.
  Debe contener, como mínimo, los siguientes módulos:

    manager.py                          → Orquestador central (Telegram)
    Backtesting_Long.py                 → Backtest L-V1 Trend Following
    Backtesting_Long_V2_BOLLINGER.py    → Backtest L-V2 Bollinger Rebound
    Backtesting_Short.py                → Backtest S-V1 Short Classic
    Backtesting_Short_V5_BEAR_MASTER.py → Backtest S-V5 Institutional BearMaster
    BotFuturos_Long.py                  → Motor en vivo LONG (1m)
    BotFuturos_Long_Bollinger.py        → Motor en vivo LONG Bollinger (15m)
    BotFuturos_Short.py                 → Motor en vivo SHORT V1
    BotFuturos_Short_V5_BearMaster.py   → Motor en vivo SHORT V5

  IMPORTANTE: El archivo .env NO está incluido en el repositorio
  por razones de seguridad. Debe crearse manualmente (sección 4).

================================================================================
  3. CREACIÓN DEL ENTORNO VIRTUAL E INSTALACIÓN DE DEPENDENCIAS
================================================================================

  Paso 1: Crear un entorno virtual de Python.

    python3 -m venv venv

  Paso 2: Activar el entorno virtual.

    En Linux/macOS:
      source venv/bin/activate

    En Windows (CMD):
      venv\Scripts\activate.bat

    En Windows (PowerShell):
      venv\Scripts\Activate.ps1

  Paso 3: Instalar las dependencias principales.

    pip install python-binance
    pip install pandas
    pip install pandas_ta
    pip install numpy
    pip install matplotlib
    pip install python-telegram-bot
    pip install python-dotenv
    pip install requests
    pip install asyncio

  Paso 4: Verificar que todas las librerías se instalaron correctamente.

    pip list

  Nota: Si existe un archivo requirements.txt en el repositorio, puede
  usar alternativamente:

    pip install -r requirements.txt

================================================================================
  4. CONFIGURACIÓN DEL ARCHIVO .env
================================================================================

  Paso 1: Crear el archivo .env en la raíz del proyecto.

    touch .env          (Linux/macOS)
    type nul > .env     (Windows CMD)

  Paso 2: Editar el archivo .env con un editor de texto y agregar
  las siguientes variables de entorno:

    BINANCE_TESTNET_API_KEY=su_api_key_de_testnet
    BINANCE_TESTNET_SECRET=su_secret_de_testnet
    TELEGRAM_TOKEN=su_token_de_bot_telegram
    TELEGRAM_CHAT_ID=su_chat_id_autorizado

  Paso 3: Guardar y cerrar el archivo.

  ADVERTENCIA DE SEGURIDAD:
  ──────────────────────────────────────────────────────────────────
  - El archivo .env NUNCA debe subirse a un repositorio público.
  - Verifique que .env esté incluido en .gitignore.
  - No comparta este archivo ni lo adjunte en documentación.
  - Si las credenciales se ven comprometidas, regenérelas de
    inmediato desde el panel de Binance Testnet y desde BotFather.
  ──────────────────────────────────────────────────────────────────

================================================================================
  5. CONFIGURACIÓN DEL BOT DE TELEGRAM
================================================================================

  El orquestador (manager.py) se controla exclusivamente por Telegram.
  Para crear el bot:

  Paso 1: Abrir Telegram y buscar "@BotFather".

  Paso 2: Enviar el comando /newbot y seguir las instrucciones:
    - Asignar un nombre al bot (ej: "MiBotTrading")
    - Asignar un username único (ej: "mi_bot_trading_tfg_bot")

  Paso 3: BotFather responderá con un TOKEN con formato:
    123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

  Paso 4: Copiar ese token y colocarlo en la variable
  TELEGRAM_TOKEN del archivo .env.

  Paso 5: Obtener su CHAT_ID:
    - Iniciar una conversación con el bot creado (/start)
    - Visitar: https://api.telegram.org/bot<TOKEN>/getUpdates
    - Buscar el campo "chat":{"id": XXXXXXXXX}
    - Copiar ese número y colocarlo en TELEGRAM_CHAT_ID del .env

  Nota: El manager.py filtra por chat_id. Solo el chat configurado
  en TELEGRAM_CHAT_ID podrá interactuar con el sistema. Cualquier
  otro chat recibirá el mensaje "No autorizado."

================================================================================
  6. OBTENCIÓN DE CREDENCIALES BINANCE TESTNET
================================================================================

  Paso 1: Ingresar a https://testnet.binancefuture.com

  Paso 2: Iniciar sesión con una cuenta de GitHub o registrarse.

  Paso 3: Una vez logueado, ir al panel de API:
    - Sección "API Key" → "Create API Key"
    - Asignar un nombre descriptivo (ej: "TFG_Bot_Trading")

  Paso 4: Copiar la API Key y el Secret Key.

  Paso 5: Colocar ambos valores en el archivo .env:
    BINANCE_TESTNET_API_KEY=...
    BINANCE_TESTNET_SECRET=...

  IMPORTANTE: Este proyecto opera EXCLUSIVAMENTE contra Testnet.
  Los motores en vivo usan testnet=True y la URL:
    https://testnet.binancefuture.com/fapi/v1
  No se conecta a producción ni se utiliza capital real.

================================================================================
  7. VERIFICACIÓN DE DEPENDENCIAS
================================================================================

  Antes de ejecutar, realizar las siguientes comprobaciones:

  7.1. Verificar que el entorno virtual esté activo:
    (venv) $ python3 -c "import binance; print('python-binance OK')"
    (venv) $ python3 -c "import pandas; print('pandas OK')"
    (venv) $ python3 -c "import pandas_ta; print('pandas_ta OK')"
    (venv) $ python3 -c "import numpy; print('numpy OK')"
    (venv) $ python3 -c "import matplotlib; print('matplotlib OK')"
    (venv) $ python3 -c "import telegram; print('python-telegram-bot OK')"
    (venv) $ python3 -c "import dotenv; print('python-dotenv OK')"

  7.2. Verificar que el archivo .env existe y tiene las 4 variables:
    (venv) $ grep -c "=" .env
    Debe devolver 4 (o más si hay variables adicionales).

  7.3. Verificar conectividad a Binance (datos públicos):
    (venv) $ python3 -c "
    from binance.client import Client
    c = Client()
    k = c.get_klines('BTCUSDT', Client.KLINE_INTERVAL_1MINUTE, limit=1)
    print('Conexión a Binance OK. Velas recibidas:', len(k))
    "

  7.4. Verificar conectividad a Telegram:
    (venv) $ python3 -c "
    import asyncio
    from telegram import Bot
    from dotenv import load_dotenv
    import os
    load_dotenv()
    async def test():
        bot = Bot(token=os.getenv('TELEGRAM_TOKEN'))
        me = await bot.get_me()
        print(f'Telegram OK. Bot: @{me.username}')
    asyncio.run(test())
    "

================================================================================
  8. PUESTA EN MARCHA DEL ORQUESTADOR (manager.py)
================================================================================

  El punto de entrada principal del sistema es manager.py.

  Paso 1: Asegurar que el entorno virtual está activo.

  Paso 2: Ejecutar el orquestador:

    (venv) $ python3 manager.py

  Paso 3: El sistema quedará escuchando eventos de Telegram.
  En la consola verá el inicio del polling de Telegram.

  Paso 4: Abrir Telegram y enviar al bot:

    /start

  Se mostrará el menú principal con opciones para iniciar/detener
  motores en vivo.

  Paso 5: Para acceder al laboratorio de backtesting, enviar:

    /test

  Se mostrará el menú de backtesting con las 4 estrategias
  disponibles.

  Menú principal (/start):
  ┌─────────────────────────────────────────────┐
  │  start_long      → Inicia motor LONG V1    │
  │  stop_long       → Detiene motor LONG V1   │
  │  start_short     → Inicia motor SHORT V1   │
  │  stop_short      → Detiene motor SHORT V1  │
  └─────────────────────────────────────────────┘

  Menú de backtesting (/test):
  ┌──────────────────────────────────────────────────────┐
  │  run_test_l1 → L-V1 Trend Following                 │
  │  run_test_l2 → L-V2 Bollinger Rebound               │
  │  run_test_s1 → S-V1 Short Classic                   │
  │  run_test_s5 → S-V5 Institutional BearMaster        │
  └──────────────────────────────────────────────────────┘

  Nota: Los backtests se ejecutan en un ThreadPoolExecutor para
  no bloquear el event loop de asyncio ni la comunicación con
  Telegram.

================================================================================
  9. EJECUCIÓN DE BACKTESTING
================================================================================

  Los backtesting pueden ejecutarse de dos formas:

  OPCIÓN A — Desde Telegram (recomendado):
    1. Enviar /test al bot
    2. Seleccionar la estrategia deseada
    3. El bot responde "Corriendo Backtest: [nombre]..."
    4. Al finalizar, se recibe un reporte con métricas y un
       dashboard PNG por Telegram

  OPCIÓN B — Desde línea de comandos (directo):

    (venv) $ python3 Backtesting_Long.py
    (venv) $ python3 Backtesting_Long_V2_BOLLINGER.py
    (venv) $ python3 Backtesting_Short.py
    (venv) $ python3 Backtesting_Short_V5_BEAR_MASTER.py

  Parámetros por defecto de los backtests:

    Símbolo:          BTCUSDT
    Intervalo:        15 minutos (KLINE_INTERVAL_15MINUTE)
    Ventana:          90 días hacia atrás
    Cantidad (QTY):   0.002 BTC (0.005 en S-V5)
    Comisión:         0.04% taker por operación
    Balance inicial:  $1000.00
    Datos:            Públicos (no requiere API key)

  Métricas generadas al finalizar cada backtest:
    - Total de operaciones
    - Win Rate (%)
    - PnL Neto
    - Total de comisiones
    - Máximo Drawdown
    - Sharpe Ratio

  El reporte se envía automáticamente a Telegram con un gráfico
  de 5 paneles (precio, MACD, StochRSI, RSI, KPIs).

================================================================================
  10. EJECUCIÓN DE MOTORES EN VIVO
================================================================================

  ADVERTENCIA: Los motores en vivo operan EXCLUSIVAMENTE en
  Binance TESTNET. No se conectan a cuentas de producción.

  Los motores se controlan desde Telegram a través del manager:

  10.1. Motor LONG V1 — Trend Following (intervalo 1m):
    - Enviar /start → seleccionar "start_long"
    - El motor se suscribe al WebSocket de klines 1m
    - Evalúa: EMA200 + cruce MACD + RSI 45-85
    - SL: ATR × 4.0 | TP: ATR × 4.0 × 3.0 (RR 1:3)
    - Para detener: /start → "stop_long"

  10.2. Motor LONG V2 — Bollinger Rebound (intervalo 15m):
    - Controlado desde manager
    - Evalúa: EMA200 + banda inferior Bollinger + RSI > 30
    - SL: ATR × 3.0 | TP: ATR × 3.0 × 3.0 (RR 1:3)

  10.3. Motor SHORT V1 — Short Classic:
    - Enviar /start → seleccionar "start_short"
    - Evalúa: precio bajo EMA200 + cruce bajista MACD + RSI 30-55
    - SL: ATR × 3.5 (arriba) | TP: ATR × 3.5 × 3.0 (abajo)

  10.4. Motor SHORT V5 — Institutional BearMaster:
    - Evalúa: tendencia bajista + rechazo StochRSI + volumen alto
    - SL: ATR × 3.0 | TP: ATR × 3.0 × 2.0 (RR 1:2)
    - QTY: 0.005

  Al detener cualquier motor (cancelación de tarea asyncio):
    1. Se ejecuta el bloque finally
    2. Se calcula get_summary() con métricas de sesión
    3. Se genera el dashboard de 5 paneles (PNG)
    4. Se envía por Telegram con caption resumen
    5. Se cierra la conexión AsyncClient

  Apalancamiento configurado: 10x (Config.LEVERAGE = 10)

================================================================================
  11. ESTRUCTURA DE ARCHIVOS DE PERSISTENCIA
================================================================================

  Cada estrategia genera un archivo JSON con el historial de
  operaciones cerradas:

    historial_long_v1.json     → Motor LONG V1
    historial_long_v2.json     → Motor LONG V2 Bollinger
    historial_short_v1.json    → Motor SHORT V1
    historial_short_v5.json    → Motor SHORT V5 BearMaster

  Estructura de cada registro:

  {
    "type": "LONG",
    "entry_price": 74397.9,
    "entry_time": "2026-04-20 06:35:00",
    "sl": 74261.88,
    "tp": 74669.94,
    "status": "CLOSED",
    "comm_in": 0.0595,
    "exit_price": 74699.9,
    "exit_time": "2026-04-20 06:46:00",
    "total_comm": 0.1193,
    "pnl_neto": 0.4847
  }

  Estos archivos se cargan automáticamente al reiniciar un motor
  (load_history) y se actualizan al cerrar cada operación
  (save_history).

  Para reiniciar el historial de una estrategia, basta con
  eliminar el archivo JSON correspondiente antes de iniciar
  el motor.

================================================================================
  12. VISUALIZACIÓN DE RESULTADOS
================================================================================

  El sistema genera dashboards PNG mediante la clase
  TradingVisualizer con las siguientes características:

  - Backend: Agg (no requiere entorno gráfico / headless)
  - Zona horaria: America/Argentina/La_Rioja
  - Estilo: dark_background
  - Resolución: 200 DPI
  - Dimensiones: 16×18 pulgadas

  El dashboard contiene 5 paneles:
    Panel 1: Precio + EMA 200 + marcadores de entrada/salida
             (^ verde = entrada | v verde = ganancia | v rojo = pérdida)
    Panel 2: MACD + señal + histograma
    Panel 3: Stochastic RSI (umbrales 20/80)
    Panel 4: RSI 14 (umbrales 30/70)
    Panel 5: Resumen ejecutivo (Win Rate, PnL, Comisiones,
             Profit Factor, Sharpe, Máximo Drawdown)

  Los dashboards se generan:
    - Al finalizar cada backtest
    - Al detener un motor en vivo (bloque finally)
    - Se envían automáticamente por Telegram como sendPhoto

================================================================================
  13. SOLUCIÓN DE PROBLEMAS FRECUENTES
================================================================================

  PROBLEMA: "No autorizado." al enviar comandos al bot
  CAUSA: El chat_id no coincide con TELEGRAM_CHAT_ID del .env
  SOLUCIÓN: Verificar el chat_id correcto (sección 5, paso 5)
            y actualizar el archivo .env

  -----------------------------------------------------------------

  PROBLEMA: ModuleNotFoundError: No module named 'binance'
  CAUSA: Entorno virtual no activado o dependencia no instalada
  SOLUCIÓN:
    source venv/bin/activate
    pip install python-binance

  -----------------------------------------------------------------

  PROBLEMA: Error de autenticación Binance
  CAUSA: API Key/Secret incorrectas o expiradas
  SOLUCIÓN: Regenerar credenciales en
            https://testnet.binancefuture.com → API Key
            Actualizar .env con los nuevos valores

  -----------------------------------------------------------------

  PROBLEMA: El bot no responde en Telegram
  CAUSA: Token incorrecto o manager.py no está en ejecución
  SOLUCIÓN:
    1. Verificar que TELEGRAM_TOKEN es correcto
    2. Confirmar que manager.py está corriendo:
       ps aux | grep manager.py
    3. Reiniciar: python3 manager.py

  -----------------------------------------------------------------

  PROBLEMA: Error al generar dashboard (matplotlib)
  CAUSA: Backend gráfico no disponible en servidor sin GUI
  SOLUCIÓN: El sistema usa matplotlib.use('Agg') por defecto.
            Si persiste, verificar:
            pip install matplotlib --force-reinstall

  -----------------------------------------------------------------

  PROBLEMA: Backtest demora demasiado
  CAUSA: Descarga de 90 días de klines + procesamiento
  SOLUCIÓN: Es normal. El backtest se ejecuta en un hilo
            separado (ThreadPoolExecutor) y no bloquea Telegram.
            Espere el mensaje "Backtest [nombre] finalizado."

  -----------------------------------------------------------------

  PROBLEMA: Archivo .env no se lee correctamente
  CAUSA: Formato incorrecto o espacios en las variables
  SOLUCIÓN: Verificar que NO haya espacios alrededor del "="
            BINANCE_TESTNET_API_KEY=valor_sin_espacios
            No usar comillas alrededor de los valores

  -----------------------------------------------------------------

  PROBLEMA: El motor en vivo no ejecuta órdenes
  CAUSA: Puede estar operando en período sin señales
  SOLUCIÓN: Verificar que el WebSocket está conectado
            (mensajes en consola). Las estrategias requieren
            condiciones específicas de mercado para disparar
            entradas. Puede esperar o verificar con un backtest
            previo si hay señales en el período actual.

================================================================================
  14. CONSIDERACIONES DE SEGURIDAD
================================================================================

  1. El archivo .env NUNCA debe incluirse en control de versiones.
     Verificar que .gitignore contenga la línea: .env

  2. Todas las credenciales se cargan con load_dotenv().
     No hay credenciales hardcodeadas en el código fuente.

  3. El manager implementa filtrado por chat_id. Solo el chat
     configurado en TELEGRAM_CHAT_ID puede operar el sistema.

  4. Los motores en vivo operan EXCLUSIVAMENTE contra Testnet:
       testnet=True
       FUTURES_URL = 'https://testnet.binancefuture.com/fapi/v1'
     No se conectan a producción ni manejan capital real.

  5. El repositorio público en GitHub NO contiene el archivo .env
     ni credenciales de ningún tipo.

  6. Si sospecha que sus credenciales fueron comprometidas:
     a) Detenga el manager inmediatamente (Ctrl+C)
     b) Regenera las API keys en Binance Testnet
     c) Revoca el token del bot con BotFather (/revoke)
     d) Actualice el archivo .env con las nuevas credenciales
     e) Reinicie el sistema

  7. En un entorno de servidor/VPS, se recomienda:
     - Ejecutar dentro de screen o tmux
     - Configurar un servicio systemd para reinicio automático
     - Restringir permisos del archivo .env: chmod 600 .env

================================================================================
  RESUMEN RÁPIDO DE PUESTA EN MARCHA
================================================================================

  # 1. Clonar repositorio
  git clone -b Stable https://github.com/CHANTYS/Tesis_Bot_Algoritmico_Binance.git
  cd Tesis_Bot_Algoritmico_Binance

  # 2. Crear y activar entorno virtual
  python3 -m venv venv
  source venv/bin/activate

  # 3. Instalar dependencias
  pip install python-binance pandas pandas_ta numpy matplotlib \
              python-telegram-bot python-dotenv requests

  # 4. Crear y configurar .env
  cat > .env << 'EOF'
  BINANCE_TESTNET_API_KEY=su_api_key
  BINANCE_TESTNET_SECRET=su_secret
  TELEGRAM_TOKEN=su_token
  TELEGRAM_CHAT_ID=su_chat_id
  EOF

  # 5. Ejecutar el orquestador
  python3 manager.py

  # 6. Abrir Telegram y enviar /start o /test al bot

================================================================================
  Fin del Instructivo
  TFG Rojo Santiago — 2026
  Universidad Nacional de La Rioja
================================================================================
