from ...helpers.google_auth import auth
from googleapiclient.discovery import build
from datetime import date
from dateutil.relativedelta import relativedelta

def create_filter_body(filters=[], dimensions=['page'], start_date=date.today()+relativedelta(months=-16), end_date=date.today()):
    body = {
        "startDate": start_date.isoformat(), 
        "endDate": end_date.isoformat(),
        "dimensions": dimensions,
        "dimensionFilterGroups": filters 
    }
    return body

demo_content_filters = [{
    'dimension': 'PAGE',
    'operator': 'CONTAINS',
    'expression': 'nau.edu/online'
}]
def main(filters=demo_content_filters):
    # oauth2 flow on every run, not stored to disk 
    credentials = auth('client_secrets.json')
    authenticated_gsc = build(
        'searchconsole',
        'v1', 
        credentials = credentials
    )

    sitesList = authenticated_gsc.sites().list().execute()
    for site in sitesList['siteEntry']:
        print(site)
        print(f"URL: {site['siteUrl']}")
        print(f"Permission level: {site['permissionLevel']}")
        print("")

    gsc_filter = create_filter_body(
        filters,
    )
    print(f"{gsc_filter}")
    gsc_pages = authenticated_gsc.searchanalytics().query(
        siteUrl = 'sc-domain:nau.edu',
        body = gsc_filter
    ).execute()
    print(gsc_pages)

    # gsc_filter_body = {
    #             "startDate": start_date,
    #             "endDate": end_date,
    #             "dimensions": ["page"],
    #             "dimensionFilterGroups": [
    #               {
    #                 "filters": [
    #                   {
    #                     "dimension": "page",
    #                     "operator": page_include_exclude,
    #                     "expression": page_filter
    #                   },
    #                   {
    #                     "dimension": "query",
    #                     "operator": query_include_exclude,
    #                     "expression": query_filter
    #                   }
    #                 ]
    #               }
    #             ],
    #       }
    # 
    # filter_match = authenticated_gsc.

main()