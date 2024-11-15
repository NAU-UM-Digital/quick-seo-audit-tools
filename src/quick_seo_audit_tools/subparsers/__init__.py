## REGISTER SUBPARSERS HERE ##
# import subparsers and add to array to make available to argparse
# ensure that each subparser has an add() function that takes the parser as an argument

from . import links_status
from . import custom_request_headers
from . import sitemap_content_scrape

all_subparsers_array = [
    links_status,
    sitemap_content_scrape,
    custom_request_headers,
]