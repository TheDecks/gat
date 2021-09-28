from typing import Collection, Dict, List, Optional

import website_analyser.analysing.paths
import website_analyser.shared.webpage
import website_analyser.shared.website

Webpage = website_analyser.shared.webpage.Webpage
Website = website_analyser.shared.website.Website
Paths = website_analyser.analysing.paths.Paths
PagesPath = website_analyser.analysing.paths.PagesPath


class Explorer:

    def __init__(self, website: Website, paths: Paths):
        self.website = website
        self.paths = paths

    def report_dead_links(self) -> str:
        dead_links = {
            page.url.url: linked.url.url
            for page, linked_pages in self._find_dead_links().items()
            for linked in linked_pages
        }
        linked_in_max_url = max([len(url) for url in dead_links.keys()]) + 4
        single_line_template = f"{{url:<{linked_in_max_url}}}\t{{linked_url}}"
        return "\n".join(
            [single_line_template.format(url=url, linked_url=linked_url) for url, linked_url in dead_links.items()]
        )

    def report_most_linked(self, top: Optional[int] = None, bot: Optional[int] = None) -> str:
        times_linked = self._get_times_linked_count()
        if top:
            no = top
            reverse = True
        elif bot:
            no = bot
            reverse = False
        else:
            raise
        relevant_webpages = sorted(times_linked, key=lambda x: times_linked[x], reverse=reverse)[:no]
        url_field_len = max([len(page.url.url) for page in relevant_webpages]) + 4
        single_line_template = f"{{url:<{url_field_len}}}\t{{times_linked}}"
        return "\n".join([
            single_line_template.format(url=page.url.url, times_linked=times_linked[page]) for page in relevant_webpages
        ])

    def _find_dead_links(self) -> Dict[Webpage, List[Webpage]]:
        dead_webpages = {
            page for page in self.website.webpages
            if page.response_status_code is not None and page.response_status_code != 200
        }
        return {page: page.linked_webpages.intersection(dead_webpages) for page in self.website.webpages}

    def _get_times_linked_count(self, only_domain: bool = True) -> Dict[Webpage, int]:
        if only_domain:
            pages = {page for page in self.website.webpages if page.is_from_domain}
        else:
            pages = self.website.webpages
        counts: Dict[Webpage, int] = {page: 0 for page in pages}
        for page in pages:
            for linked in page.linked_webpages:
                if linked in pages:
                    counts[linked] += 1
        return counts
