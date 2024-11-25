import requests

def appRequestGet(destination, userAgent=False, email=False):
    headers = {}
    if userAgent is not False:
        headers.update({'User-Agent':userAgent})
    if email is not False:
        headers.update({'Email':email})
    r = requests.get(destination, timeout=5)
    return(r)