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


def run_remote_command(pemLocation, vmIP, remoteCommand):
    subprocess.Popen('ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -i ' + pemLocation + ' ravello@' + vmIP + ' -C "' + remoteCommand + '"', shell=True, stdout=subprocess.PIPE)

def set_password_update_auth(pemLocation, vmIP, vmPassword):
    # Now set the password on the VM
    remoteCommand = 'echo \'ravello:' + vmPassword + '\' | sudo chpasswd'
    run_remote_command(pemLocation, vmIP, remoteCommand)

    # Copy in sshd config file to allow password auth as blueprint process overwrites this
    remoteCommand = 'sudo cp /root/sshd_config /etc/ssh/sshd_config'
    run_remote_command(pemLocation, vmIP, remoteCommand)
    remoteCommand = 'sudo service sshd restart'
    run_remote_command(pemLocation, vmIP, remoteCommand)

    # Shutdown the VM
    remoteCommand = 'sudo shutdown -h now'
    run_remote_command(pemLocation, vmIP, remoteCommand)

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

# Params
ravelloUsername = None
ravelloPassword = None
pemLocation = None
vmPassword = None
userFirstName = None
userLastName = None
userEmail = None

blueprintID = 73401922

# Parse out the arguments
try:
    opts, args = getopt.getopt(sys.argv[1:],'hu:p:k:f:l:e:v:',['username=','password=','pemKey=','firstName=','lastName=','email=','vmPassword='])
except getopt.GetoptError:
    print 'python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -f <firstName>  -l <lastName> -e <email> -v <vmPassword>'
    sys.exit(2)
for opt, arg in opts:
    if opt == '-h':
        print 'python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -f <firstName>  -l <lastName> -e <email> -v <vmPassword>'
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

if userFirstName == None:
    print '-f not set for canidate first name'
    shouldStop = True

if userLastName == None:
    print '-l not set for canidate last name'
    shouldStop = True

if userEmail == None:
    print '-e not set for canidate email'
    shouldStop = True

if vmPassword == None:
    print '-v not set for VM password'
    shouldStop = True

if shouldStop:
    print 'python labUtils.sh -u <ravelloUsername> -p <ravelloPassword> -k <pemLocation> -f <firstName>  -l <lastName> -e <email> -v <vmPassword>'
    sys.exit(-1)

print "Starting app publish"

# Login to Ravello
client = RavelloClient()
client.login(ravelloUsername, ravelloPassword)

# Get the Java 101 BluePrint
Java101BP = client.get_blueprint(blueprintID)

# Use a standardized description for the app, this is use as part of clean up
dateString = generate_standard_date_string()
appDesc = 'Candidate application for: ' + userEmail + ' created on: ' + dateString
appName = 'Candiate_TB_Java 101'

# Create an app and publish it
appName = appName + ' ' + dateString
appDefinition = {'name': appName, 'baseBlueprintId': Java101BP['id'], 'description' : appDesc}
app = client.create_application(appDefinition)
client.publish_application(app['id'])
client.set_application_expiration(app['id'], 1800)

# Check for VM start
app = client.get_application(app['id'])
vm = app['deployment']['vms'][0]
while vm['state'] != 'STARTED':
    print vm['state']
    time.sleep(30)
    app = client.get_application(app['id'])
    vm = app['deployment']['vms'][0]
print vm['state']

# It takes time for sshd to come up, so we're going to sleep
# TB - 2016/07/17 - I should find a better way to do this
time.sleep(60)
vmIP = vm['networkConnections'][0]['ipConfig']['publicIp']
print(vmIP)

set_password_update_auth(pemLocation, vmIP, vmPassword)

print "App publish completed"

# Now create User
print "Creating ravello user"
createUserSelenium(ravelloUsername, ravelloPassword, userFirstName, userLastName, userEmail)

# Print summary
print 'Lab Created'
print 'Application Name: ' + appName
print 'Ravello password: ' + vmPassword


