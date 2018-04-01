#!/bin/bash

#pip3 install RPi.GPIO
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root" 1>&2
   exit 1
fi

BIN_DIR='/opt/bin'
SERVICE_DIR='/etc/systemd/system'

echo $BIN_DIR
echo $SERVICE_DIR

cp rpi_fan_control.py $BIN_DIR/fan_control.py
chmod +x $BIN_DIR/fan_control.py

cp fan_control.service $SERVICE_DIR
systemctl daemon-reload