from typing import List, Optional

import bs4
import requests

import website_analyser.parsing.crawler
import website_analyser.parsing.extract.base
import website_analyser.shared.url_utils
import website_analyser.shared.webpage
import website_analyser.shared.website
from website_analyser.mixins.logger_mixin import LoggerMixin


class FairExtractor(LoggerMixin, website_analyser.parsing.extract.base.ExtractorBase):

    def __init__(
            self,
            starting_url: str,
            propagate_to_sub_domains: bool,
            restrict_only_to_sitemaps: bool,
    ) -> None:
        self.starting_url = website_analyser.shared.url_utils.Url(starting_url)
        self.propagate_to_sub_domains = propagate_to_sub_domains
        self.restrict_only_to_sitemaps = restrict_only_to_sitemaps
        self.robots_txt_url = f"{self.starting_url.url_base}/robots.txt"

    def extract_website_structure(self) -> website_analyser.shared.website.Website:
        robots_txt_content = self.get_robots_txt()
        self.logger.debug("Received robots.txt" if robots_txt_content is not None else "No robots.txt")
        crawler = self._get_crawler(robots_txt_content)
        webpages = crawler.get_webpages()
        if robots_txt_content is not None:
            site_map_webpages = {
                website_analyser.shared.webpage.Webpage(
                    website_analyser.shared.url_utils.Url(url), True, True, True, True,
                )
                for url in self.get_sitemaps_urls(robots_txt_content)
            }
            webpages.update(site_map_webpages)

        return website_analyser.shared.website.Website(webpages)

    def _get_crawler(self, robots_txt_content: Optional[str]) -> website_analyser.parsing.crawler.Crawler:
        allowed_pages = None
        disallowed_patterns = None
        if robots_txt_content is not None:
            if self.restrict_only_to_sitemaps:
                allowed_pages = self.get_sitemaps_urls(robots_txt_content)
                self.logger.debug(f"Found {len(allowed_pages)} sized sitemap space")
            disallowed_patterns = self.find_lines_values(robots_txt_content, "Disallow")
            self.logger.debug(f"Found {len(disallowed_patterns)} unreachable directories")
        return website_analyser.parsing.crawler.Crawler(
            starting_url=self.starting_url.url,
            propagate_crawl_to_sub_domains=self.propagate_to_sub_domains,
            disallowed_url_patterns=disallowed_patterns,
            crawl_only_pages=allowed_pages,
        )

    def get_robots_txt(self) -> Optional[str]:
        response = requests.get(self.robots_txt_url)
        if response.status_code == 200:
            return response.text
        return None

    def get_sitemaps_urls(self, robots_txt_content: str) -> List[str]:
        urls: List[str] = []
        site_maps = self.find_lines_values(robots_txt_content, "Sitemap")
        for s_map in site_maps:
            urls.extend(self.find_pages_in_sitemap(s_map))
        return urls

    @staticmethod
    def find_pages_in_sitemap(site_map_url: str) -> List[str]:
        response = requests.get(site_map_url)
        if response.status_code == 200:
            soup = bs4.BeautifulSoup(response.text, features="html.parser")
            return [website_analyser.shared.url_utils.create_clean_url(tag.text) for tag in soup.find_all(["loc"])]
        return []

    @staticmethod
    def find_lines_values(robots_txt_content: str, line_key: str) -> List[str]:
        line_key = line_key + ":"
        values: List[str] = []
        for line in robots_txt_content.split("\n"):
            if line.startswith(line_key):
                values.append(line.replace(line_key, "").strip())
        return values
