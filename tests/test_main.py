from unittest.mock import patch
import pytest
import httpx
from pytest_httpx import HTTPXMock

from main import (
    check_link,
    image2photo,
    InputMediaPhoto,
    images2album,
)

image_headers = {"content-type": "image/jpeg", "content-length":  b"1", "content": b"1"}


@pytest.fixture(autouse=True)
def mock_get_image_dimensions():
    with patch("main.get_image_dimensions") as mock_get_image_dimensions:
        mock_get_image_dimensions.return_value = (100, 200)
        yield mock_get_image_dimensions


async def test_check_link_empty_message():
    link = ""
    result = await check_link(link)
    assert result[0] == "Empty message!"


async def test_check_link_not_a_link():
    link = "not_a_link"
    result = await check_link(link)
    assert result[0] == "Not a link!"


async def test_check_link_instagram_post():
    link = "https://www.instagram.com/p/12345/"
    result = await check_link(link)
    assert result[0] is None


async def test_check_link_joyreactor_post():
    link = "https://joyreactor.cc/post/12345"
    result = await check_link(link)
    assert result[0] is None


async def test_check_link_downloadable_video(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4"}
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.get_headers", return_value=headers)

    result = await check_link(link)
    assert result[0] is None


async def test_check_link_non_downloadable_video(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/vid"}
    mocker.patch("main.is_downloadable_video", return_value=False)
    mocker.patch("main.get_headers", return_value=headers)

    result = await check_link(link)
    assert (
        result[0]
        == "Can't download https://example.com/some_video.mp4 - video/vid unknown!"
    )

async def test_check_link_big_file(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4", "content-length": "500000000"}  # 500 MB
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.is_big", return_value=True)
    mocker.patch("main.get_headers", return_value=headers)

    result = await check_link(link)
    assert (
        result[0]
        == "Can't download this https://example.com/some_video.mp4 - file is too big!"
    )


async def test_check_link_regular_case(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4"}
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.is_big", return_value=False)
    mocker.patch("main.get_headers", return_value=headers)

    result = await check_link(link)
    assert result[0] is None


async def test_image2photo(httpx_mock: HTTPXMock):
    image_link = "https://example.com/image.jpg"
    httpx_mock.add_response(url=image_link, headers=image_headers)
    caption = "This is a caption"
    async with httpx.AsyncClient(follow_redirects=True) as client:
        result = await image2photo(client, image_link, caption)
    assert isinstance(result, InputMediaPhoto)
    assert result.caption == caption


async def test_image2photo_empty_caption(httpx_mock: HTTPXMock):
    url = "https://example.com/image.jpg"
    httpx_mock.add_response(url=url, headers=image_headers)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        result = await image2photo(client, url)
    assert isinstance(result, InputMediaPhoto)
    assert not result.caption

async def test_images2album_5_images(httpx_mock: HTTPXMock):
    image_links = [f"https://example.com/album/image{i}.jpg" for i in range(1, 6)]
    for url in image_links:
        httpx_mock.add_response(url=url, headers=image_headers)
    link = "https://example.com/album"
    result = await images2album(image_links, link)
    assert len(result) == 5


async def test_images2album_2_images(httpx_mock: HTTPXMock):
    image_links = [
        "https://example.com/album/image1.jpg",
        "https://example.com/album/image2.jpg",
    ]
    for url in image_links:
        httpx_mock.add_response(url=url, headers=image_headers)
    link = "https://example.com/album"
    result = await images2album(image_links, link)
    assert len(result) == 2


async def test_images2album_more_than_9_images(httpx_mock: HTTPXMock):
    image_links = [f"https://example.com/album/image{i}.jpg" for i in range(1, 20)]
    for url in image_links:
        httpx_mock.add_response(url=url, headers=image_headers)
    link = "https://example.com/album"
    result = await images2album(image_links, link)
    assert len(result) == 19


async def test_images2album_no_images():
    image_links = []
    link = "https://example.com/album"
    expected_result = []
    result = await images2album(image_links, link)
    assert result == expected_result
