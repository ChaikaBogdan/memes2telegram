import pytest
from converter import convert2mp4


@pytest.mark.asyncio
async def test_convert2mp4_with_empty_filename():
    filename = ""
    result = convert2mp4(filename)
    assert result is None


# Write your tests here


@pytest.mark.asyncio
async def test_convert2mp4_with_non_existing_filename():
    filename = "test.txt"
    result = convert2mp4(filename)
    assert result is None
