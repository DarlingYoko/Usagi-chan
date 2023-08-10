# Usagi-chan

## Modular bot for your Discord server!
This bot can manage different cogs for separate servers.

### Current cogs list: 
 1. `AI` - Wrapper to ChatGPT to ask questions.
 2. `Events` - Handle all events on server. 🚫
 3. `Fun` - Different funny commands
 4. `Genshin` - Wrapper for Genshin API
 5. `Main` - Some basic utils 🚫
 6. `Moderation` - Set up your server as you wish. 🚫
 7. `Music` - Music player (YouTube, SoundCloud, etc.)
 8. `Tech` - User interaction with your server
 9. `Twitch` - Twitch streams notify
 10. `Wordle` - Wordle game in Discord Threads

> [!IMPORTANT]
> 🚫 No ability to disable by moders

### How to run bot.
1. Insert in `usagi-variables.env` your tokens
2. `docker compose build`
3. `docker compose up`

It will be set up and run postgres db and bot in containers.
   
Instalation requirements:
* Ubuntu requires pythonX.X-dev
* Windows "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/

psql access from docker:
`docker compose exec -it postgres psql -U <user_name> -W <base_name>`