#!/usr/bin/env python

import io
import logging

import psycopg2

from config import config
from law import LawHandler, DEFAULT, ADD

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, ConversationHandler, filters


async def strexis_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await update.message.reply_text(
        "/add [CET#] -- add a new law to the record\n"
        "/remove [CET#] -- remove a law from the record\n"
        "/get [CET#] -- get information about a law\n"
        "/list -- list all laws"
    )


async def strexis_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    await update.message.reply_text("StrexisNexis started.")

    return DEFAULT


def main():

    logging.basicConfig(
        format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level = logging.INFO
    )

    logging.getLogger("httpx").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)

    law_handler = LawHandler()

    token_file = open("TOKEN", "r", encoding = "utf-8")
    token = token_file.readline()

    if token[-1] == '\n':

        token = token[:-1]

    token_file.close()

    application = Application.builder().token(token).build()

    conversation_handler = ConversationHandler(
        entry_points = [CommandHandler("start", strexis_start)],
        states = {
            DEFAULT: [
                CommandHandler("add", law_handler.add),
                CommandHandler("get", law_handler.get),
                CommandHandler("help", strexis_help),
                CommandHandler("list", law_handler.list),
                CommandHandler("remove", law_handler.remove)
            ],
            ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, law_handler.wait_add)]
        },
        fallbacks = []
    )

    application.add_handler(conversation_handler)

    application.run_polling(allowed_updates = Update.ALL_TYPES)

    law_handler.close()


if __name__ == "__main__":
    main()
