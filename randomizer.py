import random
import subprocess
from cachetools import cached, TTLCache

random.seed()


def random_blade_length(min_blade: int = 15, max_blade: int = 160) -> int:
    return random.randint(min_blade, max_blade)


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def sword(user_id: str) -> str:
    if not user_id:
        raise TypeError(Exception("user_id cannot be empty"))
    length = random_blade_length()
    sword_message = f"{user_id} blade is {length}cm long. "

    swords = {
        25: "Cute dagger, rogue",
        35: "Deadly stiletto, assassin",
        45: "Scary machete, organizing tours through jungles?",
        60: "Sharp short sword, fighter",
        75: "Exotic katana, samurai",
        85: "Handy gladius, but Rome has fallen, centurion",
        90: "Swift sabre, ranger",
        100: "Elegant rapier, duelist",
        115: "Good broadsword, warrior",
        120: "Frightening bastard sword, barbarian",
        130: "Shiny longsword, knight",
        140: "Impressive claymore, now return it back to Clare, please",
        150: "What a flamberge! Go earn some fair mercenary coins, landsknecht",
        160: "Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul",
    }

    for blade_length, description in swords.items():
        if length <= blade_length:
            return sword_message + description

    return sword_message


@cached(cache=TTLCache(maxsize=100, ttl=43200))
def fortune(user_id: str) -> str:
    try:
        completed_process = subprocess.run(["fortune"], capture_output=True, text=True)
        if completed_process.returncode == 0:
            return f"{user_id} fortune for today:\n{completed_process.stdout.strip()}"
        else:
            return "Error executing fortune command"
    except FileNotFoundError:
        return "The 'fortune' is not installed on bot system."
