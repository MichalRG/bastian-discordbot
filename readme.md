# General Information:

## Config - konfiguracja
Kolejnośc parametrów w config.json dla legit guilds ma znaczenie!!!

## Limitations
- For most actions, such as sending messages, the rate limit is around 5 requests per 5 seconds per channel.
- For joining and leaving servers, the limit is around 1,000 per 24 hours.
- When creating or updating global slash commands, changes can take up to an hour to propagate due to Discord's caching. This isn't a rate limit per se, but it does limit how often you can effectively update these commands.
- The rate limit for sending messages is typically 5 messages per 20 seconds per user per guild, and 5 messages per 5 seconds per channel.
- If you exceed a rate limit, Discord's API will respond with a 429 status code (Too Many Requests). The response will include a Retry-After header indicating how long to wait before making another request.

* If system will go into sleep mode/ snooze mode/ watch mode it will stop bot in the background and it will reset when u resume your system.

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