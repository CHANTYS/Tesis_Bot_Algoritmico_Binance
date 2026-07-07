import os
import pandas as pd
import pandas_ta as ta
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from binance.client import Client
from dotenv import load_dotenv
import requests

# --- CONFIGURACIÓN PRO ---
load_dotenv() # Carga las credenciales del archivo .env
SYMBOL = 'BTCUSDT'
INTERVAL = Client.KLINE_INTERVAL_15MINUTE
DAYS_BACK = "90 days ago UTC" 
QTY = 0.002
COMMISSION_RATE = 0.0004 
ATR_MULTIPLIER = 4.0
RISK_REWARD_RATIO = 3.0

def send_telegram_backtest_report(photo_path, stats):
    """Envía el dashboard y las estadísticas finales a Telegram."""
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    caption = (
        f"📊 REPORTE DE BACKTESTING (90 DÍAS)\n"
        f"----------------------------------\n"
        f"Operaciones Totales: {stats['total_trades']}\n"
        f"Win Rate: {stats['win_rate']:.2f}%\n"
        f"PnL Neto Total: ${stats['net_pnl']:.2f}\n"
        f"Comisiones Totales: ${stats['total_comm']:.2f}\n"
        f"Max Drawdown: ${stats['max_drawdown']:.2f}\n"
        f"Ratio de Sharpe: {stats['sharpe_ratio']:.2f}"
    )
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    # Sistema de reintentos para evitar errores de red
    for intento in range(3):
        try:
            with open(photo_path, 'rb') as f:
                response = requests.post(
                    url, 
                    data={'chat_id': chat_id, 'caption': caption}, 
                    files={'photo': f}, 
                    timeout=30 
                )
                if response.status_code == 200:
                    print(f"✅ Reporte enviado a Telegram correctamente (Intento {intento + 1}).")
                    return
        except Exception as e:
            print(f"🔄 Reintentando envío a Telegram... ({intento + 1}/3) - Error: {e}")
            continue

def run_pro_backtest():
    print(f"Descargando 3 meses de datos de 15m para {SYMBOL}...")
    client = Client()
    klines = client.get_historical_klines(SYMBOL, INTERVAL, DAYS_BACK)

    df = pd.DataFrame(klines).iloc[:, :6]
    df.columns = ['ts', 'open', 'high', 'low', 'close', 'vol']
    df['ts'] = pd.to_datetime(df['ts'], unit='ms')
    df.set_index('ts', inplace=True)
    df = df.astype(float)

    # Indicadores
    df['EMA_200'] = ta.ema(df['close'], length=200)
    df['RSI_14'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    df['MACD'] = macd.iloc[:, 0]
    df['MACDs'] = macd.iloc[:, 2]
    df['ATR'] = ta.atr(df['high'], df['low'], df['close'], length=14)
    df.dropna(inplace=True)

    # Simulación
    active_trade = None
    trades = []
    balance = 1000.0
    commissions_paid = 0.0  # Variable para rastrear el gasto total en comisiones
    equity_curve = [balance]
    timestamps = [df.index[0]]

    for i in range(2, len(df)):
        current = df.iloc[i]
        prev = df.iloc[i-1]
        prev_2 = df.iloc[i-2]
        price = prev['close']
        
        if active_trade is None:
            # Estrategia
            if price > prev['EMA_200'] and prev['MACD'] > prev['MACDs'] and prev_2['MACD'] <= prev_2['MACDs'] and 45 < prev['RSI_14'] < 85:
                risk = prev['ATR'] * ATR_MULTIPLIER
                active_trade = {
                    'entry': price, 
                    'sl': price - risk, 
                    'tp': price + (risk * RISK_REWARD_RATIO), 
                    'comm_entry': price * QTY * COMMISSION_RATE
                }
        else:
            if current['low'] <= active_trade['sl'] or current['high'] >= active_trade['tp']:
                exit_p = active_trade['sl'] if current['low'] <= active_trade['sl'] else active_trade['tp']
                
                # Calcular comisión de salida y total de la operación
                comm_exit = exit_p * QTY * COMMISSION_RATE
                total_trade_comm = active_trade['comm_entry'] + comm_exit
                commissions_paid += total_trade_comm
                
                # Calcular PnL restando la comisión total de la operación
                pnl = ((exit_p - active_trade['entry']) * QTY) - total_trade_comm
                
                balance += pnl
                trades.append(pnl)
                equity_curve.append(balance)
                timestamps.append(df.index[i])
                active_trade = None

    # --- GENERACIÓN DE DASHBOARD PRO ---
    plt.style.use('dark_background')
    fig = plt.figure(figsize=(15, 10))
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.5, 1])

    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(timestamps, equity_curve, color='#00ff88', lw=2, label='Equity Curve')
    ax1.fill_between(timestamps, 1000, equity_curve, color='#00ff88', alpha=0.1)
    ax1.set_title(f'PERFORMANCE DASHBOARD - {SYMBOL} (90 DÍAS)', fontsize=16, pad=20)
    ax1.set_ylabel('Balance (USD)')
    ax1.grid(alpha=0.2)

    ax2 = fig.add_subplot(gs[1, 0])
    equity_series = pd.Series(equity_curve)
    drawdown = (equity_series - equity_series.cummax())
    ax2.fill_between(range(len(drawdown)), drawdown, color='#ff4444', alpha=0.5)
    ax2.set_title('Inmersión de Riesgo (Drawdown)')
    ax2.set_ylabel('Caída desde el pico ($)')

    ax3 = fig.add_subplot(gs[1, 1])
    ax3.hist(trades, bins=20, color='#3498db', edgecolor='white')
    ax3.axvline(0, color='white', linestyle='--', alpha=0.5)
    ax3.set_title('Distribución de Ganancias/Pérdidas')
    ax3.set_xlabel('PnL por Operación ($)')

    plt.tight_layout()
    filename = "Dashboard_Tesis_Pro.png"
    plt.savefig(filename, dpi=300)
    print(f"Dashboard guardado localmente como '{filename}'")
    
    trade_series = pd.Series(trades)
    wins = len(trade_series[trade_series > 0])
    total_t = len(trades)
    
    # Diccionario de estadísticas actualizado
    stats_summary = {
        'total_trades': total_t,
        'win_rate': (wins / total_t * 100) if total_t > 0 else 0,
        'net_pnl': balance - 1000.0,
        'total_comm': commissions_paid,
        'max_drawdown': drawdown.min() if total_t > 0 else 0,
        'sharpe_ratio': (trade_series.mean() / trade_series.std()) if len(trades) > 1 and trade_series.std() != 0 else 0
    }

    send_telegram_backtest_report(filename, stats_summary)

if __name__ == "__main__":
    run_pro_backtest()