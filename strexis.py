from telegram.ext import CallbackContext, ContextTypes, ConversationHandler, MessageHandler, filters
from telegram import ForceReply, Update

from configparser import ConfigParser
import psycopg2

DEFAULT, ADD = range(2)
AD, INFO, PSA = range(3)

def config (filename, section):

    parser = ConfigParser()
    parser.read(filename)

    settings = {}
    
    if parser.has_section(section):

        params = parser.items(section)

        for param in params:

            settings[param[0]] = param[1]

    else:

        raise Exception(f"Section \"%(section)s\" not found in %(filename)s")

    return settings


class StrexisHandler:

    def __init__(self):

        filename = "config.ini"

        db = config(filename, "postgresql")

        self.connection = psycopg2.connect(**db)
        self.cursor = self.connection.cursor()        

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS laws ("
                "id text PRIMARY KEY,"
                "content text NOT NULL"
            ")"
        )

        self.cursor.execute(
            "DO $$ BEGIN"
            "    CREATE TYPE adtype AS ENUM ('ad', 'info', 'psa');"
            "EXCEPTION"
            "   WHEN duplicate_object THEN null;"
            "END $$;"
        )

        self.cursor.execute(
            "CREATE TABLE IF NOT EXISTS ads ("
                "id SERIAL PRIMARY KEY,"
                "type adtype NOT NULL,"
                "content text NOT NULL"
            ")"
        )

        self.connection.commit()

        tg = config(filename, "telegram")

        self.chat_id = tg["chat_id"]
        self.adfreq = int(tg["ad_frequency"])

        self.current_ad = 0
        self.advertising = False


    async def start(self, update: Update, context: CallbackContext):

        await update.message.reply_text("StrexisNexis started.")

        if not self.advertising:

            context.job_queue.run_repeating(self.advertise, interval = self.adfreq, first = 0,
                chat_id = update.message.chat_id)

            self.advertising = True

        return DEFAULT


    async def advertise(self, context: CallbackContext): 

        self.cursor.execute("SELECT * FROM ads WHERE id = %s", (self.current_ad + 1,))
        ad = self.cursor.fetchone()

        header = ""
        match ad[1]:

            case "ad":

                header = "ADVERTISEMENT"

            case "info":

                header = "INFORMATION"

            case "psa":

                header = "PUBLIC SERVICE ANNOUNCEMENT"

        header = "----- {0} -----".format(header)

        body = ad[2]

        message = header + "\n\n" + body

        await context.bot.send_message(chat_id = self.chat_id, text = message)

        self.cursor.execute("SELECT count(*) FROM ads")
        ad_count = self.cursor.fetchone()[0]

        self.current_ad = (self.current_ad + 1) % ad_count


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

        return DEFAULT


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

        return DEFAULT


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

        return DEFAULT


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

        return DEFAULT


    def close(self):

        self.cursor.close()
        self.connection.close()
