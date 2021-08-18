# EmailBot

This repo was forked from [gg2001/EmailBot](https://github.com/gg2001/EmailBot).

## About

**EmailBot** allows for email address verification from Discord server members. This version is a security feature customized for the PennApps XXII. We want to verify that only accepted hackers can access the server.

All users start out as **unverified**, and this bot removes this role upon reception of a matching code. From there, users are able to see the #rules channel and can acess the rest of the server after accepting.

Our bot user is called **platy** and is hosted on Heroku.

## Usage

Commands (access with `.vstatus`):

```
User commands: 
   .verify -> Sends a DM to the user to verify their email
   .vstatus -> This help message

Admin commands: 
 - Use .rolechange instead of server settings to change the name of the verified role.
   .enableonjoin -> Enables verifying users on join
   .disableonjoin -> Disables verifying users on join
   .rolechange role -> Changes the name of the verified role

Domains: all
Verify when a user joins? (default=False): False
Verified role (default=Verified): Verified
```

## Installation

Install the dependencies:

```
pip install -r requirements.txt
```

Before running it make sure these environment variables are set. You will need a [Sendgrid](https://sendgrid.com/docs/for-developers/sending-email/api-getting-started/) and [Discord](https://discordpy.readthedocs.io/en/latest/discord.html#discord-intro) account (both are free). 

```
export SENDGRID_API_KEY='YOUR_SENDGRID_API_KEY'
export SENDGRID_EMAIL='YOUR_SENDGRID_EMAIL'
export DISCORD_TOKEN='YOUR_DISCORD_TOKEN'
export AUTH_EMAILS_FILEPATH='YOUR_FILEPATH'
```

Run the bot with:

```
python bot.py
```

## License

EmailBot is licensed under [GNU GPL v3](LICENSE).
