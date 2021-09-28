from typing import Collection, Dict, Any

import website_analyser.analysing.paths
import website_analyser.shared.webpage
import website_analyser.shared.website
from website_analyser.mixins.logger_mixin import LoggerMixin

Webpage = website_analyser.shared.webpage.Webpage
Website = website_analyser.shared.website.Website
Paths = website_analyser.analysing.paths.Paths
PagesPath = website_analyser.analysing.paths.PagesPath


class MetricsReporter(LoggerMixin):

    def __init__(self, website: Website, paths: Paths) -> None:
        self.website = website
        self.paths = paths
        self.metrics: Dict[str, Any] = {}

    @property
    def report(self) -> str:
        metric_name_len = max([len(name) for name in self.metrics.keys()]) + 4
        single_metric_template = f"{{metric:<{metric_name_len}}}\t{{value}}"
        return "\n".join(
            [single_metric_template.format(metric=metric, value=value) for metric, value in self.metrics.items()]
        )

    def add_metrics(self) -> None:
        self._add_path_metrics()
        self._add_links_metrics()
        self._add_size_metrics()

    def _add_path_metrics(self) -> None:
        longest_domain_path = self.get_longest_path({page for page in self.website.webpages if page.is_from_domain})
        longest_dom_space_path = self.get_longest_path(
            {page for page in self.website.webpages if page.is_from_domain_space}
        )
        self._add_metric("longest_domain_path", f"{longest_domain_path[0].url} -> -.. -> {longest_domain_path[-1].url}")
        self._add_metric("longest_domain_path_length", len(longest_domain_path))
        self._add_metric(
            "longest_domain_space_path",
            f"{longest_dom_space_path[0].url} -> ... -> {longest_dom_space_path[-1].url}",
        )
        self._add_metric("longest_domain_space_path_length", len(longest_dom_space_path))

    def _add_links_metrics(self) -> None:
        links_to_domain = self.get_links_count({page for page in self.website.webpages if page.is_from_domain})
        links_to_dom_space = self.get_links_count({page for page in self.website.webpages if page.is_from_domain_space})
        links_to_external = self.get_links_count(
            {page for page in self.website.webpages if not page.is_from_domain and not page.is_from_domain_space}
        )

        self._add_metric("average_internal_links", sum(links_to_domain.values())/len(links_to_domain))
        self._add_metric("average_sub_domains_links", sum(links_to_dom_space.values()) / len(links_to_dom_space))
        self._add_metric("average_external_links", sum(links_to_external.values()) / len(links_to_external))

    def _add_size_metrics(self) -> None:
        sizes = [
            page.response_content_length
            for page in self.website.webpages
            if page.response_content_length is not None
        ]
        self._add_metric("average_size", sum(sizes) / len(self.website.webpages))

    def _add_metric(self, metric_name: str, metric_value: Any) -> None:
        self.logger.debug(f"Adding metric: {metric_name}")
        self.metrics[metric_name] = metric_value

    def get_longest_path(self, accept_webpages: Collection[Webpage]) -> PagesPath:
        paths_flat = [
            path
            for from_web, to_web_paths in self.paths.webpages_shortest_paths.items()
            for to_web, path in to_web_paths.items()
            if from_web in accept_webpages and to_web in accept_webpages
        ]
        return max(paths_flat, key=lambda x: len(x))

    def get_links_count(self, accept_coming_into: Collection[Webpage]) -> Dict[Webpage, int]:
        webpage_to_links_no: Dict[Webpage, int] = {}
        for page in self.website.webpages:
            webpage_to_links_no[page] = len(page.linked_webpages.intersection(accept_coming_into))
        return webpage_to_links_no
