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
import quick_seo_audit_tools.functions.links_status_functions as lsf
import quick_seo_audit_tools.functions.database as db

def testAppRequestGet():
    global args
    appRequestGet(args.destination, userAgent=args.user_agent, email=args.email)

def getLinksStatus():
    global args
    queue = []
    link_log = []

    if args.xml_index is not False:
        print("beginning sitemap parse...")
        # add starting sitemap to queue
        queue.append(args.xml_index)
        print(f'appended {args.xml_index} to queue...')

        iter = 0
        while iter < len(queue):
            links = lsf.handle_url(queue[iter], contains=args.contains)

            if len(links) > 0:
                for i in links:
                    if i not in queue:
                        queue.append(i) 
            iter += 1

        db.list_link_data_join()
        print(f'scrape complete')
#        allSitemaps, allPages = parseInputSitemap(args.xml_index)
#        print("sitemap parse complete, searching for links...")
#        allPageStatus = []
#        foundUrlsLookup = []
#        alreadyAuditedPages = []
#        for i in allPages:
#            allPageStatus, foundUrlsLookup, alreadyAuditedPages = searchForHyperlinksOnPage(i, allPageStatus, foundUrlsLookup, alreadyAuditedPages)
#        print("links search complete, logging to file...\n\n")
#
#        if args.output_csv is not False:
#            with open(args.output_csv, 'w') as f:
#                write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
#                write.writerow(['source URL','found URL','link text','opens in new tab?','initial response status','X-Redirect-By header', 'redirect chain length', 'destination URL','final response status','final response content type','notes and exception responses'])
#
#        combinedPageLookups = matchPagesWithFoundUrls(allPageStatus, foundUrlsLookup)
#        cliPrint("ALL PAGES FOUND WITH STATUS")
#        for page in combinedPageLookups:
#            cliPrint(page)
#            if args.output_csv is not False:
#                with open(args.output_csv, 'a') as f:
#                    write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
#                    write.writerow(page)
#
    else:
        print("no supported flags provided—try --help or -h for usage.")

def sitemapScrapeToMarkdown():
    global args
    if args.xml_index is not False:
        print("beginning sitemap parse...")
        allSitemaps, allPages = parseInputSitemap(args.xml_index)
        print("sitemap parse complete, scraping pages to file...")

        if args.output_folder[-1] != "/":
            scrape_output_folder = args.output_folder+"/"
        else:
            scrape_output_folder = args.output_folder

        for i in allPages:
            cliPrint("-----", False)
            scrape_convert_writefile(i, outputPath=scrape_output_folder, getBodyClass=True)

        cliPrint("-----", False)
        print("scrape complete, pages scraped to markdown at destination: "+scrape_output_folder)
    else:
        print("no supported flags provided—try --help or -h for usage.")

parser = argparse.ArgumentParser(
    "seo-tools"
)

general = parser.add_argument_group("general output")
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

subparsers = parser.add_subparsers(
    title="cli tools for SEO auditing"
)
requestHeaders_parser = subparsers.add_parser("alpha-headers", help="[ALPHA] customize request headers with flags")
requestHeaders_parser.add_argument("destination")
requestHeaders_parser.add_argument("--email", metavar="STRING", action="store", help="add email to response headers", default=False)
requestHeaders_parser.add_argument("--user-agent", metavar="STRING", action="store", help="customize user-agent in response headers", default=False)
requestHeaders_parser.set_defaults(func=testAppRequestGet)

linksStatus_parser = subparsers.add_parser("links-status", help="[PROD] process on-page hyperlinks for response status")
linksStatus_parser.add_argument(
    "--xml-index",
    action="store",
    metavar="URL",
    help="destination URL returns xml index of pages or other xml indexes",
    default=False
)
linksStatus_parser.add_argument(
    "--output-csv",
    action="store",
    metavar="FILE",
    help="relative filepath for csv output",
    default=False
)
linksStatus_parser.add_argument(
    "--contains",
    action="store",
    metavar="STRING",
    help="contains filter to limit parsing page for links",
    default=False
)

linksStatus_parser.set_defaults(func=getLinksStatus)

markdownScrape_parser = subparsers.add_parser("sitemap-scrape", help="[ALPHA] scrape copy from pages listed in sitemap")
markdownScrape_parser.add_argument(
    "--xml-index",
    action="store",
    metavar="URL",
    help="destination URL returns xml index of pages or other xml indexes",
    default=False
)
markdownScrape_parser.add_argument(
    "--output-folder",
    action="store",
    metavar="FILE",
    help="relative folder path for markdown output",
    default='sitemap_scrape/'
)
markdownScrape_parser.add_argument(
    "--keep-html",
    action="store_true",
    help="save response html to file"
)
markdownScrape_parser.add_argument(
    "--no-markdown",
    action="store_true",
    help="suppress markdown convert/export"
)

markdownScrape_parser.set_defaults(func=sitemapScrapeToMarkdown)

args = parser.parse_args()

