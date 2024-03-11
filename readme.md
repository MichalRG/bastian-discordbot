# General Information - podstawowe informacje:

### Bot configuration - konfiugracja bota
### English
Currently not available
### Polish
1. Bot należy zaprosić na serwer najlepiej z 1197656938121527306 takim zestawem uprawnień
2. Jeżeli chcemy by informacje na temat danej guildy (serwera) zostały pobrane należy dodać swoją gildie w jakiś nazewniczo jasny sposób w config.json, pod kluczem "permissions". Jeżeli to całkowicie nowa gilidia nazwa jest dowolna, ale przez obecny zjebany stan kodu po dodaniu wpisu należałoby:
   1. W pliku main.py, w metodzie __set_allowed_channels dopisać w linijce 83 należy dodać variable dla naszej gildi jedno przechowujący kanąły tekstowe, drugi przechowujący instancje gildi.
   2. Następnie w metodzie __get_guilds_and_text_channels należy dopisać 2 zmienne tak jak dla pozostałych serwerów, jedna przechowująca arrayke text channeli, druga dla obiektu gildii. Nastepnie dokładamy warunek  elif gdzie guild.name == legit_guild[X] <- gdzie za X musisz wpisac numer indeksu Twojej gildi z arrayki permissions (patrz generaly opis kroku 2).
   3. Tak przypisane kanały tekstowe i obiekt gildi mają być zwracane z metody
   4. Następnie w __set_allowed_channels ponownie w 86 linicje zaczyna sie if statement którym musi dopisa ckolejnego ifka czy jest permision dla naszej gildi, przekazujemy tam arrayke text channel i obiket gildi do __get_allowed_channels
3. Gotowe teraz w config.json w legit key -> guilds key, do value dodajemy do arrayki dokładną nazwę naszej gildi
4. Podobnie dodajemy kanały do których chcemy by nasz bot mogl miec dostęp
5. Kolejno botowi nalezy przypisać dostęp do tych kanałów na samym serwerze (w gildi)
6. Gotowe wszystko powinno działać
7. * Jeżeli komendy nie pojawiają się u Twojego bota możę przy komendzie sync trzeba dodać id Twojej gildii

## Runnign bot - odpalanie bota
### English
To run this bot you have to install packages from requiremnets.txt (python 3.10 it's recommended). Then you have to set up your DISCORD TOKEN in env veraiables then you can run main.py and check the bot capabilities.
### Polish
By uruchomić bota zainstaluj paczki z requriements.txt (zalecana wersja pythona to 3.10). Następnie ustaw w zmiennych środowiskowych DISCORD TOKEN, umożliwi to korzystanie z API. Po konfiguracji odapl main.py i sprawdź możliwości bota.

## Config - configuration -konfiguracja
### English
The order in config.json for guilds has meaning!!!
### Polish
1. Kolejnośc parametrów w config.json dla legit guilds ma znaczenie!!!
2. Ustawiąjąc allowed_eye_player_channels_ids definiujemy na jakich kanałach można grać + będą zapisywane logi zwycięstw. Ustawiając allowed_eye_test_channels_ids na tych kanałach także można grać ale logi zwycięstw będą ignorowane.
3. bot_players - mowi o dostepnych graczach powinni wiec oni pokrywac sie z tym co jest zdefiniowane w kluczu players. Boty, które są wypisane jako dostępne powinny miec process ustawione na true by działać.

## Limitations
- For most actions, such as sending messages, the rate limit is around 5 requests per 5 seconds per channel.
- For joining and leaving servers, the limit is around 1,000 per 24 hours.
- When creating or updating global slash commands, changes can take up to an hour to propagate due to Discord's caching. This isn't a rate limit per se, but it does limit how often you can effectively update these commands.
- The rate limit for sending messages is typically 5 messages per 20 seconds per user per guild, and 5 messages per 5 seconds per channel.
- If you exceed a rate limit, Discord's API will respond with a 429 status code (Too Many Requests). The response will include a Retry-After header indicating how long to wait before making another request.

* If system will go into sleep mode/ snooze mode/ watch mode it will stop bot in the background and it will reset when u resume your system.

# DEV Section

## COMMANDS:
### pylint
- sh
```shell
pylint $(find . -name "*.py")
```
- ps
```shell
Get-ChildItem -Recurse -Filter "*.py" | ForEach-Object { pylint $_.FullName }
```
- ps
```shell
pylint --rcfile=./.pylintrc src
```

## TODO:
1. - [x] Change names into ids
2. - [ ] Separate guilds and channels somehow currently it randomly choose one channel which use it's not desired action
3. - [x] Sync - I solve the problem by adding new guild id but it didnt want to update it by itselfs.
4. commands for admins:
     - [x] to clean players who played with bot
     - [x] get players who played with bot
     - [x] to get logs
     - [x] to clean log file
     - [x] to stop bot
5. - [ ] expiring game when player doesnt react/ respond
6. - [x] refactor for players, it requires to rewrite player methods to more abstract level
7. - [x] get-sumuplogs returns commends
8. - [x] oko-gracze command required to create again
9. - [x] test-oko shouldnt save logs **SOLUTION: It doesn't save winning logs only**
10. - [ ] I added validators class it would be goodt o move rupella validators also to validator class
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
