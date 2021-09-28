import abc
import website_analyser.shared.website


class ExtractorBase:

    @abc.abstractmethod
    def extract_website_structure(self) -> website_analyser.shared.website.Website: ...
