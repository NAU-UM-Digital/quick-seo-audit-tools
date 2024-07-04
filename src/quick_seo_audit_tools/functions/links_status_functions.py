import requests
from bs4 import BeautifulSoup
from lxml import etree
import urllib3
from urllib.parse import urlparse, urldefrag, urljoin
import quick_seo_audit_tools.functions.database as db
import ssl

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


def handle_url(url, contains=False):

    print(f'handling URL: {url}')
    with get_legacy_session().get(url, stream=True, timeout=5) as r:

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

        print(f'status code: {r.status_code}')
        if 'text/xml' in r.headers.get('Content-Type')  and 'sitemap' in r.url and r.status_code == 200:
            print(f'attempting to parse sitemap: {r.url}')
            return parse_sitemap(r)
        elif 'text/html' in r.headers.get('Content-Type') and r.status_code == 200:
            if ( contains is not False and contains not in r.url):
                return []
            else:
                return parse_html(r)
        elif r.status_code != 200:
            return handle_error(f'status code: {r.status_code}') #COME BACK TO THIS WE STILL NEED TO HANDLE ERRORS
        else:
            return [] 

def parse_sitemap(request): 
    sitemap_queue = []

    print(request.text)
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

def parse_html(request, self_link=False):
    links_queue = []
    
    soup = BeautifulSoup(request.text, 'html.parser')
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
    return links_queue

def handle_error(error):
    print(error)
    return []
    