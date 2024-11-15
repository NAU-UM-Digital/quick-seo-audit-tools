import argparse
#import pkgutil
import requests
from bs4 import BeautifulSoup
import csv
import re
import lxml
from urllib.parse import urljoin, urlsplit, urlunsplit
import os
import json
import pandoc
from .helpers import globals

## REGISTER SUBPARSERS ##
# import subparsers and add to array to make available to argparse
# ensure that the subparser has an add() function that takes the parser as an argument

from .subparsers import links_status
from .subparsers import custom_request_headers
from .subparsers import sitemap_content_scrape
all_subparsers_array = [
    links_status,
    sitemap_content_scrape,
    custom_request_headers,
]

## END OF SUBPARSER REGISTRATION ##

# Initialize the argument parser
def init_args():
    global all_subparsers_array

    parser = argparse.ArgumentParser(
        "seo-tools"
    )

    # Add global arguments to the parser
    general = parser.add_argument_group("global flags")
    general.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="suppress response text"
    )
    general.add_argument(
        "--debug",
        action="store_true",
        help="show errors on failure"
    )

    # Add subparsers imported and registered above in array
    subparsers = parser.add_subparsers(
        title="cli tools for SEO auditing"
    )
    for new_subparser in all_subparsers_array:
        new_subparser.add(subparsers)
        

    args = parser.parse_args()
    globals.args = args
    return args



def main_cli():
    global args
    args = init_args()

    if args.debug is True:
        args.func(args)
    else:
        try:
            args.func(args)
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise

if __name__ == '__main__':
    main_cli()