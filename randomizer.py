import logging
import random
import subprocess

random.seed()

FORTUNE_WIDTH = 20
logger = logging.getLogger(__name__)


def random_blade_length(min_blade: int = 15, max_blade: int = 160) -> int:
    return random.randint(min_blade, max_blade)


def sword(user_id: str | None) -> str:
    if not user_id:
        return "User id can't be empty"
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
            return f"{sword_message}{description}"

    return sword_message


def fortune(user_id: str) -> str:
    try:
        fortune_process = subprocess.run(
            ["/usr/games/fortune", "-s"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return "The 'fortune' is not installed on bot system."
    if fortune_process.returncode != 0:
        return "Error executing 'fortune' command"
    fortune_line = fortune_process.stdout.strip()
    try:
        subprocess.run(["/usr/games/cowsay", "-l"], capture_output=True)
    except FileNotFoundError:
        logger.warning("The 'cowsay' is not installed on bot system")
    else:
        cowsay_process = subprocess.run(
            ["/usr/games/cowsay", "-W", str(FORTUNE_WIDTH), fortune_line],
            capture_output=True,
            text=True,
        )
        fortune_line = cowsay_process.stdout.strip()
    fortune_header = f"{user_id} fortune for today"
    return f"{fortune_header}<pre><code>{fortune_line}</code></pre>"
