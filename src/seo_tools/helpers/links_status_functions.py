import requests
from bs4 import BeautifulSoup
from lxml import etree
import urllib3
from urllib.parse import urlparse, urldefrag, urljoin
from . import database as db
import ssl
from .general import *

# custom adapter to allow legacy SSL renegotiation—does make crawl vulnerable to man-in-the-middle attacks
class CustomHttpAdapter (requests.adapters.HTTPAdapter):
    # "Transport adapter" that allows us to use custom ssl_context.

    def __init__(self, ssl_context=None, **kwargs):
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=connections, maxsize=maxsize,
            block=block, ssl_context=self.ssl_context)

def get_legacy_session():
    ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
    ctx.options |= 0x4  # OP_LEGACY_SERVER_CONNECT
    session = requests.session()
    session.mount('https://', CustomHttpAdapter(ctx))
    return session


def handle_url(url, contains=False, self_link=False):

    print(f'handling URL: {url}')
    try:
        r = get_legacy_session().get(url, stream=True, timeout=5)
    except:
        db.add_request_to_db( 
            request_url = url,
            resolved_url = url,
            status_code = 'ERROR',
            initial_status_code = 'ERROR',
            no_of_redirects = 'N/A',
            content_type_header = 'N/A'
        )
        db.add_url_to_page_db(
            resolved_url=url
        )
        print(f'\n\n\n\nERROR\n\n')
        return []
    else:
        with r:

            if len(r.history) > 0:
                initial_status_code = r.history[0].status_code
            else:
                initial_status_code = r.status_code
            db.add_request_to_db( 
                request_url = url,
                resolved_url = r.url,
                status_code = r.status_code,
                initial_status_code = initial_status_code,
                no_of_redirects = len(r.history),
                content_type_header = r.headers.get('Content-Type')
            )

            #if redirected, pass URL back to queue to avoid duplicating links
            if len(r.history) > 0:
                return [r.url]

            cliPrint(f'status code: {r.status_code}')
            if r.headers.get('Content-Type') and 'xml' in r.headers.get('Content-Type')  and 'sitemap' in r.url and r.status_code == 200:
                print(f'attempting to parse sitemap: {r.url}')
                return parse_sitemap(r)
            elif r.headers.get('Content-Type') and 'html' in r.headers.get('Content-Type') and r.status_code == 200:
                if ( contains is not False and contains not in r.url):
                    return []
                else:
                    return parse_html(r, self_link=self_link)
            elif r.status_code != 200:
                return handle_error(f'status code: {r.status_code}') #TODO: COME BACK TO THIS WE STILL NEED TO HANDLE ERRORS
            else:
                return [] 

def parse_sitemap(request): 
    sitemap_queue = []

    cliPrint(request.text)
    sitemapSoup = BeautifulSoup(request.text, 'xml') 
    locsSoup = sitemapSoup.find_all('loc')
    for loc in locsSoup:
        url = loc.text
        urlParsed = urlparse(url) 
        if (urlParsed.scheme == 'http' or urlParsed.scheme == 'https'):
            urlDefragd = urldefrag(url).url
            if request.url != urlDefragd:
                #db.add_link_to_db(request.url, urlDefragd, 'N/A')
                sitemap_queue.append(urlDefragd)

    return sitemap_queue

def return_title(soup):
    try:
        title = soup.find('title').text
    except:
        title = None
    return title

def return_meta_description(soup):
    try:
        descr = soup.find('meta', {'name': 'description'})['content']
    except:
        descr = None
    return descr

def return_meta_robots(soup):
    meta_robots = soup.find_all('meta', {'name': 'robots'})
    content = [i.get('content') for i in meta_robots]
    return ','.join(content)

def return_canonical_url(soup):
    try:
        canonical = soup.find('link', {'rel': 'canonical'})['href']
    except:
        canonical = None
    return canonical

def return_header(soup, heading_level):
    try:
        heading = soup.find(heading_level).text
    except:
        heading = None
    return heading

def safe_len(list):
    try:
        return len(list)
    except:
        return 0

def parse_html(request, self_link=False):
    links_queue = []
    
    soup = BeautifulSoup(request.text, 'html.parser')

    db.add_url_to_page_db(
        resolved_url=request.url, 
        declared_canonical_url=return_canonical_url(soup), 
        page_title=return_title(soup), 
        page_title_len=safe_len(return_title(soup)), 
        meta_description=return_meta_description(soup), 
        meta_description_len=safe_len(return_meta_description(soup)), 
        meta_robots=return_meta_robots(soup), 
        robots_header=request.headers.get('X-Robots-Tag'), 
        heading1=return_header(soup, 'h1'), 
        heading2=return_header(soup, 'h2')
        )


    links_soup = soup.find_all('a')
    for link in links_soup:
        if link.has_attr('href'):
            href = link['href']
            url = urljoin(request.url, href)
            urlParsed = urlparse(url)
            if (urlParsed.scheme == 'http' or urlParsed.scheme == 'https'):
                urlDefragd = urldefrag(url).url
                if request.url != urlDefragd or self_link is True:
                    db.add_link_to_db(request.url, urlDefragd, link.text.strip())
                    links_queue.append(urlDefragd)
    if return_canonical_url(soup) is not None:
        links_queue.append(return_canonical_url(soup))
    return links_queue

def handle_error(error):
    #TODO: Determine how best to handle errors when crawling. Some errors are expected, some are not. But I also don't expect the average user would be able to predict while parsing the output.
    print(error)
    return []
    