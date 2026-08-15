import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from binance.client import Client
from dotenv import load_dotenv
import requests

# --- CONFIGURACIÓN ESTRATEGIA 3: BOLLINGER REBOUND ---
load_dotenv()
SYMBOL = 'BTCUSDT'
INTERVAL = Client.KLINE_INTERVAL_15MINUTE
DAYS_BACK = "90 days ago UTC" 
QTY = 0.002
COMMISSION_RATE = 0.0004 
ATR_MULTIPLIER = 3.0    # Stop Loss más ajustado
RISK_REWARD_RATIO = 3.0 # Ratio 1:3

def send_telegram_backtest_report(photo_path, stats):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    caption = (
        f"💎 ESTRATEGIA 3: BOLLINGER REBOUND (LONG)\n"
        f"----------------------------------\n"
        f"Operaciones Totales: {stats['total_trades']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"PnL Neto Total: ${stats['net_pnl']:.2f}\n"
        f"Max Drawdown: ${stats['max_drawdown']:.2f}\n"
        f"Ratio de Sharpe: {stats['sharpe_ratio']:.2f}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'photo': f}, timeout=30)
        print("✅ Reporte Estrategia 3 enviado.")
    except Exception as e:
        print(f"❌ Error enviando reporte: {e}")

def run_bollinger_backtest():
    print(f"Ejecutando Estrategia Bollinger Rebound para {SYMBOL}...")
    client = Client()
    klines = client.get_historical_klines(SYMBOL, INTERVAL, DAYS_BACK)

    df = pd.DataFrame(klines).iloc[:, :6]
    df.columns = ['ts', 'open', 'high', 'low', 'close', 'vol']
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    df = df.astype(float)

    # --- INDICADORES ---
    # 1. EMA de tendencia
    df['EMA_200'] = ta.ema(df['close'], length=200)
    # 2. Bandas de Bollinger (20, 2)
    bbands = ta.bbands(df['close'], length=20, std=2)
    df['BBL'] = bbands.iloc[:, 0] # Banda Inferior
    df['BBM'] = bbands.iloc[:, 1] # Banda Media
    df['BBU'] = bbands.iloc[:, 2] # Banda Superior
    # 3. RSI y ATR
    df['RSI_14'] = ta.rsi(df['close'], length=14)
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    
    df.dropna(inplace=True)

    # --- SIMULACIÓN ---
    active_trade = None
    trades = []
    balance = 1000.0
    equity_curve = [balance]
    timestamps = [df.index[0]]

    for i in range(1, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        price = current['open'] # Entramos al abrir la vela
        
        if active_trade is None:
            # LÓGICA DE ENTRADA (COMPRA EN RETROCESO):
            # 1. Tendencia alcista (Precio > EMA 200)
            # 2. El precio cerró por debajo de la banda inferior (Sobreventa estadística)
            # 3. RSI está empezando a subir (evitamos cuchillo cayendo)
            cond_trend = prev['close'] > prev['EMA_200']
            cond_bb = prev['close'] < prev['BBL']
            cond_rsi = prev['RSI_14'] > 30 
            
            if cond_trend and cond_bb and cond_rsi:
                risk = prev['ATR'] * ATR_MULTIPLIER
                active_trade = {
                    'entry': price, 
                    'sl': price - risk, 
                    'tp': price + (risk * RISK_REWARD_RATIO),
                    'comm': price * QTY * COMMISSION_RATE
                }
        else:
            # GESTIÓN DE SALIDA
            if current['low'] <= active_trade['sl'] or current['high'] >= active_trade['tp']:
                exit_p = active_trade['sl'] if current['low'] <= active_trade['sl'] else active_trade['tp']
                comm_total = active_trade['comm'] + (exit_p * QTY * COMMISSION_RATE)
                pnl = ((exit_p - active_trade['entry']) * QTY) - comm_total
                
                balance += pnl
                trades.append(pnl)
                equity_curve.append(balance)
                timestamps.append(df.index[i])
                active_trade = None

    # --- GENERACIÓN DE DASHBOARD ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1])

    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(timestamps, equity_curve, color='#00d4ff', lw=2)
    ax1.fill_between(timestamps, 1000, equity_curve, color='#00d4ff', alpha=0.1)
    ax1.set_title(f'BOLLINGER REBOUND LONG - {SYMBOL}', fontsize=16)
    ax1.grid(alpha=0.1)

    ax2 = fig.add_subplot(gs[1, 0])
    equity_series = pd.Series(equity_curve)
    drawdown = (equity_series - equity_series.cummax())
    ax2.fill_between(range(len(drawdown)), drawdown, color='#ff4444', alpha=0.5)
    ax2.set_title('Drawdown')

    ax3 = fig.add_subplot(gs[1, 1])
    if trades:
        ax3.hist(trades, bins=20, color='#00d4ff', edgecolor='white')
    ax3.set_title('Distribución PnL')

    plt.tight_layout()
    filename = "Dashboard_Bollinger_Long.png"
    plt.savefig(filename, dpi=300)
    
    trade_series = pd.Series(trades)
    stats = {
        'total_trades': len(trades),
        'win_rate': (len(trade_series[trade_series > 0]) / len(trades) * 100) if len(trades) > 0 else 0,
        'net_pnl': balance - 1000.0,
        'max_drawdown': drawdown.min() if len(trades) > 0 else 0,
        'sharpe_ratio': (trade_series.mean() / trade_series.std()) if len(trades) > 1 else 0
    }

    send_telegram_backtest_report(filename, stats)

if __name__ == "__main__":
    run_bollinger_backtest()