from ravello_sdk import *

ravelloUsername = ''
ravelloPassword = ''
client = RavelloClient()
client.login(ravelloUsername,ravelloPassword)

apps = client.get_applications()
candidateApps = []
for app in apps:
    if app['name'].startswith('Candidate'):
        candidateApps.append(app)
for app in candidateApps:
    print(app['ownerDetails']['name'])
