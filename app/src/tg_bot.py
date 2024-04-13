from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

from dotenv import load_dotenv
import os

from llm import MainLlm

# Load environment variables from .env file
load_dotenv()
llm = MainLlm()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = llm.call(update.message.text)
    print(f"Received response: {response}")
    await update.message.reply_text("Hello! I am a language model. Ask me anything!")

async def handle_text(update: Update, context: CallbackContext) -> None:
    bot_message = await update.message.reply_text("🤖")
    await update.message.reply_chat_action("typing")
    print(f"Received text: {update.message.text}")
    response = await llm.call(update.message.text, update)
    print(f"Received response: {response}")
    await update.message.reply_text(response, parse_mode="Markdown")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=bot_message.message_id)

def main() -> None:
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    # Handlers define how different types of updates are handled
    app.add_handler(CommandHandler("start", start))
    # Add a message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  

    print("Starting the bot...")
    # Run the bot until you press Ctrl-C
    app.run_polling()

if __name__ == '__main__':
    main()