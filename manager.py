import asyncio
import logging
import os
import sys

# --- FIX DE CODIFICACIÓN PARA WINDOWS (EVITA ERRORES CON EMOJIS) ---
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

# --- FIX PARA QUE FUNCIONE DENTRO DEL .EXE (PyInstaller) ---
if getattr(sys, 'frozen', False):
    # Estamos ejecutando el .exe compilado
    base_path = sys._MEIPASS
    sys.path.insert(0, base_path)
else:
    # Estamos ejecutando el código normal (desarrollo)
    base_path = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, base_path)

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- IMPORTACIONES DE LOS BOTS EN VIVO ---
try:
    from BotFuturos_Long import EliteTradingEngine as EngineLongV1
    from BotFuturos_Long_Bollinger import EliteTradingEngine as EngineLongV2
    from BotFuturos_Short import EliteTradingEngine as EngineShortV1
    from BotFuturos_Short_V5_BearMaster import EliteTradingEngine as EngineShortV5
    
    from Backtesting_Long import run_pro_backtest as run_long_v1
    from Backtesting_Long_V2_BOLLINGER import run_bollinger_backtest as run_long_v2
    from Backtesting_Short import run_short_backtest as run_short_v1
    from Backtesting_Short_V5_BEAR_MASTER import run_short_v5_backtest as run_short_v5
except ImportError as e:
    print(f"❌ Error al importar estrategias: {e}")

load_dotenv()
TOKEN = os.getenv('TELEGRAM_TOKEN')
try:
    MI_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID'))
except:
    MI_CHAT_ID = 0

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("manager.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def handle_task_result(task: asyncio.Task):
    try:
        task.result()
    except asyncio.CancelledError:
        logger.info("ℹ️ Tarea de bot detenida por el usuario.")
    except Exception as e:
        logger.error(f"FALLO CRÍTICO EN EL BOT: {e}", exp_info=True)

class TesisBotManager:
    def __init__(self):
        self.active_tasks = {} 

    async def check_security(self, update: Update):
        if update.effective_chat.id != MI_CHAT_ID:
            await update.effective_chat.send_message("🚫 No autorizado.")
            return False
        return True

    async def main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await self.check_security(update): return
        
        lv1_running = 'long_v1' in self.active_tasks and not self.active_tasks['long_v1'].done()
        lv2_running = 'long_v2' in self.active_tasks and not self.active_tasks['long_v2'].done()
        sv1_running = 'short_v1' in self.active_tasks and not self.active_tasks['short_v1'].done()
        sv5_running = 'short_v5' in self.active_tasks and not self.active_tasks['short_v5'].done()

        keyboard = [
            [InlineKeyboardButton("🚀 Iniciar Long V1", callback_data='start_long_v1'),
             InlineKeyboardButton("🛑 Parar", callback_data='stop_long_v1')],
            [InlineKeyboardButton("💎 Iniciar Long V2 (BolingerBds)", callback_data='start_long_v2'),
             InlineKeyboardButton("🛑 Parar", callback_data='stop_long_v2')],
            [InlineKeyboardButton("📉 Iniciar Short V1", callback_data='start_short_v1'),
             InlineKeyboardButton("🛑 Parar", callback_data='stop_short_v1')],
            [InlineKeyboardButton("🐻 Iniciar Short V5(BearMr)", callback_data='start_short_v5'),
             InlineKeyboardButton("🛑 Parar", callback_data='stop_short_v5')],
            [InlineKeyboardButton("📊 MENÚ DE BACKTESTING (/test)", callback_data='test_menu')],
            [InlineKeyboardButton("🆘 CERRAR TODOS", callback_data='emergency_stop')]
        ]
        
        texto = (f"🤖 **CONTROL EN VIVO (TESTNET)**\n\n"
                 f"📈 Long V1: {'🟢 `ACTIVO`' if lv1_running else '⚪ `APAGADO`'}\n"
                 f"💎 Long V2: {'🟢 `ACTIVO`' if lv2_running else '⚪ `APAGADO`'}\n"
                 f"📉 Short V1: {'🟢 `ACTIVO`' if sv1_running else '⚪ `APAGADO`'}\n"
                 f"🐻 Short V5: {'🟢 `ACTIVO`' if sv5_running else '⚪ `APAGADO`'}")
        
        try:
            if update.message: 
                await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
            else: 
                await update.callback_query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        except Exception: pass 

    async def test_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.id != MI_CHAT_ID: return
        keyboard = [
            [InlineKeyboardButton("📈 Long V1 (Trend)", callback_data='run_test_l1'), InlineKeyboardButton("💎 Long V2 (BB)", callback_data='run_test_l2')],
            [InlineKeyboardButton("📉 Short V1 (Classic)", callback_data='run_test_s1'), InlineKeyboardButton("🐻 Short V5 (BM)", callback_data='run_test_s5')],
            [InlineKeyboardButton("🔙 Volver al Control Vivo", callback_data='back_to_main')]
        ]
        texto = "🧪 **LABORATORIO DE PRUEBAS**\nSeleccione la estrategia:"
        if update.message: await update.message.reply_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        else: await update.callback_query.edit_message_text(texto, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')

    async def handle_actions(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        loop = asyncio.get_event_loop()

        if query.data.startswith('start_') or query.data.startswith('stop_'):
            action, bot_key = query.data.split('_', 1) 
            engine_map = {'long_v1': EngineLongV1, 'long_v2': EngineLongV2, 'short_v1': EngineShortV1, 'short_v5': EngineShortV5}
            
            if action == 'start' and bot_key in engine_map:
                if bot_key not in self.active_tasks or self.active_tasks[bot_key].done():
                    task = asyncio.create_task(engine_map[bot_key]().run())
                    task.add_done_callback(handle_task_result)
                    self.active_tasks[bot_key] = task
                    
            elif action == 'stop' and bot_key in self.active_tasks:
                self.active_tasks[bot_key].cancel()
                del self.active_tasks[bot_key]
                
            await self.main_menu(update, context)

        elif query.data.startswith('run_test_'):
            mapping = {'run_test_l1': ("Long V1 Trend", run_long_v1), 'run_test_l2': ("Long V2 Bollinger", run_long_v2),
                       'run_test_s1': ("Short V1 Classic", run_short_v1), 'run_test_s5': ("Short V5 BearMaster", run_short_v5)}
            name, func = mapping[query.data]
            await context.bot.send_message(MI_CHAT_ID, f"⏳ Corriendo Backtest: **{name}**...")
            await loop.run_in_executor(None, func)
            await context.bot.send_message(MI_CHAT_ID, f"✅ Backtest **{name}** finalizado.")

        elif query.data == 'test_menu': await self.test_menu(update, context)
        elif query.data == 'back_to_main': await self.main_menu(update, context)
        elif query.data == 'emergency_stop':
            for t in self.active_tasks.values(): t.cancel()
            self.active_tasks.clear()
            await query.edit_message_text("☢️ SISTEMA APAGADO TOTALMENTE.")

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
