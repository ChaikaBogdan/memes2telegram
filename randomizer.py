import random, subprocess
from cachetools import cached, TTLCache

random.seed()

def random_blade_length(min_blade: int = 15, max_blade: int = 160) -> int:
    return random.randint(min_blade, max_blade)

@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id: str) -> str:
    length = random_blade_length()
    sword_message = f'{user_id} blade is {str(length)}cm long. '

    if length <= 25:
        sword_message += 'Cute dagger, rogue'
    elif length <= 35:
        sword_message += 'Deadly stiletto, assassin'
    elif length <= 45:
        sword_message += 'Scary machete, organizing tours through jungles?'
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
        sword_message += 'Good broadsword, warrior'
    elif length <= 120:
        sword_message += 'Frightening bastard sword, barbarian'
    elif length <= 130:
        sword_message += 'Shiny longsword, knight'
    elif length <= 140:
        sword_message += 'Impressive claymore, now return it back to Clare, please'
    elif length <= 150:
        sword_message += 'What a flamberge! Go earn some fair mercenary coins, landsknecht'
    elif length <= 160:
        sword_message += 'Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul'
    return sword_message


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def fortune(user_id: str) -> str:
    try:
        completed_process = subprocess.run(["fortune"], capture_output=True, text=True)
        if completed_process.returncode == 0:
            return f'{user_id} fortune for today:\n{completed_process.stdout.strip()}' 
        else:
            return f"Error executing fortune command. Return code: {completed_process.returncode}"
    except FileNotFoundError:
        return "The 'fortune' command is not installed or not found on bot system."
