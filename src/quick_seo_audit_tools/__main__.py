import argparse
#import pkgutil
import requests
from bs4 import BeautifulSoup
import csv
import re
import lxml
from urllib.parse import urljoin, urlsplit, urlunsplit

def testAppRequestGet():
    global args
    appRequestGet(args.destination, userAgent=args.user_agent, email=args.email)

def getLinksStatus():
    global args
    if args.xml_index is True:
        print("beginning sitemap parse...")
        allSitemaps, allPages = parseInputSitemap(args.destination)
        print("sitemap parse complete, searching for links...")
        allPageStatus = []
        foundUrlsLookup = []
        alreadyAuditedPages = []
        for i in allPages:
            allPageStatus, foundUrlsLookup, alreadyAuditedPages = searchForHyperlinksOnPage(i, allPageStatus, foundUrlsLookup, alreadyAuditedPages)
        print("links search complete, logging to file...\n\n")

        if args.output_csv is not False:
            with open(args.output_csv, 'w') as f:
                write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
                write.writerow(['source URL','found URL','link text','initial response status','X-Redirect-By header', 'redirect chain length', 'destination URL','final response status','notes and exception responses'])

        combinedPageLookups = matchPagesWithFoundUrls(allPageStatus, foundUrlsLookup)
        cliPrint("ALL PAGES FOUND WITH STATUS")
        for page in combinedPageLookups:
            cliPrint(page)
            if args.output_csv is not False:
                with open(args.output_csv, 'a') as f:
                    write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
                    write.writerow(page)

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
    help="supress response text"
)

subparsers = parser.add_subparsers(
    title="dev or testing"
)
requestHeaders_parser = subparsers.add_parser("alpha-headers", help="customize request headers with flags")
requestHeaders_parser.add_argument("destination")
requestHeaders_parser.add_argument("--email", metavar="STRING", action="store", help="add email to response headers", default=False)
requestHeaders_parser.add_argument("--user-agent", metavar="STRING", action="store", help="customize user-agent in response headers", default=False)
requestHeaders_parser.set_defaults(func=testAppRequestGet)

linksStatus_parser = subparsers.add_parser("links-status", help="process on-page hyperlinks for response status")
linksStatus_parser.add_argument("destination")
linksStatus_parser.add_argument(
    "--xml-index",
    action="store_true",
    help="destination URL returns xml index of pages or other xml indexes"
)
linksStatus_parser.add_argument(
    "--output-csv",
    action="store",
    metavar="FILE",
    help="relative filepath for csv output",
    default='False'
)

linksStatus_parser.set_defaults(func=getLinksStatus)

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
        r = requests.get(sitemap)
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
        parser.exit(1, message="error: referenced sitemap did not return xml\n")

    return allSitemaps, allPages

def searchForHyperlinksOnPage(pageUrl, allPageStatus=[], foundUrlsLookup=[], alreadyAuditedPages=[]):
    try:
        r = appRequestGet(pageUrl)
    except:
        parser.exit(1, message="error: failed to request referenced page: "+pageUrl)
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
            #cliPrint(i['href'])
            #cliPrint("scheme: "+urlParts.scheme)
            #cliPrint("netloc: "+urlParts.netloc)
            if urlParts.scheme != "" and urlParts.netloc != "":
                links.append(i)
            else:
                cliPrint("found incomplete href \""+i['href']+"\" on page: "+r.url)
                if urlParts.scheme == "":
                    prependHttps = "https://"+i['href']
                    #cliPrint("Attempting to prepend https: "+prependHttps)
                    urlParts = urlsplit(prependHttps)
                    #cliPrint("scheme: "+urlParts.scheme)
                    #cliPrint("netloc: "+urlParts.netloc)

                    if urlParts.netloc == "" or urlParts.netloc == "." or urlParts.netloc == "..":
                        i['href'] = urljoin(r.url, i['href'])
                    else:
                        i['href'] = urlunsplit(urlParts)
                cliPrint("created found url: "+i['href'])
                links.append(i)
    links.append({'href':pageUrl})
    for i in links:
        try:
            linkText = i.text.strip()
        except:
            linkText = "no link text found"
        foundUrlsLookup.append([pageUrl, i['href'], linkText])
        if i['href'] in alreadyAuditedPages:
            cliPrint("already found this URL: "+i['href'])
        else:
            allPageStatus.append(checkHyperlinkUrl(i['href']))
            alreadyAuditedPages.append(i['href'])
    return allPageStatus, foundUrlsLookup, alreadyAuditedPages

def checkHyperlinkUrl(foundUrl):
    try:
        r = appRequestGet(foundUrl)
        try:
            historyStatus = r.history[0].status_code
        except:
            historyStatus = r.status_code
        try:
            xRedirectBy = r.history[0].headers['X-Redirect-By']
        except:
            try:
                test = r.history[0]
                xRedirectBy = "no X-Redirect-By header"
            except:
                xRedirectBy = "--"
        linkInfo = [foundUrl, historyStatus, xRedirectBy, len(r.history), r.url, r.status_code]
    except Exception as inst:
        print("\n\n\nERROR: exception in found URL request\n\n\n")
        linkInfo = [foundUrl,"EXCEPTION","--","--","--","EXCEPTION",str(inst)]
    cliPrint(linkInfo)
    return linkInfo

def matchPagesWithFoundUrls(urlStatuses, lookupUrls):
    for urlLookup in lookupUrls:
        for foundPageStatus in urlStatuses:
            if foundPageStatus[0] == urlLookup[1]:
                urlLookup.extend(foundPageStatus[1:])
    return lookupUrls

def main_cli():
    try:
        args.func()
    except:
        print("try asking for --help")
