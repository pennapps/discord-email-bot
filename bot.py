''' SETUP '''
import discord
from discord.ext import commands
from bot_db import EmailBotDB
import os
import random
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from keep_alive import keep_alive

''' INITIALIZE BOT DATABASE '''
db = EmailBotDB()


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
        activity=discord.Game(name="github.com/pennapps/EmailBot")
    )

@client.event
async def on_member_join(member):
    # Check which guild a member is being verified for
    curr_guild = db.get_guild(member.guild.id)

    # If guild isn't in db, add to db
    if curr_guild == None:
        db.new_guild(member.guild.id)
    
    # Else if verification is enabled for the guild
    elif curr_guild[1] == 1:
        # Check if user exists with guild in db
        user_guild_info = db.get_user_guild(member.guild.id, member.id)
        
        # If user not with the guild in db
        if user_guild_info == None:
            # Send verification message and add user with guild to db
            await member.send(db.verify_message(member.guild))
            db.new_user(member.id, member.guild.id)
        
        # Else if user if unverified
        elif user_guild_info[4] == 0:
            # Send verification message
            await member.send(db.verify_message(member.guild))
        
        # Else if user is verified
        elif user_guild_info[4] == 1:
            # Change role to verified role (create if doesn't exist)
            role = discord.utils.get(member.guild.roles, name=curr_guild[2])
            if not role:
                await member.guild.create_role(name=curr_guild[2])
                role = discord.utils.get(
                    member.guild.roles, 
                    name=curr_guild[2]
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
    if (message.guild == None) and db.email_check(message_content):
        # Get all guild info
        users_guilds = db.get_users_guilds(message.author.id)
        if len(users_guilds) > 0:
            guild_list = [i[1] for i in users_guilds if i[4] == 0]
            verif_list = []
            
            # Verify email has domain for each guild
            for guild_id in guild_list:
                email_guild = db.get_emails_guilds(guild_id, message_content)
                if len(email_guild) == 0:
                    verif_list.append(guild_id)
                
            if len(verif_list) > 0:
                # Generate random code
                random_code = random.randint(100000, 999999)
                
                # Insert code into db for all guilds
                for verified_guild_id in verif_list:
                    db.insert_code(
                        random_code, 
                        message.author.id, 
                        verified_guild_id
                    )
                    db.insert_email(
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
                        "Email sent. **Reply here with your verification code**. " +
                        "If you haven't received it, check your spam folder."
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
        users_with_code = db.get_users_codes(message.author.id, verif_code)
        unverified_users_with_code = [
            user for user in users_with_code if user[4] == 0
        ]
        users_to_verify = []
        for user in unverified_users_with_code:
            user_emails = db.get_emails_guilds(user[1], user[2])
            if len(user_emails) == 0:
                users_to_verify.append(user)
        
        # Verify user in guilds
        if len(users_to_verify) > 0:
            for user in users_to_verify:
                db.verify_user(message.author.id, user[1])
                user_guild = client.get_guild(user[1])
                guild_info = db.get_guild(user[1])

                member = user_guild.get_member(message.author.id)

                # Add verified role
                verify_role = discord.utils.get(
                    user_guild.roles, 
                    name=guild_info[3]
                )
                
                # Create verified role if one doesn't exist
                if not verify_role:
                    await user_guild.create_role(name=guild_info[3])
                    verify_role = discord.utils.get(
                        user_guild.roles, 
                        name=guild_info[3]
                    )

                if verify_role not in member.roles:
                    await member.add_roles(verify_role)
                
                # Remove unverified role
                unverified_role = discord.utils.get(
                    user_guild.roles, 
                    name='unverified'
                )
                
                # Create unverified role if one doesn't exist
                if not unverified_role:
                    await user_guild.create_role(name='unverified')
                    unverified_role = discord.utils.get(
                        user_guild.roles, 
                        name='unverified'
                    )

                if unverified_role in member.roles:
                    await member.remove_roles(unverified_role)

                # Send confirmation message
                await message.channel.send(
                    "You have been verified on " + 
                    client.get_guild(user[1]).name + 
                    ". Please enter your team name. If you are not on a team," +
                    " send \".SKIP\""
                )
        else:
            await message.channel.send("Incorrect code.")

    # Else check if user has been verified
    else:
        user_guilds = db.get_users_guilds(message.author.id)
        for user in user_guilds:
            # If user is verified, this bot should handle nickname changes
            if user[4] == 1:
                if message_content and message_content != ".SKIP":
                    user_guild = client.get_guild(user[1])
                    guild_info = db.get_guild(user[1])

                    member = user_guild.get_member(message.author.id)
                    new_nick = message_content + "-" + member.name
                    await member.edit(nick=new_nick)
                    await message.channel.send(
                        "Nickname successfully changed to " + new_nick + ". " +
                        "If your team name changes, reply back with the " + 
                        "new name. Make sure that all your team members " + 
                        "change their team name!"
                    )
            
            # Else we have an invalid email
            elif message.guild == None:
                await message.channel.send("Invalid email.")
    
    await client.process_commands(message)

@client.event
async def on_guild_join(guild):
    # Insert guild into db if not already there when bot joins
    curr_guild = db.get_guild(guild.id)
    if curr_guild == None:
        db.new_guild(guild.id)


''' DISCORD COMMANDS '''
@client.command()
async def rolechange(ctx, role=None):
    if role and ctx.guild and ctx.author.guild_permissions.administrator:
        role = role.strip()
        
        # Get guild info (if none, add to db)
        curr_guild = db.get_guild(ctx.guild.id)
        if curr_guild == None:
            db.new_guild(ctx.guild.id)
            curr_guild = db.get_guild(ctx.guild.id)
        
        # Get current verified role
        curr_verified_role = discord.utils.get(
            ctx.guild.roles, 
            name=curr_guild[2]
        )
        
        # Check if verified role doesn't exist
        if not curr_verified_role:
            # If it doesn't, see if there is a role with the new name
            new_verified_role = discord.utils.get(ctx.guild.roles, name=role)
            
            # If it doesn't, create it
            if not new_verified_role:
                await ctx.guild.create_role(name=role)

        db.change_role(role, ctx.guild.id)
        await ctx.send(
            "```Verified role: " + db.get_guild(ctx.guild.id)[3] + ".```"
        )

@client.command()
async def enableonjoin(ctx):
    if ctx.guild and ctx.author.guild_permissions.administrator:
        # Get guild info (if none, add to db)
        curr_guild = db.get_guild(ctx.guild.id)
        if curr_guild == None:
            db.new_guild(ctx.guild.id)
        
        # Enable verification and send message
        db.enable_onjoin(ctx.guild.id)
        await ctx.send("```Verify when a user joins? True```")

@client.command()
async def disableonjoin(ctx):
    if ctx.guild and ctx.author.guild_permissions.administrator:
        # Get guild info (if none, add to db)
        curr_guild = db.get_guild(ctx.guild.id)
        if curr_guild == None:
            db.new_guild(ctx.guild.id)
        
        # Disable verification and send message
        db.disable_onjoin(ctx.guild.id)
        await ctx.send("```Verify when a user joins? False```")

@client.command()
async def vstatus(ctx):
    if ctx.guild:
        # Get guild info (if none, add to db)
        curr_guild = db.get_guild(ctx.guild.id)
        if curr_guild == None:
            db.new_guild(ctx.guild.id)
            curr_guild = db.get_guild(ctx.guild.id)
        on_join = bool(curr_guild[2])

        # Send info message
        await ctx.send("```" +
            "Ping: " + "{0}ms".format(round(client.latency * 1000)) + "\n" +
            "User commands: " + "\n" +
            "   .verify -> Sends a DM to the user to verify their email" + "\n" +
            "   .vstatus -> This help message" + "\n\n" +
            "Admin commands: " + "\n" +
            " - Use .rolechange instead of server settings to change the name of the verified role." + "\n" +
            "   .enableonjoin -> Enables verifying users on join" + "\n" +
            "   .disableonjoin -> Disables verifying users on join" + "\n" +
            "   .rolechange role -> Changes the name of the verified role" + "\n\n" +
            "Domains: all\n" + 
            "Verify when a user joins? (default=False): " + str(on_join) + "\n" + 
            "Verified role (default=Verified): " + curr_guild[2] + "```"
        )

@client.command()
async def vping(ctx):
    await ctx.send("{0}ms".format(round(client.latency * 1000)))

@client.command()
async def verify(ctx):
    if ctx.guild:
        # Get guild info (if none, add to db)
        curr_guild = db.get_guild(ctx.guild.id)
        if curr_guild == None:
            db.new_guild(ctx.guild.id)
            curr_guild = db.get_guild(ctx.guild.id)
        
        # Get user info for guild
        user_guild_info = db.get_user_guild(ctx.guild.id, ctx.author.id)
        
        # If user not in db, add and send verify message
        if user_guild_info == None:
            db.new_user(ctx.author.id, ctx.guild.id)
            await ctx.author.send(db.verify_message(ctx.guild))
        
        # Else send verify message
        elif user_guild_info[4] == 0:
            await ctx.author.send(db.verify_message(ctx.guild))


''' RUN '''
# Keep alive and run client
keep_alive()
client.run(os.environ.get('DISCORD_TOKEN'))
