

def check_players(player, games):
    for game in games:
        if player in game:
            return True
    return False
