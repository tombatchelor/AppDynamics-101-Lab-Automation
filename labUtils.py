#   THIS CODE AND INFORMATION ARE PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND/OR FITNESS
#   FOR A PARTICULAR PURPOSE. THIS CODE AND INFORMATION ARE NOT SUPPORTED BY APPDYNAMICS.

################################################################################
# 2016-07-17 - 1 - Tom Batchelor - Initial release to support creating a Java 101 Lab Application
#                        and a user
# 2018-01-17 - 2 - Change to ephemeral access tokens
#
#
################################################################################


from ravello_sdk import *
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
    time.sleep(10)
    if vmOSUser == 'ubuntu':
        remoteCommand = 'sudo service ssh restart'
    else:
        remoteCommand = 'sudo service sshd restart'
    run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand)

def build_user_dict(firstName, lastName, email):
    userDict = {}
    userDict['email'] = email
    userDict['name'] = firstName
    userDict['surname'] = lastName
    userDict['roles'] = ['PROSPECTS']
    return userDict

def getExpiryTimestamp():
    currTimeMillis = int(time.time()) * 1000
    # Add on a week
    weekMillis = 60 * 60 * 24 * 7 * 1000
    return currTimeMillis + weekMillis

# Constants

usageString = ''' Single app usage:
    python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -f <firstName>  -l <lastName> -e <email> -v <vmPassword> -b <blueprintID> -o vmOSUser
    Multi app usage:
    python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -a <attendeeFile> -b <blueprintID> -o vmOSUser -t appTimeout
    '''

#template
ephemeralToken = {'description': 'bob',
'expirationTime': 1516488864831,
'permissions':
    [
     {
     'resourceType': 'APPLICATION',
     'filterCriterion': {
     'operator': 'Or',
     'type': 'COMPLEX',
     'criteria':
     [
      {
      'index': 1,
      'propertyName': 'ID',
      'operand': '3125662683471',
      'operator': 'Equals',
      'type': 'SIMPLE'}
      ]
     },
     'actions': [
                 'EXECUTE', 'READ'
                 ]
     }
     ],
'name': 'bobq'}

# Params
ravelloUsername = None
ravelloPassword = None
pemLocation = None
vmPassword = None
userFirstName = None
userLastName = None
email = None
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
        firstName = arg
    elif opt in ('-l', '--lastName'):
        lastName = arg
    elif opt in ('-e', '--email'):
        email = arg
    elif opt in ('-v', '--evmPassword'):
        vmPassword = arg
    elif opt in ('-b', '--blueprint'):
        blueprintID = arg.strip()
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
    if firstName == None:
        print '-f not set for canidate first name or attendee file not provided'
        shouldStop = True

    if lastName == None:
        print '-l not set for canidate last name or attendee file not provided'
        shouldStop = True

    if email == None:
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
                     'firstName' : line[0],
                     'lastName' : line[1],
                     'email' : line[2],
                     'vmPassword' : line[3]
                     }
            userList.append(user)
else:
    userList = [{
                'firstName' : firstName,
                'lastName' : lastName,
                'email' : email,
                'vmPassword' : vmPassword
                }]

print userList
print "Starting app publish"

# Check BP ID, if using broken 101 Blueprint, bomb out.
if blueprintID == '73401922':
    print('Using old Java 101 Blueprint, auto-update fixed this, please run again')
    sys.exit(-2)

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
        appDesc = 'Candidate application for: ' + user['email'] + ' created on: ' + dateString
        appName = 'Candidate_' + user['firstName'][0] + user['lastName'][0] + '_Java 101 ' + dateString
    else:
        appDesc = 'Auto created application for : ' + user['email'] + ' from: ' + blueprint['name']
        appName = blueprint['name'] + ' for: ' + user['firstName'] + ' ' + user['userLastName']

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

# Only create the Access Token if we are doing a java 101 lab
if "101" in blueprint['name']:
    print "Creating access Token"
    ephemeralToken['expirationTime'] = getExpiryTimestamp()
    ephemeralToken['name'] = 'Token for: ' + user['appName']
    ephemeralToken['description'] = 'Token for: ' + user['appName']
    ephemeralToken['permissions'][0]['filterCriterion']['criteria'][0]['operand'] = user['appID']
    user['tokenID'] = client.create_ephemeral_access_token(ephemeralToken)['token']


# Set timeout is set
if appTimeout != None:
    appTimeout = int(appTimeout)
    appTimeout = appTimeout * 60 * 60
    for user in userList:
        client.set_application_expiration(user['appID'], appTimeout)

time.sleep(60)
print('Restarting SSHD on VMs')
for user in userList:
    vmIPs = user['vmIPs']
    for vmIP in vmIPs:
        if vmOSUser == 'ubuntu':
            remoteCommand = 'sudo service ssh restart'
            run_remote_command(pemLocation, vmIP, vmOSUser, remoteCommand)
print('Done with SSHD restart')

# Print summary
print userList
for user in userList:
    print 'Lab Created'
    print 'Application Name: ' + user['appName']
    print 'Ravello VM password: ' + user['vmPassword']
    print 'Access URL: https://cloud.ravellosystems.com/#/' + user['tokenID']
    print 'IPs:'
    print user['vmIPs']

summaryReport = open('automation-output.csv', 'w')

summaryReport.write("Email, Application, VM Username, Password, IPs\n");

for user in userList:
    # for multi IP applications
    vmIPstring = ''
    for ip in user['vmIPs']:
        vmIPstring = vmIPstring + ip
        vmIPstring = vmIPstring + ' '
    user['vmIPstring'] = vmIPstring
    summaryReport.write(
        user['email'] + ', ' +
        user['appName'] + ', ' +
        vmOSUser + ', ' +
        user['vmPassword'] + ', ' +
        user['vmIPstring'] + '\n'
)