def appRequestGet(destination, userAgent=False, email=False):
    headers = {}
    if userAgent is not False:
        headers.update({'User-Agent':userAgent})
    if email is not False:
        headers.update({'Email':email})
    r = requests.get(destination, timeout=5)
    return(r)

def cliPrint(input, introDash=True):
    global args
    if args.quiet is False:
        if introDash is True:
            print("--",str(input))
        else:
            print(str(input))
        
def getHyperlinkUrlStatus(foundUrl):
    r = requests.get(foundUrl)
    try:
        historyStatus = r.history[0].status_code
    except:
        historyStatus = r.status_code
    linkInfo = [foundUrl, historyStatus, r.url, r.status_code]
    return linkInfo

def parseInputSitemap(inputXml):
    try:
        r = requests.get(inputXml)
    except:
        parser.exit(1, message="error: failed to request destination xml sitemap\n")
    if "xml" in r.headers.get('content-type'):
        cliPrint("initial xml sitemap request successful")
        allSitemaps = [inputXml]
        allPages = []
        for i in allSitemaps:
            allSitemaps, allPages = parseSitemapsAndPagesFromSitemap(i, allSitemaps, allPages)
    else:
        cliPrint("sitemap request headers on error:")
        cliPrint(r.headers, False)
        parser.exit(1, message="error: provided destination did not return xml\n")
    return allSitemaps, allPages

def parseSitemapsAndPagesFromSitemap(sitemap, allSitemaps=[], allPages=[]):
    try:
        r = requests.get(sitemap, stream=True)
    except:
        parser.exit(1, message="error: failed to request a referenced sitemap")
    if "xml" in r.headers.get('content-type'):
        sitemapSoup = BeautifulSoup(r.text, "lxml-xml")
        locations = sitemapSoup.find_all("loc")
        for i in locations:
            if "xml" in i.text:
                allSitemaps.append(i.text)
                cliPrint("found sitemap: "+i.text)
            else:
                if i.text in allPages:
                    cliPrint("already found this URL:")
                else:
                    allPages.append(i.text)
                cliPrint("found page: "+i.text)
    else:
        cliPrint("recommended: check referenced sitemaps for text/xml content-type headers")
        cliPrint("sitemap request headers on error:")
        cliPrint(r.headers, False)
        print("error: referenced sitemap did not return xml \n\n\n\n\n")

    r.close()

    return allSitemaps, allPages

def searchForHyperlinksOnPage(pageUrl, allPageStatus=[], foundUrlsLookup=[], alreadyAuditedPages=[]):
    try:
        with appRequestGet(pageUrl) as r:
            if 'text/html' in r.headers.get('Content-Type'):
                pageSoup = BeautifulSoup(r.text, "html.parser")
                rawLinks = pageSoup.find_all('a')
                cleanedLinks = []
                for a in rawLinks:
                    if a.has_attr('href'):
                        cleanedLinks.append(a)
                links = []
                for i in cleanedLinks:
                    telMailtoStatus = re.match('(tel.+|mailto.+)', i['href'])
                    if telMailtoStatus:
                        pass
                    else:
                        urlParts = urlsplit(i['href'])
                        if urlParts.scheme != "" and urlParts.netloc != "":
                            links.append(i)
                        else:
                            cliPrint("found incomplete href \""+i['href']+"\" on page: "+r.url)
                            if urlParts.scheme == "":
                                prependHttps = "https://"+i['href']
                                urlParts = urlsplit(prependHttps)

                                if urlParts.netloc == "" or urlParts.netloc == "." or urlParts.netloc == "..":
                                    i['href'] = urljoin(r.url, i['href'])
                                else:
                                    i['href'] = urlunsplit(urlParts)
                            elif urlParts.netloc == "":
                                cliPrint("found incomplete href \""+i['href']+"\" but will test anyway. Found on page: "+r.url)
                            cliPrint("created found url: "+i['href'])
                            links.append(i)
                links.append({'href':pageUrl})
                for i in links:
                    try:
                        linkText = i.text.strip()
                    except:
                        linkText = "no link text found"
                    try:
                        if i.attrs['target'] == "_blank":
                            opensNewTab = "opens in new tab"
                        else:
                            opensNewTab = ""
                    except:
                        opensNewTab = ""
                    foundUrlsLookup.append([pageUrl, i['href'], linkText, opensNewTab])
                    if i['href'] in alreadyAuditedPages:
                        cliPrint("already found this URL: "+i['href'])
                    else:
                        allPageStatus.append(checkHyperlinkUrl(i['href']))
                        alreadyAuditedPages.append(i['href'])
            else:
                cliPrint(f'{r.url} does not have text/html content type')
    except:
        print("error: failed to complete search for hyperlinks on page -- "+pageUrl) 
    return allPageStatus, foundUrlsLookup, alreadyAuditedPages

