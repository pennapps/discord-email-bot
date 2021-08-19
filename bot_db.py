import sqlite3
import csv
import os

class EmailBotDB:
    """Handles SQLite database operations for EmailBot.

    Uses three tables
        users: (userid, guildid, email, code, verified)
            A table for all user info within a guild.
        guilds: (guildid, onjoin, role)
            A table for all guilds a bot is in.
        authenticated_emails: (email)
            An automatically populated table containing 
            the emails of users that are allowed to join
            the server.

    Attributes:
        conn: A connection to the database
        c: A cursor for the previously mentions connection
    """

    def __init__(self):
        """ Initializes DB and creates tables """
        self.conn = sqlite3.connect('bot.db')
        self.c = self.conn.cursor()

        # Create users table if one doesn't exist
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                userid INT,
                guildid INT,
                email TEXT,
                code INT,
                verified INT
            );
            """
        )

        # Create guides table if one doesn't exist
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS guilds(
                guildid INT PRIMARY KEY,
                onjoin INT,
                role TEXT
            );
            """
        )

        # Create authenticated emails table if one doesn't exist
        self.c.execute(
            """
            CREATE TABLE IF NOT EXISTS authenticated_emails (
                email TEXT
            );
            """
        )
        self.conn.commit()

        self.populate_emails_table(os.environ.get('AUTH_EMAILS_FILEPATH'))
    
    def get_guild(self, guildid):
        """ Returns guild with specific ID """
        return self.c.execute(
            "SELECT * FROM guilds WHERE guildid=?", 
            (guildid,)
        ).fetchone()

    def new_guild(self, guildid, onjoin=0, role="verified"):
        """ Inserts new guild into the DB """
        self.c.execute(
            "INSERT INTO guilds VALUES (?, ?, ?)", 
            (guildid, onjoin, role)
        )
        self.conn.commit()

    def get_user_guild(self, guildid, userid):
        """ Returns user info within a specific guild """
        return self.c.execute(
            "SELECT * FROM users WHERE guildid=? AND userid=?", 
            (guildid, userid)
        ).fetchone()

    def get_users_guilds(self, userid):
        """ Returns user info (within all guilds) """
        return self.c.execute(
            "SELECT * FROM users WHERE userid=?", 
            (userid,)
        ).fetchall()

    def get_emails_guilds(self, guildid, email):
        """ Returns user info given email and guild """
        return self.c.execute(
            "SELECT * FROM users WHERE guildid=? AND email=? AND verified=1", 
            (guildid, email)
        ).fetchall()

    def get_users_codes(self, userid, code):
        """ Returns user info if given code matches """
        return self.c.execute(
            "SELECT * FROM users WHERE userid=? AND code=?", 
            (userid, code)
        ).fetchall()

    def verify_message(self, guildname):
        """ Display verify message """
        return "To verify yourself on {}, **reply here with your email address**."\
            .format(guildname)

    def new_user(self, userid, guildid, email="", code=0, verified=0):
        """ Inserts new user into the DB """
        self.c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
            (userid, guildid, email, code, verified)
        )
        self.conn.commit()

    def verify_user(self, userid, guildid):
        """ Verifies user in the DB """
        self.c.execute(
            "UPDATE users SET verified=1 WHERE userid=? AND guildid=?", 
            (userid, guildid)
        )
        self.conn.commit()

    def change_role(self, role, guildid):
        """ Change role of verified user in a guild """
        self.c.execute(
            "UPDATE guilds SET role=? WHERE guildid=?", 
            (role, guildid)
        )
        self.conn.commit()

    def enable_onjoin(self, guildid):
        """ Enables verification on join """
        self.c.execute(
            "UPDATE guilds SET onjoin=? WHERE guildid=?", 
            (1, guildid)
        )
        self.conn.commit()

    def disable_onjoin(self, guildid):
        """ Disables verification on join """
        self.c.execute(
            "UPDATE guilds SET onjoin=? WHERE guildid=?", 
            (0, guildid)
        )
        self.conn.commit()

    def insert_code(self, code, userid, guildid):
        """ Inserts the random code for a user in the DB """
        self.c.execute(
            "UPDATE users SET code=? WHERE userid=? AND guildid=?", 
            (code, userid, guildid)
        )
        self.conn.commit()

    def insert_email(self, email, userid, guildid):
        """ Inserts email for a user in the DB """
        self.c.execute(
            "UPDATE users SET email=? WHERE userid=? AND guildid=?", 
            (email, userid, guildid)
        )
        self.conn.commit()

    def email_check(self, email):
        """ Checks that email exists in authenticated_emails """
        found_email = self.c.execute(
            "SELECT email FROM authenticated_emails WHERE email=?", 
            (email,)
        ).fetchone()
        return found_email != None

    def add_authenticated_email(self, email):
        """ Inserts an email into the emails table """
        self.c.execute(
            "INSERT INTO authenticated_emails VALUES (?)", 
            (email, )
        )
        self.conn.commit()

    def populate_emails_table(self, emails_filepath):
        """ Populates authenticated email table from a file """
        emails_file = open(emails_filepath, encoding='utf-8-sig')
        auth_emails = csv.DictReader(emails_file, delimiter=',')

        for row in auth_emails:
            self.add_authenticated_email(row['email'])
