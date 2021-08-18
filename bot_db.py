import sqlite3
import csv
import os

class EmailBotDB:
    def __init__(self):
        # Uncomment for dotenv
        '''
        import dotenv
        dotenv.load_dotenv()
        '''

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
    
    # Returns guild with specific ID
    def get_guild(self, guildid):
        return self.c.execute(
            "SELECT * FROM guilds WHERE guildid=?", 
            (guildid,)
        ).fetchone()

    # Inserts new guild into the db
    def new_guild(self, guildid, onjoin=0, role="verified"):
        self.c.execute(
            "INSERT INTO guilds VALUES (?, ?, ?)", 
            (guildid, onjoin, role)
        )
        self.conn.commit()

    # Returns user info within a specific guild
    def get_user_guild(self, guildid, userid):
        return self.c.execute(
            "SELECT * FROM users WHERE guildid=? AND userid=?", 
            (guildid, userid)
        ).fetchone()

    # Returns user info (all guilds)
    def get_users_guilds(self, userid):
        return self.c.execute(
            "SELECT * FROM users WHERE userid=?", 
            (userid,)
        ).fetchall()

    # Returns user info given email and guild
    def get_emails_guilds(self, guildid, email):
        return self.c.execute(
            "SELECT * FROM users WHERE guildid=? AND email=? AND verified=1", 
            (guildid, email)
        ).fetchall()

    # Returns user info if given code matches
    def get_users_codes(self, userid, code):
        return self.c.execute(
            "SELECT * FROM users WHERE userid=? AND code=?", 
            (userid, code)
        ).fetchall()

    # Display verify message
    def verify_message(self, guildname):
        return "To verify yourself on {}, **reply here with your email address**."\
            .format(guildname)

    # Inserts new user into the db
    def new_user(self, userid, guildid, email="", code=0, verified=0):
        self.c.execute(
            "INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
            (userid, guildid, email, code, verified)
        )
        self.conn.commit()

    # Verifies user in the db
    def verify_user(self, userid, guildid):
        self.c.execute(
            "UPDATE users SET verified=1 WHERE userid=? AND guildid=?", 
            (userid, guildid)
        )
        self.conn.commit()

    # Change role of user in a guild
    def change_role(self, role, guildid):
        self.c.execute(
            "UPDATE guilds SET role=? WHERE guildid=?", 
            (role, guildid)
        )
        self.conn.commit()

    # Enables verification on join
    def enable_onjoin(self, guildid):
        self.c.execute(
            "UPDATE guilds SET onjoin=? WHERE guildid=?", 
            (1, guildid)
        )
        self.conn.commit()

    # Disables verification on join
    def disable_onjoin(self, guildid):
        self.c.execute(
            "UPDATE guilds SET onjoin=? WHERE guildid=?", 
            (0, guildid)
        )
        self.conn.commit()

    # Insert code for a user in the db
    def insert_code(self, code, userid, guildid):
        self.c.execute(
            "UPDATE users SET code=? WHERE userid=? AND guildid=?", 
            (code, userid, guildid)
        )
        self.conn.commit()

    # Insert email for a user in the db
    def insert_email(self, email, userid, guildid):
        self.c.execute("UPDATE users SET email=? WHERE userid=? AND guildid=?", (email, userid, guildid))
        self.conn.commit()

    # Checks that email is authenticated
    def email_check(self, email):
        found_email = self.c.execute(
            "SELECT email FROM authenticated_emails WHERE email=?", 
            (email,)
        ).fetchone()
        return found_email != None

    # Populate authenticated email table
    def add_authenticated_email(self, email):
        self.c.execute(
            "INSERT INTO authenticated_emails VALUES (?)", 
            (email, )
        )
        self.conn.commit()

    def populate_emails_table(self, emails_filepath):
        emails_file = open(emails_filepath, encoding='utf-8-sig')
        auth_emails = csv.DictReader(emails_file, delimiter=',')

        for row in auth_emails:
            self.add_authenticated_email(row['email'])
