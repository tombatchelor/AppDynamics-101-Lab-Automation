# AppDynamics Lab Automation

This project contains code to automate some processes in Ravello. While this has been written to address some specific use cases required at [AppDynamics](http://www.appdynamics.com/), elements of this could be useful elsewhere.

## Dependencies

These scripts are dependent on the [Ravello Python API](https://github.com/ravello/python-sdk). This can be installed locally using PIP (steps below have been tested on OS X):

1. IF you do not have PIP installed, get that:

		`sudo easy_install pip`

2. Then install the Ravello API:

		`sudo pip install ravello-sdk`
	
As creating users is not supported through the API as of August 17, 2016, Selenium and Firefox are used. The Python Selenuim bindings can be installed with:

	`pip install selenium`

If this fails on OS X, try this:

	`sudo easy_install selenium`
	
# Usage

There are two use cases supported

## AppDynamics 101 Lab

Make sure RAVELLO_USERNAME and PEM_LOCATION are set in the setEnv.sh. PEM_LOCATION should point to the Bleuprint access key.

To use the script to create a Java 101 Canidate lab and associated user, you can run the script as follows:

	`createLab.sh -p YourRavelloPassword -f Joe -l Bloggs -e dexterberkeley@me.com -v ThisIsTheVMPassword1`

Where the switches are as follows:

* -p: Ravello password
* -f: Candidate first name
* -l: Candidate last name
* -e: Candidate email

This will create the Ravello application and then the user. Note this will also autoupdate these utilities from GitHub

## AppDynamics AppSphere Hand On Lab

Make sure RAVELLO_USERNAME and PEM_LOCATION are set in setEnv.sh. PEM_LOCATION should point to the Bleuprint access key.

The script requires a CSV file which list out the lab attendees to create Ravello apps for. This is of the format:

FirstName,LastName,Email,OSPassword

An example is in sampleInput.csv

A execution looks like the following

	`createHOL.sh -p YourRavelloPassword -b BlueprintID -a sampleInput.csv -o osUser -t timeout`

Where the switches are as follows:

* -p: Ravello password
* -b: HOL Blueprint ID
* -a: user CSV file
* -t: App timeout in hours

This will create a Ravello app for each user in the CSV, and set the timeout. This then presents an output like:

~~~~
App publish completed
[{'userEmail': 'jeff@jeff.com', 'appName': u'test-appsphere-42-lab-SRVVisPlus-bp for: Jeff Bridges', 'vmPassword': 'password1', 'vmIPs': [u'104.198.137.221', u'104.198.67.100'], 'userFirstName': 'Jeff', 'userLastName': 'Bridges', 'appID': 75108706}, {'userEmail': 'great@test.com', 'appName': u'test-appsphere-42-lab-SRVVisPlus-bp for: Great Scott', 'vmPassword': 'password2', 'vmIPs': [u'104.198.58.104', u'104.197.87.83'], 'userFirstName': 'Great', 'userLastName': 'Scott', 'appID': 75108707}]
Lab Created
userEmail: jeff@jeff.com
Application Name: test-appsphere-42-lab-SRVVisPlus-bp for: Jeff Bridges
Ravello VM password: password1
IPs:
[u'104.198.137.221', u'104.198.67.100']
Lab Created
userEmail: great@test.com
Application Name: test-appsphere-42-lab-SRVVisPlus-bp for: Great Scott
Ravello VM password: password2
IPs:
[u'104.198.58.104', u'104.197.87.83']
~~~~