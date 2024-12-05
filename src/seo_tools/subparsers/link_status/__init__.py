import requests
from bs4 import BeautifulSoup
import csv
import re
import lxml
from urllib.parse import urljoin, urlsplit, urlunsplit
import os
import json
import pandoc
from datetime import datetime
from ...helpers import links_status_functions as lsf
from ...helpers import database as db
from ...helpers.general import cliPrint, parse_url_string

# add subparser for import to __main__
def add(subparsers):
    command_string = "links-status"
    feature_status = "REFACTORING IN PROGRESS"
    description = "process on-page hyperlinks for response status"
    
    new_subparser = subparsers.add_parser(command_string, help=f"[{feature_status}] {description}")
    new_subparser.add_argument(
        "--seed-url",
        action="store",
        metavar="URL",
        help="destination URL: can be HTML or XML that includes links to other URLs",
        default=False
    )
    new_subparser.add_argument(
        "--output",
        action="store",
        metavar="FOLDER",
        help="relative filepath to contain reports",
        default=False
    )
    new_subparser.add_argument(
        "--contains",
        action="store",
        metavar="STRING",
        help="only URLs matching string will be checked for new links",
        default=False
    )
    new_subparser.set_defaults(func=parseArgsGetLinksStatus)

    return new_subparser

# parser's function can take args
def parseArgsGetLinksStatus(args):
    for i in [('seed URL', args.seed_url), ('output folder', args.output), ('contains string', args.contains)]:
        if i[1] is False:
            exit(f"ERROR: {i[0]} not provided. Please ask for --help")
    getLinksStatus(args.seed_url, args.output, args.contains)

# main function
def getLinksStatus(seed_url,output_folder,contains_string):

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    db_path = f'{output_folder}/{datetime.today().strftime("%Y-%m-%d")}_crawl-database.db'
    if os.path.exists(db_path):
        os.remove(db_path)
    db.init_output_db(db_path)

    queue = []
    link_log = []

    if seed_url is not False:
        print("beginning crawl from seed url...")
        # add seed URL to queue
        queue.append(parse_url_string(seed_url))
        cliPrint(f'appended {seed_url} to queue...')

        iter = 0
        while iter < len(queue):
            print(f'handling found URL {iter}/{len(queue)}')
            links = lsf.handle_url(queue[iter], contains=contains_string, self_link=True)

            if len(links) > 0:
                for i in links:
                    url_string = parse_url_string(i)
                    if url_string not in queue:
                        cliPrint(f'found new URL: {url_string}')
                        queue.append(url_string) 
                    else:
                        cliPrint(f'found already known URL: {url_string}')
            iter += 1

        db.parse_canonical_urls()


        network_visualization_path = f'{output_folder}/Network-Visualization_{datetime.today().strftime("%Y-%m-%d")}.html'        
        if os.path.exists(network_visualization_path):
            os.remove(network_visualization_path)
        db.create_link_graph(network_visualization_path)
        links_status_data = db.list_link_data_join()
        network_analysis_data = db.list_network_analysis_values()
        if output_folder is not False and len(links_status_data) > 0:
            with open(f'{output_folder}/Links-Status_{datetime.today().strftime("%Y-%m-%d")}.csv', 'w') as f:
                writer = csv.DictWriter(f, fieldnames=list(links_status_data[0].keys()))
                writer.writeheader()
                for row in links_status_data:
                    writer.writerow(row)
            with open(f'{output_folder}/Network-Analysis_{datetime.today().strftime("%Y-%m-%d")}.csv', 'w') as f:
                writer = csv.DictWriter(f, fieldnames=list(network_analysis_data[0].keys()))
                writer.writeheader()
                for row in network_analysis_data:
                    writer.writerow(row)
        print(f'scrape complete: crawled {len(links_status_data)} links and {len(queue)} unique URLs')
#        allSitemaps, allPages = parseInputSitemap(seed_url)
#        print("sitemap parse complete, searching for links...")
#        allPageStatus = []
#        foundUrlsLookup = []
#        alreadyAuditedPages = []
#        for i in allPages:
#            allPageStatus, foundUrlsLookup, alreadyAuditedPages = searchForHyperlinksOnPage(i, allPageStatus, foundUrlsLookup, alreadyAuditedPages)
#        print("links search complete, logging to file...\n\n")
#
#        if output_folder is not False:
#            with open(output_folder, 'w') as f:
#                write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
#                write.writerow(['source URL','found URL','link text','opens in new tab?','initial response status','X-Redirect-By header', 'redirect chain length', 'destination URL','final response status','final response content type','notes and exception responses'])
#
#        combinedPageLookups = matchPagesWithFoundUrls(allPageStatus, foundUrlsLookup)
#        cliPrint("ALL PAGES FOUND WITH STATUS")
#        for page in combinedPageLookups:
#            cliPrint(page)
#            if output_folder is not False:
#                with open(output_folder, 'a') as f:
#                    write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
#                    write.writerow(page)
#
    else:
        print("no supported flags provided—try --help or -h for usage.")
