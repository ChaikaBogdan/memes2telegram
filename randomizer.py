import asyncio
import logging
import html
import random

random.seed()

LINE_WIDTH = 30
FORTUNE_SCRIPT = "/usr/games/fortune"
COWSAY_SCRIPT = "/usr/games/cowsay"
FIGLET_SCRIPT = "/usr/bin/figlet"
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


async def sword(user_id: str) -> str:
    length = random_blade_length()
    sword_message = f"{user_id} blade is {length}cm long."

    for blade_length, description in SWORDS.items():
        if length <= blade_length:
            return f"{sword_message} {description}"

    return sword_message


async def _run_command(*args) -> str:
    process = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    return stdout.decode()


async def fortune(user_id: str) -> str:
    fortune_line = await _run_command(FORTUNE_SCRIPT, "-s")
    cowsay_line = await _run_command(COWSAY_SCRIPT, "-W", str(LINE_WIDTH), fortune_line.strip())
    escaped_line = html.escape(cowsay_line.strip())
    return f"{user_id} fortune for today<pre><code>{escaped_line}</code></pre>"


async def nsfw(text: str = "not safe for work", lines_count: int = 4) -> str:
    lines = '\n'.join(text.upper() for _ in range(lines_count))
    figlet_line =  await _run_command(FIGLET_SCRIPT, "-w", str(LINE_WIDTH), "-c", lines)
    escaped_line = html.escape(figlet_line)
    return f"Пригнись! Там женщина!<pre><code>{escaped_line}</code></pre>"
