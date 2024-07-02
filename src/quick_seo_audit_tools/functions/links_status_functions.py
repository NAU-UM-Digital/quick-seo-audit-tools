import requests
from bs4 import BeautifulSoup
from lxml import etree
from urllib.parse import urlparse, urldefrag
import quick_seo_audit_tools.functions.database as db

def handle_url(url, contains=False):

    print(f'handling URL: {url}')
    with requests.get(url, stream=True, timeout=5) as r:

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
            db.add_link_to_db(request.url, urlDefragd, 'N/A')
            sitemap_queue.append(urlDefragd)

    return sitemap_queue

def parse_html(request):
    links_queue = []
    
    soup = BeautifulSoup(request.text, 'html.parser')
    links_soup = soup.find_all('a')
    for link in links_soup:
        if link.has_attr('href'):
            url = link['href']
            urlParsed = urlparse(url)
            if (urlParsed.scheme == 'http' or urlParsed.scheme == 'https'):
                urlDefragd = urldefrag(url).url
                db.add_link_to_db(request.url, urlDefragd, link.text.strip())
                links_queue.append(urlDefragd)
    return links_queue

def handle_error(error):
    print(error)
    return []
    