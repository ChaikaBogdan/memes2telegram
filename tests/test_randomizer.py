import pytest
import re
from randomizer import sword, random_blade_length

length_pattern = re.compile(r"\b(\d+)\s*cm\b")


def extract_length_from_message(message):
    match = re.search(length_pattern, message)
    if match:
        return int(match.group(1))
    return None


def test_extract_re_valid():
    message = "User blade is 45cm long."
    assert extract_length_from_message(message) == 45


def test_extract_re_non_valid():
    message = "Non valid"
    assert extract_length_from_message(message) is None


def test_extract_re_empty():
    message = ""
    assert extract_length_from_message(message) is None


async def test_sword_result():
    user_id = "test_user"
    result = await sword(user_id)
    assert isinstance(result, str)
    assert user_id in result


def test_random_blade_length_within_range():
    blade_length = random_blade_length()
    assert 15 <= blade_length <= 160


def test_random_blade_length_integer():
    blade_length = random_blade_length()
    assert isinstance(blade_length, int)


def test_random_blade_length_min_max_values():
    min_blade = 50
    max_blade = 50
    blade_length = random_blade_length(min_blade, max_blade)
    assert blade_length == 50


def test_random_blade_length_custom_range():
    min_blade = 200
    max_blade = 250
    blade_length = random_blade_length(min_blade, max_blade)
    assert 200 <= blade_length <= 250


def test_random_blade_length_negative_range():
    with pytest.raises(ValueError):
        random_blade_length(min_blade=160, max_blade=15)


async def test_sword_message():
    user_id = "test_user"
    result = await sword(user_id)
    assert user_id in result, f"The user_id {user_id} should be present in the result"
    assert "blade is " in result, "The 'blade is ' part should be present in the result"


async def test_sword_length():
    user_id = "test_user"
    result = await sword(user_id)
    assert extract_length_from_message(result) in range(15, 160)


async def test_sword_length_descriptions():
    user_id = "test_user"
    swords = [
        "Cute dagger, rogue",
        "Deadly stiletto, assassin",
        "Scary machete, organizing tours through jungles?",
        "Sharp short sword, fighter",
        "Exotic katana, samurai",
        "Handy gladius, but Rome has fallen, centurion",
        "Swift sabre, ranger",
        "Elegant rapier, duelist",
        "Good broadsword, warrior",
        "Frightening bastard sword, barbarian",
        "Shiny longsword, knight",
        "Impressive claymore, now return it back to Clare, please",
        "What a flamberge! Go earn some fair mercenary coins, landsknecht",
        "Giant Dad™ chaos zweihander +5, I hope you did not level DEX, casul",
    ]
    result = await sword(user_id)
    assert result.split(". ")[1] in swords
