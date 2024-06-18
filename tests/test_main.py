from main import (
    check_link,
    image2photo,
    InputMediaPhoto,
    images2album,
)


def test_check_link_empty_message():
    link = ""
    result = check_link(link)
    assert result == "Empty message!"


def test_check_link_not_a_link():
    link = "not_a_link"
    result = check_link(link)
    assert result == "Not a link!"


def test_check_link_instagram_post():
    link = "https://www.instagram.com/p/12345/"
    result = check_link(link)
    assert result is None


def test_check_link_joyreactor_post():
    link = "https://joyreactor.cc/post/12345"
    result = check_link(link)
    assert result is None


def test_check_link_downloadable_video(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4"}
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.get_headers", return_value=headers)

    result = check_link(link)
    assert result is None


def test_check_link_non_downloadable_video(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "image/jpeg"}
    mocker.patch("main.is_downloadable_video", return_value=False)
    mocker.patch("main.get_headers", return_value=headers)

    result = check_link(link)
    assert result == "Can't download this type of link!"


def test_check_link_big_file(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4", "content-length": "500000000"}  # 500 MB
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.is_big", return_value=True)
    mocker.patch("main.get_headers", return_value=headers)

    result = check_link(link)
    assert result == "Can't download - video is too big!"


def test_check_link_regular_case(mocker):
    link = "https://example.com/some_video.mp4"
    headers = {"content-type": "video/mp4"}
    mocker.patch("main.is_downloadable_video", return_value=True)
    mocker.patch("main.is_big", return_value=False)
    mocker.patch("main.get_headers", return_value=headers)

    result = check_link(link)
    assert result is None


def test_image2photo():
    image_link = "https://example.com/image.jpg"
    caption = "This is a caption"
    result = image2photo(image_link, caption)
    expected_result = InputMediaPhoto(media=image_link, caption=caption)
    assert isinstance(result, InputMediaPhoto)
    assert result.media == expected_result.media
    assert result.caption == expected_result.caption


def test_image2photo_empty_caption():
    image_link = "https://example.com/image.jpg"
    result = image2photo(image_link)
    expected_result = InputMediaPhoto(media=image_link, caption="")
    assert isinstance(result, InputMediaPhoto)
    assert result.media == expected_result.media
    assert result.caption == expected_result.caption


def test_images2album_5_images():
    image_links = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
        "https://example.com/image3.jpg",
        "https://example.com/image4.jpg",
        "https://example.com/image5.jpg",
    ]
    link = "https://example.com/album"
    result = images2album(image_links, link)
    assert len(result) == 5


def test_images2album_2_images():
    image_links = [
        "https://example.com/image1.jpg",
        "https://example.com/image2.jpg",
    ]
    link = "https://example.com/album"
    result = images2album(image_links, link)
    assert len(result) == 2


def test_images2album_more_than_9_images():
    image_links = ["https://example.com/image{}.jpg".format(i) for i in range(1, 20)]
    link = "https://example.com/album"
    result = images2album(image_links, link)
    assert len(result) == 19


def test_images2album_no_images():
    image_links = []
    link = "https://example.com/album"
    expected_result = []
    result = images2album(image_links, link)
    assert result == expected_result
