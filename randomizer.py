import random
from cachetools import cached, TTLCache

random.seed()


def length():
    return random.randint(15, 215)


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id):
    l = length()
    sword_message = f'{user_id} blade is {str(l)}cm long. '
    if l <= 25:
        sword_message += 'Cute dagger, rogue'
    if l <= 35:
        sword_message += 'Deadly stiletto, assassin'
    if l <= 45:
        sword_message += 'Scary machete, organising tours through jungles?'
    elif l <= 60:
        sword_message += 'Sharp short sword, fighter'
    elif l <= 75:
        sword_message += 'Exotic katana, samurai'
    elif l <= 85:
        sword_message += 'Handy gladius, but Rome has fallen, centurion'
    elif l <= 90:
        sword_message += 'Swift sabre, ranger'
    elif l <= 100:
        sword_message += 'Elegant rapier, duelist'
    elif l <= 115:
        sword_message += 'Good broad sword, warrior'
    elif l <= 120:
        sword_message += 'Frightening bastard sword, barbarian'
    elif l <= 130:
        sword_message += 'Shiny long sword, knight'
    elif l <= 140:
        sword_message += 'Impressive claymore, now return it back to Clare, please'
    elif l <= 170:
        sword_message += 'What a flamberge! Go earn some fair mercenary coins, landsknecht'
    elif l <= 215:
        sword_message += 'Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul'
    return sword_message
