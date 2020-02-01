#!/bin/bash

#use e.g with that script: MySensor.sh 
#!/bin/bash
#DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
#$DIR/opt3001.py -d <device> -e 60 --name MySensor --callback sendToInflux.sh


curl -s -i -u "user:pass" -XPOST http://<host>/write?db=openhab_db\&precision=s --data-binary "Opt3001Sensors,sensorname=$2 lux=$3 $4"
