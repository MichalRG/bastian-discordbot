# General Information - podstawowe informacje:

## Runnign bot - odpalanie bota
### English
To run this bot you have to install packages from requiremnets.txt (python 3.10 it's recommended). Then you have to set up your DISCORD TOKEN in env veraiables then you can run main.py and check the bot capabilities.
### Polish
By uruchomić bota zainstaluj paczki z requriements.txt (zalecana wersja pythona to 3.10). Następnie ustaw w zmiennych środowiskowych DISCORD TOKEN, umożliwi to korzystanie z API. Po konfiguracji odapl main.py i sprawdź możliwości bota.

## Config - configuration -konfiguracja
### English
The order in config.json for guilds has meaning!!!
### Polish
Kolejnośc parametrów w config.json dla legit guilds ma znaczenie!!!

# DEV Section
## Synhronizing bots
1. Shared Backend or Database
If both bots have access to a shared backend service or database, Bot1 can update a shared resource, which Bot2 regularly checks. For example:

- Bot1: After a game event, Bot1 updates a shared database or sends a request to a shared backend service indicating that a user has lost 5 coins.
- Bot2: Regularly checks the database or receives notifications from the backend service, and then performs the necessary action (like removing 5 coins).
2. Using APIs/Webhooks
If both bots expose an API or webhook:

- Bot1: Sends a request to Bot2's API or webhook when a user loses in the game.
- Bot2: Listens for incoming requests from Bot1 and performs the /remove logic upon receiving a valid request.
3. Bot-to-Bot Communication Through a Server
Use a Discord server as an intermediary:

- Bot1: Sends a specially formatted message to a dedicated channel in the Discord server.
- Bot2: Listens for messages in that channel. When it detects a message from Bot1 with the specific format, it performs the /remove action.
4. Manual Trigger by Bot Admin
If automated solutions are complex:

- Bot1: Notifies an admin or sends a message to a channel when a user should lose coins.
- Admin/Bot2 Operator: Manually triggers Bot2's /remove command.
