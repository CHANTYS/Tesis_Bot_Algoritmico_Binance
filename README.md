1. Introducción
El presente manual describe cómo instalar, configurar y operar el sistema de trading algorítmico desarrollado en el marco del Trabajo Final de Grado. El sistema permite:
•	Ejecutar cuatro estrategias de backtesting histórico (90 días, temporalidad 15 minutos) sobre el par BTC/USDT.
•	Operar motores en vivo sobre Binance Futures Testnet (sin capital real).
•	Controlar todo el ciclo de vida del sistema de forma remota mediante un bot de Telegram.
•	Recibir dashboards gráficos y métricas de rendimiento (PnL, Win Rate, Sharpe, Max Drawdown) por el mismo canal.
El alcance operativo se limita al entorno de simulación (Testnet). No se contempla el uso con dinero real en el marco de este TFG.
2. Requisitos previos
2.1. Hardware y sistema operativo
•	Equipo con acceso a Internet estable (recomendado: VPS o PC siempre encendido si se desean sesiones largas en vivo).
•	Sistema operativo compatible con Python 3.10 o superior (Linux, Windows o macOS).
2.2. Software
•	Python 3.10+
•	pip (gestor de paquetes)
•	Cuenta de Telegram y un bot creado con @BotFather
•	Cuenta en Binance Futures Testnet (https://testnet.binancefuture.com) con API Key y Secret generados
2.3. Dependencias Python
Instalar con el siguiente comando (desde la carpeta del proyecto):
pip install python-binance pandas pandas_ta numpy matplotlib python-telegram-bot python-dotenv requests

2.4. Código fuente
El código completo (excepto el archivo .env) está disponible en:
https://github.com/CHANTYS/Tesis_Bot_Algoritmico_Binance/tree/Stable
Rama recomendada: Stable.
 
3. Configuración inicial
3.1. Archivo de credenciales (.env)
Crear un archivo llamado .env en la raíz del proyecto (mismo directorio que manager.py) con el siguiente contenido. No subir este archivo a GitHub ni compartirlo.
BINANCE_TESTNET_API_KEY=su_api_key_de_testnet
BINANCE_TESTNET_SECRET=su_secret_de_testnet
TELEGRAM_TOKEN=token_del_bot_obtenido_en_BotFather
TELEGRAM_CHAT_ID=su_chat_id_numerico

Cómo obtener cada valor:
•	API Key / Secret: panel de Binance Futures Testnet → API Management → Create API.
•	TELEGRAM_TOKEN: conversar con @BotFather en Telegram → /newbot → copiar el token.
•	TELEGRAM_CHAT_ID: enviar un mensaje al bot y consultar https://api.telegram.org/bot<TOKEN>/getUpdates (campo chat.id).
El sistema solo responde al chat_id configurado. Cualquier otro usuario recibirá el mensaje «No autorizado».
3.2. Estructura de carpetas esperada
Tras clonar el repositorio, la raíz debe contener al menos:
•	manager.py
•	Backtesting_Long.py, Backtesting_Long_V2_BOLLINGER.py, Backtesting_Short.py, Backtesting_Short_V5_BEAR_MASTER.py
•	BotFuturos_Long.py, BotFuturos_Long_Bollinger.py, BotFuturos_Short.py (y/o BotFuturos_Short_V5_BearMaster.py)
•	.env (creado por el usuario, no versionado)
Los archivos historial_*.json se crean automáticamente al cerrar la primera operación de cada motor.
3.3. Arranque del orquestador
Desde la carpeta del proyecto ejecutar:
python manager.py

Si la configuración es correcta, la consola mostrará un mensaje del tipo: «Manager Pro activo. Usa /start para vivo o /test para backtesting». El proceso debe permanecer en ejecución mientras se opere el sistema.
 
4. Operación mediante Telegram
Toda la interacción de control se realiza desde el chat del bot de Telegram asociado al TELEGRAM_TOKEN. Solo el chat_id autorizado puede enviar comandos.
4.1. Menú de control en vivo (/start)
Enviar el comando /start (o pulsar el botón equivalente). El bot responde con el panel de control:


 

Botón	Función
Iniciar Short	Arranca el motor en vivo SHORT (BearMaster / Classic según importación).
Parar Short	Cancela la tarea del motor SHORT, genera el reporte final y cierra la conexión.
Iniciar Long	Arranca el motor en vivo LONG (Bollinger Rebound en la configuración por defecto del manager).
Parar Long	Cancela la tarea del motor LONG y genera el dashboard de sesión.
MENÚ DE BACKTESTING (/test)	Abre el laboratorio de pruebas con las cuatro estrategias históricas.
CERRAR TODO	Detiene todos los motores activos de forma inmediata (emergency stop).

El estado de cada motor se indica en el texto del menú: «ACTIVO» (verde) o «APAGADO» (gris).
4.2. Menú de backtesting (/test)
Enviar /test o pulsar el botón «MENÚ DE BACKTESTING». Se muestran cuatro opciones:




 
•	Long V1 (Trend) — Backtesting_Long.py
•	Long V2 (Bollinger) — Backtesting_Long_V2_BOLLINGER.py
•	Short V1 (Classic) — Backtesting_Short.py
•	Short V5 (BearMaster) — Backtesting_Short_V5_BEAR_MASTER.py
Al seleccionar una estrategia:
1.	El bot confirma: «Corriendo Backtest: [nombre]…».
2.	El backtest se ejecuta en un hilo separado (no bloquea Telegram).
3.	Al finalizar se descarga el historial de 90 días, se simulan las operaciones, se genera un dashboard de 3 paneles (equity curve, drawdown, histograma de PnL) y se envía la imagen más un caption con las métricas.
4.	El bot notifica: «Backtest [nombre] finalizado».
Cada backtest puede tardar entre varios segundos y un minuto, según la conexión a Binance y el hardware.
4.3. Notificaciones automáticas en vivo
Mientras un motor en vivo está activo, el operador recibe mensajes automáticos:
•	Confirmación de conexión al arrancar.
•	Alerta de entrada (precio, SL y TP cuando aplica).
•	Alerta de cierre con PnL neto de la operación.
•	Al detener el motor: imagen del dashboard de 5 paneles y resumen de la sesión (operaciones, win rate, PnL, comisiones, Sharpe, max drawdown).
 
5. Descripción operativa de las estrategias
Las cuatro estrategias evalúan el par BTC/USDT. En backtesting se usa temporalidad de 15 minutos y ventana de 90 días. En vivo, el intervalo depende del motor (1m o 15m).
5.1. L-V1 Trend Following (LONG)
•	Idea: comprar en continuación de tendencia alcista.
•	Filtros: precio > EMA 200; cruce alcista de MACD; RSI entre 45 y 85.
•	Riesgo: Stop Loss = ATR × 4; Take Profit = 3 × distancia del SL (backtest) o 2 × (vivo).
•	Tamaño: 0,002 BTC.
5.2. L-V2 Bollinger Rebound (LONG)
•	Idea: comprar en retroceso hacia la media dentro de tendencia alcista.
•	Filtros: precio > EMA 200; cierre por debajo de la banda inferior de Bollinger; RSI > 30.
•	Riesgo: SL = ATR × 3; TP = 3 × distancia del SL.
•	Tamaño: 0,002 BTC.
5.3. S-V1 Short Classic (SHORT)
•	Idea: vender en estructura bajista con agotamiento de impulso alcista.
•	Filtros: precio < EMA 200; cruce bajista de MACD; RSI entre 30 y 55.
•	Riesgo: SL por encima del precio (ATR × 3,5); TP por debajo (ratio 1:3).
•	Tamaño: 0,002 BTC.
En la ventana de evaluación de 90 días fue la única estrategia con PnL neto positivo.
5.4. S-V5 Institutional BearMaster (SHORT)
•	Idea: vender ante rechazo en zona de sobrecompra con confirmación de volumen.
•	Filtros: precio < EMA 200; Stochastic RSI cruzando hacia abajo desde > 80; volumen > media.
•	Riesgo: SL = ATR × 3; TP con ratio 1:2.
•	Tamaño: 0,005 BTC (mayor que el resto).
 
6. Interpretación de reportes y métricas
6.1. Dashboard de backtesting (3 paneles)
•	Panel superior: curva de equity (evolución del capital simulado desde USD 1.000).
•	Panel inferior izquierdo: drawdown (caída desde el máximo de capital alcanzado).
•	Panel inferior derecho: histograma de PnL por operación (ganancias y pérdidas). 

 








6.2. Dashboard en vivo (5 paneles)
•	Precio + EMA 200 (y bandas de Bollinger si es la estrategia Rebound), con triángulos de entrada/salida.
•	MACD y señal.
•	Stochastic RSI.
•	RSI 14.
•	Resumen textual de KPIs de la sesión.

 






6.3. Métricas del caption / resumen

Métrica	Significado
Operaciones	Cantidad de trades cerrados en el período.
Win Rate	Porcentaje de operaciones con PnL neto positivo.
PnL Neto	Ganancia o pérdida total después de descontar comisiones (0,04 % taker por lado).
Comisiones	Suma de fees de entrada y salida de todas las operaciones.
Max Drawdown	Máxima caída del capital desde un pico hasta un valle posterior.
Sharpe	Relación retorno / volatilidad sobre la serie de PnL por operación. Valores < 1 indican que el retorno no compensa el riesgo asumido.
Profit Factor	Suma de ganancias / valor absoluto de la suma de pérdidas. Mayor que 1 implica más ganancias que pérdidas en magnitud.

 
7. Procedimientos recomendados
7.1. Primera puesta en marcha
5.	Clonar el repositorio (rama Stable) e instalar dependencias.
6.	Crear el archivo .env con las cuatro variables indicadas en la sección 3.1.
7.	Ejecutar python manager.py y dejar el proceso en ejecución.
8.	Desde Telegram, enviar /start y verificar que el menú responde.
9.	Ejecutar un backtest de prueba (por ejemplo Long V1) y comprobar que llega el dashboard.
10.	Opcional: iniciar un motor en vivo por unos minutos, observar mensajes de conexión y luego detenerlo con «Parar» para recibir el reporte de sesión.
7.2. Sesión de evaluación de estrategias
11.	Con el manager en marcha, abrir /test.
12.	Ejecutar las cuatro estrategias de forma secuencial (esperar el mensaje de finalización de cada una).
13.	Conservar las imágenes y captions enviados por Telegram para el análisis comparativo.
14.	Contrastar con el informe web si está actualizado.
7.3. Sesión en vivo controlada
15.	Verificar saldo y permisos en Testnet (el sistema no opera con dinero real).
16.	Iniciar solo un motor a la vez si se desea aislar el comportamiento de una estrategia.
17.	Monitorear las alertas de entrada/salida.
18.	Al concluir, usar «Parar» (no cerrar solo la terminal) para forzar el reporte final y el guardado del historial JSON.
19.	En emergencia, usar «CERRAR TODO».
7.4. Detención segura
Evitar matar el proceso del manager con Ctrl+C mientras haya motores activos, si se desea el reporte final. Preferir los botones «Parar Short», «Parar Long» o «CERRAR TODO». Tras detener los motores, sí puede finalizarse el manager con Ctrl+C.
 
8. Limitaciones y advertencias
•	El sistema opera únicamente en Binance Futures Testnet. No está configurado para producción ni para capital real.
•	Los resultados de backtesting corresponden a una ventana histórica concreta (90 días) y no garantizan rendimiento futuro.
•	La simulación de salida intra-barra (SL/TP) es una aproximación: no modela el orden exacto de ticks dentro de cada vela.
•	Las comisiones se modelan como taker fijo (0,04 %). No se incluye funding rate de los perpetuos ni slippage variable.
•	El tamaño de posición es fijo; no hay position sizing dinámico ni gestión de capital proporcional al equity.
•	Solo el chat_id configurado puede controlar el bot. No compartir el token ni el .env.
9. Resolución de problemas frecuentes
Síntoma	Acción sugerida
El bot no responde en Telegram	Verificar que manager.py está en ejecución; comprobar TELEGRAM_TOKEN y que el mensaje sale del chat_id autorizado.
Mensaje «No autorizado»	El chat_id del usuario no coincide con TELEGRAM_CHAT_ID del .env. Corregir y reiniciar el manager.
Error al importar módulos	Ejecutar desde la carpeta del proyecto; verificar que todos los .py están presentes y que las dependencias están instaladas.
Backtest no envía imagen	Revisar conectividad a Internet, validez del token y que matplotlib pueda escribir el PNG en el directorio de trabajo.
Motor en vivo no conecta a Binance	Verificar API Key/Secret de Testnet, que testnet=True esté activo y que la URL de Futures Testnet sea la correcta.
No se generan historial_*.json	Los archivos se crean al cerrar la primera operación. Si no hubo trades, el archivo puede no existir aún.
 
10. Referencias rápidas
•	Código fuente completo (sin .env): https://github.com/CHANTYS/Tesis_Bot_Algoritmico_Binance/tree/Stable
•	Informe de backtesting consolidado: en el bot de Telegram reporte visual .png + métricas
•	Binance Futures Testnet: https://testnet.binancefuture.com
•	Creación de bots de Telegram: @BotFather
Este manual forma parte de los anexos del Trabajo Final de Grado y debe interpretarse junto con la memoria principal (capítulos de diseño, implementación y resultados) y el anexo de extractos de código fuente.
