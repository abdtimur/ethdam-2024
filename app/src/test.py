from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackContext

from dotenv import load_dotenv
import os

from llm import MainLlm

# Load environment variables from .env file
load_dotenv()
llm = MainLlm()
response = llm.call("I'm going to send tx to 0xdac17f958d2ee523a2206206994597c13d831ec7, is it safe?")
# response = llm.call("I want to mint USDT tokens, is it safe?")
print(f"Received response: {response}")