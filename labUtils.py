#   THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS
#   FOR A PARTICULAR PURPOSE. THIS CODE AND INFORMATION ARE NOT SUPPORTED BY APPDYNAMICS.

################################################################################
# 2016-07-17 - 1 - Tom Batchelor - Initial release to support creating a Java 101 Lab Application
#                        and a user
#
#
################################################################################


from ravello_sdk import *
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import socket
import subprocess
import datetime
import getopt
import sys
import csv

def generate_standard_date_string():
    today = datetime.date.today()
    dateString = str(today.year)
    month = today.month
    if month < 10:
        dateString = dateString + '0' + str(month)
    else:
        dateString = dateString + str(month)
    dateString = dateString + str(today.day)
    return dateString


def run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand):
    subprocess.Popen('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ' + pemLocation + ' ' + vmOSUser + '@' + vmIP + ' -C "' + remoteCommand + '"', shell=True, stdout=subprocess.PIPE)

def set_password_update_auth(pemLocation, vmIP, vmOSUser, vmPassword):
    # Now set the password on the VM
    remoteCommand = 'echo \'' + vmOSUser + ':' + vmPassword + '\' | sudo chpasswd'
    run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand)

    # Copy in sshd config file to allow password auth as blueprint process overwrites this
    remoteCommand = 'sudo cp /root/sshd_config /etc/ssh/sshd_config'
    run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand)
    time.sleep(3)
    if vmOSUser == 'ubuntu':
        remoteCommand = 'sudo service ssh restart'
    else:
        remoteCommand = 'sudo service sshd restart'
    run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand)

def build_user_dict(userFirstName, userLastName, userEmail):
    userDict = {}
    userDict['email'] = userEmail
    userDict['name'] = userFirstName
    userDict['surname'] = userLastName
    userDict['roles'] = ['PROSPECTS']
    return userDict

def createUserSelenium(ravelloUsername, ravelloPassword, userFirstName, userLastName, userEmail):
    driver = webdriver.Firefox()
    wait = WebDriverWait(driver, 60)

    driver.get('https://login.ravellosystems.com/cas/login?service=https%3A%2F%2Fcloud.ravellosystems.com%2FloginSuccess%3Fservice%3DaHR0cHM6Ly9jbG91ZC5yYXZlbGxvc3lzdGVtcy5jb20v')
    elem = driver.find_element_by_css_selector('#login-email')
    elem.send_keys(ravelloUsername)
    elem = driver.find_element_by_css_selector('#login-password')
    elem.send_keys(ravelloPassword)
    elem = driver.find_element_by_css_selector('#loginBtn')
    elem.click()

    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#navigation-menu-admin')))
    elem.click()
    elem = driver.find_element_by_css_selector('#menu-goto-users-page > span > span')
    elem.click()

    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'button.ravello-btn.main-btn')))
    elem.click()

    elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '#first-name')))
    elem.send_keys(userFirstName)
    elem = driver.find_element_by_css_selector('#last-name')
    elem.send_keys(userLastName)
    elem = driver.find_element_by_css_selector('#email')
    elem.send_keys(userEmail)
    elem = driver.find_element_by_css_selector('a.ui-icon-delete')
    elem.click()
    elem = driver.find_element_by_css_selector('a.chosen-single.chosen-default')
    elem.click()
    elem = driver.find_element_by_css_selector('ul.chosen-results > li:nth-of-type(6)')
    elem.click()
    elem = driver.find_element_by_css_selector('#Invite-btn')
    elem.click()
    driver.close()

# Constants

usageString = ''' Single app usage:
    python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -f <firstName>  -l <lastName> -e <email> -v <vmPassword> -b <blueprintID> -o vmOSUser
    Multi app usage:
    python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -a <attendeeFile> -b <blueprintID> -o vmOSUser -t appTimeout
    '''

# Params
ravelloUsername = None
ravelloPassword = None
pemLocation = None
vmPassword = None
userFirstName = None
userLastName = None
userEmail = None
blueprintID = None
attendeeFile = None
appTimeout = None
vmOSUser = None

# Parse out the arguments
try:
    opts, args = getopt.getopt(sys.argv[1:],'hu:p:k:f:l:e:v:b:a:t:o:',['username=','password=','pemKey=','firstName=','lastName=','email=','vmPassword=','blueprint=','attendeeFile','appTimeout', 'vmOSUser'])
except getopt.GetoptError:
    print usageString
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print usageString
        sys.exit(-1)
    elif opt in ('-u', '--username'):
        ravelloUsername = arg
    elif opt in ('-p', '--password'):
        ravelloPassword = arg
    elif opt in ('-k', '--pemKey'):
         pemLocation = arg
    elif opt in ('-f', '--firstName'):
        userFirstName = arg
    elif opt in ('-l', '--lastName'):
        userLastName = arg
    elif opt in ('-e', '--email'):
        userEmail = arg
    elif opt in ('-v', '--evmPassword'):
        vmPassword = arg
    elif opt in ('-b', '--blueprint'):
        blueprintID = arg
    elif opt in ('-a', '--attendeeFile'):
        attendeeFile = arg
    elif opt in ('-t', '--appTimeout'):
        appTimeout = arg
    elif opt in ('-o', '--vmOSUser'):
        vmOSUser = arg

