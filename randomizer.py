import random
import subprocess

random.seed()

AVAILABLE_COWS = []
FORTUNE_WIDTH = 20

try:
    cows_l = subprocess.run(["cowsay", "-l"], capture_output=True)
except FileNotFoundError:
    print("The 'cowsay' is not installed on bot system.")
else:
    cows_list = subprocess.run(
        ["tail", "-n", "+2"],
        input=cows_l.stdout,
        capture_output=True,
    )
    AVAILABLE_COWS = cows_list.stdout.decode().strip().split(" ")


def random_blade_length(min_blade: int = 15, max_blade: int = 160) -> int:
    return random.randint(min_blade, max_blade)


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
            return f"{sword_message}{description}"

    return sword_message


def fortune(user_id: str) -> str:
    fortune_header = f"{user_id} fortune for today"
    try:
        fortune_process = subprocess.run(
            ["fortune", "-s", "fortunes"], capture_output=True, text=True
        )
    except FileNotFoundError:
        return "The 'fortune' is not installed on bot system."
    if fortune_process.returncode == 0:
        fortune_line = fortune_process.stdout.strip()
        if AVAILABLE_COWS:
            cowsay_process = subprocess.run(
                ["cowsay", "-W", str(FORTUNE_WIDTH), fortune_line],
                capture_output=True,
                text=True,
            )
            fortune_line = cowsay_process.stdout.strip()
        return f"{fortune_header}<pre><code>{fortune_line}</code></pre>"
    return "Error executing fortune command"
