from google_auth_oauthlib.flow import InstalledAppFlow

def auth(secrets_path: str):
    flow = InstalledAppFlow.from_client_config(
        #client config stored in code required for desktop distribution. as noted in Google docs, there is no assumption that these can remain secret. always ensure project scopes are locked down.
        client_config={"installed":{"client_id":"727700222373-j5p0hs3ep85jife8rvtc62m6465jtbh4.apps.googleusercontent.com","project_id":"seo-tools-443700","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","client_secret":"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","redirect_uris":["http://localhost"]}},
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
