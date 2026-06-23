import pytest
import requests
from unittest.mock import patch, MagicMock
from modules.fetch_web import (
    fetch_url_text, read_uploaded_file,
    FetchConnectionError, FetchHTTPError,
    FetchTimeoutError, FetchContentTypeError, FetchEncodingError
)


def test_read_uploaded_file_utf8():
    content = "人工智能测试".encode("utf-8")
    text, encoding = read_uploaded_file(content, "test.txt")
    assert text == "人工智能测试"
    assert encoding == "utf-8"


def test_read_uploaded_file_gbk():
    content = "人工智能测试".encode("gbk")
    text, encoding = read_uploaded_file(content, "test.txt")
    assert text == "人工智能测试"
    assert encoding == "gbk"


def test_read_uploaded_file_fallback():
    content = "人工智能测试".encode("gbk")
    text, encoding = read_uploaded_file(content, "test.txt")
    assert text == "人工智能测试"


def test_read_uploaded_file_fail():
    content = b"\xff\xfe\xfd"
    with pytest.raises(ValueError):
        read_uploaded_file(content, "test.bin")


@patch("modules.fetch_web.requests.get")
def test_fetch_url_text_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
    mock_response.apparent_encoding = "utf-8"
    mock_response.text = "<html><body>人工智能测试</body></html>"
    mock_get.return_value = mock_response
    
    text = fetch_url_text("https://example.com")
    assert "人工智能测试" in text


@patch("modules.fetch_web.requests.get")
def test_fetch_url_text_connection_error(mock_get):
    mock_get.side_effect = requests.ConnectionError("Connection refused")
    
    with pytest.raises(FetchConnectionError):
        fetch_url_text("https://example.com")


@patch("modules.fetch_web.requests.get")
def test_fetch_url_text_http_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    
    with pytest.raises(FetchHTTPError) as exc_info:
        fetch_url_text("https://example.com")
    assert exc_info.value.status_code == 404


@patch("modules.fetch_web.requests.get")
def test_fetch_url_text_timeout(mock_get):
    mock_get.side_effect = requests.Timeout("Timeout")
    
    with pytest.raises(FetchTimeoutError):
        fetch_url_text("https://example.com", timeout=1)


@patch("modules.fetch_web.requests.get")
def test_fetch_url_text_content_type_error(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/pdf"}
    mock_get.return_value = mock_response
    
    with pytest.raises(FetchContentTypeError):
        fetch_url_text("https://example.com")