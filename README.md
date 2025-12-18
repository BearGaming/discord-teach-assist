# discord-teach-assist
Archived Discord bot that used an API for the teachassist platform to display student data in discord – historical screenshots and behavior documentation

Spawned from earlier projects involving discord bots that helped students with courses during COVID when many students myself included had to attend classes virtually. This project was in development about around 2021-2023 and made for fun. It used to be hosted on heroku until they updated their free tier in such a way that it was forced to migrate. An attempt was made to bring it to deta space but that service ended up shutting down.
[`TAssist.py`](./TAssist.py) is the python wrapper I made for an existing TA API mentioned as a dependency below.

## Dependencies
This project was built using:
- [discord.py](https://github.com/Rapptz/discord.py)
- [Fetch-TA-Data](https://github.com/PegasisForever/Fetch-TA-Data)

Subsequent API and permission model changes in Discord have made the
original implementation incompatible without a full rewrite.

## Screenshots

Examples of the bot’s behavior and commands are available in the
[`screenshots/`](./screenshots) directory.

Also indicative of the bots capabilities are the images under the various folders in the [`TA`/](./TA) directory. Making these plots look nice was took a long time especially as it was my first serious attempt at using matplotlib in python for my own needs in a project beyond following the explicit instructions of some tutorial on youtube where you can make something that works and not really appreciate unless you happen to make mistakes along the way. 
