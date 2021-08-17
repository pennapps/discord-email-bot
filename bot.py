''' SETUP '''
import discord
from discord.ext import commands
import sqlite3
import re
import os
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from keep_alive import keep_alive

# Uncomment for dotenv
'''
import dotenv
dotenv.load_dotenv()
'''

# Connect to database
conn = sqlite3.connect('bot.db')
c = conn.cursor()

# Create users table if one doesn't exist
c.execute(
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
c.execute(
    """
    CREATE TABLE IF NOT EXISTS guilds(
        guildid INT PRIMARY KEY,
        domains TEXT,
        onjoin INT,
        role TEXT
    );
"""
)
conn.commit()


''' DATABASE METHODS '''
# Returns guild with specific ID
def get_guild(guildid):
    return c.execute(
        "SELECT * FROM guilds WHERE guildid=?", 
        (guildid,)
    ).fetchone()

# Inserts new guild into the db
def new_guild(guildid, domains="", onjoin=0, role="verified"):
    c.execute(
        "INSERT INTO guilds VALUES (?, ?, ?, ?)", 
        (guildid, domains, onjoin, role)
    )
    conn.commit()

# Returns user info within a specific guild
def get_user_guild(guildid, userid):
    return c.execute(
        "SELECT * FROM users WHERE guildid=? AND userid=?", 
        (guildid, userid)
    ).fetchone()

# Returns user info (all guilds)
def get_users_guilds(userid):
    return c.execute(
        "SELECT * FROM users WHERE userid=?", 
        (userid,)
    ).fetchall()

# Returns user info given email and guild
def get_emails_guilds(guildid, email):
    return c.execute(
        "SELECT * FROM users WHERE guildid=? AND email=? AND verified=1", 
        (guildid, email)
    ).fetchall()

# Returns user info if given code matches
def get_users_codes(userid, code):
    return c.execute(
        "SELECT * FROM users WHERE userid=? AND code=?", 
        (userid, code)
    ).fetchall()

# Display verify message
def verify_message(guildname, domains):
    return "To verify yourself on {}, **reply here with your email address**."\
        .format(guildname)

# Inserts new user into the db
def new_user(userid, guildid, email="", code=0, verified=0):
    c.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?)", 
        (userid, guildid, email, code, verified)
    )
    conn.commit()

# Verifies user in the db
def verify_user(userid, guildid):
    c.execute(
        "UPDATE users SET verified=1 WHERE userid=? AND guildid=?", 
        (userid, guildid)
    )
    conn.commit()

# Get domains from db
def get_domains(guildid):
    return get_guild(guildid)[1]

# Add domain to db in a pipe-separated format
def add_domain(domain, guildid):
    d_get = get_domains(guildid)
    prevdomains = []
    if d_get != "":
        prevdomains = get_domains(guildid).split('|')
    if domain not in prevdomains:
        prevdomains.append(domain)
        c.execute(
            "UPDATE guilds SET domains=? WHERE guildid=?", 
            ('|'.join(prevdomains), guildid)
        )
        conn.commit()

# Remove domain from db
def remove_domain(domain, guildid):
    prevdomains = get_domains(guildid).split('|')
    if domain in prevdomains:
        prevdomains.remove(domain)
        c.execute(
            "UPDATE guilds SET domains=? WHERE guildid=?", 
            ('|'.join(prevdomains), guildid)
        )
        conn.commit()

# Change role of user in a guild
def change_role(role, guildid):
    c.execute(
        "UPDATE guilds SET role=? WHERE guildid=?", 
        (role, guildid)
    )
    conn.commit()

# Enables verification on join
def enable_onjoin(guildid):
    c.execute(
        "UPDATE guilds SET onjoin=? WHERE guildid=?", 
        (1, guildid)
    )
    conn.commit()

# Disables verification on join
def disable_onjoin(guildid):
    c.execute(
        "UPDATE guilds SET onjoin=? WHERE guildid=?", 
        (0, guildid)
    )
    conn.commit()

# Insert code for a user in the db
def insert_code(code, userid, guildid):
    c.execute("UPDATE users SET code=? WHERE userid=? AND guildid=?", (code, userid, guildid))
    conn.commit()

# Insert email for a user in the db
def insert_email(email, userid, guildid):
    c.execute("UPDATE users SET email=? WHERE userid=? AND guildid=?", (email, userid, guildid))
    conn.commit()

# Checks that email is of the correct format
def email_check(email):
    regex = "(?:[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21\x23-\x5b\x5d-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])*\")@(?:(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?|\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-z0-9-]*[a-z0-9]:(?:[\x01-\x08\x0b\x0c\x0e-\x1f\x21-\x5a\x53-\x7f]|\\[\x01-\x09\x0b\x0c\x0e-\x7f])+)\])"
    if re.search(regex, email):
        return True
    else:
        return False


