import csv
from bs4 import BeautifulSoup
import json
from quick_seo_audit_tools.main import *

def scrapeExtensionReturnsHTML(contentSoup, title, canonicalURL, description, template, scrapeDataDestination):
    try:
        weirdDivs = contentSoup.findAll(
            "div", {"class": "panelLinkTypeArrow"})
        for weirdDiv in weirdDivs:
            weirdLinks = weirdDiv.findAll("a")
            for wlink in weirdLinks:
                wlinkURL = wlink.get("href")
                wlinkALT = wlink.get("alt")
                blockUrlTag = str("<a href='")+wlinkURL + \
                    str("'>")+wlinkALT+str("</a>")
                urlSoup = BeautifulSoup(blockUrlTag, "html.parser")
                try:
                    wlink.append(urlSoup)
                except:
                    cliPrint("couldn't find wlink")
    except:
        weirdLinks = "No weird NAU21 block links"
        cliPrint(weirdLinks)
    
    try:
        statsBlocks = [
            contentSoup.find_all("div", {"data-repository": True})
        ]
        for statsBlockSelector in statsBlocks:
            try:
                for i in statsBlockSelector:
                    try:
                        logIdentifier = i['class']
                        statContent = i.find("div", {"class": "content"})
                        try:
                            statRepoId = 'https://in.nau.edu/repository/wp-admin/post.php?post=' + \
                                i['data-repository'] + '&action=edit'
                            def requestNauRepoItem(repoType, repoId):
                                    try:
                                        tryUrl = 'https://in.nau.edu/repository/wp-json/content-repo/v1/content/'+repoType+'/'+repoId+'/'
                                        repoData = requests.get(tryUrl)
                                        data = json.loads(repoData.content)
                                        repoPostStatus = data[0]["post_status"]
                                        return repoPostStatus
                                    except:
                                        return False
                            repoTypesToTry = ['statistic', 'testimonial', 'blurb']
                            statRepoPostStatus = False
                            repoIter = 0
                            while (statRepoPostStatus is False and repoIter < len(repoTypesToTry)):
                                statRepoPostStatus = requestNauRepoItem(repoTypesToTry[repoIter], i['data-repository'])
                                if statRepoPostStatus is False:
                                    repoIter =+ 1
                            if statRepoPostStatus is False:
                                statRepoPostStatus = "COULD NOT FIND REPO POST STATUS"
                        except:
                            statRepoId = "COULD NOT FIND REPO ID"
                            statRepoPostStatus = "COULD NOT FIND REPO POST STATUS"
                        try:
                            statEyebrow = statContent.find("div", {"class": "eyebrow-underline"}).get_text().strip()
                        except:
                            statEyebrow = ""
                        try:
                            statNum = statContent.find("div", {"class": "number"}).get_text().strip()
                        except:
                            statNum = ""
                        try:

                            statLabel = statContent.find("div", {"class": "label"}).get_text().strip()
                        except:
                            statLabel = ""
                        try:
                            statPub = statContent.find("div", {"class": "publication"}).get_text().strip()
                        except:
                            statPub = ""
                        allStatsList = [str(statRepoId), str(statRepoPostStatus), str(statEyebrow), str(statNum), str(statLabel), str(statPub), str(logIdentifier), str(canonicalURL)]
                        cliPrint(allStatsList)
                        with open(scrapeDataDestination+'stats.csv', 'a') as f:
                            write = csv.writer(f, quoting=csv.QUOTE_ALL, lineterminator='\n')
                            write.writerow(allStatsList)
                    except:
                        cliPrint("\n\n\n\n HAD AN ISSUE PULLING SINGLE STAT")
                        pass
            except:
                cliPrint("\n\n\n\n HAD AN ISSUE PULLING ALL STATS ON PAGE")
                pass
    except:
        pass

    try:
        tagsToRemove = [
            contentSoup.findAll("head"),
            contentSoup.findAll("noscript"),
            contentSoup.findAll("div", {"id": "top-nav-wrapper"}),
            contentSoup.findAll("div", {"id": "simple-page-footer"}),
            contentSoup.findAll("div", {"id": "program-of-interest-mobile"}),
            contentSoup.findAll("div", {"id": "left-nav-menu"}),
            contentSoup.findAll("div", {"class": "ginput_container"}),
            contentSoup.findAll("div", {"class": "ginput_recaptcha"}),
            contentSoup.findAll("div", {"class": "gfield"}),
            contentSoup.findAll("div", {"class": "event-container"}),
            contentSoup.findAll("span", {"class": "screen-reader-text"}),
            contentSoup.findAll("div", {"class": "screen-reader-text"}),
            contentSoup.findAll("li", {"class": "gfield"}),
            contentSoup.findAll("a", {"id": "request-info"}),
            contentSoup.findAll("footer"),
            contentSoup.findAll("iframe"),
        ]
        try:
            for foundAll in tagsToRemove:
                try:
                    for tag in foundAll:
                        try:
                            tag.decompose()
                        except:
                            pass
                except:
                    pass
        except:
            pass
        body = str(contentSoup)

        logBody = open(scrapeDataDestination+"body.html", "w")
        logBody.write(body)
        logBody.close()
    except:
        body = str(contentSoup.findAll("div", {"class": "entry-content"}))
    head = "<head>"+title+description+template+"</head>"
    html = head+body    
    return html