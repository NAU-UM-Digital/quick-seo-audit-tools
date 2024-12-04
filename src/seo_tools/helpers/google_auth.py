from google_auth_oauthlib.flow import InstalledAppFlow

def auth(secrets_path: str):
    flow = InstalledAppFlow.from_client_secrets_file(
        secrets_path,
        scopes=[
            'https://www.googleapis.com/auth/webmasters.readonly'
        ]
    )

    try_port = 8080
    credentials = False 
    while try_port < 8099 and credentials is False:
        try:
            print(f'Trying port {try_port}...')
            credentials = flow.run_local_server(
                host='localhost',
                port=try_port,
                authorization_prompt_message='Please visit this URL: {url}', 
                success_message='The auth flow is complete; you may close this window.',
                open_browser=True)
        except Exception as e:
            if "Address already in use" in str(e):
                try_port += 1
            else:
                raise e

    return credentials
