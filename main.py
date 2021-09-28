import logging
from typing import Optional, Callable, Union, Dict

import fire

import website_analyser.analysing.explorer
import website_analyser.analysing.metrics
import website_analyser.analysing.paths
import website_analyser.parsing.extract.fair_extractor
import website_analyser.shared.url_utils
import website_analyser.shared.website


class AnalyseCLI:
    def __init__(self, get_website_method: Callable[[str], website_analyser.shared.website.Website]):
        self._get_website = get_website_method

    def metrics(self, path_or_url: str) -> str:
        website = self._get_website(path_or_url)
        paths = self._get_paths(website)
        metrics = website_analyser.analysing.metrics.MetricsReporter(website, paths)
        metrics.add_metrics()
        return metrics.report

    def dead_links(self, path_or_url: str) -> str:
        website = self._get_website(path_or_url)
        paths = self._get_paths(website)
        explorer = website_analyser.analysing.explorer.Explorer(website, paths)
        return explorer.report_dead_links()

    def most_linked(self, path_or_url: str, top: Optional[int] = 10, bot: Optional[int] = None) -> str:
        if bot is not None:
            top = None
        website = self._get_website(path_or_url)
        paths = self._get_paths(website)
        explorer = website_analyser.analysing.explorer.Explorer(website, paths)
        return explorer.report_most_linked(top, bot)

    @staticmethod
    def _get_paths(website: website_analyser.shared.website.Website) -> website_analyser.analysing.paths.Paths:
        paths = website_analyser.analysing.paths.Paths(website)
        paths.find_all_shortest_paths()
        return paths


class TextUI:
    MENU: str = """Allowed actions:
        1. Query for shortest path between two urls
        0. Exit
        """

    def __init__(self, website: website_analyser.shared.website.Website) -> None:
        self.website = website
        self.paths = website_analyser.analysing.paths.Paths(website)
        self.paths.find_all_shortest_paths()

    def run(self):
        while True:
            self.print_menu()
            user_response = self.prompt_user_response()
            self.handle_user_response(user_response)

    def print_menu(self) -> None:
        print(self.MENU)

    def prompt_user_response(self) -> int:
        while True:
            try:
                response = int(input("Specify action: "))
            except ValueError:
                print("Menu items are referenced by ints")
                continue
            if response in self.MENU_ITEM_TO_METHOD.keys():
                return response
            else:
                print(f"Invalid menu item {response}")

    def handle_user_response(self, response: int) -> None:
        self.MENU_ITEM_TO_METHOD[response](self)

    def exit_ui(self) -> None:
        exit()

    def query_shortest_path(self) -> None:
        url_from: str = website_analyser.shared.url_utils.create_clean_url(input("From URL: "))
        url_to: str = website_analyser.shared.url_utils.create_clean_url(input("To URL: "))
        if url_from not in self.website.urls:
            print(f"Didn't find {url_from} in website")
            return
        if url_to not in self.website.urls:
            print(f"Didn't find {url_from} in website")
            return
        website_from = self.website.url_to_webpage[url_from]
        website_to = self.website.url_to_webpage[url_to]
        shortest_path = self.paths.webpages_shortest_paths.get(website_from, {}).get(website_to)
        if shortest_path is None:
            print(f"No path found")
        print("\n".join([page.url.url for page in shortest_path]))

    MENU_ITEM_TO_METHOD: Dict[int, Callable[['TextUI'], None]] = {
        0: exit_ui,
        1: query_shortest_path,
    }


class RunCLI:

    def __init__(
            self,
            sub_domains: bool = False,
            only_sitemaps: bool = False,
            logging_level: Union[str, int] = "WARNING",
    ):
        self.sub_domains = sub_domains
        self.only_sitemaps = only_sitemaps
        self.analyse = AnalyseCLI(self._get_website)
        self._set_up_logging(logging_level)

    def parse_structure(self, url: str, output: Optional[str] = None) -> Optional[str]:
        website_structure = self._get_website_structure_from_url(url)
        if output is None:
            return website_structure.to_json()
        else:
            website_structure.save(output)

    def explore(self, path_or_url: str) -> None:
        """Simple text based UI"""
        TextUI(self._get_website(path_or_url)).run()

    def _get_website(self, path_or_url: str) -> website_analyser.shared.website.Website:
        if website_analyser.shared.url_utils.is_uri(path_or_url):
            return self._get_website_structure_from_url(path_or_url)
        return website_analyser.shared.website.Website.load(path_or_url)

    def _get_website_structure_from_url(self, url: str) -> website_analyser.shared.website.Website:
        extractor = website_analyser.parsing.extract.fair_extractor.FairExtractor(
            starting_url=url,
            propagate_to_sub_domains=self.sub_domains,
            restrict_only_to_sitemaps=self.only_sitemaps,
        )
        return extractor.extract_website_structure()

    @staticmethod
    def _set_up_logging(level: Union[str, int]) -> None:
        logging.basicConfig(format="{name:^15} |{asctime}| [{levelname:^10}]: {message}", style="{", level=level)


if __name__ == "__main__":
    fire.Fire(RunCLI)
