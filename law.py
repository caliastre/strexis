from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import ForceReply, Update

from config import config
import psycopg2

DEFAULT, ADD = range(2)

class LawHandler:

    def __init__(self):

        params = config()
        self.connection = psycopg2.connect(**params)
        self.cursor = self.connection.cursor()        

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS laws ("
                "id text PRIMARY KEY,"
                "content text NOT NULL"
            ")"
        )


    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        command = update.message.text

        law_id = ""

        if "/add@StrexisNexisBot" in command:

            law_id = command[len("/add@StrexisNexisBot "):]

        else:

            law_id = command[len("/add "):]

        setattr(self, "id", law_id)

        await update.message.reply_text(
            f"Reply with the text of {law_id}.",
            reply_markup = ForceReply(selective = True)
        )

        return ADD


    async def wait_add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        law_id = getattr(self, "id")
        content = update.message.text

        self.cursor.execute(
            "INSERT INTO laws (id, content) VALUES (%s, %s)",
            (law_id, content)
        )

        self.connection.commit()

        await update.message.reply_text(f"{law_id} added to database.")

        return DEFAULT


    async def get(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        command = update.message.text

        law_id = ""

        if "/get@StrexisNexisBot" in command:

            law_id = command[len("/get@StrexisNexisBot "):]

        else:

            law_id = command[len("/get "):]

        self.cursor.execute("SELECT content FROM laws WHERE id = %s", (law_id,))
        content = self.cursor.fetchone()[0]

        await update.message.reply_text(content)


    async def remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        command = update.message.text

        law_id = ""

        if "/remove@StrexisNexisBot" in command:

            law_id = command[len("/remove@StrexisNexisBot "):]

        else:

            law_id = command[len("/remove "):]

        self.cursor.execute("DELETE FROM laws WHERE id = %s", (law_id,))
        self.connection.commit()

        await update.message.reply_text(f"{law_id} removed from database.")


    async def list(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        self.cursor.execute("SELECT id FROM laws")
        ids = self.cursor.fetchall()

        id_list = ""

        for law_id in ids:

            id_list = id_list + law_id[0] + "\n"

        if id_list == "":

            await update.message.reply_text("Database is empty.")

        else:

            await update.message.reply_text(id_list)


    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):

        command = update.message.text

        keyphrase = ""

        if "/search@StrexisNexisBot" in command:

            keyphrase = command[len("/search@StrexisNexisBot "):]

        else:

            keyphrase = command[len("/search "):]

        self.cursor.execute("SELECT * FROM laws")
        laws = self.cursor.fetchall()

        count = 0
        results = []

        for law in laws:

            if keyphrase.lower() in law[1].lower():

                count = count + 1
                results.append("{0}\n\n{1}".format(law[0], law[1]))

        await update.message.reply_text("Found {0} results.".format(count))

        for result in results:

            await update.message.reply_text(result)


    def close(self):

        self.cursor.close()
        self.connection.close()