''' DISCORD EVENT HANDLING '''
# Default intents + members
intents = discord.Intents.default()
intents.members = True

# Create client with prefix "."
client = commands.Bot(
    command_prefix = '.', 
    intents=intents
)

@client.event
async def on_ready():
    # Log login message and set Game
    print("We have logged in as {0.user}".format(client))
    await client.change_presence(
        activity=discord.Game(
            name='.vstatus | github.com/gg2001/EmailBot'
        )
    )

@client.event
async def on_member_join(member):
    # Check which guild a member is being verified for
    curr_guild = get_guild(member.guild.id)

    # If guild isn't in db, add to db
    if curr_guild == None:
        new_guild(member.guild.id)
    
    # Else if verification is enabled for the guild
    elif curr_guild[2] == 1:
        # Check if user exists with guild in db
        user_guild_info = get_user_guild(member.guild.id, member.id)
        
        # If user not with the guild in db
        if user_guild_info == None:
            # Send verification message and add user with guild to db
            await member.send(verify_message(member.guild, curr_guild[1]))
            new_user(member.id, member.guild.id)
        
        # Else if user if unverified
        elif user_guild_info[4] == 0:
            # Send verification message
            await member.send(verify_message(member.guild, curr_guild[1]))
        
        # Else if user is verified
        elif user_guild_info[4] == 1:
            # Change role to verified role (create if doesn't exist)
            role = discord.utils.get(member.guild.roles, name=curr_guild[3])
            if not role:
                await member.guild.create_role(name=curr_guild[3])
                role = discord.utils.get(
                    member.guild.roles, 
                    name=curr_guild[3]
                )
            
            if role not in member.roles:
                await member.add_roles(role)

@client.event
async def on_message(message):
    # Stop if message was from self
    if message.author == client.user:
        return
    
    # Get last sent message sans whitespace
    message_content = message.content.strip()

    # If the user sends message through DM with email address
    if (message.guild == None) and email_check(message_content):
        # Get all guild info
        users_guilds = get_users_guilds(message.author.id)
        if len(users_guilds) > 0:
            guild_list = [i[1] for i in users_guilds if i[4] == 0]
            verif_list = []
            
            # Verify email has domain for each guild
            for guild_id in guild_list:
                email_guild = get_emails_guilds(guild_id, message_content)
                if len(email_guild) == 0:
                    verif_list.append(guild_id)
                
            
            if len(verif_list) > 0:
                # Generate random code
                random_code = random.randint(100000, 999999)
                
                # Insert code into db for all guilds
                for verified_guild_id in verif_list:
                    insert_code(
                        random_code, 
                        message.author.id, 
                        verified_guild_id
                    )
                    insert_email(
                        message_content, 
                        message.author.id, 
                        verified_guild_id
                    )
                
                # Send email
                emailmessage = Mail(
                    from_email=os.environ.get('SENDGRID_EMAIL'),
                    to_emails=message_content,
                    subject='Verify your server email',
                    html_content=str(random_code))
                try:
                    sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
                    response = sg.send(emailmessage)
                    print(response.status_code)
                    print(response.body)
                    print(response.headers)
                    await message.channel.send(
                        "Email sent. **Reply here with your verification code**. \
                        If you haven't received it, check your spam folder."
                    )
                except Exception as e:
                    await message.channel.send("Email failed to send.")
            else:
                await message.channel.send("Invalid email.")
        else:
            await message.channel.send("You have not joined a server.")
    
    # Else if user sends a six-digit code
    elif (len(message_content) == 6) and message_content.isdigit():
        verif_code = int(message_content)
        
        # Get user info if code matches
        users_with_code = get_users_codes(message.author.id, verif_code)
        unverified_users_with_code = [
            user for user in users_with_code if user[4] == 0
        ]
        users_to_verify = []
        for user in unverified_users_with_code:
            user_emails = get_emails_guilds(user[1], user[2])
            if len(user_emails) == 0:
                users_to_verify.append(user)
        
        # Verify user in guilds
        if len(users_to_verify) > 0:
            for user in users_to_verify:
                verify_user(message.author.id, user[1])
                user_guild = client.get_guild(user[1])
                guild_db = get_guild(user[1])
                role = discord.utils.get(user_guild.roles, name=guild_db[3])
                if not role:
                    await user_guild.create_role(name=guild_db[3])
                    role = discord.utils.get(user_guild.roles, name=guild_db[3])
                    
                member = user_guild.get_member(message.author.id)
                if role not in member.roles:
                        await member.add_roles(role)
                
                await message.channel.send(
                    "You have been verified on " + \
                    client.get_guild(user[1]).name + "."
                )
        else:
            await message.channel.send("Incorrect code.")
    elif message.guild == None:
        await message.channel.send("Invalid email.")
    await client.process_commands(message)

