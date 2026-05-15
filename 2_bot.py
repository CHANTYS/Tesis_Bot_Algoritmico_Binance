import os
import time
import logging
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv



# --- Configuración de Logging ---
# Se establece un sistema de registro dual: 
# 1. Archivo fisico (.log) para persistencia de auditoría de la tesis.
# 2. Consola para monitoreo en tiempo real.


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("analisis_tesis.log"), logging.StreamHandler()]
    
    
)


 #            Constructor de la clase: Inicializa el entorno de trading.
class TesisTradingBot:
    def __init__(self, symbol='BTCUSDT', trade_qty=0.001):
        self.symbol = symbol
        self.trade_qty = trade_qty
        self.in_position = False
               
       # Constructor de la clase: Inicializa el entorno de trading.
       # - Define el activo (symbol) y la cantidad por operación (trade_qty).
       # - Establece el estado inicial de mercado (in_position).
        
        
        # --- Parámetros de Realismo (Indicadores Sugerencias Director) -----------------------------------------------------------------------
        self.fee_rate = 0.001       # 0.1% Comisión estándar de Binance
        self.slippage_rate = 0.0005 # 0.05% Desfase estimado de ejecución
        
        # --- Estructuras de Datos 
        # --- Almacenamiento de Datos para Métricas ---
        self.trade_history = [] # Almacena diccionarios con logs de ejecución para análisis posterior.----------------------***********
        self.price_history = [] # Para calcular indicadores
        
        
                       # --- Autenticación de API ---                      
                       
        # Carga variables de entorno en archivo .env para seguridad y conecta con el entorno de pruebas (Testnet) de Binance.
        
        load_dotenv()
        self.client = Client(os.getenv('BINANCE_TESTNET_API_KEY'), 
                             os.getenv('BINANCE_TESTNET_SECRET'), 
                             testnet=True)

    def get_indicators(self):
        """Obtiene datos históricos y calcula EMA y RSI."""
        try:
         #-- Procesamiento de Datos y Análisis Tecnico:
         
             #---- Obtiene OHLCV (Open, High, Low, Close, Volume) mediante REST API.
             #---- Calcula indicadores tendenciales (EMA) y de momentum (RSI).
            
            #--------------------------------------------------------------------------- Pedimos las últimas 100 velas de 1 minuto            
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
            df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            df['close'] = df['close'].astype(float) # -------> Conversión de strings de la API a floats para cálcular.
            
            # --- Media Móvil Exponencial (EMA) ---
            # Se calcula con ajuste 'False' para seguir la fórmula clásica de recursividad.
            # Cálcula de EMA 20
            df['ema'] = df['close'].ewm(span=20, adjust=False).mean()
            
            
            
            # --- Índice de Fuerza Relativa (RSI) --- 
            # Calculo de RSI 14 (Lógica manual para no depender de librerías externas y pesadas)           
            # Cálculo de cambios de precio (delta) para separar ganancias y pérdidas promedio.
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            
            rs = gain / loss   # Relative Strength
            
            df['rsi'] = 100 - (100 / (1 + rs))
            
            # Retorna el último valor calculado de cada serie para la toma de decisiones inmediata.
            return df.iloc[-1]['close'], df.iloc[-1]['ema'], df.iloc[-1]['rsi']
        except Exception as e:
            logging.error(f"Error calculando indicadores: {e}")
            return None, None, None

    def execute_trade(self, side, price):
        #--------""" Ejecuta orden y aplica Slippage + Fees para realismo."""
         
       #-------- Módulo de Ejecución de Órdenes:
       #-------- - Simula el impacto del slippage en el precio contable.
       #-------- - Envía la instrucción MARKET a la API de Binance.
       #-------- - Registra la transacción incluyendo costos operativos (fees).
       
        try:
            # Aplicamos el SLIPPAGE al precio de ejecución para el registro
            # Cálculo del precio efectivo considerando el deslizamiento de mercado (Slippage).
            exec_price = price * (1 + self.slippage_rate) if side == 'BUY' else price * (1 - self.slippage_rate)
            cost_fees = (exec_price * self.trade_qty) * self.fee_rate
            
            # Orden real en Testnet
            # Envío de orden de mercado a la infraestructura de Binance Testnet.
            
            order = self.client.create_order(
                symbol=self.symbol, side=side, type='MARKET', quantity=self.trade_qty
            )
            
            # Almacenamiento de metadatos de la operación para el cálculo de métricas de tesis.
            self.trade_history.append({
                'side': side,
                'price': exec_price,
                'fee': cost_fees,
                'timestamp': time.time()
            })
            
            logging.info(f"ORDEN {side} ejecutada a {exec_price:.2f} (Fee: {cost_fees:.4f} USDT)")
            return True
        except BinanceAPIException as e:
            logging.error(f"Error en orden: {e}")
            return False

    def calculate_thesis_metrics(self):
       # Análisis de Desempeño Estadístico:
       #  - Calcula el Sharpe Ratio para medir el retorno ajustado por riesgo.
       #  - Calcula el Max Drawdown para evaluar la pérdida máxima histórica desde el pico.
        
        if len(self.trade_history) < 2:
            return "Datos insuficientes para métricas."

        # Convertir historial a retornos
        prices = [t['price'] for t in self.trade_history]
        returns = pd.Series(prices).pct_change().dropna()
        
        # Sharpe Ratio 
        # Anualización mediante raíz cuadrada de 252 (días comerciales), asumiendo datos diarios o equivalentes.
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        
        # Max Drawdown
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_dd = drawdown.min()
        
        return f"Sharpe Ratio: {sharpe:.2f} | Max Drawdown: {max_dd:.2%}"

    def run(self):
        #----Bucle Principal (Main Loop):
        #---- - Implementa la lógica de la estrategia de trading.
        #---- - Gestiona el control de tiempo (polling) para evitar saturar la API.
        
        logging.info("Iniciando Bot con Estrategia EMA/RSI...")
        while True:
            
            
            # 1. Actualización de datos técnicos.
            
            price, ema, rsi = self.get_indicators()
            if price is None: continue

            logging.info(f"BTC: {price:.2f} | EMA: {ema:.2f} | RSI: {rsi:.2f}")

            # 2. Evaluación de Condiciones de Entrada (Estrategia):
            if not self.in_position:
                # COMPRA: Precio cruza arriba de EMA + RSI sobrevendido (<40)(Tendencia alcista + Zona de infravaloración).
                
               
                if price > ema and rsi < 40:
                    if self.execute_trade('BUY', price):
                        self.in_position = True
            else:
                # VENTA: Precio cruza abajo de EMA o RSI sobrecomprado (>70)
                # Condición Cierre: Precio < EMA (Cambio de tendencia) O RSI > 70 (Zona de sobrecompra).
                if price < ema or rsi > 70:
                    if self.execute_trade('SELL', price):
                        self.in_position = False
                        logging.info(f"Resumen de Riesgo: {self.calculate_thesis_metrics()}")

                # Pausa de 10 segundos para sincronizar con el cierre de velas y respetar límites de tasa (rate limits).                
            time.sleep(10) # Intervalo sugerido para velas de 1min

if __name__ == "__main__":
    # Punto de entrada del script. Instancia el objeto y maneja la interrupción manual (Ctrl+C).
    bot = TesisTradingBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot apagado. Informe final generado en el log.")