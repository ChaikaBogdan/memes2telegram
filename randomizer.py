import logging
import html
import random
import subprocess

random.seed()

FORTUNE_WIDTH = 20
FORTUNE_SCRIPT = "/usr/games/fortune"
COWSAY_SCRIPT = "/usr/games/cowsay"
logger = logging.getLogger(__name__)

SWORDS = {
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


def random_blade_length(min_blade: int = 15, max_blade: int = 160) -> int:
    return random.randint(min_blade, max_blade)


def sword(user_id: str) -> str:
    length = random_blade_length()
    sword_message = f"{user_id} blade is {length}cm long."

    for blade_length, description in SWORDS.items():
        if length <= blade_length:
            return f"{sword_message} {description}"

    return sword_message


class RandomizerException(Exception):
    pass


def fortune(user_id: str) -> str:
    fortune_process = subprocess.run(
        [FORTUNE_SCRIPT, "-s"], capture_output=True, text=True
    )
    return_code = fortune_process.returncode
    if return_code != 0:
        raise RandomizerException(f"Error executing {FORTUNE_SCRIPT} - return code: {return_code}")
    fortune_line = fortune_process.stdout.strip()
    try:
        subprocess.run([COWSAY_SCRIPT, "-l"], capture_output=True)
    except FileNotFoundError as exc:
        logger.warning(str(exc))
    else:
        cowsay_process = subprocess.run(
            [COWSAY_SCRIPT, "-W", str(FORTUNE_WIDTH), fortune_line],
            capture_output=True,
            text=True,
        )
        return_code = cowsay_process.returncode
        if return_code != 0:
            logger.warning("Error executing %s - return code: %d", COWSAY_SCRIPT, return_code)
        else:
            fortune_line = cowsay_process.stdout.strip()
    fortune_line = html.escape(fortune_line)
    fortune_header = f"{user_id} fortune for today"
    return f"{fortune_header}<pre><code>{fortune_line}</code></pre>"
