from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

from dotenv import load_dotenv
import os

from llm import MainLlm

load_dotenv()
llm = MainLlm()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛡️ Welcome to Cryptic Shield! 🛡️\n\n" +"I'm here to help you navigate the complex world of on-chain crypto transactions with enhanced security and insight. Here's what I can do for you:\n"
    + "• *Static Analysis of Contract Codes*: Send me any smart contract code with upcoming tx details, and I'll use the powerful Slither API to analyze it. I check for common vulnerabilities and issues using both public and custom detectors.\n"
    + "• *Risk Assessment*: I'll provide an evaluation of potential risks associated with the contract to help you make informed decisions.\n"
    + "• *Guidance and Suggestions*: Based on the analysis, I offer practical steps and recommendations to enhance the safety of your transactions.\n\n"
    + "To get started, simply send me a smart contract address or the contract code itself, and I'll take care of the rest.\n"
    + "Let's secure your crypto journey together! 💪", parse_mode="Markdown")

async def handle_test1(update: Update, context: CallbackContext):
    test1 = "Want to approve some amount at furucombo contract here:\n 0xA013AfbB9A92cEF49e898C87C060e6660E050569\nCan you check it for me please?"
    await update.message.reply_text("Replying to test1 message:\n" + test1)
    await process_request(update, test1, context)

async def handle_test2(update: Update, context: CallbackContext):
    test2 = "I want to use 1inch to convert my USDC to ETH. It says I need to approve my tokens first, is it safe?\nHere is the target contract code:\n0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
    await update.message.reply_text("Replying to test2 message:\n" + test2)
    await process_request(update, test2, context)

async def handle_text(update: Update, context: CallbackContext):
    await process_request(update, update.message.text, context)

async def process_request(update: Update, text: str, context: CallbackContext):
    bot_message = await update.message.reply_text("🤖")
    await update.message.reply_chat_action("typing")
    print(f"Received text: {text}")
    response = await llm.call(text, update)
    print(f"Received response: {response}")
    await update.message.reply_text(response, parse_mode="Markdown")
    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=bot_message.message_id)

def main() -> None:
    app = Application.builder().token(os.getenv('TELEGRAM_TOKEN')).build()
    
    # Handlers define how different types of updates are handled
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("test1", handle_test1))
    app.add_handler(CommandHandler("test2", handle_test2))
    # Add a message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))  

    print("Starting the bot...")
    # Run the bot until you press Ctrl-C
    app.run_polling()

if __name__ == '__main__':
    main()