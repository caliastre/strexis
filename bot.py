#!/usr/bin/env python

import io
import logging
import random
import time

import psycopg2

from strexis import StrexisHandler, DEFAULT, ADD

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext, MessageHandler, ConversationHandler, filters


async def strexis_help(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "/add [CET#] -- add a new law to the record\n"
        "/remove [CET#] -- remove a law from the record\n"
        "/get [CET#] -- get information about a law\n"
        "/search [term] -- search by keyphrase\n"
        "/list -- list all laws"
    )

    return DEFAULT


def main():

    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    strexis_handler = StrexisHandler()

    token_file = open("TOKEN", "r", encoding = "utf-8")
    token = token_file.readline()

    if token[-1] == '\n':

        token = token[:-1]

    token_file.close()

    application = Application.builder().token(token).build()

    conversation_handler = ConversationHandler(
        entry_points = [CommandHandler("start", strexis_handler.start)],
        states = {
            DEFAULT: [
                CommandHandler("add", strexis_handler.add),
                CommandHandler("get", strexis_handler.get),
                CommandHandler("help", strexis_help),
                CommandHandler("list", strexis_handler.list),
                CommandHandler("remove", strexis_handler.remove),
                CommandHandler("search", strexis_handler.search)
            ],
            ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, strexis_handler.wait_add)]
        },
        fallbacks = []
    )

    application.add_handler(conversation_handler)

    application.run_polling(allowed_updates = Update.ALL_TYPES)

    strexis_handler.close()


if __name__ == "__main__":
    main()
