from urllib.parse import urlparse, parse_qs, urlencode
from queue import Queue
from bs4 import BeautifulSoup
import requests
from datetime import datetime
import csv
from pyvis.network import Network
import networkx as nx

## Generate filename based on a suffix
file_suffix = "query-audit" # define file suffix
file_prefix = f"{datetime.today().strftime('%Y-%m-%d')}" # define file prefix
global_file_name = f"./{file_prefix}_{file_suffix}.csv" # define filename with extension

# Uncomment degree list to select URLs manually
#degree_microsite_list = ['https://degree-search.nau.edu/degree/INDTMBAS', 'https://test.degree-search.nau.edu/degree/ESABAS']

# Add to this list to manually add URLs to the scrape, will be added in reverse order at the beginning of the scrape
urls_to_prepend = ['https://degree-search.nau.edu']


## FUNCTION DEFINITIONS ##
# Funct to read URL list from saved sitemap on file

scrape_count = 0
def global_scrape_count():
    global scrape_count
    scrape_count += 1
    return scrape_count

def get_people_also_ask_options(query):
    with HTMLSession() as session:
        r = session.get(f'https://google.com/search?{ urlencode({"q": query}) }')
        r.html.render(sleep=5)
        found_questions = []
        try:
            for link in r.html.find("div", containing="People also ask")[3].links: ## THIS IS A LIKELY BREAK POINT. I DON'T KNOW THAT THEY'LL KEEP THE PARENT AT THIS LEVEL FOREVER.
                if "google.com" in link:
                    try:
                        question = {
                            'query': parse_qs(urlparse(link).query)['q'][0],
                            'source query': query,
                            'hostname': urlparse(link).hostname,
                        }
                        found_questions.append(question)
                    except:
                        pass
        except:
            print(r.html.html)

        return(found_questions)

def read_sitemap_from_file(file_path):
    global urls_to_prepend
    with open(file_path, "r") as file:
        xml_string = file.read()
        file.close()
    sitemap_dict = xmltodict.parse(xml_string)
    #print(sitemap_dict)
    sitemap_list = [i['loc'] for i in sitemap_dict['urlset']['url']]
    for url in urls_to_prepend:
        if url not in sitemap_list:
            sitemap_list = [url] + sitemap_list
    print(sitemap_list)
    return(sitemap_list)

def read_links_status_sheet(file_name):
    with open(file_name, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        return [row for row in reader]

def write_file(list_dicts, file_name=global_file_name, write_header=False):
    if write_header is True:
        open_type = "w"
    else:
        open_type = "a"
    with open(file_name, mode=open_type) as file:
        w = csv.DictWriter(file, list_dicts[0].keys())
        if write_header is True:
            w.writeheader()
        w.writerows(list_dicts)
        print(f'completed writing file')

def check_degree_search_url(microsite_url):
    print(microsite_url)
    retry = 0
    session = HTMLSession()
    r = session.get(microsite_url)

    while retry < 5:
        print(retry)
        r.html.render(sleep=5)

        try:
            scrape_dict = {'url': microsite_url}
            try:
                scrape_dict['canonical'] = r.html.find('link[rel=canonical]', first=True).attrs['href']
                if scrape_dict['canonical'] == microsite_url:
                    scrape_dict['sitemap_canonical_match'] = True
                else:
                    scrape_dict['sitemap_canonical_match'] = False
            except:
                scrape_dict['canonical'] = "NA"
                scrape_dict['sitemap_canonical_match'] = False
            try:
                scrape_dict['title'] = r.html.find('title', first=True).text
                scrape_dict['title_len'] = len(scrape_dict['title'])
            except:
                scrape_dict['tile'] = "NA"
                scrape_dict['title_len'] = 0
            try:
                scrape_dict['meta_description'] = r.html.find('meta[name=description]', first=True).attrs['content']
                scrape_dict['meta_description_len'] = len(scrape_dict['meta_description'])
            except:
                scrape_dict['meta_description'] = "NA"
                scrape_dict['meta_description_len'] = 0
            try:
                scrape_dict['h1'] = r.html.find('h1', first=True).html
            except:
                scrape_dict['h1'] = "NA"
            try:
                scrape_dict['msIntro'] = r.html.find('#msIntro', first=True).html
            except:
                scrape_dict['msIntro'] = "NA"
            if "&lt;" in scrape_dict['msIntro'] or "&gt;" in scrape_dict['msIntro']:
                scrape_dict['msIntro_needs_clean'] = True
            else:
                scrape_dict['msIntro_needs_clean'] = "NA"

            print(scrape_dict)
            retry = 5
            r.session.close()
        except:
            retry += 1
            r.session.close()

    return(scrape_dict)

def try_degree_search_n_times(n, url):
    tries = 0
    while tries < n:
        try:
            data = check_degree_search_url(url)
            tries = 999
            if global_scrape_count() == 1:
                write_file([data], write_header=True)
            else:
                write_file([data])
            return(data)
        except:
            tries += 1

def summarize_query_log(log):
    for dict in log:
        dict['query count'] = len([i for i in log if i.get('query') == dict['query']])

def create_network_graph(log, list):
    G = nx.MultiDiGraph()
    G.add_nodes_from(list)
    G.add_edges_from([(i['source URL'], i['destination URL']) for i in log])
    return G

def visualize_network_graph(graph):
    net = Network(height="100vh", width="100vw", bgcolor="#222222", font_color="white")
    net.from_nx(graph)
    net.save_graph("networkx-pyvis.html")


## MAIN ##

links_status_dict = read_links_status_sheet('test.csv')
destinations_list = []
edges_list = []
for row in links_status_dict:
    if row['destination URL'] not in destinations_list:
        destinations_list.append(row['destination URL'])
print(destinations_list)
graph = create_network_graph(links_status_dict, edges_list)
visualize_network_graph(graph)
#summarize_query_log(global_query_log)
#write_file(global_query_log, file_name=global_file_name, write_header=True)
