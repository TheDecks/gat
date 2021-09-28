import dataclasses
from typing import Optional, Set

import website_analyser.shared.url_utils


@dataclasses.dataclass
class Webpage:
    url: website_analyser.shared.url_utils.Url
    is_in_website_space: bool = dataclasses.field(compare=False, repr=False)
    is_accepted_path: bool = dataclasses.field(compare=False, repr=False)
    is_from_domain: bool = dataclasses.field(compare=False, repr=False)
    is_from_domain_space: bool = dataclasses.field(compare=False, repr=False)
    response_status_code: Optional[int] = dataclasses.field(default=None, compare=False, init=False, repr=False)
    response_content_length: Optional[int] = dataclasses.field(default=None, compare=False, init=False, repr=False)
    linked_webpages: Set['Webpage'] = dataclasses.field(default_factory=set, compare=False, init=False, repr=False)

    def __hash__(self) -> int:
        return hash(self.url)

    def set_response_status_code(self, code: Optional[int]) -> None:
        object.__setattr__(self, "response_status_code", code)

    def set_response_content_length(self, content_length: Optional[int]) -> None:
        object.__setattr__(self, "response_content_length", content_length)
