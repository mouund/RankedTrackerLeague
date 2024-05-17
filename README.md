# RTracker
## Configuration

:warning: Clone the repository into your home directory

:warning: **The two modifications are to be done whatever Installation solution you use**: Be very careful here!
Customize the needed configuration:
- Modify the ".env" to add your Riot API key and discord token and the icon URL you want to use.
```
API_KEY = <RIOT-API_KEY>
D_TOKEN = <DISCORD-BOT-TOKEN>
ICON_URL = <ICON-URL>
```


- Modify the "main.py" to add the Discord guild (aka server) ID and channel ID. 
```
uild_id = <YOUR-GUILD-ID-HERE>
channel_id = <YOUR-CHANNEL-ID-HERE>
```
# Get started
## Using Linux service

`git clone git@github.com:mouund/RankedTracker.git`

`cd RankedTracker`

`chmod +x start-bot.sh`

`mkdir -p $HOME/.config/systemd/user/`

`cp discord-bot.service $HOME/.config/systemd/user/`

`systemctl --user enable discord-bot`

`systemctl --user start discord-bot`

Ensure that the bot is running

`systemctl --user status discord-bot.service`

```
● discord-bot.service - Discord bot
     Loaded: loaded (/etc/systemd/system/discord-bot.service; enabled; vendor p>
     Active: **active** (running) since Sat 2024-04-27 19:40:12 UTC; 17h ago
   Main PID: 432074 (start-bot.sh)
      Tasks: 4 (limit: 1056)
     Memory: 35.4M
        CPU: 5.022s
     CGroup: /system.slice/discord-bot.service
             ├─432074 /bin/bash /home/ubuntu/RTracker/start-bot.sh
             └─432080 python3 /home/ubuntu/RTracker/main.py
```

Need to troubleshoot ? Use journalctl

`journalctl --user -eu discord-bot`

To display logs live

`journalctl --user -fu discord-bot`


## Using Docker

 :memo: **Note:** Docker needs to be installed on your machine in order to use this installation method, refer to https://docs.docker.com/engine/install/

`chmod +x docker-build.sh`

Create the docker image

`./docker-build.sh`

Start your container 

`docker run rtracker`

You're all done :D

# Usage

## Available /commands

`/ping` : Get the ping of he bot

`/list_players` : List the players currently tracked

`/add_player` : Add a plyer to the tracked players

`/history` : Get the last x games for a certain player

## Bot events

- The bot will send a message when a Solo ranked starts for one of the tracked player
- It will update the message regularly and send the result when the game is finished
- Send the leaderboard of the tracked players every days

The code needs optimization, factorization, feel free to contribute ! I don't really have time to work on this project anymore. 