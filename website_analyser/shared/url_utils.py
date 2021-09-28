import urllib.parse
from typing import Optional, Tuple

import tld


class Url:

    def __init__(self, url: str) -> None:
        self.tld_suffix: Optional[str]
        self.tld: Optional[str]
        self.tld_prefix: Optional[str]
        self.domain: Optional[str]
        self.protocol_prefix: Optional[str]
        self.resource_path: Optional[str]

        self.url = url
        self.tld_suffix, self.tld, self.tld_prefix = tld.parse_tld(url)
        if self.tld and self.tld_suffix:
            self.domain = ".".join(map(str, filter(lambda x: bool(x), [self.tld_prefix, self.tld, self.tld_suffix])))
            self.protocol_prefix, resource_path = self.url.split(self.domain, maxsplit=1)
            self.resource_path = resource_path.rstrip("/") or None
        else:
            self.domain = None
            self.protocol_prefix = None
            self.resource_path = None

    @property
    def url_base(self) -> Optional[str]:
        if self.domain is not None:
            return f"{self.protocol_prefix}{self.domain}"
        return None

    def shares_domain_space(self, other: 'Url'):
        return self.tld == other.tld and self.tld_suffix == other.tld_suffix

    def __hash__(self) -> int:
        return hash(self.url)

    def __eq__(self, other) -> bool:
        return bool(self.url == other.url)

    def __str__(self) -> str:
        return self.url

    __repr__ = __str__


def is_uri(url: str, check_attributes: Tuple[str, ...] = ("scheme", "netloc")):
    _parse_url = urllib.parse.urlparse(url)
    return all(map(bool, (getattr(_parse_url, attr_name) for attr_name in check_attributes)))


def create_url_from_path(base_url: str, resource_path: str, base_url_extension: Optional[str] = None) -> str:
    if resource_path.startswith("./"):
        resource_path = resource_path[2:]
    if resource_path.startswith("/") or base_url_extension is None:
        elements = [base_url, resource_path]
    else:
        elements = [base_url, base_url_extension, "/", resource_path]
    return "".join(elements)


def create_clean_url(url: str, parent_url_base: Optional[str] = None, parent_url_resource: Optional[str] = None) -> str:
    # url_obj is actually a path
    if not is_uri(url) and parent_url_base is not None:
        return create_url_from_path(parent_url_base, url, parent_url_resource)
    return url.strip("/")
