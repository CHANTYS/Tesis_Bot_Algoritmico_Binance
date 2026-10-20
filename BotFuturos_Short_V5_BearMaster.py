import os
import sys
import logging
import asyncio
import json
import socket
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import requests
import aiohttp
from aiohttp.resolver import ThreadedResolver
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException

# --- FIX DE CODIFICACION PARA LOGS INDIVIDUALES ---
if sys.platform == 'win32':
    try: sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError: pass

# --- CONFIGURACION DE LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler("trading_futures_short_v5.log", encoding='utf-8'), 
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class Config:
    load_dotenv()
    SYMBOL = 'BTCUSDT'
    QTY = 0.005             
    INTERVAL = AsyncClient.KLINE_INTERVAL_1MINUTE
    LEVERAGE = 10           
    RISK_REWARD_RATIO = 2.0 
    ATR_MULTIPLIER = 3.0    
    COMMISSION_RATE = 0.0004 
    
    BINANCE_KEY = os.getenv('BINANCE_TESTNET_API_KEY')
    BINANCE_SECRET = os.getenv('BINANCE_TESTNET_SECRET')
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    HISTORY_FILE = "historial_short_v5.json"

class TradingVisualizer:
    @staticmethod
    def generate_dashboard(df: pd.DataFrame, trades: List[Dict], stats: Dict):
        if df.empty: return None
        tz_local = 'America/Argentina/La_Rioja'
        df_plot = df.copy()
        df_plot.index = df_plot.index.tz_localize('UTC').tz_convert(tz_local)
        
        plt.style.use('dark_background')
        fig = plt.figure(figsize=(16, 18))
        fig.set_facecolor('#0d1117')
        gs = gridspec.GridSpec(5, 1, height_ratios=[3, 1, 1, 1, 0.8], hspace=0.3)

        ax1 = fig.add_subplot(gs[0])
        ax1.set_facecolor('#0d1117')
        ax1.plot(df_plot.index, df_plot['close'], color='#58a6ff', lw=1.5, label=f"Precio {Config.SYMBOL}")
        if 'EMA_200' in df_plot.columns:
            ax1.plot(df_plot.index, df_plot['EMA_200'], color='#f0883e', ls='--', alpha=0.8, label="EMA 200")
        
        for t in trades:
            try:
                e_t = pd.to_datetime(t['entry_time']).tz_localize('UTC').tz_convert(tz_local)
                ax1.scatter(e_t, t['entry_price'], marker='v', color='#f85149', s=200, zorder=5, label='Entrada Short' if 'Entrada Short' not in ax1.get_legend_handles_labels()[1] else "")
                if t['status'] == 'CLOSED':
                    x_t = pd.to_datetime(t['exit_time']).tz_localize('UTC').tz_convert(tz_local)
                    color = '#3fb950' if t['pnl_neto'] > 0 else '#f85149'
                    ax1.scatter(x_t, t['exit_price'], marker='^', color=color, s=200, zorder=5, label='Cierre Short' if 'Cierre Short' not in ax1.get_legend_handles_labels()[1] else "")
            except: continue
            
        ax1.legend(loc='upper left', frameon=False)
        ax1.grid(color='#30363d', alpha=0.3)

        ax2 = fig.add_subplot(gs[1], sharex=ax1)
        if 'MACD' in df_plot.columns:
            ax2.plot(df_plot.index, df_plot['MACD'], color='#58a6ff', lw=1)
            ax2.plot(df_plot.index, df_plot['MACDs'], color='#f0883e', lw=1)
            colors = ['#238636' if x >= 0 else '#da3633' for x in df_plot['MACDh']]
            ax2.bar(df_plot.index, df_plot['MACDh'], color=colors, alpha=0.5)
        ax2.set_ylabel("MACD", fontsize=10)

        ax3 = fig.add_subplot(gs[2], sharex=ax1)
        if 'STOCH_K' in df_plot.columns:
            ax3.plot(df_plot.index, df_plot['STOCH_K'], color='#bc8cff', lw=1.2)
            ax3.axhline(80, color='#f85149', ls=':', alpha=0.5)
            ax3.axhline(20, color='#3fb950', ls=':', alpha=0.5)
        ax3.set_ylabel("Stoch RSI", fontsize=10)

        ax4 = fig.add_subplot(gs[3], sharex=ax1)
        if 'RSI_14' in df_plot.columns:
            ax4.plot(df_plot.index, df_plot['RSI_14'], color='#3fb950', lw=1.2)
            ax4.axhline(70, color='#f85149', ls=':', alpha=0.5)
            ax4.axhline(30, color='#3fb950', ls=':', alpha=0.5)
            ax4.fill_between(df_plot.index, 30, 70, color='#3fb950', alpha=0.05)
        ax4.set_ylabel("RSI 14", fontsize=10)
        ax4.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=df_plot.index.tz))
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')

        ax5 = fig.add_subplot(gs[4])
        ax5.axis('off')
        summary_text = (
            f"RESUMEN DE SESIÓN: BEAR MASTER V5 (SHORT)\n"
            f"{'='*60}\n"
            f"Operaciones Totales: {stats['total_trades']}  |  Win Rate: {stats['win_rate']:.2f}%\n"
            f"PnL Neto Total: ${stats['net_pnl']:.4f}  |  Comisiones: ${stats['total_commissions']:.4f}\n"
            f"Profit Factor: {stats['profit_factor']:.2f}  |  Ratio de Sharpe: {stats['sharpe_ratio']:.2f}\n"
            f"Máximo Drawdown: ${stats['max_drawdown']:.2f}"
        )
        ax5.text(0.5, 0.5, summary_text, fontsize=13, ha='center', va='center', family='monospace',
                 bbox=dict(boxstyle="round", facecolor='#161b22', edgecolor='#30363d', pad=1))

        filename = f"reporte_short_pro_v5_{datetime.now().strftime('%H%M')}.png"
        plt.savefig(filename, dpi=200, facecolor='#0d1117', bbox_inches='tight')
        plt.close()
        return filename

