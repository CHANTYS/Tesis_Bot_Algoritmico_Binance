import os
import time
import logging
import pandas as pd
import numpy as np
from binance.client import Client
from binance.exceptions import BinanceAPIException
from dotenv import load_dotenv

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("analisis_tesis.log"), logging.StreamHandler()]
)

class TesisTradingBot:
    def __init__(self, symbol='BTCUSDT', trade_qty=0.001):
        self.symbol = symbol
        self.trade_qty = trade_qty
        self.in_position = False
        
        # --- Parámetros de Realismo (Sugerencia del Director) ---
        self.fee_rate = 0.001       # 0.1% Comisión estándar de Binance
        self.slippage_rate = 0.0005 # 0.05% Desfase estimado de ejecución
        
        # --- Almacenamiento de Datos para Métricas ---
        self.trade_history = [] # Lista de dicts con cada trade
        self.price_history = [] # Para calcular indicadores
        
        # Carga de credenciales
        load_dotenv()
        self.client = Client(os.getenv('BINANCE_TESTNET_API_KEY'), 
                             os.getenv('BINANCE_TESTNET_SECRET'), 
                             testnet=True)

    def get_indicators(self):
        """Obtiene datos históricos y calcula EMA y RSI."""
        try:
            # Pedimos las últimas 100 velas de 1 minuto
            klines = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_1MINUTE, limit=100)
            df = pd.DataFrame(klines, columns=['time', 'open', 'high', 'low', 'close', 'vol', 'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'])
            df['close'] = df['close'].astype(float)
            
            # Cálculo de EMA 20
            df['ema'] = df['close'].ewm(span=20, adjust=False).mean()
            
            # Cálculo de RSI 14 (Lógica manual para no depender de librerías externas pesadas)
            delta = df['close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            df['rsi'] = 100 - (100 / (1 + rs))
            
            return df.iloc[-1]['close'], df.iloc[-1]['ema'], df.iloc[-1]['rsi']
        except Exception as e:
            logging.error(f"Error calculando indicadores: {e}")
            return None, None, None

    def execute_trade(self, side, price):
        """Ejecuta orden y aplica Slippage + Fees para realismo."""
        try:
            # Aplicamos el slippage al precio de ejecución para el registro
            exec_price = price * (1 + self.slippage_rate) if side == 'BUY' else price * (1 - self.slippage_rate)
            cost_fees = (exec_price * self.trade_qty) * self.fee_rate
            
            # Orden real en Testnet
            order = self.client.create_order(
                symbol=self.symbol, side=side, type='MARKET', quantity=self.trade_qty
            )
            
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
        """Calcula Sharpe Ratio y Max Drawdown (Exigencia del tribunal)."""
        if len(self.trade_history) < 2:
            return "Datos insuficientes para métricas."

        # Convertir historial a retornos
        prices = [t['price'] for t in self.trade_history]
        returns = pd.Series(prices).pct_change().dropna()
        
        # Sharpe Ratio (Simplificado para la tesis)
        sharpe = (returns.mean() / returns.std()) * np.sqrt(252) if returns.std() != 0 else 0
        
        # Max Drawdown
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        drawdown = (cumulative - peak) / peak
        max_dd = drawdown.min()
        
        return f"Sharpe Ratio: {sharpe:.2f} | Max Drawdown: {max_dd:.2%}"

    def run(self):
        logging.info("Iniciando Bot con Estrategia EMA/RSI...")
        while True:
            price, ema, rsi = self.get_indicators()
            if price is None: continue

            logging.info(f"BTC: {price:.2f} | EMA: {ema:.2f} | RSI: {rsi:.2f}")

            # Lógica de Estrategia Técnica
            if not self.in_position:
                # COMPRA: Precio cruza arriba de EMA + RSI sobrevendido (<40)
                if price > ema and rsi < 40:
                    if self.execute_trade('BUY', price):
                        self.in_position = True
            else:
                # VENTA: Precio cruza abajo de EMA o RSI sobrecomprado (>70)
                if price < ema or rsi > 70:
                    if self.execute_trade('SELL', price):
                        self.in_position = False
                        logging.info(f"Resumen de Riesgo: {self.calculate_thesis_metrics()}")

            time.sleep(10) # Intervalo sugerido para velas de 1min

if __name__ == "__main__":
    bot = TesisTradingBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info("Bot apagado. Informe final generado en el log.")