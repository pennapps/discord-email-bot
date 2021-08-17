# EmailBot

This repo was forked from [gg2001/EmailBot](https://github.com/gg2001/EmailBot).

## About

**EmailBot** allows for email address verification from Discord server members. This version is a security feature customized for the PennApps XXII.

Our bot user is called **platy** and is hosted on Heroku.

## Usage

Commands (access with `.vstatus`):

```
User commands: 
   .verify -> Sends a DM to the user to verify their email
   .vstatus -> This help message

Admin commands: 
 - A domain must be added before users can be verified.
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
```

Run the bot with:

```
python bot.py
```

## License

EmailBot is licensed under [GNU GPL v3](LICENSE).
