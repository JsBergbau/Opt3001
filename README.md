#  Read data from Texas Instruments Opt3001 light sensor
With this script you can read out the value of your TI opt3001 sensor, e.g. with Raspberry PI. 

## Prequisites / Requirements
You need Python3 3.7 or above because of the dataclasses used in the callback function. 

For example Raspbian Stretch has only Python 3.5.3. If you like to upgrade your Distribution to current Buster release follow this Tutorial https://pimylifeup.com/upgrade-raspbian-stretch-to-raspbian-buster/ If doing so: Omit the rpi-update step.

If you like installing/compiling Python3.7 please take a look at this tutorial https://gist.github.com/SeppPenner/6a5a30ebc8f79936fa136c524417761d However it took about 5 hours to compile/run the regressiontests on a Raspberry PI3B. I use this compiled version directly without install. If you do, too, you have to change the first line in the script, pointing to your compiled Python version. 

Prequisites: python3 python3-smbus
install via

`sudo apt install python3 python3-smbus`




## Usage
```
usage: opt3001.py [-h] [--device 0xff] [--device2 0xff] [--round ROUND]
                  [--every N] [--callback CALLBACK] [--name NAME]

optional arguments:
  -h, --help            show this help message and exit
  --device 0xff, -d 0xff
                        Set the device adress in format 0xff
  --device2 0xff, -d2 0xff
                        Set the second device adress in format 0xff
  --round ROUND, -r ROUND
                        Round Lux value to N decimal place
  --every N, -e N       Measure every N seconds

Callback related functions:
  --callback CALLBACK, -call CALLBACK
                        Pass the path to a program/script that will be called
                        on each new measurement
  --name NAME, -n NAME  Give this sensor a name reported to the callback
                        script

  ```
  
The sensor resolution is 2 decimal places.

 
  ## Further Infos
The opt3001 is used in the full auto range mode with a integration intervall of 800 ms. This gives according to Texas instruments documentation best accuracy. Integration intervall of 800 ms means roughly said that the average lux in the last 800 ms is read.

### Second sensor
The opt3001 only measures up to 83865.6 Lux. Now if you want to know how much more light than these 83865.6 lux is there, this script supports a second sensor. These high lux values will only be reached in direct sunlight and probably not behind a window (depending on the location and season). You can put the second sensor behind semi transparent acrylic glass to get less light to the Chip. Acrylic glass is UV resistant and not UV permeable.

Please note: You have to change the I2C address of the second sensor. E.g. put VCC on ADDR Pin.
 
  ## Sample output
```  
./opt3001.py -d 0x45 -e 10
Lux: 31.86
Lux: 31.56
Lux: 31.72
```

```  
./opt3001.py -d 0x45 -d2 0x44
Lux: 31.76, Lux2: 36.49
Lux: 31.6, Lux2: 36.4
Lux: 31.8, Lux2: 36.4
Lux: 31.71, Lux2: 36.36
```
Note: The 2 sensor are not equally aligned, thus the values differ.

## Callback for processing the data
Via the --call option a script can be passed to sent the data to. 
Example
`./opt3001.py -d 0x44 -e 10 --callback sendData.sh`
If you don't give the sensor a name `opt3001` is used. The callback script must be within the same folder as this script.
The values outputted depends whether you use a second sensor or not. So the format is printed in the first argument.
Example callback
```
#!/bin/bash
echo $@ >> data.txt
```
Gives in data.txt `sensorname,lux,timestamp opt3001 36.46 1580595841`

Whereas the timestamp is in the Unix timestamp format in UTC (seconds since 1.1.1970 00:00). 

All data received from the sensor is stored in a list and transmitted sequentially. This means if your backend like influxdb is not reachable when a new measurement is received, it will be tried again later (currently waiting 5 seconds before the next try). Thus no data is lost when your storage engine has some trouble. There is no upper limit (the only limit should be the RAM). Keep this in mind when specifing a wrong backend. 

"sendToInflux.sh" is an example script for sending the data to influxdb via http-API. Precision was set to the level of seconds. This gives better compression ratios in influxdb.

For further backends please the all the various backends of the Xiaomi Mi Temperature 2 script https://github.com/JsBergbau/MiTemperature2
