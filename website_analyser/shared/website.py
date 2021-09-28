import dataclasses
import json
from typing import List, Any, Dict, Set, Collection

import website_analyser.shared.url_utils
import website_analyser.shared.webpage

Webpage = website_analyser.shared.webpage.Webpage


@dataclasses.dataclass
class Website:
    webpages: Set[Webpage]
    url_to_webpage: Dict[str, Webpage] = dataclasses.field(default_factory=dict, init=False)

    @property
    def urls(self) -> Collection[str]:
        return self.url_to_webpage.keys()

    def __post_init__(self) -> None:
        self.url_to_webpage = {page.url.url: page for page in self.webpages}

    def __getitem__(self, url: str) -> Webpage:
        return self.url_to_webpage[url]

    def _to_json_compliant_objects(self) -> List[Dict[str, Any]]:
        pages: List[Dict[str, Any]] = []
        for page in self.webpages:
            pages.append(self.webpage_to_dict(page))
        return pages

    def to_json(self) -> str:
        return json.dumps(self._to_json_compliant_objects())

    def save(self, file_path: str) -> None:
        with open(file_path, "w") as f_h:
            f_h.write(self.to_json())

    @staticmethod
    def load(file_path: str) -> 'Website':
        with open(file_path, "r") as f_h:
            json_structure = json.loads(f_h.read())
        site_to_links: Dict[Webpage, Set[str]] = {}
        for page_json in json_structure:
            site = Webpage(
                url=website_analyser.shared.url_utils.Url(page_json["url_obj"]),
                is_in_website_space=page_json["is_in_website_space"],
                is_accepted_path=page_json["is_accepted_path"],
                is_from_domain=page_json["is_from_domain"],
                is_from_domain_space=page_json["is_from_domain_space"],
            )
            site.set_response_status_code(page_json["response_status_code"])
            site.set_response_content_length(page_json["response_content_length"])
            site_to_links[site] = set(page_json.get("linked_webpages", []))
        structure: Set[website_analyser.shared.webpage.Webpage] = set(site_to_links.keys())
        for site, links in site_to_links.items():
            site.linked_webpages.update({linked for linked in structure if linked.url.url in links})
        return Website(structure)

    @staticmethod
    def webpage_to_dict(webpage: Webpage) -> Dict[str, Any]:
        return {
            "url_obj": webpage.url.url,
            "is_from_domain_space": webpage.is_from_domain_space,
            "is_from_domain": webpage.is_from_domain,
            "is_in_website_space": webpage.is_in_website_space,
            "is_accepted_path": webpage.is_accepted_path,
            "response_status_code": webpage.response_status_code,
            "response_content_length": webpage.response_content_length,
            "linked_webpages": [page.url.url for page in webpage.linked_webpages],
        }
