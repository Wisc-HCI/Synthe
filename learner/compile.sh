#!/bin/bash

ip=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
echo $ip

python3 create_alphabet.py $1

if [ $# -eq 0 ]
  then
    python3 gui.py $ip $1
  else
  	python3 gui.py $ip $1 $2
fi
