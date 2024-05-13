import pytest
from crawler import Crawler
from requests.exceptions import RequestException

INVALID_URL = "invalid-url"
VALID_URL = "http://example.com"
VALID_DOMAIN = "example.com"


def test_init_invalid_url():
    with pytest.raises(ValueError):
        Crawler(base_url=INVALID_URL)


def test_init_valid_url(mocker):
    mocker.patch('os.path.exists', return_value=False)
    mocker.patch('os.mkdir')
    crawler = Crawler(base_url=VALID_URL)
    assert crawler.base_url == VALID_URL
    assert crawler.output_folder == VALID_DOMAIN


def test_fetch_success(mocker):
    mock_get = mocker.patch('requests.get')
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.text = 'OK'
    mock_response.raise_for_status = mocker.MagicMock()
    mock_get.return_value = mock_response

    crawler = Crawler(base_url=VALID_URL)
    response = crawler.fetch(VALID_URL)
    assert response == 'OK'


def test_fetch_fail(mocker):
    mocker.patch('requests.get', side_effect=RequestException("Failed"))
    mocker.patch('time.sleep', return_value=None)  # To speed up the retry delay
    crawler = Crawler(base_url=VALID_URL)
    response = crawler.fetch(VALID_URL)
    assert response is None


def test_worker_invalid_url(mocker):
    mocker.patch('crawler.validators.url', return_value=False)

    with pytest.raises(ValueError) as e:
        Crawler(base_url=INVALID_URL)
    assert str(e.value) == "Invalid base URL"


def test_worker_valid_url(mocker):
    test_url = f"{VALID_URL}/page"
    new_page_url = f"{VALID_URL}/new_page"
    html_content = f"<html><head></head><body><a href='{new_page_url}'>Link</a></body></html>"

    mock_fetch = mocker.patch('crawler.Crawler.fetch', return_value=html_content)
    mock_save_page = mocker.patch('crawler.Crawler.save_page')
    mock_put = mocker.patch('queue.Queue.put')
    mocker.patch('w3lib.url.canonicalize_url', side_effect=lambda x: x)  # Simplifying the URL canonicalization

    crawler = Crawler(base_url=VALID_URL)
    crawler.worker(test_url)

    mock_fetch.assert_called_once_with(test_url)
    mock_save_page.assert_called_once_with(html_content, test_url)
    mock_put.assert_called_with(new_page_url)
