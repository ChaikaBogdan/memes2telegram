import random
from cachetools import cached, TTLCache

random.seed()


def length():
    return random.randint(1, 40)


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id):
    l = length()
    sword_message = f'{user_id} blade is {str(l)}cm long. '
    if l <= 5:
        sword_message += 'Cute dagger, rogue'
    elif l <= 10:
        sword_message += 'Nice short sword, assassin'
    elif l <= 15:
        sword_message += 'Cool rapier, ranger'
    elif l <= 20:
        sword_message += 'Good broad sword, warrior'
    elif l <= 25:
        sword_message += 'Shiny long sword, knight'
    elif l <= 30:
        sword_message += 'Frightening bastard sword, barbarian'
    elif l <= 35:
        sword_message += 'Impressive claymore, go (s)lay some demons or something'
    elif l <= 40:
        sword_message += 'Gigantic zweihander, go (s)lay some dragons or something'
    return sword_message