@client.event
async def on_guild_join(guild):
    # Insert guild into db if not already there when bot joins
    curr_guild = get_guild(guild.id)
    if curr_guild == None:
        new_guild(guild.id)


''' DISCORD COMMANDS '''
@client.command()
async def rolechange(ctx, role=None):
    if role and ctx.guild and ctx.author.guild_permissions.administrator:
        role = role.strip()
        
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
            curr_guild = get_guild(ctx.guild.id)
        
        # Get current verified role
        curr_verified_role = discord.utils.get(
            ctx.guild.roles, 
            name=curr_guild[3]
        )
        
        # Check if verified role doesn't exist
        if not curr_verified_role:
            # If it doesn't, see if there is a role with the new name
            new_verified_role = discord.utils.get(ctx.guild.roles, name=role)
            
            # If it doesn't, create it
            if not new_verified_role:
                await ctx.guild.create_role(name=role)

        change_role(role, ctx.guild.id)
        await ctx.send(
            "```Verified role: " + get_guild(ctx.guild.id)[3] + ".```"
        )

@client.command()
async def domainadd(ctx, domain=None):
    if domain and ctx.guild and ctx.author.guild_permissions.administrator:
        domain = domain.strip()
        
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
        
        # Add domain and send message
        add_domain(domain, ctx.guild.id)
        await ctx.send(
            "```Current email domains: " + get_domains(ctx.guild.id) + "```"
        )

@client.command()
async def domainremove(ctx, domain=None):
    if domain and ctx.guild and ctx.author.guild_permissions.administrator:
        domain = domain.strip()
       
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
        
        # Remove domain and send message
        remove_domain(domain, ctx.guild.id)
        await ctx.send(
            "```Current email domains: " + get_domains(ctx.guild.id) + "```"
        )

@client.command()
async def enableonjoin(ctx):
    if ctx.guild and ctx.author.guild_permissions.administrator:
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
        
        # Enable verification and send message
        enable_onjoin(ctx.guild.id)
        await ctx.send("```Verify when a user joins? True```")

@client.command()
async def disableonjoin(ctx):
    if ctx.guild and ctx.author.guild_permissions.administrator:
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
        
        # Disable verification and send message
        disable_onjoin(ctx.guild.id)
        await ctx.send("```Verify when a user joins? False```")

@client.command()
async def vstatus(ctx):
    if ctx.guild:
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
            curr_guild = get_guild(ctx.guild.id)
        on_join = bool(curr_guild[2])

        # Send info message
        await ctx.send("```" +
            "Ping: " + "{0}ms".format(round(client.latency * 1000)) + "\n" +
            "User commands: " + "\n" +
            "   .verify -> Sends a DM to the user to verify their email" + "\n" +
            "   .vstatus -> This help message" + "\n\n" +
            "Admin commands: " + "\n" +
            " - A domain must be added before users can be verified." + "\n" +
            " - Use .rolechange instead of server settings to change the name of the verified role." + "\n" +
            "   .enableonjoin -> Enables verifying users on join" + "\n" +
            "   .disableonjoin -> Disables verifying users on join" + "\n" +
            "   .rolechange role -> Changes the name of the verified role" + "\n\n" +
            "Domains: all\n" + 
            "Verify when a user joins? (default=False): " + str(on_join) + "\n" + 
            "Verified role (default=Verified): " + curr_guild[3] + "```")

@client.command()
async def vping(ctx):
    await ctx.send("{0}ms".format(round(client.latency * 1000)))

@client.command()
async def verify(ctx):
    if ctx.guild:
        # Get guild info (if none, add to db)
        curr_guild = get_guild(ctx.guild.id)
        if curr_guild == None:
            new_guild(ctx.guild.id)
            curr_guild = get_guild(ctx.guild.id)
        
        # Get user info for guild
        user_guild_info = get_user_guild(ctx.guild.id, ctx.author.id)
        
        # If user not in db, add and send verify message
        if user_guild_info == None:
            new_user(ctx.author.id, ctx.guild.id)
            await ctx.author.send(verify_message(ctx.guild, curr_guild[1]))
        
        # Else send verify message
        elif user_guild_info[4] == 0:
            await ctx.author.send(verify_message(ctx.guild, curr_guild[1]))


''' RUN '''
# Keep alive and run client
keep_alive()
client.run(os.environ.get('DISCORD_TOKEN'))