class EliteTradingEngine:
    def __init__(self):
        self.client = None
        self.data = pd.DataFrame()
        self.trades = self.load_history() 
        self.active_trade = None
        self.is_running = False

    def load_history(self):
        if os.path.exists(Config.HISTORY_FILE):
            try:
                with open(Config.HISTORY_FILE, 'r') as f: return json.load(f)
            except: return []
        return []

    def save_history(self):
        try:
            with open(Config.HISTORY_FILE, 'w') as f: json.dump(self.trades, f, indent=4)
        except Exception as e: logger.error(f"Error historial: {e}")

    def get_summary(self):
        closed = [t for t in self.trades if t['status'] == 'CLOSED']
        if not closed: 
            return {'total_trades': 0, 'win_rate': 0.0, 'net_pnl': 0.0, 'max_drawdown': 0.0, 
                    'total_commissions': 0.0, 'sharpe_ratio': 0.0, 'profit_factor': 0.0}
        
        pnls = [t['pnl_neto'] for t in closed]
        comms = [t['total_comm'] for t in closed]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        
        pf = sum(wins) / abs(sum(losses)) if losses and sum(losses) != 0 else 0.0
        sharpe = (np.mean(pnls) / np.std(pnls)) if len(pnls) > 1 and np.std(pnls) > 0 else 0.0
        
        cum_pnl = np.cumsum(pnls)
        peak = np.maximum.accumulate(cum_pnl)
        drawdown = peak - cum_pnl

        return {
            'total_trades': len(closed), 'win_rate': (len(wins) / len(closed)) * 100,
            'net_pnl': sum(pnls), 'max_drawdown': np.max(drawdown) if len(drawdown) > 0 else 0.0,
            'total_commissions': sum(comms), 'sharpe_ratio': sharpe, 'profit_factor': pf
        }

    def send_telegram_msg(self, text):
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendMessage"
        try: requests.post(url, json={"chat_id": Config.TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}, timeout=5)
        except: pass

    def send_telegram_photo(self, path, stats):
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_TOKEN}/sendPhoto"
        caption = (
            f"🔴 <b>EXPERT REPORT: SHORT V5 SESSION</b>\n"
            f"----------------------------------\n"
            f"PnL Neto: ${stats['net_pnl']:.4f}\n"
            f"Comisiones: ${stats['total_commissions']:.4f}\n"
            f"Win Rate: {stats['win_rate']:.1f}%\n"
            f"Operaciones: {stats['total_trades']}"
        )
        try:
            with open(path, 'rb') as f:
                requests.post(url, data={'chat_id': Config.TELEGRAM_CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}, files={'photo': f}, timeout=15)
        except: pass

    async def execute_order(self, side, reason, price, time, sl=None, tp=None):
        try:
            order = await self.client.futures_create_order(
                symbol=Config.SYMBOL, side=side, type='MARKET', quantity=Config.QTY
            )
            comm = price * Config.QTY * Config.COMMISSION_RATE
            if reason == 'SHORT':
                self.active_trade = {'type': 'SHORT', 'entry_price': price, 'entry_time': str(time), 'sl': sl, 'tp': tp, 'status': 'OPEN', 'comm_in': comm}
                self.send_telegram_msg(f"🔴 <b>ENTRADA SHORT (V5)</b>\nPrecio: ${price:.2f}\nSL: ${sl:.2f} | TP: ${tp:.2f}")
            else:
                t = self.active_trade
                pnl_bruto = (t['entry_price'] - price) * Config.QTY
                total_comm = comm + t['comm_in']
                t.update({'exit_price': price, 'exit_time': str(time), 'total_comm': total_comm, 'pnl_neto': pnl_bruto - total_comm, 'status': 'CLOSED'})
                self.trades.append(t)
                self.save_history()
                self.active_trade = None
                emoji = "✅" if t['pnl_neto'] > 0 else "❌"
                self.send_telegram_msg(f"{emoji} <b>CIERRE SHORT</b>\nPnL Neto: ${t['pnl_neto']:.4f}")
        except Exception as e: logger.error(f"Error Orden: {e}")

    async def run(self):
        custom_connector = aiohttp.TCPConnector(
            resolver=ThreadedResolver(),
            family=socket.AF_INET,
            ssl=False
        )

        self.client = await AsyncClient.create(
            Config.BINANCE_KEY, 
            Config.BINANCE_SECRET, 
            testnet=True,
            session_params={'connector': custom_connector}
        )
        self.client.FUTURES_URL = 'https://testnet.binancefuture.com/fapi/v1'
        
        try:
            await self.client.futures_change_leverage(symbol=Config.SYMBOL, leverage=Config.LEVERAGE)
            logger.info(f"Leverage: {Config.LEVERAGE}x")
        except: pass

        logger.info("Bot Short Bear Master V5 Activo...")
        self.send_telegram_msg("🚀 <b>Bot Short V5 (Bear Master) Conectado</b>")
        
        self.is_running = True
        try:
            while self.is_running:
                try:
                    bm = BinanceSocketManager(self.client)
                    async with bm.futures_multiplex_socket([f"{Config.SYMBOL.lower()}@kline_15m"]) as stream:
                        while self.is_running:
                            res = await stream.recv()
                            if not res or 'data' not in res: continue
                            k = res['data']['k']
                            
                            # 1. Tick a Tick: Evaluar SL / TP
                            price_live = float(k['c'])
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] {Config.SYMBOL} ${price_live} | OK", end='\r')
                            
                            if self.active_trade:
                                t = self.active_trade
                                if price_live >= t['sl'] or price_live <= t['tp']:
                                    await self.execute_order('BUY', 'CIERRE', price_live, datetime.now())
                                continue 
                            
                            # 2. Cierre de Vela: Lógica Bear Master V5
                            if k['x'] and not self.active_trade:
                                klines = await self.client.futures_historical_klines(Config.SYMBOL, Config.INTERVAL, "3 days ago UTC")
                                df = pd.DataFrame(klines).iloc[:, :6]
                                df.columns = ['ts', 'open', 'high', 'low', 'close', 'vol']
                                df.set_index(pd.to_datetime(df['ts'], unit='ms'), inplace=True)
                                self.data = df.astype(float)
                                
                                self.data['EMA_200'] = ta.ema(self.data['close'], length=200)
                                self.data['RSI_14'] = ta.rsi(self.data['close'], length=14)
                                stoch = ta.stochrsi(self.data['close'])
                                if stoch is not None: self.data['STOCH_K'] = stoch.iloc[:, 0]
                                self.data['VOL_MA'] = ta.sma(self.data['vol'], length=20)
                                self.data['ATR'] = ta.atr(self.data['high'], self.data['low'], self.data['close'], length=14)
                                macd = ta.macd(self.data['close'])
                                if macd is not None:
                                    self.data['MACD'], self.data['MACDh'], self.data['MACDs'] = macd.iloc[:,0], macd.iloc[:,1], macd.iloc[:,2]

                                last = self.data.iloc[-1]
                                prev = self.data.iloc[-2]
                                price_close = last['close']

                                if price_close < last['EMA_200'] and prev['STOCH_K'] > 80 and last['STOCH_K'] < 80 and last['vol'] > last['VOL_MA']:
                                    risk = last['ATR'] * Config.ATR_MULTIPLIER
                                    await self.execute_order('SELL', 'SHORT', price_close, self.data.index[-1], price_close + risk, price_close - (risk * Config.RISK_REWARD_RATIO))
                                    
                except asyncio.CancelledError:
                    self.is_running = False
                    raise 
                except Exception as e:
                    if self.is_running:
                        # Emoji quitado de la consola local para evitar errores en Windows
                        logger.error(f"Caida de red detectada: {e}. Reconectando en 15s...")
                        await asyncio.sleep(15)

        except asyncio.CancelledError:
            # Emoji quitado de la consola local
            logger.info("Tarea de bot Short V5 detenida por el Manager.")
        finally:
            logger.info("Generando reporte final y cerrando...")
            stats = self.get_summary()
            
            # Evita el error al cerrar si no hay datos descargados aún
            if not self.data.empty:
                path = TradingVisualizer.generate_dashboard(self.data, self.trades, stats)
                if path: self.send_telegram_photo(path, stats)
            else:
                logger.info("No se generaron graficos porque el bot se detuvo antes de registrar datos del mercado.")
                self.send_telegram_msg("⚠️ <b>Sesión finalizada</b>\nEl bot se detuvo antes de registrar datos suficientes para el gráfico.")
            
            if self.client:
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_running():
                        await self.client.close_connection()
                except RuntimeError:
                    pass

if __name__ == "__main__":
    asyncio.run(EliteTradingEngine().run())