from ...helpers.google_auth import auth
from googleapiclient.discovery import build
from datetime import date
from dateutil.relativedelta import relativedelta
from typing import NamedTuple
import csv

# add subparser for import to __main__
def add(subparsers):
    command_string = "gsc-top-queries"
    feature_status = "dev"
    description = "pull report of top search queries per page"
    
    new_subparser = subparsers.add_parser(command_string, help=f"[{feature_status}] {description}")
    new_subparser.add_argument(
        "--property",
        action="store",
        metavar="STRING",
        help="name of Google Search Console property",
        default=False
    )
    new_subparser.add_argument(
        "--start-date",
        action="store",
        metavar="DATE",
        help="optional YYYY-MM-DD start date -- Google Search Console data only goes back 16 months",
        default=date.today()+relativedelta(months=-16)
    )
    new_subparser.add_argument(
        "--page-limit",
        action="store",
        metavar="INT",
        help="limit number of pages checked -- default 25 pages",
        default=25
    )
    new_subparser.add_argument(
        "--query-limit",
        action="store",
        metavar="INT",
        help="limit number of queries checked -- default 5 queries per page",
        default=5
    )
    new_subparser.add_argument(
        "--end-date",
        action="store",
        metavar="DATE",
        help="optional YYYY-MM-DD end date -- Google Search Console data only goes back 16 months",
        default=date.today()
    )
    new_subparser.add_argument(
        "--filename",
        action="store",
        metavar="STRING",
        help="relative filepath for output .csv -- defaults to YYYY-MM-DD_top_queries-report.csv",
        default=f'{date.today().isoformat()}_top-queries-report.csv'
    )
    new_subparser.add_argument(
        "--filters",
        action="store",
        metavar="STRING",
        help="optional filters -- must match dimensionFilterGroups.filters spec https://developers.google.com/webmaster-tools/v1/searchanalytics/query#auth",
        default=[]
    )
    new_subparser.set_defaults(func=parse_gsc_top_queries_args)

    return new_subparser








# definition and defaults for QueryData
class QueryData(NamedTuple):
    url: str
    query: str=""
    clicks: int=0
    impressions: int=0
    click_through_rate: float=0.0
    average_serp_position: float=0.0

def parse_gsc_top_queries_args(args):
    function_args = {}
    if args.property != False:
       function_args['property_string'] = args.property
    else:
        raise f'Google Search Console property string required. Please ask for --help'
    try:
        function_args['filters'] = args.filters
        function_args['start_date'] = args.start_date
        function_args['end_date'] = args.end_date
        function_args['page_limit'] = args.page_limit
        function_args['query_limit'] = args.query_limit
        function_args['output_filename'] = args.filename
    except Exception as e:
        raise e    
    
    
    return gsc_top_queries_report(**function_args)

### Main GSC top queries report function ###
## Required params ##
# property_string -- must match GSC property for which user has appropriate permissions 
## Optional params ##
# filters -- array ot dicts matching the GSC API format. Requires dimension, operator, and expression for each dict
def gsc_top_queries_report(
    property_string: str,
    filters: list=[],
    start_date: date=date.today()+relativedelta(months=-16),
    end_date: date=date.today(),
    page_limit: int=20,
    query_limit: int=5,
    output_filename: str=f'{date.today().isoformat()}_top-queries-report.csv') -> list:

    output_query_data = []

    # oauth2 flow on every run, not stored to disk 
    credentials = auth('client_secrets.json')
    authenticated_gsc = build(
        'searchconsole',
        'v1', 
        credentials = credentials
    )

    sitesList = authenticated_gsc.sites().list().execute()
    authorized_sites = [ i['siteUrl'] for i in sitesList['siteEntry'] ]

    # Check if property is authorized to user
    if property_string in authorized_sites:

        gsc_filter = {
            "rowLimit": page_limit,
            "startDate": start_date.isoformat(), 
            "endDate": end_date.isoformat(),
            "dimensions": ['page'],
            "dimensionFilterGroups": [{"filters": filters}], 
        }

        print(f"{gsc_filter}")
        gsc_pages = authenticated_gsc.searchanalytics().query(
            siteUrl = property_string,
            body = gsc_filter
        ).execute()
        
        if len(gsc_pages.get('rows', [])) > 0:
            with open(output_filename, 'w', newline='' ) as f: 
                output_writer = csv.writer(f)
                output_writer.writerow(QueryData._fields) # header

                for i in gsc_pages['rows']:
                    pagedata = QueryData(
                        url = i['keys'][0],
                        clicks = int(i['clicks']), 
                        impressions = int(i['impressions']), 
                        click_through_rate = float(i['ctr']),
                        average_serp_position = float(i['position'])
                    )
                    output_writer.writerow(pagedata)
                    output_query_data.append(pagedata)
                    print(f'\n\nChecking top queries for URL: {pagedata.url} ({pagedata.clicks} clicks, {pagedata.impressions} impressions)')
                    
                    top_queries = check_url_queries(
                        property_string=property_string,
                        url=pagedata.url,
                        start_date=start_date,
                        end_date=end_date,
                        authenticated_gsc=authenticated_gsc,
                        limit=query_limit)

                    for query in top_queries:
                        output_writer.writerow(query)
                        output_query_data.append(query)
                        print(f'  -- {query.query} ({query.clicks} clicks, {query.impressions} impressions)')
            
            return output_query_data

        # If no rows returned for given data
        else:
            raise Exception(f'No results found for property {property_string} with given filters between {start_date} and {end_date}')
    # If property not authorized, raise error
    else:
        error = f"Property '{property_string}' not authorized. Authorized properties available to this user:"
        for i in authorized_sites:
            error += f"\n{i}"
        raise Exception(error)

def check_url_queries(property_string, url, start_date, end_date, authenticated_gsc, limit):
    body = {
        "rowLimit": limit,
        "startDate": start_date.isoformat(), 
        "endDate": end_date.isoformat(),
        "dimensions": ['query'],
        "dimensionFilterGroups": {"filters": [{'dimension': 'PAGE', 'operator': 'EQUALS', 'expression': url}]},
    }
    related_queries = authenticated_gsc.searchanalytics().query(
        siteUrl = property_string,
        body = body,
    ).execute()
    
    all_queries = []
    if len(related_queries.get("rows", [])) > 0:
        for i in related_queries["rows"]:
            new_query_data = QueryData(
                url = url, 
                query = i["keys"][0], 
                clicks = int(i["clicks"]), 
                impressions = int(i["impressions"]), 
                click_through_rate = float(i["ctr"]), 
                average_serp_position = float(i["position"]),
             )
            all_queries.append(new_query_data)
        
    return all_queries 














# Testing while in development #
#demo_property = 'https://nau.edu/'
#demo_content_filters = [
#    {
#        'dimension': 'PAGE',
#        'operator': 'CONTAINS',
#        'expression': '/online/'
#    }
#]
#gsc_top_queries_report(property_string=demo_property, filters=demo_content_filters)