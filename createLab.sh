#!/bin/bash
# Execute as createLab.sh -p <ravelloPassword> -f <firstName>  -l <lastName> -e <email> -v <vmPassword>
# Ravello username and PEM location should be set in setEnv.sh
#

. `dirname $0`/setEnv.sh

python labUtils.py -u $RAVELLO_USERNAME -k $PEM_LOCATION $@