def checkHyperlinkUrl(foundUrl):
    try:
        r = appRequestGet(foundUrl)
        try:
            historyStatus = r.history[0].status_code
        except:
            historyStatus = r.status_code
        try:
            contentType = r.headers['Content-Type']
        except:
            contentType = "unknown"
        try:
            xRedirectBy = r.history[0].headers['X-Redirect-By']
        except:
            try:
                test = r.history[0]
                xRedirectBy = "no X-Redirect-By header"
            except:
                xRedirectBy = "--"
        linkInfo = [foundUrl, historyStatus, xRedirectBy, len(r.history), r.url, r.status_code, contentType]
    except Exception as inst:
        cliPrint("\n\n\n")
        print("error: exception in found URL request -- "+foundUrl)
        cliPrint("\n\n\n")
        linkInfo = [foundUrl,"EXCEPTION","--","--","--","EXCEPTION","--",str(inst)]
    cliPrint(linkInfo)
    return linkInfo

def matchPagesWithFoundUrls(urlStatuses, lookupUrls):
    for urlLookup in lookupUrls:
        for foundPageStatus in urlStatuses:
            if foundPageStatus[0] == urlLookup[1]:
                urlLookup.extend(foundPageStatus[1:])
        
    return lookupUrls

def check_create_directory(dir, verbose=True):
    if not os.path.exists(dir):
        os.makedirs(dir)
        if verbose is True:
            cliPrint("Directory "+dir+" Created ")
    else:    
        if verbose is True:
            cliPrint("Directory "+dir+" already exists")


def scrape_convert_writefile(URL, outputPath="scrape_output/", getBodyClass=True):

    scrapeDataDestination = outputPath+"_scrape-data/"
    check_create_directory(scrapeDataDestination, verbose=False)

    page = requests.get(URL)
    contentSoup = BeautifulSoup(page.content, "html.parser")

    markdownPath = str(URL[:-1].replace("https://", outputPath+"markdown/")+".md")
    cliPrint("LOCAL PATH: "+markdownPath)

    if args.keep_html is True:
        htmlPath = str(URL[:-1].replace("https://", outputPath+"html/")+".html")
        htmlDir = htmlPath.rsplit('/', 1)[0]
        check_create_directory(htmlDir)
        logTextResponse = open(htmlPath, "w")
        logTextResponse.write(page.text)
        logTextResponse.close()

    try:
        title = str(contentSoup.find("title"))
    except:
        title = "<title>ERROR PULLING ATTRIBUTE FROM NODE</title>"
    try:
        description = str("<meta name=\"description\" content=\"")+str(
            contentSoup.find("meta", {"name": "description"}).get("content"))+str("\"/>")
    except:
        description = "<meta name=\"description\" content=\"ERROR PULLING ATTRIBUTE FROM NODE\"/>"

    try:
        canonicalURL = str(contentSoup.find(
            "link", {"rel": "canonical"}).get("href"))
    except:
        canonicalURL = "ERROR PULLING ATTRIBUTE FROM NODE"
    cliPrint("CANONICAL URL: "+canonicalURL)
    for link in contentSoup.find_all('a'):
        linkStr = ""
        linkStr = str(link.get("href"))
        if ("nau.edu" in linkStr) and ("mailto" not in linkStr):
            logURLs = open(scrapeDataDestination+"urls.csv", "a")
            logURLs.write(canonicalURL+","+linkStr+"\n")
            logURLs.close()

    if getBodyClass == True:
        try:
            templateStr = str(contentSoup.find("body").get("class"))
            template = str(
                "<meta name=\"body-class\" content=\"")+templateStr+str("\"/>\n<meta name=\"canonical\" content=\"")+canonicalURL+str("\">")
        except:
            template = str("<meta name=\"body-class\" content=\"ERROR PULLING ATTRIBUTE FROM NODE\"/>\n<meta name=\"canonical\" content=\"")+canonicalURL+str("\">")
    else:
        template = "" 

    try:
        from quick_seo_audit_tools.extensions import scrapeExtensionReturnsHTML
        extensionAdded = True
    except:
        extensionAdded = False
        
    if extensionAdded is True:
        html = scrapeExtensionReturnsHTML(contentSoup, title, canonicalURL, description, template, scrapeDataDestination)
    else:
        html = contentSoup

    cliPrint("BODY GOOD")
    log = open(scrapeDataDestination+"log.csv", "a")
    log.write(URL+","+canonicalURL+",GOOD BODY\n")
    log.close()

    if args.no_markdown is not True:
        markdownDir = markdownPath.rsplit('/', 1)[0]
        check_create_directory(markdownDir)
        pandocInput = pandoc.read(html, format="html")
        pandocOutput = pandoc.write(pandocInput, format="markdown_strict-raw_html+simple_tables+yaml_metadata_block", options=["--wrap=none", "-s"], file=markdownPath)
        return pandocOutput
    else:
        return True

def main_cli():
    if args.debug is True:
        args.func()
    else:
        try:
            args.func()
        except Exception as err:
            print(f"Unexpected {err=}, {type(err)=}")
            raise
