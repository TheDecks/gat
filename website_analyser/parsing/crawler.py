import dataclasses
import re
import urllib.parse
from typing import List, Iterable, Optional, Collection, Set, Tuple

import bs4
import requests
import urllib3.exceptions

import website_analyser.shared.url_utils
import website_analyser.shared.webpage
from website_analyser.mixins.logger_mixin import LoggerMixin

Url = website_analyser.shared.url_utils.Url
Webpage = website_analyser.shared.webpage.Webpage


@dataclasses.dataclass
class CrawlingTask:
    parent_webpage: Optional[Webpage]
    current_webpage: Webpage


class Crawler(LoggerMixin):

    def __init__(
            self,
            starting_url: str,
            propagate_crawl_to_sub_domains: bool = False,
            disallowed_url_patterns: Optional[Iterable[str]] = None,
            crawl_only_pages: Optional[Collection[str]] = None,
    ) -> None:
        self.starting_url: Url = Url(starting_url)
        self.propagate_to_sub_domains = propagate_crawl_to_sub_domains
        self.crawl_only_pages = crawl_only_pages
        self.resource_path_exclude_pattern: Optional[re.Pattern] = self._create_exclude_pattern(disallowed_url_patterns)

    @staticmethod
    def _create_exclude_pattern(exclusion_patterns: Optional[Iterable[str]]) -> Optional[re.Pattern]:
        if exclusion_patterns is not None and exclusion_patterns:
            return re.compile("|".join(re.escape(pat) for pat in exclusion_patterns))
        return None

    @property
    def is_excluding_paths(self) -> bool:
        return self.resource_path_exclude_pattern is not None

    @property
    def is_restricting_search(self) -> bool:
        return bool(self.crawl_only_pages)

    def get_webpages(self) -> Set[Webpage]:
        starting_webpage = self._create_webpage(self.starting_url.url)
        webpages: Set[Webpage] = {starting_webpage}
        crawl_tasks: List[Webpage] = [starting_webpage]
        while crawl_tasks:
            webpage = crawl_tasks.pop(0)
            if self.should_crawl(webpage):
                self.logger.info(f"Crawling {webpage}")
                content, status, size = self._get_content_status_size(webpage)
                webpage.set_response_status_code(status)
                webpage.set_response_content_length(size)
                if content:
                    linked_webpages = self._extract_linked_webpages(content, webpage)
                    already_exists = linked_webpages & webpages
                    to_add = linked_webpages - already_exists
                    webpage.linked_webpages.update(already_exists | to_add)
                    webpages.update(to_add)
                    crawl_tasks.extend(to_add)
        return webpages

    def _create_webpage(self, url: str, parent_webpage: Optional[Webpage] = None) -> Webpage:
        parent_url_base = parent_webpage.url.url_base if parent_webpage else None
        parent_url_resource = parent_webpage.url.resource_path if parent_webpage else None
        url_obj = Url(website_analyser.shared.url_utils.create_clean_url(url, parent_url_base, parent_url_resource))
        if (
                self.is_excluding_paths
                and url_obj.resource_path is not None
                and self.resource_path_exclude_pattern.search(url_obj.resource_path)  # noqa
        ):
            is_url_accepted = False
        else:
            is_url_accepted = True
        webpage = Webpage(
            url=url_obj,
            is_in_website_space=url_obj.url in self.crawl_only_pages if self.is_restricting_search else True,
            is_from_domain=url_obj.domain == self.starting_url.domain,
            is_from_domain_space=url_obj.shares_domain_space(self.starting_url),
            is_accepted_path=is_url_accepted,
        )
        self.logger.debug(f"Created {webpage}")
        return webpage

    # TODO: sub-domains can have a different excluding pattern for urls...
    def should_crawl(self, webpage: Webpage) -> bool:
        if webpage.is_in_website_space and webpage.is_accepted_path:
            if webpage.is_from_domain:
                return True
            elif webpage.is_from_domain_space and self.propagate_to_sub_domains:
                return True
        return False

    def _extract_linked_webpages(self, content: str, from_webpage: Webpage) -> Set[Webpage]:
        links = Crawler._extract_raw_links(content)
        links = Crawler._filter_links(links)
        self.logger.debug(f"Gathered {len(links)} for {from_webpage}")
        return {self._create_webpage(link, from_webpage) for link in links}

    @staticmethod
    def _get_content_status_size(webpage: Webpage) -> Tuple[Optional[str], int, Optional[int]]:
        content: Optional[str] = None
        status: int = 404  # TODO: Find a more reliable way of marking failure to parse url_obj
        size: Optional[int] = None
        try:
            response = requests.get(webpage.url.url)
            # TODO: This is `hacky` way. This function should be thoroughly rewritten and logic split to concerns
            if "html" in response.headers.get("content-type", "html").lower():
                if response.status_code == 200:
                    content = response.text
                status = response.status_code
                size = response.headers.get("content-length")
                size = int(size) if size else None
        except urllib3.exceptions.LocationParseError:
            pass
        return content, status, size

    @staticmethod
    def _extract_raw_links(content: str) -> List[str]:
        soup = bs4.BeautifulSoup(content, features="html.parser")
        return [link_tag["href"] for link_tag in soup.find_all("a", href=True)]

    # TODO: Possibly add more rules
    @staticmethod
    def _filter_links(links: List[str]) -> List[str]:
        return [link for link in links if link == urllib.parse.quote(link, safe="/:")]
