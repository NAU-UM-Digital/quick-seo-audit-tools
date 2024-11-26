import requests
from bs4 import BeautifulSoup
import csv
import re
import lxml
from urllib.parse import urljoin, urlsplit, urlunsplit
import os
import json
import pandoc
from ...helpers import links_status_functions as lsf
from ...helpers import database as db
from ...helpers.general import *
from ...helpers import globals
from ...helpers import requests as req
from datetime import datetime

# add subparser for import to __main__
def add(subparsers):
    command_string = "sitemap-scrape"
    feature_status = "REFACTORING IN PROGRESS"
    description = "scrape copy from pages listed in sitemap"
    
    new_subparser = subparsers.add_parser(command_string, help=f"[{feature_status}] {description}")
    new_subparser.add_argument(
        "--seed-url",  
        action="store",
        metavar="URL",
        help="destination URL returns xml index of pages or other xml indexes",
        default=False
    )
    new_subparser.add_argument(
        "--output-folder",
        action="store",
        metavar="FILE",
        help="relative folder path for markdown output",
        default='sitemap_scrape/'
    )
    new_subparser.add_argument(
        "--keep-html",
        action="store_true",
        help="save response html to file"
    )
    new_subparser.add_argument(
        "--no-markdown",
        action="store_true",
        help="suppress markdown convert/export"
    )

    new_subparser.set_defaults(func=sitemapScrapeToMarkdown)

    return new_subparser

# parser's function can take args
def sitemapScrapeToMarkdown(args):
    if args.seed_url is not False:
        print("beginning sitemap parse...")
        allSitemaps, allPages = parseInputSitemap(args.seed_url)
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


def parseInputSitemap(inputXml):
    try:
        r = requests.get(inputXml)
    except:
        #parser.exit(1, message="error: failed to request destination xml sitemap\n")
        exit
    if "xml" in r.headers.get('content-type'):
        cliPrint("initial xml sitemap request successful")
        allSitemaps = [inputXml]
        allPages = []
        for i in allSitemaps:
            allSitemaps, allPages = parseSitemapsAndPagesFromSitemap(i, allSitemaps, allPages)
    else:
        cliPrint("sitemap request headers on error:")
        cliPrint(r.headers, False)
        exit
        #parser.exit(1, message="error: provided destination did not return xml\n")
    return allSitemaps, allPages


def scrape_convert_writefile(URL, outputPath="scrape_output/", getBodyClass=True):

    scrapeDataDestination = outputPath+"_scrape-data/"
    check_create_directory(scrapeDataDestination, verbose=False)

    page = requests.get(URL)
    contentSoup = BeautifulSoup(page.content, "html.parser")

    markdownPath = str(URL[:-1].replace("https://", outputPath+"markdown/")+".md")
    cliPrint("LOCAL PATH: "+markdownPath)

    if globals.args.keep_html is True:
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

    html = contentSoup

    cliPrint("BODY GOOD")
    log = open(scrapeDataDestination+"log.csv", "a")
    log.write(URL+","+canonicalURL+",GOOD BODY\n")
    log.close()

    if globals.args.no_markdown is not True:
        markdownDir = markdownPath.rsplit('/', 1)[0]
        check_create_directory(markdownDir)
        pandocInput = pandoc.read(html, format="html")
        pandocOutput = pandoc.write(pandocInput, format="markdown_strict-raw_html+simple_tables+yaml_metadata_block", options=["--wrap=none", "-s"], file=markdownPath)
        return pandocOutput
    else:
        return True
    
      
def getHyperlinkUrlStatus(foundUrl):
    r = requests.get(foundUrl)
    try:
        historyStatus = r.history[0].status_code
    except:
        historyStatus = r.status_code
    linkInfo = [foundUrl, historyStatus, r.url, r.status_code]
    return linkInfo

def parseSitemapsAndPagesFromSitemap(sitemap, allSitemaps=[], allPages=[]):
    try:
        r = requests.get(sitemap, stream=True)
    except:
        #parser.exit(1, message="error: failed to request a referenced sitemap")
        exit
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
        with req.appRequestGet(pageUrl) as r:
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
        r = req.appRequestGet(foundUrl)
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

