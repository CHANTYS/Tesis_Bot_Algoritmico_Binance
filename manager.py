import asyncio
import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- IMPORTACIONES DE TUS ARCHIVOS DE BACKTESTING ---
try:
    from BotFuturos_Short import EliteTradingEngine as EngineShort
    from BotFuturos_Long_Bollinger import EliteTradingEngine as EngineLong
    
    # Importamos las funciones de ejecución de los 4 archivos solicitados
    from Backtesting_Long import run_pro_backtest as run_long_v1
    from Backtesting_Long_V2_BOLLINGER import run_bollinger_backtest as run_long_v2
    from Backtesting_Short import run_short_backtest as run_short_v1
    from Backtesting_Short_V5_BEAR_MASTER import run_short_v5_backtest as run_short_v5
except ImportError as e:
    print(f"❌ Error al importar estrategias o backtestings: {e}")

# Cargar variables de entorno
load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
try:
    MI_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))
except:
    MI_CHAT_ID = 0

# Configuración de Logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("manager.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TesisBotManager:
    def __init__(self):
        self.active_tasks = {} 

    async def check_security(self, update: Update):
        if update.effective_chat.id != MI_CHAT_ID:
            await update.effective_chat.send_message("🚫 No autorizado.")
            return False
        return True

    # --- MENÚ PRINCIPAL (BOTS EN VIVO) ---
    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_security(update): return
        
        # CORRECCIÓN: Verificar si la tarea existe Y si no ha terminado (está corriendo)
        sh_running = 'short' in self.active_tasks and not self.active_tasks['short'].done()
        lg_running = 'long' in self.active_tasks and not self.active_tasks['long'].done()

        st_short = "🟢 ACTIVO" if sh_running else "⚪ APAGADO"
        st_long = "🟢 ACTIVO" if lg_running else "⚪ APAGADO"

        keyboard = [
            [InlineKeyboardButton("🚀 Iniciar Short", callback_data='start_short'),
             InlineKeyboardButton("🛑 Parar Short", callback_data='stop_short')],
            [InlineKeyboardButton("🚀 Iniciar Long", callback_data='start_long'),
             InlineKeyboardButton("🛑 Parar Long", callback_data='stop_long')],
            [InlineKeyboardButton("📊 MENÚ DE BACKTESTING (/test)", callback_data='test_menu')],
            [InlineKeyboardButton("🆘 CERRAR TODO", callback_data='emergency_stop')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        texto = f"🤖 **CONTROL EN VIVO**\nShort: `{st_short}`\nLong: `{st_long}`"
        
        # CORRECCIÓN: Manejar edición de mensaje para refrescar estado
        try:
            if update.message: 
                await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
            else: 
                await update.callback_query.edit_message_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
        except Exception:
            pass # Evita error si el mensaje es idéntico

    # --- NUEVO MENÚ DE PRUEBAS (/test) ---
    async def test_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Genera el menú con las 4 estrategias de backtesting"""
        if update.effective_chat.id != MI_CHAT_ID: return

        keyboard = [
            [
                InlineKeyboardButton("📈 Long V1 (Trend)", callback_data='run_test_l1'),
                InlineKeyboardButton("💎 Long V2 (Bollinger)", callback_data='run_test_l2')
            ],
            [
                InlineKeyboardButton("📉 Short V1 (Classic)", callback_data='run_test_s1'),
                InlineKeyboardButton("🔴 Short V5 (BearMaster)", callback_data='run_test_s5')
            ],
            [InlineKeyboardButton("🔙 Volver al Control Vivo", callback_data='back_to_main')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        texto = "🧪 **LABORATORIO DE PRUEBAS**\nSeleccione la estrategia para correr backtesting (90 días):"
        
        if update.message:
            await update.message.reply_text(texto, reply_markup=reply_markup, parse_mode='Markdown')
        else:
            await update.callback_query.edit_message_text(texto, reply_markup=reply_markup, parse_mode='Markdown')

    async def handle_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        loop = asyncio.get_event_loop()

        # --- LÓGICA DE BOTS EN VIVO ---
        if query.data == 'start_short':
            if 'short' not in self.active_tasks or self.active_tasks['short'].done():
                self.active_tasks['short'] = asyncio.create_task(EngineShort().run())
                # Refrescamos el menú para mostrar el círculo verde
                await self.main_menu(update, context)
        
        elif query.data == 'stop_short':
            if 'short' in self.active_tasks:
                self.active_tasks['short'].cancel()
                del self.active_tasks['short']
                await self.main_menu(update, context)
        
        elif query.data == 'start_long':
            if 'long' not in self.active_tasks or self.active_tasks['long'].done():
                self.active_tasks['long'] = asyncio.create_task(EngineLong().run())
                await self.main_menu(update, context)
        
        elif query.data == 'stop_long':
            if 'long' in self.active_tasks:
                self.active_tasks['long'].cancel()
                del self.active_tasks['long']
                await self.main_menu(update, context)

        # --- LÓGICA DE BACKTESTING ---
        elif query.data.startswith('run_test_'):
            mapping = {
                'run_test_l1': ("Long V1 Trend", run_long_v1),
                'run_test_l2': ("Long V2 Bollinger", run_long_v2),
                'run_test_s1': ("Short V1 Classic", run_short_v1),
                'run_test_s5': ("Short V5 BearMaster", run_short_v5)
            }
            name, func = mapping[query.data]
            await context.bot.send_message(MI_CHAT_ID, f"⏳ Corriendo Backtest: **{name}**...\nEsto tardará unos segundos.")
            await loop.run_in_executor(None, func)
            await context.bot.send_message(MI_CHAT_ID, f"✅ Backtest **{name}** finalizado.")

        # --- NAVEGACIÓN ---
        elif query.data == 'test_menu':
            await self.test_menu(update, context)
        elif query.data == 'back_to_main':
            await self.main_menu(update, context)
        elif query.data == 'emergency_stop':
            for t in self.active_tasks.values(): t.cancel()
            self.active_tasks = {}
            await query.edit_message_text("☢️ SISTEMA APAGADO.")

def main():
    manager = TesisBotManager()
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", manager.main_menu))
    app.add_handler(CommandHandler("test", manager.test_menu))
    app.add_handler(CallbackQueryHandler(manager.handle_actions))

    print("🤖 Manager Pro activo. Usa /start para vivo o /test para backtesting.")
    app.run_polling()

if __name__ == '__main__':
    main()