# Validate args
shouldStop = False
if ravelloUsername == None:
    print '-u not set for ravello username'
    shouldStop = True

if ravelloPassword == None:
    print '-p not set for ravello password'
    shouldStop = True

if pemLocation == None:
    print '-k not set for pem location'
    shouldStop = True

if attendeeFile == None:
    if userFirstName == None:
        print '-f not set for canidate first name or attendee file not provided'
        shouldStop = True

    if userLastName == None:
        print '-l not set for canidate last name or attendee file not provided'
        shouldStop = True

    if userEmail == None:
        print '-e not set for canidate email or attendee file not provided'
        shouldStop = True

    if vmPassword == None:
        print '-v not set for VM password or attendee file not provided'
        shouldStop = True

if blueprintID == None:
    print '-b not set for Blueprint ID'
    shouldStop = True

if vmOSUser == None:
    print '-o not set for VM OS User'
    shouldStop = True

if shouldStop:
    print usageString
    sys.exit(-1)

userList = []

if attendeeFile != None:
    with open(attendeeFile, 'rb') as f:
        reader = csv.reader(f)
        tempList = list(reader)
        for line in tempList:
            user = {
                     'userFirstName' : line[0],
                     'userLastName' : line[1],
                     'userEmail' : line[2],
                     'vmPassword' : line[3]
                     }
            userList.append(user)
else:
    userList = [{
                'userFirstName' : userFirstName,
                'userLastName' : userLastName,
                'userEmail' : userEmail,
                'vmPassword' : vmPassword
                }]

print userList
print "Starting app publish"

# Login to Ravello
client = RavelloClient()
client.login(ravelloUsername, ravelloPassword)

# Get the BluePrint
blueprint = client.get_blueprint(blueprintID)

if blueprint is None:
    print "Blueprint with ID: " + blueprintID + " not found, exiting"
    sys.exit(-2)

# Creata app and publish for each user in the userList
for user in userList:
    # Use a standardized description for the app, this is use as part of clean up
    # Use legacy format for 101 lab
    if "101" in blueprint['name']:
        dateString = generate_standard_date_string()
        appDesc = 'Candidate application for: ' + user['userEmail'] + ' created on: ' + dateString
        appName = 'Candidate_' + user['userFirstName'][0] + user['userLastName'][0] + '_Java 101 ' + dateString
    else:
        appDesc = 'Auto created application for : ' + user['userEmail'] + ' from: ' + blueprint['name']
        appName = blueprint['name'] + ' for: ' + user['userFirstName'] + ' ' + user['userLastName']

    # Create an app and publish it
    user['appName'] = appName
    appDefinition = {'name': appName, 'baseBlueprintId': blueprint['id'], 'description' : appDesc}
    app = client.create_application(appDefinition)
    client.publish_application(app['id'])
    client.set_application_expiration(app['id'], 1800) # If a app timeout has been set, we take care of that later
    user['appID'] = app['id']

# Check for VM start for each VM in each app started
for user in userList:
    app = client.get_application(user['appID'])
    vmCounter = 0 # There is probably a better way to manage this
    for vm in app['deployment']['vms']:
        while vm['state'] != 'STARTED':
            print vm['state']
            time.sleep(30)
            app = client.get_application(user['appID'])
            vm = app['deployment']['vms'][vmCounter]
        print vm['state']
        vmCounter = vmCounter + 1

# It takes time for sshd to come up on the VMs, so we're going to sleep
# TB - 2016/07/17 - I should find a better way to do this
time.sleep(150)

# Change passwords on the VMs
for user in userList:
    user['vmIPs'] = []
    app = client.get_application(user['appID'])
    for vm in app['deployment']['vms']:
        vmIP = vm['networkConnections'][0]['ipConfig']['publicIp']
        print(vmIP)
        user['vmIPs'].append(vmIP)
        set_password_update_auth(pemLocation, vmIP, vmOSUser, user['vmPassword'])

print "App publish completed"

# Only create the Ravello user if we are doing a java 101 lab
if "101" in blueprint['name']:
    print "Creating ravello user"
    createUserSelenium(ravelloUsername, ravelloPassword, user['userFirstName'], user['userLastName'], user['userEmail'])

# Set timeout is set
if appTimeout != None:
    appTimeout = int(appTimeout)
    appTimeout = appTimeout * 60 * 60
    for user in userList:
        client.set_application_expiration(user['appID'], appTimeout)

# Print summary
print userList
for user in userList:
    print 'Lab Created'
    print 'userEmail: ' + user['userEmail']
    print 'Application Name: ' + user['appName']
    print 'Ravello VM password: ' + user['vmPassword']
    print 'IPs:'
    print user['vmIPs']

summaryReport = open('automation-output.csv', 'w')

summaryReport.write("Email, Application, VM Username, Password, IPs\n");

for user in userList:
    summaryReport.write(
        user['userEmail'] + ', ' +
        user['appName'] + ', ' +
        vmOSUser + ', ' +
        user['vmPassword'] + ', ' +
        user['vmIPs'][0] + '\n'
)



