from typing import Dict, List, Set, Tuple

import website_analyser.shared.webpage
import website_analyser.shared.website
from website_analyser.mixins.logger_mixin import LoggerMixin

Webpage = website_analyser.shared.webpage.Webpage
Website = website_analyser.shared.website.Website
PagesPath = Tuple[Webpage, ...]


class Paths(LoggerMixin):

    def __init__(self, website: Website) -> None:
        self.website = website
        self.webpages_shortest_paths: Dict[Webpage, Dict[Webpage, PagesPath]] = {
            page: {} for page in self.website.webpages
        }

    def find_all_shortest_paths(self) -> None:
        for from_webpage in self.website.webpages:
            self._find_shortest(from_webpage)

    def _find_shortest(self, from_page: Webpage) -> None:
        self.logger.debug(f"Finding all shortest paths from {from_page}")
        shortest_paths = self._get_shortest_paths(from_page)
        for path in shortest_paths:
            to_page = path[-1]
            self.webpages_shortest_paths[from_page][to_page] = path

    def _get_shortest_paths(self, from_page: Webpage) -> List[PagesPath]:
        visited: Set[Webpage] = set()
        shortest_paths: List[PagesPath] = []
        paths_to_process: List[PagesPath] = [(from_page,)]
        while paths_to_process:
            path = paths_to_process.pop(0)
            current_page: Webpage = path[-1]
            if current_page not in visited:
                visited.add(current_page)
                shortest_paths.append(path)
                paths_to_process.extend(
                    [path + (linked, ) for linked in current_page.linked_webpages if linked not in visited]  # noqa
                )
        return shortest_paths


def construct_shortest_paths(webpages: Set[Webpage]) -> Dict[Webpage, Dict[Webpage, List[Webpage]]]:
    """Unsatisfying execution time"""
    paths: Dict[Webpage, Dict[Webpage, List[Webpage]]] = {page: {} for page in webpages}
    paths.update({
        page: {linked: [page] if page != linked else []}
        for page in webpages
        for linked in page.linked_webpages
    })

    for mid_page in webpages:
        for from_page in webpages:
            for to_page in webpages:
                if len({mid_page, from_page, to_page}) < 3:
                    continue
                current_path = paths[from_page].get(to_page)
                from_mid_path = paths[from_page].get(mid_page)
                mid_to_path = paths[mid_page].get(to_page)
                if from_mid_path is None or mid_to_path is None:
                    continue
                new_path = from_mid_path + mid_to_path
                if current_path is None or len(current_path) > len(new_path):
                    paths[from_page][to_page] = from_mid_path + mid_to_path

    return paths


def get_longest_shortest_path(shortest_paths: Dict[Webpage, Dict[Webpage, List[Webpage]]]) -> List[Webpage]:
    """Obsolete due to runtime of function this depends on."""
    paths = [path for to_w in shortest_paths.values() for path in to_w.values()]
    return max(paths, key=lambda p: len(p))
