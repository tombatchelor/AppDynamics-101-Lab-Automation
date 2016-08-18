# AppDynamics Java 101 Lab Automation

This project contains code to automate some processes in Ravello. While this has been written to address some specific use cases required at [AppDynamics](http://www.appdynamics.com/), elements of this could be useful elsewhere.

## Dependencies

These scripts are dependent on the [Ravello Python API](https://github.com/ravello/python-sdk). This can be installed locally using PIP (steps below have been tested on OS X):

1. IF you do not have PIP installed, get that:

	`sudo easy_install pip`

2. Then install the Ravello API:

	`sudo pip install ravello-sdk`
	
As creating users is not supported through the API as of August 17, 2016, Selenium and Firefox are also used. The Python Selenuim bindings can be installed with:

	`pip install selenium`
	
# Usage

To use the script to create a Java 101 Canidate lab and associated user, you can run the script as follows:

	`python labUtils.py  -u ravello.user@somedomain.com -p SomePassword -k /Users/tom.batchelor/Java_Lab.pem -f Joe -l Bloggs -e dexterberkeley@me.com -v ThisIsTheVMPassword1`

Where the switches are as follows:

* -u: Ravello user name (must be an admin)
* -p: Ravello password
* -k: Path to the PEM file for the Blueprint
* -f: Candidate first name
* -l: Candidate last name
* -e: Candidate email

This will create the Ravello application and then the user.

