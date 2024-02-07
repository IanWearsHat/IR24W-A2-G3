import re
from lxml import html
from bs4 import UnicodeDammit, BeautifulSoup
from urllib.parse import urlparse


def scraper(url, resp):
    links = extract_next_links(url, resp)
    valid_links = []
    save_all_valid_urls = open("urls.txt", "a")
    for link in links:
        if is_valid(link):
            save_all_valid_urls.write(link + "\n")
            valid_links.append(link)
    save_all_valid_urls.close()
    return valid_links


def load_stop_words(file_path):
    with open(file_path, 'r') as file:
        stop_words = set(file.read().strip().split('\n'))
    return stop_words


def get_no_stop_words(page_text: str):
    stop_words_file = "stopword.txt"
    stop_words = load_stop_words(stop_words_file)
    words = page_text.split()

    filtered_text = ' '.join([word for word in words if word.lower() not in stop_words])

    return filtered_text


def decode_html(html_string):
    """
    Uses Beautiful Soup to detect encoding.
    
    Returns Unicode string if successful

    Code taken from lxml docs at the website below:
    https://lxml.de/elementsoup.html#:~:text=(tag_soup)-,Using%20only%20the%20encoding%20detection,-Even%20if%20you
    """
    converted = UnicodeDammit(html_string)
    if not converted.unicode_markup:
        raise UnicodeDecodeError(
            "Failed to detect encoding, tried [%s]",
            ', '.join(converted.tried_encodings))

    return converted.unicode_markup


# TODO: see if "no data" means like one word or something
# ex. "http://sli.ics.uci.edu/Pubs/Pubs?action=download&upname=kdsd08.pdf"
# gives "Forbidden" which isn't really anything
def has_no_page_data(soup_text: str) -> bool:
    """
    Detect if there is any text content on the webpage.

    Handles "dead URLs that return a 200 status but no data"
    """
    return len(soup_text) == 0


def has_repeating_dir(url: str):
    parsed = urlparse(url)
    split_dirs = parsed.path.split("/")

    return len(set(split_dirs)) != len(split_dirs)


def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scraped from resp.raw_response.content

    # TODO: look at robots.txt for sites and see if it's even required to check robots.txt
    debug = True

    hyperlinks = []

    if (resp.status != 200):
        return list()

    soup = BeautifulSoup(resp.raw_response.content, "lxml")

    text = soup.get_text(separator=' ', strip=True)

    # TODO: maybe have all trap checks in one function
    if has_no_page_data(text):
        return list()
    
    # example use for get_no_stop_words
    # get_no_stop_words(text)

    a_tags = soup.findAll("a")
    for link in a_tags:
        content = link.get("href")
        if content:
            content = content.strip()
        else:
            continue
        # TODO: in the below if check, use is_valid
        if is_valid(url) and not has_repeating_dir(url):
            hyperlinks.append(content)

    return hyperlinks


def is_allowed_domain(netloc: str):
    if any(domain in netloc for domain in set([".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu"])):
        return True
    
    if any(domain == netloc for domain in set(["ics.uci.edu", "cs.uci.edu", "informatics.uci.edu", "stat.uci.edu"])):
        return True
    
    return False


def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)

        if parsed.scheme not in set(["http", "https"]):
            return False

        if not is_allowed_domain(parsed.netloc):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

        # TODO: see if you need to check for parsed.query bc of urls like
        # "http://sli.ics.uci.edu/Pubs/Pubs?action=download&upname=kdsd08.pdf"
    
        # TODO: .r files
        # "http://www.ics.uci.edu/~yamingy/bayesD_demo3.r"

    except TypeError:
        print ("TypeError for ", parsed)
        raise


if __name__ == '__main__':
    from utils.download import download
    from utils.config import Config
    from utils.server_registration import get_cache_server
    from configparser import ConfigParser

    cparser = ConfigParser()
    cparser.read("config.ini")
    config = Config(cparser)
    config.cache_server = get_cache_server(config, False)

    test_url = "http://sli.ics.uci.edu/Pubs/Pubs?action=download&upname=kdsd08.pdf"
    # test_url = "http://sli.ics.uci.edu/Classes/2015W-273a"
    print("Split url:", urlparse(test_url))
    print()
    print("Is valid URL:", is_valid(test_url))
    print()

    resp = download(test_url, config)
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    text = soup.get_text(separator=' ', strip=True)

    links = extract_next_links(test_url, resp)
    print(links)
    print()

    print("status is not 200?", resp.status != 200)
    print()
    print("text of page:", text)