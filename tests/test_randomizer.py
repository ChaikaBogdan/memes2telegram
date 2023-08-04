from unittest.mock import patch
import pytest
import re
from randomizer import sword, fortune, random_blade_length


def extract_length_from_message(message):
    pattern = r"\b(\d+)\s*cm\b"
    match = re.search(pattern, message)
    if match:
        return int(match.group(1))
    else:
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


def test_sword_result():
    user_id = "test_user"
    result = sword(user_id)
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


def test_sword_with_cache(mocker):
    user_id = "test_user"
    mocker.patch("randomizer.random_blade_length", return_value=50)
    result1 = sword(user_id)
    result2 = sword(user_id)
    assert result1 == result2


def test_sword_message():
    user_id = "test_user"
    result = sword(user_id)
    assert user_id in result, f"The user_id {user_id} should be present in the result"
    assert "blade is " in result, "The 'blade is ' part should be present in the result"


def test_sword_with_invalid_user_id():
    user_id = ""
    with pytest.raises(TypeError):
        sword(user_id)


def test_sword_length():
    user_id = "test_user"
    result = sword(user_id)
    assert extract_length_from_message(result) in range(15, 160)


def test_sword_length_descriptions():
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
    result = sword(user_id)
    assert result.split(". ")[1] in swords


def test_fortune_success():
    user_id = "test_user"
    expected_output = f"{user_id} fortune for today:\nFortune text goes here"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Fortune text goes here"

        result = fortune(user_id)
        assert result == expected_output


def test_fortune_failure():
    user_id = "test_user"
    expected_output = f"{user_id} fortune for today:\nFortune text goes here"

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stdout = "Fortune text goes here"

        result = fortune(user_id)
        assert result == expected_output


def test_fortune_with_cache(mocker):
    user_id = "test_user"
    mocker.patch("randomizer.fortune", return_value="Fortune text goes here")
    result1 = fortune(user_id)
    result2 = fortune(user_id)
    assert result1 == result2
