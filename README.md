# gat - gather-analyse-tool

# Task

Provide a tool to create a map of a website. Provided the website structure, create a tool that allows its analysis.

# Setup

Install dependency packages via `pip install -r requirement.txt` in desired environment.

# Solution

To solve the task I relied only on python implementation. 

I decided that the best data structure to store information about website structure is directed graph, where webpages 
are nodes and links are edges (if a link to webpage A appears on webpage B, a directed edge B -> A is created). I could
have used an already existing solution to handling such a structure, i.e. by using `networkx`, but I decided to keep it 
in own dataclasses.

The solution consist of two parts:
 * `parsing`
 * `analysing`

## Parsing
This component is responsible for finding, building and saving website structure.
The heart of this part is `parsing/crawler` - the tool that is responsible for iteratively searching and extracting 
relevant information from webpages. Crawler is setup and ran by a `StructureExtractor` class, that provides crawling rules.
One implemented extractor is `FairExtractor` that reads `robot.txt` file and creates rules from that.

The results of parsing can be stored in `.json` format.

To run website structure parsing you can run the code through command line:
```bash
python main.py parse_structure https://www.globalapptesting.com
```

The parsing can be parametrised and following flags are accepted:
 * `--sub_domains` - by default crawling is restricted to domain only (`example.com`). Setting this parameter also crawls domains from the same domain space (`sub.example.com`, `sub2.example.com`)
 * `--only_sitemaps` - by default all reachable and allowed pages are crawled. Setting this parameter will only allow crawling on webpages provided in page sitemaps

```bash
python main.py parse_structure https://www.globalapptesting.com --sub_domains
```

By default, the output os passed to console. To dump the results to file, `--output` parameter is available:
```bash
python main.py parse_structure https://www.globalapptesting.com --output="globalapptesting.json"
```

## Analysing
The component is responsible for traversing the structure and providing answers to selected type of questions. There are
multiple subcomponents, with varying responsibility:
 * `metrics` - calculate aggregate measures for provided structure.
 * `explorer`- get interesting webpages and paths.
 * `paths` - store information about paths in structure.

These components are accessible through following command:

```bash
python main.py analyse [OPERATION] [path_or_url]
```

where `[OPERATION]` is one of:
 * `metrics` - get report of predefined metrics.
 * `dead_links` - get two column list of dead or invalid links in website. Columns: `page_url`, `link_url`.
 * `most_linked` - get two column list of most or least linked pages in website. Additional parameters can be specified:
   * `--top` - number of most linked pages to show. Default is `--top=10`.
   * `--bot` - number of least linked pages to show. Overrides `--top`.
 
and `[path_or_url]` is either a path to `.json` file with pre-parsed structure or a link to website to be parsed.

Example:

```bash
python main.py analyse most_linked globalapptesting.json --bot=20
```

Will show `20` least linked webpages in structure available in file `globalapptesting.json`.

## Additional features

### Explore
Running

```bash
python main.py explore [path_or_url]
```

will open a simple text-based UI that allows to query for shortest path.

### Logs verbosity

In any command, option `--logging_level` can be set to control the verbosity of logging. The levels are compliant with those from `logging` facility.

# Is the task solved?

I do think that for the most part, the task is solved. I see multiple places where things are not handled perfectly or some case if overlooked, but this
is mostly a draft of an extensible solution. Two points from the list are hard to answer due to implementation limitation:
 * `We would like to know if there are any dead (pointing to the non-existing pages) links on our site.` - currently only invalid links or internal dead links can be spotted - response status of external pages is not checked.
 * `Average size of the page in our website (HTML only!)` - size information is taken from `content-length` and this is not always available. Also no distinction between HTML and non-HTML content is made.

Both of the problems can be solved by changing a bit how the crawler works. Possibly:
 * `crawler` should make a `HEAD` request to a webpage and get relevant information from there;
 * `crawler` should make another `GET` request only in case given page should be crawled and content type is HTML.

Also following additional requirement is not met: `We would like to see graphical representation of the subpages of our website and their relations.`. This is due to lack of time, but normally, the procedure is following:
 * transform internal structure into `networkx` graph
 * use predefined nodes layout or implement rules for new layout creation
 * draw a graph using provided tools
 * customize nodes and edges look based on data available from crawling

# Insights
I am not fully satisfied with the solution, mostly due to the structure of code, overengineering, inconsistency in imports and insufficient or badly designed abstraction layer.
Some classes are also tightly coupled and their interface is not clear. Aaaand there are no tests or docstrings... I probably should have used already implemented
tools for most of the operations, like `scrapy` or `networkx`, but it was more fun this way.

# Further improvements
A looooooooooot. More abstraction to crawler (and in general - improve and make it more readable), clearer code, handling domain switch mid-crawl to follow right `robots.txt`, more metrics, extend `explore`...