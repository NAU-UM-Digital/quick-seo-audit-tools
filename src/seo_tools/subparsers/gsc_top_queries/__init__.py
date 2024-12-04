from ...helpers.google_auth import auth
from googleapiclient.discovery import build
from datetime import date
from dateutil.relativedelta import relativedelta
from collections import namedtuple
import csv

# definition of QueryData namedtuple
QueryData = namedtuple('QueryData', ['url', 'query', 'clicks', 'impressions', 'click_through_rate', 'average_serp_position'])

### Main GSC top queries report function ###
## Required params ##
# property_string -- must match GSC property for which user has appropriate permissions 
## Optional params ##
# filters -- array ot dicts matching the GSC API format. Requires dimension, operator, and expression for each dict
def main(
    property_string: str,
    filters: list=[],
    start_date: date=date.today()+relativedelta(months=-16),
    end_date: date=date.today(),
    limit: int=25,
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
                        query = "",
                        clicks = int(i['clicks']), 
                        impressions = int(i['impressions']), 
                        click_through_rate = float(i['ctr']),
                        average_serp_position = float(i['position'])
                    )
                    output_writer.writerow(pagedata)
                    output_query_data.append(pagedata)
                    print(f'\n\nChecking top queries for URL: {pagedata.url}')
                    
                    top_queries = check_url_queries(
                        property_string=property_string,
                        url=pagedata.url,
                        start_date=start_date,
                        end_date=end_date,
                        authenticated_gsc=authenticated_gsc,
                        limit=5)

                    for query in top_queries:
                        output_writer.writerow(query)
                        output_query_data.append(query)
                        print(f'  -- {query.query}')
            
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
demo_property = 'https://nau.edu/'
demo_content_filters = [
    {
        'dimension': 'PAGE',
        'operator': 'CONTAINS',
        'expression': '/online/'
    }
]
main(property_string=demo_property, filters=demo_content_filters)