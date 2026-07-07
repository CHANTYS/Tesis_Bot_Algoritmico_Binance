import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from binance.client import Client
from dotenv import load_dotenv
import requests

# --- CONFIGURACIÓN ESTRATEGIA V5: INSTITUTIONAL SHORT REJECTION ---
load_dotenv()
SYMBOL = 'BTCUSDT'
INTERVAL = Client.KLINE_INTERVAL_15MINUTE
DAYS_BACK = "90 days ago UTC" 
QTY = 0.005 
COMMISSION_RATE = 0.0004 
RISK_REWARD_RATIO = 2.0 # Buscamos trades rápidos y seguros

def send_telegram_backtest_report(photo_path, stats):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    caption = (
        f"🔴 ESTRATEGIA V5: INSTITUTIONAL SHORT (BEAR MASTER)\n"
        f"----------------------------------\n"
        f"Operaciones Totales: {stats['total_trades']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"PnL Neto Total: ${stats['net_pnl']:.2f}\n"
        f"Comisiones: ${stats['total_comm']:.2f}\n"
        f"Max Drawdown: ${stats['max_drawdown']:.2f}\n"
        f"Ratio de Sharpe: {stats['sharpe_ratio']:.2f}"
    )
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as f:
            requests.post(url, data={'chat_id': chat_id, 'caption': caption}, files={'photo': f}, timeout=30)
    except: pass

def run_short_v5_backtest():
    print(f"Iniciando Backtesting Short V5 para {SYMBOL}...")
    client = Client()
    klines = client.get_historical_klines(SYMBOL, INTERVAL, DAYS_BACK)

    df = pd.DataFrame(klines).iloc[:, :6]
    df.columns = ['ts', 'open', 'high', 'low', 'close', 'vol']
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    df = df.astype(float)

    # --- INDICADORES PARA SHORT ---
    # 1. Tendencia Bajista (Precio debajo de EMA 200)
    df['EMA_200'] = ta.ema(df['close'], length=200)
    
    # 2. Stochastic RSI (Para detectar rebotes agotados)
    stoch = ta.stochrsi(df['close'], length=14, rsi_length=14, k=3, d=3)
    df['STOCH_K'] = stoch['STOCHRSIk_14_14_3_3']
    
    # 3. Volumen MA
    df['VOL_MA'] = ta.sma(df['vol'], length=20)
    
    # 4. ATR para el Stop Loss
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    
    df.dropna(inplace=True)

    # --- SIMULACIÓN DE SHORT ---
    active_trade = None
    trades = []
    balance = 1000.0
    commissions_paid = 0.0
    equity_curve = [balance]
    timestamps = [df.index[0]]

    for i in range(2, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        
        if active_trade is None:
            # LÓGICA DE ENTRADA (SHORT):
            # 1. El precio está por DEBAJO de la EMA 200 (Tendencia bajista).
            # 2. El Stoch RSI estaba sobrecomprado (> 80) y empieza a cruzar hacia abajo.
            # 3. El volumen es mayor al promedio.
            cond_trend = current['close'] < current['EMA_200']
            cond_stoch = prev['STOCH_K'] > 80 and current['STOCH_K'] < 80
            cond_vol = current['vol'] > current['VOL_MA']
            
            if cond_trend and cond_stoch and cond_vol:
                price = current['close']
                # En SHORT, el SL está ARRIBA del precio
                sl_dist = current['ATR'] * 3.0
                active_trade = {
                    'entry': price, 
                    'sl': price + sl_dist, 
                    'tp': price - (sl_dist * RISK_REWARD_RATIO),
                    'comm_entry': price * QTY * COMMISSION_RATE
                }
        else:
            # GESTIÓN DE SALIDA (SHORT)
            # Toca SL (subió) o toca TP (bajó)
            if current['high'] >= active_trade['sl'] or current['low'] <= active_trade['tp']:
                exit_p = active_trade['sl'] if current['high'] >= active_trade['sl'] else active_trade['tp']
                comm_exit = exit_p * QTY * COMMISSION_RATE
                total_comm = active_trade['comm_entry'] + comm_exit
                
                # PnL de un Short: (Precio Entrada - Precio Salida)
                pnl = ((active_trade['entry'] - exit_p) * QTY) - total_comm
                
                balance += pnl
                commissions_paid += total_comm
                trades.append(pnl)
                equity_curve.append(balance)
                timestamps.append(df.index[i])
                active_trade = None

    # --- DASHBOARD ROJO (TEMA SHORT) ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1])
    
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(timestamps, equity_curve, color='#e74c3c', lw=2) # Rojo Bear
    ax1.fill_between(timestamps, 1000, equity_curve, color='#e74c3c', alpha=0.1)
    ax1.set_title(f'V5 SHORT REJECTION PRO - {SYMBOL}', fontsize=16)
    
    ax2 = fig.add_subplot(gs[1, 0])
    equity_series = pd.Series(equity_curve)
    drawdown = (equity_series - equity_series.cummax())
    ax2.fill_between(range(len(drawdown)), drawdown, color='#ff4444', alpha=0.5)
    
    ax3 = fig.add_subplot(gs[1, 1])
    if trades:
        pd.Series(trades).hist(ax=ax3, bins=15, color='#e74c3c', edgecolor='white')

    plt.tight_layout()
    filename = "Dashboard_Short_V5.png"
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
    run_short_v5_backtest()