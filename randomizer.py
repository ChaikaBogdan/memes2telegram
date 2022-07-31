import random
from cachetools import cached, TTLCache

random.seed()


def length():
    return random.randint(15, 160)


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id):
    lenght = length()
    sword_message = f'{user_id} blade is {str(lenght)}cm long. '
    if lenght <= 25:
        sword_message += 'Cute dagger, rogue'
    elif lenght <= 35:
        sword_message += 'Deadly stiletto, assassin'
    elif lenght <= 45:
        sword_message += 'Scary machete, organising tours through jungles?'
    elif lenght <= 60:
        sword_message += 'Sharp short sword, fighter'
    elif lenght <= 75:
        sword_message += 'Exotic katana, samurai'
    elif lenght <= 85:
        sword_message += 'Handy gladius, but Rome has fallen, centurion'
    elif lenght <= 90:
        sword_message += 'Swift sabre, ranger'
    elif lenght <= 100:
        sword_message += 'Elegant rapier, duelist'
    elif lenght <= 115:
        sword_message += 'Good broad sword, warrior'
    elif lenght <= 120:
        sword_message += 'Frightening bastard sword, barbarian'
    elif lenght <= 130:
        sword_message += 'Shiny long sword, knight'
    elif lenght <= 140:
        sword_message += 'Impressive claymore, now return it back to Clare, please'
    elif lenght <= 150:
        sword_message += 'What a flamberge! Go earn some fair mercenary coins, landsknecht'
    elif lenght <= 160:
        sword_message += 'Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul'
    return sword_message
