import os
import discord
import requests
import json
from discord.ext import tasks
from time import strftime, localtime
import time
from collections import defaultdict
import logging
from dotenv import load_dotenv

#Load dotenv file
load_dotenv()


logging.basicConfig(
    format='%(asctime)s %(levelname)s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)

guild_id = <YOUR-GUILD-ID-HERE>
channel_id = <YOUR-CHANNEL-ID-HERE>

#Modify the icon here 
bot_icon_url = os.getenv('ICON_URL')
riot_api_key = os.getenv('API_KEY')
token = os.getenv('D_TOKEN')


current_path = os.path.dirname(os.path.realpath(__file__))
id_offset_player = 0
tracked_players = defaultdict(dict)
tracked_games = defaultdict(dict)

bot = discord.Bot()
client = discord.Client()

#Definition of commands-----------
async def get_n_games_id(player_id, riot_api_key,n,queue_type):
    if type(n) is int:
      logging.info('Startup of function get_n_games_id')
      if queue_type == 'soloduo':
         queue = '420'
      url_game_historic = 'https://europe.api.riotgames.com/lol/match/v5/matches/by-puuid/'+ tracked_players[player_id]['puuid'] +'/ids?queue='+ queue +'&start=0&count='+ str(n) +'&api_key=' + riot_api_key
      game_historic = requests.get(url_game_historic)
      if game_historic.status_code == 200:
          match_ids = game_historic.text
          match_ids = match_ids.replace('\"', '')
          match_ids = match_ids.strip('[')
          match_ids = match_ids.strip(']')
          match_ids = match_ids.split(",")
          logging.info("Match ids sent for " + tracked_players[player_id]['name'] + '...')
          return (match_ids)
      if game_historic.status_code != 200:
          logging.error("erreur recuperation de la liste de games pour pour: " + tracked_players[player_id]['name'] )

def import_champs():
  logging.info("Startup import of champions...")
  global dict_champ
  global current_path
  dict_champ ={}
  with open(current_path + '/champ.json') as file:
    data = json.load(file)
    for champ in data["data"]:
        dict_champ[data["data"][champ]["key"]] = data["data"][champ]["id"]

async def update_tracked_player_data(player_name):
   global tracked_players
   logging.info("Startup of function 'update tracked players' for " + player_name + '...')
   if tracked_players != {}:
     for player,data in tracked_players.copy().items():
         if player_name == data['name']:
           #for each player retrieve name and unique id
           player_id = data['id']
           url_player = 'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-name/' + data['name'] + '?api_key=' + riot_api_key
           try:
             info_player = requests.get(url_player)
             info_player.raise_for_status()
           except requests.exceptions.HTTPError as err:
             logging.error('Error gathering player entries for' + player_name)
             raise(err)
           #get info players basics
           #get info status
           json_objet_info_player = json.loads(info_player.text)
           url_player_entries = 'https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/' + json_objet_info_player['id'] + '?api_key=' + riot_api_key
           try:
             player_entries = requests.get(url_player_entries)
             player_entries.raise_for_status()
           except requests.exceptions.HTTPError as err:
             logging.error('error gathering player entries for' + player_name)
             raise(err)
           json_player_entries = json.loads(player_entries.text)
           json_player_entries = next((item for item in json_player_entries if item["queueType"] == 'RANKED_SOLO_5x5'), None)
           #Update the necessary entries
           tracked_players[player_id].update({      
                       'level' : json_objet_info_player["summonerLevel"],
                       'tier' : json_player_entries['tier'], 
                       'rank' : json_player_entries['rank'],
                       'lp' : json_player_entries["leaguePoints"],
                       'wins' : json_player_entries["wins"],
                       'losses' : json_player_entries["losses"],
                       'veteran' : json_player_entries["veteran"],
                       'inactive' : json_player_entries["inactive"],
                       'hotStreak' : json_player_entries["hotStreak"],
                       })
           logging.info(tracked_players[player_id]["name"] + ' player information updated')
   else:
     logging.info('No player currently tracked ...')

async def get_live_match_data(player_name):
    global tracked_players
    logging.info("Startup of function 'get_live_match_data' for " + player_name)
    for player_id,data in tracked_players.items():
        if player_name == data['name']:
            url_match_by_player_id = 'https://euw1.api.riotgames.com/lol/spectator/v5/active-games/by-summoner/' + data['puuid'] + '?api_key=' + riot_api_key
            info_match_by_player_id = requests.get(url_match_by_player_id)
            json_info_match_by_player_id = json.loads(info_match_by_player_id.text)
            if info_match_by_player_id.status_code == 200 and json_info_match_by_player_id["gameQueueConfigId"] == 420:
              logging.info(player_name + ' currently in ranked game, gathering infos...')
              data['in_game'] = True
              data['current_match_id'] = json_info_match_by_player_id['gameId']
              game_id_player_id = str(json_info_match_by_player_id['gameId']) + ',' + str(player_id)
              tracked_games[game_id_player_id]['game_data'] = json_info_match_by_player_id
              tracked_games[game_id_player_id]['tracked_puuid'] = data['puuid']
              tracked_games[game_id_player_id]['tracked_name'] = data['name']
              tracked_games[game_id_player_id]['tier_before_match'] = data['tier']
              tracked_games[game_id_player_id]['lp_before_match'] = data['lp']
              tracked_games[game_id_player_id]['rank_before_match'] = data['rank']
              tracked_games[game_id_player_id]['player_id'] = player_id
              for players_ingame in json_info_match_by_player_id['participants']:
                if players_ingame['puuid'] == data['puuid']:
                  tracked_games[game_id_player_id]['champ_id'] = players_ingame['championId']
                  tracked_games[game_id_player_id]['tracked_player_team_id'] = players_ingame['teamId']
            else:
              logging.info(player_name + 'not in ranked game')
              tracked_players[player_id].update({
                          'in_game' : False,
                          'current_match_id' : 0
                          })
              
                                        
#Definition of slash commands-----------
@bot.slash_command(name="ping",description="Affiche le ping du bot",guild_ids=[guild_id])
async def ping(ctx):
    logging.info("Startup ping function...")
    await ctx.defer()
    await ctx.respond("Ping de: " + str(bot.latency *1000) + " ms")

@bot.slash_command(name="add_player",description="Ajoute un joueur dans la liste des joueurs a tracker",guild_ids=[guild_id])
async def add_players(ctx, player_name: str):
    global tracked_players
    global id_offset_player
    tracked_players_names = []
    for player,data in tracked_players.copy().items():
      tracked_players_names.append(data["name"])
    await ctx.defer()
    if '#' in player_name:
      splitted_name = player_name.split("#")
      player_name = splitted_name[0]
      player_tag = splitted_name[1]
    else:
      player_tag = 'EUW'
    #make the necessary request
    url_account = 'https://europe.api.riotgames.com/riot/account/v1/accounts/by-riot-id/' + player_name + '/' + player_tag + '?api_key=' + riot_api_key
    try:
      account = requests.get(url_account)
      account.raise_for_status()
    except requests.exceptions.HTTPError as err:
      await ctx.respond('Le joueur existe pas')
      raise(err)
    #test status code for both requests      
    if player_name in tracked_players_names:
      await ctx.respond('Déja dans la liste')
      logging.info(player_name + ' Already in the list')
    else:
      json_objet_account = json.loads(account.text)
      url_player = 'https://euw1.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/' + json_objet_account["puuid"] + '?api_key=' + riot_api_key
      try:
        info_player = requests.get(url_player)
        info_player.raise_for_status()
      except requests.exceptions.HTTPError as err:
        await ctx.respond('Erreur dans la recuperation du joueur')
        logging.info(player_name + 'error gathering player entries')
        raise(err)
      #get info players basics
      #get info status
      json_objet_info_player = json.loads(info_player.text)
      url_player_entries = 'https://euw1.api.riotgames.com/lol/league/v4/entries/by-summoner/' + json_objet_info_player['id'] + '?api_key=' + riot_api_key
      try:
        player_entries = requests.get(url_player_entries)
        player_entries.raise_for_status()
      except requests.exceptions.HTTPError as err:
        await ctx.respond('Le joueur existe pas')
        raise(err)
      json_player_entries = json.loads(player_entries.text)
      json_player_entries = next((item for item in json_player_entries if item["queueType"] == 'RANKED_SOLO_5x5'), None)
      if json_player_entries != None:
        player = {
                      'id' : id_offset_player,
                      's_id' : json_objet_info_player["id"],
                      'acc_id' : json_objet_info_player["accountId"],
                      'puuid' : json_objet_info_player["puuid"],
                      'name' : json_objet_account["gameName"],
                      'level' : json_objet_info_player["summonerLevel"],
                      'league_id' : json_player_entries["leagueId"],
                      'tier' : json_player_entries['tier'], 
                      'rank' : json_player_entries['rank'], 
                      'lp' : json_player_entries["leaguePoints"],
                      'wins' : json_player_entries["wins"],
                      'losses' : json_player_entries["losses"],
                      'veteran' : json_player_entries["veteran"],
                      'inactive' : json_player_entries["inactive"],
                      'hotStreak' : json_player_entries["hotStreak"],
                      'in_game' : False,
                      'current_match_id' : 0
                      }
        tracked_players[id_offset_player] = player
        logging.info('Player added to the tracked players dictionnary ' + tracked_players[id_offset_player]["name"] + ' with offset ' + str(id_offset_player))
        await ctx.respond(tracked_players[id_offset_player]["name"] + ' ajouté à la liste')
        id_offset_player += 1
      else:
        await ctx.respond('Pas encore ranked')
        logging.info('Player ' + player_name + ' not added so not yet ranked')

@bot.slash_command(name="delete_player",description="Supprime un joueur de liste à tracker",guild_ids=[guild_id])
async def remove_players(ctx, player_name: str):
   global tracked_players
   tracked_players_names = []
   for player_id,data in tracked_players.copy().items():
     if data['name'] == player_name:
        id_to_delete = player_id
        game_id_to_delete = str(data['current_match_id']) + ',' + str(player_id)
     tracked_players_names.append(data["name"])
   if player_name in tracked_players_names:
      tracked_players.pop(id_to_delete)
      try:
         tracked_games.pop(game_id_to_delete)
         logging.info('game' + str(game_id_to_delete)  + ' deleted while deleting player' + player_name)
      except:
         logging.info('game' + str(game_id_to_delete)  + ' not found for deletion')
      await ctx.respond('Joueur ' + player_name + ' supprimé')
      logging.info('Player' + player_name + ' not added so not yet ranked')
   else:
      await ctx.respond('Joueur ' + player_name + ' pas dans la liste')
      logging.info('Player' + player_name  + ' not in the list' )
      
@bot.slash_command(name="list_players",description="Affiche la liste à tracker",guild_ids=[guild_id])
async def remove_players(ctx,):
   global tracked_players
   tracked_players_names = []
   for player_id,data in tracked_players.copy().items():
     tracked_players_names.append(data["name"])
   if len(tracked_players_names) == 0:
     await ctx.respond('Pas de joueur tracké, utiliser /add_players pour en ajouter')
   else:
     await ctx.respond('Voici la liste des joueurs: ' + ', '.join(tracked_players_names))
   

@bot.slash_command(name="history",description="Affiche l'historique des dernieres ranked solo duo pour un joueur",guild_ids=[guild_id])
async def history(ctx, player_name: str, game_count: int):
    global tracked_players
    found = False
    if tracked_players != {}:
      logging.info("Startup of function /history...")
      await ctx.defer()
      for player_id,data in tracked_players.copy().items():
        if player_name == data['name']:
          id_to_track = player_id
          found = True
      if found == False:
        await ctx.respond("Pas dans les joueurs trackés, ajoutez le d'abord")
        logging.error("Player " + player_name + 'is not part of tracked players')
        return
      if game_count > 10:
        await ctx.respond("Nombre maximum de game 10")
        logging.error('Maximum game number requests exceeded')
        return
      else:
        embed = discord.Embed(
            title= 'Historique de ' + player_name + ' les ' + str(game_count) + ' dernières games: ' 
            )
        await ctx.respond(embed=embed)
        match_ids = await (get_n_games_id(id_to_track,riot_api_key,game_count,'soloduo'))
        for match_id in match_ids:
          ended_game_detail = 'https://europe.api.riotgames.com/lol/match/v5/matches/'+ match_id +'?api_key=' + riot_api_key
          game_detail = requests.get(ended_game_detail)
          if game_detail.status_code == 200:
            json_objet_game_detail = json.loads(game_detail.text)
            date_start = strftime('%Y-%m-%d %H:%M', localtime(json_objet_game_detail["info"]["gameStartTimestamp"]/1000))
            game_duration_minutes = str(time.strftime("%M:%S", time.gmtime(json_objet_game_detail["info"]["gameDuration"])))  
            for participant in json_objet_game_detail["info"]["participants"]:
                if participant["puuid"] == tracked_players[id_to_track]['puuid']:
                    win_bool = participant["win"]
                    player_name = participant["summonerName"]
                    kills = participant["kills"]
                    deaths = participant["deaths"]
                    assists = participant["assists"]
                    champ = participant["championName"]
                    lane = participant["lane"]
                    degats_ap = participant["magicDamageDealtToChampions"]
                    degats_ad = participant["physicalDamageDealtToChampions"]
                    visionScore = participant["visionScore"]
                    wardsPlaced = participant["wardsPlaced"]
                    wardsKilled = participant["wardsKilled"]
                    minion_killed = participant["totalMinionsKilled"]
                    neutral_minion_killed = participant["neutralMinionsKilled"]
                    ally_jungle_creep = participant["totalAllyJungleMinionsKilled"]
                    ennemey_jungle_creep = participant["totalEnemyJungleMinionsKilled"]
                    total_creep = minion_killed + neutral_minion_killed + ally_jungle_creep + ennemey_jungle_creep
                    creep_per_minute = round(minion_killed/((json_objet_game_detail["info"]["gameDuration"])/60),1)
                    totalDamageDealtToChampions = participant["totalDamageDealtToChampions"]
                    totalDamageTaken = participant["totalDamageTaken"]
                    longestTimeSpentLiving = str(time.strftime("%M:%S", time.gmtime(participant["longestTimeSpentLiving"])))  
                    goldEarned = participant["goldEarned"]
                    dragonKills = participant["dragonKills"]
                    damageDealtToBuildings = participant["damageDealtToBuildings"]
                    damageSelfMitigated = participant["damageSelfMitigated"]
                    if win_bool == False:
                      win = 'LOOSE'
                    else:
                      win = 'WIN'
                    if win == 'LOOSE':
                        color_message = discord.Colour.red()
                    if win == 'WIN':
                        color_message = discord.Colour.green()
            kda = str(kills) + '/' + str(deaths) + '/' + str(assists)
            image_in_message = 'https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/' + champ + '.png'
            embed = discord.Embed(
            title= player_name + ' | ' + champ + ' ' + lane + ' - ' + win + ' | '+  game_duration_minutes ,
            color=color_message,
            )
            embed.set_author(name="RankedTracker", url=bot_icon_url, icon_url="")
            embed.set_image(url=image_in_message)
            embed.add_field(name="KDA : " + kda + ' | CS : ' + str(total_creep) + ' ( ' + str(creep_per_minute) + ' CS/min )' + ' *tousse* volé au Jungle allié: ' + str(ally_jungle_creep) ,value='' ,inline=False)
            embed.add_field(name="Gold gagnés : " + str(goldEarned)  + " | Durée max en vie " + str(longestTimeSpentLiving),value='' ,inline=False)
            embed.add_field(name="Degats AD / Degats AP  / Total degats champ: ", value= str(degats_ad) + ' / ' + str(degats_ap) + ' / ' + str(totalDamageDealtToChampions) , inline=False)
            embed.add_field(name="Degats pris / Mitigated", value= str(totalDamageTaken) + ' / '  + str(damageSelfMitigated) , inline=False)
            embed.add_field(name="Score de vision / Ward placées / detruites", value= str(visionScore) + ' / ' + str(wardsPlaced) + ' / ' + str(wardsKilled), inline=False)
            embed.add_field(name="Drakes / Degats batiments", value= str(dragonKills) + ' / ' + str(damageDealtToBuildings), inline=False)
            embed.set_footer(text='Date: ' + str(date_start))
            await ctx.respond(embed=embed)
          else:
            await ctx.respond('Ressayez plus tard')
        embed = discord.Embed(
            title= 'Fin de l\'historique ' 
            )
        await ctx.respond(embed=embed)    
    else:
      await ctx.respond('Pas de joueurs trackés, ajoutez en d\'abord avec /add_players')
      logging.error('No tracked players in the tracked players, add before requesting history')
      return
   

#Initialisation bot
@bot.event
async def on_ready():
    logging.info("Bot startup...")
    import_champs()
    await bot.change_presence(status=discord.Status.online, activity=discord.Game(name="Venger ZizRob Sr"))
    check_live_game.start()
    update_live_match_embed.start()
    send_leaderboard.start()
    logging.info('Bot ID: {}'.format(bot.user.id))
    logging.info(f"Logged in {bot.user}")


@tasks.loop(hours=24)
async def send_leaderboard():
  guild = bot.get_guild(guild_id)
  channel = guild.get_channel(channel_id)
  global tracked_players
  tiers = {'CHALLENGER I' : [],'GRANDMASTER I' : [],'MASTER I' : [],'DIAMOND I' : [],'DIAMOND II' : [],'DIAMOND III' : [],'DIAMOND IV' : [],'EMERALD I' : [],'EMERALD II' : [],'EMERALD III' : [],'EMERALD IV' : [], 'PLATINUM I' : [], 'PLATINUM II' : [],'PLATINUM III' : [],'PLATINUM IV' : [],'GOLD I' : [],'GOLD II' : [],'GOLD III' : [],'GOLD IV' : [], 'SILVER I' : [] ,'SILVER II' : [] ,'SILVER III' : [] ,'SILVER IV' : [] ,'BRONZE I' : [], 'BRONZE II' : [],'BRONZE III' : [], 'BRONZE IV' : [], 'IRON I' : [], 'IRON II' : [], 'IRON III' : [], 'IRON IV' : [] }
  if tracked_players != {}:
    logging.info("Startup of function send_leaderboard...")
    for player_id,player in tracked_players.copy().items():
      rank = player['tier'] + ' ' +player['rank']
      for tier, tier_table in tiers.copy().items():
          if rank == tier:
            formatted_rank_elo =  []
            formatted_rank_elo.append(player['name'])
            formatted_rank_elo.append(player['tier'])
            formatted_rank_elo.append(player['rank'])
            formatted_rank_elo.append(str(player['lp']))
            tiers[tier].append(formatted_rank_elo)
    #Sorting each tier by LP
    for tier,players_ranks in tiers.copy().items():
      players_ranks.sort(reverse = True, key=lambda x: int(x[3]))
    #Displaying results
    leaderboard_position = 1
    image_in_message = ''
    embed = discord.Embed(
    title="LEADERBOARD",
    color=discord.Colour.blue(),
    )
    embed.set_author(name="RankedInspector", url=bot_icon_url, icon_url="")
    embed.set_image(url=image_in_message)
    for tier,players_ranks in tiers.copy().items():
      for player in players_ranks:
        match leaderboard_position:
           case 1:
             embed.add_field(name=str(leaderboard_position) + '. ' + ' '.join(player) + ' LP <a:trophy:1225058851875852348><a:trophy:1225058851875852348><a:trophy:1225058851875852348>',value='',inline=False)
           case 2:
             embed.add_field(name=str(leaderboard_position) + '. ' + ' '.join(player) + ' LP <a:trophy:1225058851875852348><a:trophy:1225058851875852348>',value='',inline=False)
           case 3:
             embed.add_field(name=str(leaderboard_position) + '. ' + ' '.join(player) + ' LP <a:trophy:1225058851875852348>',value='',inline=False)
           case _:
             embed.add_field(name=str(leaderboard_position) + '. ' + ' '.join(player) + ' LP' ,value='',inline=False)
        leaderboard_position += 1
    await channel.send(embed=embed)
    logging.info("Leaderboard sent..") 
  else:
    logging.info("No player to make a leaderboard...") 
    
@tasks.loop(seconds=60)
async def check_live_game():
  global tracked_games
  global tracked_players
  if tracked_players != {}:
    logging.info("Startup of function check_live_game...")
    for id,player in tracked_players.copy().items():
       await get_live_match_data(player['name'])
   

@tasks.loop(seconds=80)
async def update_live_match_embed():
  logging.info("Starting task update_live_match_embed... ")
  global tracked_games
  global tracked_players
  guild = bot.get_guild(guild_id)
  channel = guild.get_channel(channel_id)
  if tracked_games != {}:
    for game_id_player_id,game in tracked_games.copy().items():
        game_id = game_id_player_id.split(",")[0]
        logging.info("Starting update embed for game " + str(game_id))
        if 'message_id' not in game:
          message = ('Game en cours (déclarée ? <a:frog:1217413850316406835> ) \n On espere ? \nWIN : <a:frog:1217413850316406835> \n LOOSE: <a:clown:1217234376421670972> \n'.format(game['tracked_name'],dict_champ[str(game['champ_id'])]))
          image_in_message = 'https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/' + dict_champ[str(game['champ_id'])] + '.png'
          embed = discord.Embed(
          title="Ranked SOLO/DUO de " + game['tracked_name'] + '  |  ' + str(time.strftime("%M:%S", time.gmtime(game['game_data']['gameLength']))),
          description=message,
          color=discord.Colour.blue(),
          )
          embed.set_author(name="RankedInspector", url=bot_icon_url, icon_url="")
          embed.set_image(url=image_in_message)
          embed.add_field(name="Rang : ",value=game['tier_before_match'] + ' ' + game['rank_before_match'] + ' ' +  str(game['lp_before_match']) + ' LP' ,inline=False)
          embed.set_footer(text='Date: ' + strftime('%Y-%m-%d %H:%M', localtime(game['game_data']['gameStartTime']/1000)))
          sent_embed = await channel.send(embed=embed)
          tracked_games[game_id_player_id]['message_id'] = sent_embed.id
          logging.info('First message for game ' + str(game_id))
        if 'message_id' in game:
          message_id = game['message_id']
          msg = await channel.fetch_message(message_id)
          #check if game ended
          ended_game_detail = 'https://europe.api.riotgames.com/lol/match/v5/matches/EUW1_'+ str(game_id) +'?api_key=' + riot_api_key
          game_detail = requests.get(ended_game_detail)
          if game_detail.status_code == 200:
                logging.info('Game EUW1_' + str(game_id) + ' ended')
                json_objet_game_detail = json.loads(game_detail.text)
                date_start = strftime('%Y-%m-%d %H:%M', localtime(json_objet_game_detail["info"]["gameStartTimestamp"]/1000))
                game_duration_minutes = str(time.strftime("%M:%S", time.gmtime(json_objet_game_detail["info"]["gameDuration"])))  
                for participant in json_objet_game_detail["info"]["participants"]:
                    if participant["puuid"] == game['tracked_puuid']:
                        win_bool = participant["win"]
                        player_name = participant["summonerName"]
                        kills = participant["kills"]
                        deaths = participant["deaths"]
                        assists = participant["assists"]
                        champ = participant["championName"]
                        lane = participant["lane"]
                        degats_ap = participant["magicDamageDealtToChampions"]
                        degats_ad = participant["physicalDamageDealtToChampions"]
                        visionScore = participant["visionScore"]
                        wardsPlaced = participant["wardsPlaced"]
                        wardsKilled = participant["wardsKilled"]
                        minion_killed = participant["totalMinionsKilled"]
                        neutral_minion_killed = participant["neutralMinionsKilled"]
                        ally_jungle_creep = participant["totalAllyJungleMinionsKilled"]
                        ennemey_jungle_creep = participant["totalEnemyJungleMinionsKilled"]
                        total_creep = minion_killed + neutral_minion_killed + ally_jungle_creep + ennemey_jungle_creep
                        creep_per_minute = round(minion_killed/((json_objet_game_detail["info"]["gameDuration"])/60),1)
                        totalDamageDealtToChampions = participant["totalDamageDealtToChampions"]
                        totalDamageTaken = participant["totalDamageTaken"]
                        longestTimeSpentLiving = str(time.strftime("%M:%S", time.gmtime(participant["longestTimeSpentLiving"])))  
                        goldEarned = participant["goldEarned"]
                        dragonKills = participant["dragonKills"]
                        damageDealtToBuildings = participant["damageDealtToBuildings"]
                        damageSelfMitigated = participant["damageSelfMitigated"]
                        if win_bool == False:
                            win = 'LOOSE'
                        else:
                            win = 'WIN'
                if win == 'LOOSE':
                    color_message = discord.Colour.red()
                if win == 'WIN':
                    color_message = discord.Colour.green()
                logging.info('Update rank' + str(game_id) )
                await update_tracked_player_data(player_name)
                new_rank = tracked_players[game['player_id']]['rank']
                new_tier = tracked_players[game['player_id']]['tier']
                new_lp = tracked_players[game['player_id']]['lp']
                delta_lp = new_lp - game['lp_before_match']
                sign = ''
                if new_lp >= game['lp_before_match']:
                   sign = '+'
                kda = str(kills) + '/' + str(deaths) + '/' + str(assists)
                image_in_message = 'https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/' + champ + '.png'
                embed = discord.Embed(
                title= player_name + ' | ' + champ + ' ' + lane + ' - ' + win + ' | '+  game_duration_minutes ,
                color=color_message,
                )
                embed.set_author(name="RankedInspector", url=bot_icon_url, icon_url="")
                embed.set_image(url=image_in_message)
                embed.add_field(name="KDA : " + kda + ' | CS : ' + str(total_creep) + ' ( ' + str(creep_per_minute) + ' CS/min )' + ' *tousse* volé au Jungle allié: ' + str(ally_jungle_creep) ,value='' ,inline=False)
                embed.add_field(name="Rang : " ,value= new_tier + ' ' + new_rank + ' ' + str(new_lp) +' (' + sign + str(delta_lp) + ' LP )' ,inline=False)
                embed.add_field(name="Gold gagnés : " + str(goldEarned)  + " | Durée max en vie " + str(longestTimeSpentLiving),value='' ,inline=False)
                embed.add_field(name="Degats AD / Degats AP  / Total degats champ: ", value= str(degats_ad) + ' / ' + str(degats_ap) + ' / ' + str(totalDamageDealtToChampions) , inline=False)
                embed.add_field(name="Degats pris / Mitigated", value= str(totalDamageTaken) + ' / '  + str(damageSelfMitigated) , inline=False)
                embed.add_field(name="Score de vision / Ward placées / detruites", value= str(visionScore) + ' / ' + str(wardsPlaced) + ' / ' + str(wardsKilled), inline=False)
                embed.add_field(name="Drakes / Degats batiments", value= str(dragonKills) + ' / ' + str(damageDealtToBuildings), inline=False)
                embed.set_footer(text='Date: ' + str(date_start))
                await msg.edit(embed=embed)
                logging.info('Suppression of the game ' + str(game_id) + 'from the tracked_games dict...')
                tracked_games.pop(game_id_player_id)
          else:
            message = ('Game en cours (déclarée ? <a:frog:1217413850316406835> ) \n On espere ? \nWIN : <a:frog:1217413850316406835> \n LOOSE: <a:clown:1217234376421670972> \n'.format(game['tracked_name'],dict_champ[str(game['champ_id'])]))
            image_in_message = 'https://ddragon.leagueoflegends.com/cdn/14.5.1/img/champion/' + dict_champ[str(game['champ_id'])] + '.png'
            embed = discord.Embed(
            title="Ranked SOLO/DUO de " + game['tracked_name'] + '  |  ' + str(time.strftime("%M:%S", time.gmtime(game['game_data']['gameLength']))),
            description=message,
            color=discord.Colour.blue(),
            )
            embed.set_author(name="RankedInspector", url=bot_icon_url, icon_url="")
            embed.set_image(url=image_in_message)
            embed.add_field(name="Rang : ",value=game['tier_before_match'] + ' ' + game['rank_before_match'] + ' ' +  str(game['lp_before_match']) + ' LP' ,inline=False)
            embed.set_footer(text='Date: ' + strftime('%Y-%m-%d %H:%M', localtime(game['game_data']['gameStartTime']/1000)))
            await msg.edit(embed=embed)
            logging.info('Game ' + str(game_id) +' still in progess...' )
    logging.info('Update ended for the game' + str(game_id))
  else:
    logging.info('No game in progess...')
 

#Start the bot
bot.run(token)