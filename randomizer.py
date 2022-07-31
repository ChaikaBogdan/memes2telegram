import random
from cachetools import cached, TTLCache

random.seed()


def random_blade_length(min_blade=15, max_blade=160):
    return random.randint(min_blade, max_blade)


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id):
    length = random_blade_length()
    sword_message = f'{user_id} blade is {str(length)}cm long. '
    if length <= 25:
        sword_message += 'Cute dagger, rogue'
    elif length <= 35:
        sword_message += 'Deadly stiletto, assassin'
    elif length <= 45:
        sword_message += 'Scary machete, organising tours through jungles?'
    elif length <= 60:
        sword_message += 'Sharp short sword, fighter'
    elif length <= 75:
        sword_message += 'Exotic katana, samurai'
    elif length <= 85:
        sword_message += 'Handy gladius, but Rome has fallen, centurion'
    elif length <= 90:
        sword_message += 'Swift sabre, ranger'
    elif length <= 100:
        sword_message += 'Elegant rapier, duelist'
    elif length <= 115:
        sword_message += 'Good broad sword, warrior'
    elif length <= 120:
        sword_message += 'Frightening bastard sword, barbarian'
    elif length <= 130:
        sword_message += 'Shiny long sword, knight'
    elif length <= 140:
        sword_message += 'Impressive claymore, now return it back to Clare, please'
    elif length <= 150:
        sword_message += 'What a flamberge! Go earn some fair mercenary coins, landsknecht'
    elif length <= 160:
        sword_message += 'Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul'
    return sword_message
