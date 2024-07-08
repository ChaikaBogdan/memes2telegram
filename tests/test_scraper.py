import pytest
import httpx
from pytest_httpx import HTTPXMock
from scraper import (
    is_dtf_video,
    get_uuid,
    is_downloadable_image,
    is_downloadable_video,
    is_instagram_post,
    is_joyreactor_post,
    get_headers,
    is_big,
    is_link,
    is_bot_message,
    is_private_message,
    link_to_bot,
)

BOT_NAME = "@memes2telegram_bot"


def test_is_big_content_length_less_than_200MB():
    headers = {"content-length": "10000000"}  # 10 MB
    assert is_big(headers) is False


def test_is_big_content_length_equal_to_200MB():
    headers = {"content-length": "209715200"}  # 200 MB
    assert is_big(headers) is False


def test_is_big_content_length_greater_than_200MB():
    headers = {"content-length": "210000000"}  # 200.78 MB
    assert is_big(headers) is True


def test_is_big_content_length_not_present():
    headers = {}
    assert is_big(headers) is False


def test_is_big_multiple_headers_with_content_length():
    headers = {
        "content-length": "50000000",  # 50 MB
        "other-header": "some-value",
    }
    assert is_big(headers) is False


def test_is_link_valid_url():
    message = "https://www.example.com"
    assert is_link(message) is True


def test_is_link_valid_url_with_query_parameters():
    message = "https://www.example.com/?param=value"
    assert is_link(message) is True


def test_is_link_invalid_url():
    message = "this_is_not_a_url"
    assert is_link(message) is False


def test_is_link_empty_message():
    message = ""
    assert is_link(message) is False


def test_is_link_space_character():
    message = " "
    assert is_link(message) is False


def test_is_link_domain_name_only():
    message = "example.com"
    assert is_link(message) is False


def test_is_link_ftp_url():
    message = "ftp://ftp.example.com"
    assert is_link(message) is True


def test_is_bot_message_starts_with_bot_name():
    text = f"{BOT_NAME} What is your name?"
    assert is_bot_message(text) is True


def test_is_bot_message_bot_name_in_middle():
    text = f"Hello, how are you? {BOT_NAME} What is your name?"
    assert is_bot_message(text) is False


def test_is_bot_message_empty_text():
    text = ""
    assert is_bot_message(text) is False


def test_is_bot_message_only_bot_name():
    text = BOT_NAME
    assert is_bot_message(text) is True


def test_is_bot_message_bot_name_at_end():
    text = f"What do you think? {BOT_NAME}"
    assert is_bot_message(text) is False


def test_is_private_message_private(mocker):
    chat = mocker.MagicMock(type="private")
    message = mocker.MagicMock(chat=chat)
    assert is_private_message(message) is True


def test_is_private_message_group(mocker):
    chat = mocker.MagicMock(type="group")
    message = mocker.MagicMock(chat=chat)
    assert is_private_message(message) is False


def test_is_private_message_supergroup(mocker):
    chat = mocker.MagicMock(type="supergroup")
    message = mocker.MagicMock(chat=chat)
    assert is_private_message(message) is False


def test_is_private_message_channel(mocker):
    chat = mocker.MagicMock(type="channel")
    message = mocker.MagicMock(chat=chat)
    assert is_private_message(message) is False


def test_is_private_message_unknown_chat_type(mocker):
    chat = mocker.MagicMock(type="unknown")
    message = mocker.MagicMock(chat=chat)
    assert is_private_message(message) is False


def test_link_to_bot_with_bot_name():
    text = f"Hello, {BOT_NAME}. How are you?"
    assert link_to_bot(text) == ". How are you?"


def test_link_to_bot_with_bot_name_and_spaces():
    text = f"Hello,    {BOT_NAME}   . How are you?"
    assert link_to_bot(text) == ". How are you?"


def test_link_to_bot_without_bot_name():
    text = "Hello, how are you?"
    assert link_to_bot(text) == "Hello, how are you?"


def test_link_to_bot_empty_text():
    text = ""
    assert link_to_bot(text) == ""


def test_link_to_bot_only_bot_name():
    text = BOT_NAME
    assert link_to_bot(text) == ""


def test_valid_joyreactor_post_url():
    url = "https://joyreactor.cc/post/12345"
    assert is_joyreactor_post(url) is True


def test_another_valid_joyreactor_post_url():
    url = "http://www.joyreactor.cc/post/67890"
    assert is_joyreactor_post(url) is True


def test_joy_url_with_multiple_substrings_one_valid():
    url = "https://joyreactor.cc/post/98765/gallery"
    assert is_joyreactor_post(url) is True


def test_joy_url_without_substring():
    url = "https://twitter.com/user123/status/123456"
    assert is_joyreactor_post(url) is False


def test_joy_empty_url():
    url = ""
    assert is_joyreactor_post(url) is False


def test_joy_url_with_domain_only_without_path():
    url = "reactor.cc"
    assert is_joyreactor_post(url) is False


def test_joy_url_with_domain_and_query_parameter():
    url = "reactor.cc?param=value"
    assert is_joyreactor_post(url) is False


def test_valid_instagram_post_url():
    url = "https://www.instagram.com/p/ABC123/"
    assert is_instagram_post(url) is True


def test_another_valid_instagram_post_url():
    url = "https://instagram.com/p/DEF456/"
    assert is_instagram_post(url) is True


def test_insta_url_with_multiple_substrings_one_valid():
    url = "https://www.instagram.com/p/GHI789/explore/"
    assert is_instagram_post(url) is True


def test_insta_url_without_substring():
    url = "https://twitter.com/user123/status/123456"
    assert is_instagram_post(url) is False


def test_insta_empty_url():
    url = ""
    assert is_instagram_post(url) is False


def test_insta_url_with_domain_only_without_path():
    url = "instagram.com"
    assert is_instagram_post(url) is False


def test_insta_url_with_domain_and_query_parameter():
    url = "instagram.com?param=value"
    assert is_instagram_post(url) is False


def test_is_dtf_video():
    dtf_url = "https://leonardo.osnova.io/xxx/-/format/mp4/"
    assert is_dtf_video(dtf_url) is True


def test_is_not_dtf_video():
    non_dtf_url = "https://img-9gag-fun.9cache.com/photo/xxx.mp4"
    assert is_dtf_video(non_dtf_url) is False


def test_get_uuid():
    dtf_url = (
        "https://leonardo.osnova.io/c01ed790-49bd-5bea-98f6-e3534c8d7493/-/format/mp4/"
    )
    expected_uuid = "c01ed790-49bd-5bea-98f6-e3534c8d7493"
    assert get_uuid(dtf_url) == expected_uuid


def test_is_downloadable_video():
    assert is_downloadable_video({"content-type": "video/mp4"})
    assert not is_downloadable_video({"content-type": "image/jpeg"})
    assert not is_downloadable_video({"content-type": "text/html"})


def test_is_downloadable_image():
    assert is_downloadable_image({"content-type": "image/jpeg"})
    assert not is_downloadable_image({"content-type": "video/mp4"})
    assert not is_downloadable_image({"content-type": "text/html"})


@pytest.mark.asyncio
async def test_get_headers(httpx_mock: HTTPXMock):
    url = "https://img2.joyreactor.cc/pics/avatar/tag/article/1481"
    headers = {"content-type": "image/jpeg", "content-length": "1"}
    httpx_mock.add_response(url=url, headers=headers)
    async with httpx.AsyncClient(follow_redirects=True) as client:
        headers = await get_headers(client, url)
    assert "content-type" in headers
    assert "content-length" in headers
    assert headers["content-type"] == "image/jpeg"
