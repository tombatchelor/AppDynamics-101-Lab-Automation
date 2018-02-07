#!/bin/bash
# Execute as createLab.sh -p <ravelloPassword> -f <firstName>  -l <lastName> -e <email> -v <vmPassword>
# Ravello username and PEM location should be set in setEnv.sh
#

# Make sure we have the latest versions
curl https://raw.githubusercontent.com/tombatchelor/AppDynamics-101-Lab-Automation/master/createLab.sh --output createLab.sh
curl https://raw.githubusercontent.com/tombatchelor/AppDynamics-101-Lab-Automation/master/labUtils.py --output labUtils.py

. `dirname $0`/setEnv.sh

python labUtils.py -u $RAVELLO_USERNAME -k $PEM_LOCATION -o ravello -b 3125663272088 $@
