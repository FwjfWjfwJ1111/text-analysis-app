import requests
from bs4 import BeautifulSoup
from typing import Tuple, Optional


class FetchError(Exception):
    user_message = "获取文本失败"


class FetchConnectionError(FetchError):
    user_message = "无法连接到服务器，请检查 URL 是否正确"


class FetchHTTPError(FetchError):
    def __init__(self, status_code: int):
        super().__init__(f"HTTP error {status_code}")
        self.status_code = status_code
        self.user_message = f"服务器返回错误（{status_code}），请检查链接是否有效"


class FetchTimeoutError(FetchError):
    user_message = "请求超时，请检查网络或稍后重试"


class FetchContentTypeError(FetchError):
    user_message = "该链接不是可解析的网页文本"


class FetchEncodingError(FetchError):
    user_message = "无法解码网页内容，请尝试其他链接"


def fetch_url_text(url: str, timeout: int = 10) -> str:
    """
    从 URL 抓取网页文本内容。

    Args:
        url: 目标网页 URL
        timeout: 请求超时时间（秒）

    Returns:
        提取的纯文本字符串

    Raises:
        FetchConnectionError: 网络连接失败
        FetchHTTPError: HTTP 状态码错误（4xx/5xx）
        FetchTimeoutError: 请求超时
        FetchContentTypeError: 返回内容非 HTML 文本
        FetchEncodingError: 编码解码失败
    """
    try:
        response = requests.get(url, timeout=timeout)
        
        if response.status_code >= 400:
            raise FetchHTTPError(response.status_code)
        
        content_type = response.headers.get("Content-Type", "")
        if not ("text/html" in content_type or "text/plain" in content_type):
            raise FetchContentTypeError()
        
        response.encoding = response.apparent_encoding
        soup = BeautifulSoup(response.text, "html.parser")
        raw_text = soup.get_text()
        
        if not raw_text.strip():
            raise FetchEncodingError()
        
        return raw_text
    
    except requests.ConnectionError:
        raise FetchConnectionError()
    except requests.Timeout:
        raise FetchTimeoutError()
    except FetchError:
        raise
    except Exception as e:
        raise FetchEncodingError() from e


def read_uploaded_file(raw_bytes: bytes, filename: str) -> Tuple[str, str]:
    """
    检测文件编码并读取内容。优先 UTF-8，失败回退 GBK。

    Args:
        raw_bytes: 文件原始字节数据
        filename: 文件名

    Returns:
        (text_content, encoding_used)

    Raises:
        ValueError: 两种编码均无法解码
    """
    for encoding in ("utf-8", "gbk"):
        try:
            return raw_bytes.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise ValueError(f"无法以 UTF-8 或 GBK 解码文件: {filename}")