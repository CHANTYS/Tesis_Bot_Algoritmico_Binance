import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from binance.client import Client
from dotenv import load_dotenv
import requests

# --- CONFIGURACIÓN ESTRATEGIA SHORT ---
load_dotenv()
SYMBOL = 'BTCUSDT'
INTERVAL = Client.KLINE_INTERVAL_15MINUTE
DAYS_BACK = "90 days ago UTC" 
QTY = 0.002
COMMISSION_RATE = 0.0004 
ATR_MULTIPLIER = 3.5    # SL un poco más ajustado para cortos
RISK_REWARD_RATIO = 3.0 # Buscamos que un corto ganador pague tres perdedores

def send_telegram_backtest_report(photo_path, stats):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    caption = (
        f"📉 REPORTE BACKTESTING: ESTRATEGIA SHORT (15m) A 90 DÍAS\n"
        f"----------------------------------\n"
        f"Operaciones Totales: {stats['total_trades']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"PnL Neto Total: ${stats['net_pnl']:.2f}\n"
        f"Comisiones Totales: ${stats['total_comm']:.2f}\n"
        f"Max Drawdown: ${stats['max_drawdown']:.2f}\n"
        f"Ratio de Sharpe: {stats['sharpe_ratio']:.2f}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'photo': f}, timeout=30)
        print("✅ Reporte Short enviado a Telegram.")
    except Exception as e:
        print(f"❌ Error enviando reporte: {e}")

def run_short_backtest():
    print(f"Analizando oportunidades de SHORT para {SYMBOL} (15m)...")
    client = Client()
    klines = client.get_historical_klines(SYMBOL, INTERVAL, DAYS_BACK)

    df = pd.DataFrame(klines).iloc[:, :6]
    df.columns = ['ts', 'open', 'high', 'low', 'close', 'vol']
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    df = df.astype(float)

    # Indicadores Técnicos
    df['EMA_200'] = ta.ema(df['close'], length=200)
    df['RSI_14'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df['MACD'] = macd.iloc[:, 0]
    df['MACDs'] = macd.iloc[:, 2]
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df.dropna(inplace=True)

    # Simulación de Trading (SHORT)
    active_trade = None
    trades = []
    balance = 1000.0
    commissions_paid = 0.0
    equity_curve = [balance]
    timestamps = [df.index[0]]

    for i in range(2, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        prev_2 = df.iloc[i-2]
        price = prev['close']
        
        if active_trade is None:
            # LÓGICA DE VENTA (SHORT):
            # 1. Precio por DEBAJO de EMA 200 (Tendencia bajista)
            # 2. Cruce bajista de MACD (MACD cruza hacia abajo la señal)
            # 3. RSI entre 30 y 55 (Evitamos vender si ya está muy sobrevendido)
            if price < prev['EMA_200'] and prev['MACD'] < prev['MACDs'] and prev_2['MACD'] >= prev_2['MACDs'] and 30 < prev['RSI_14'] < 55:
                risk = prev['ATR'] * ATR_MULTIPLIER
                active_trade = {
                    'entry': price, 
                    'sl': price + risk, # El Stop Loss está ARRIBA del precio
                    'tp': price - (risk * RISK_REWARD_RATIO), # El Take Profit está ABAJO
                    'comm_entry': price * QTY * COMMISSION_RATE
                }
        else:
            # Verificamos si toca SL (arriba) o TP (abajo)
            if current['high'] >= active_trade['sl'] or current['low'] <= active_trade['tp']:
                exit_p = active_trade['sl'] if current['high'] >= active_trade['sl'] else active_trade['tp']
                
                comm_exit = exit_p * QTY * COMMISSION_RATE
                total_trade_comm = active_trade['comm_entry'] + comm_exit
                commissions_paid += total_trade_comm
                
                # En Short, el PnL es (Entrada - Salida)
                pnl = ((active_trade['entry'] - exit_p) * QTY) - total_trade_comm
                
                balance += pnl
                trades.append(pnl)
                equity_curve.append(balance)
                timestamps.append(df.index[i])
                active_trade = None

    # --- DASHBOARD VISUAL ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1])

    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(timestamps, equity_curve, color='#ff4444', lw=2) # Rojo para estrategia Short
    ax1.fill_between(timestamps, 1000, equity_curve, color='#ff4444', alpha=0.1)
    ax1.set_title(f'DASHBOARD ESTRATEGIA SHORT - {SYMBOL} (15m)', fontsize=16, pad=20)
    ax1.set_ylabel('Balance (USD)')
    ax1.grid(alpha=0.2)

    ax2 = fig.add_subplot(gs[1, 0])
    equity_series = pd.Series(equity_curve)
    drawdown = (equity_series - equity_series.cummax())
    ax2.fill_between(range(len(drawdown)), drawdown, color='#ff4444', alpha=0.5)
    ax2.set_title('Drawdown de la Estrategia')

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(trades, bins=20, color='#e74c3c', edgecolor='white')
    ax3.axvline(0, color='white', linestyle='--')
    ax3.set_title('Distribución PnL (Shorts)')

    plt.tight_layout()
    filename = "Dashboard_Short.png"
    plt.savefig(filename, dpi=300)
    
    trade_series = pd.Series(trades)
    stats = {
        'total_trades': len(trades),
        'win_rate': (len(trade_series[trade_series > 0]) / len(trades) * 100) if len(trades) > 0 else 0,
        'net_pnl': balance - 1000.0,
        'total_comm': commissions_paid,
        'max_drawdown': drawdown.min() if len(trades) > 0 else 0,
        'sharpe_ratio': (trade_series.mean() / trade_series.std()) if len(trades) > 1 else 0
    }

    send_telegram_backtest_report(filename, stats)

if __name__ == "__main__":
    run_short_backtest()