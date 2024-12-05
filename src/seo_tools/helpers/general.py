from . import globals
from urllib.parse import urlparse, urlunparse, urldefrag, urljoin

def cliPrint(input, introDash=True):

    if globals.args.quiet is False:
        if introDash is True:
            print("--",str(input))
        else:
            print(str(input))
      
def parse_url_string(url):
    parsed = urlparse(url)
    if parsed.path == '':
        parsed = parsed._replace(path='/')
    
    return urldefrag(urlunparse(parsed)).url
