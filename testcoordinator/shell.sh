#!/usr/bin/env bash

echo Installing Python
echo -----------------
sudo apt-get update
sudo apt-get install python python-pip -y

echo Installing Pymongo
echo ------------------
sudo pip install pymongo

echo Installing Celery
echo -----------------
sudo pip install celery

echo Upstart the Test Coordinator
echo ----------------------------
cp /vagrant/testcoordinator/test-coordinator.Upstart.templ /etc/init/testcoordinator.conf
sudo service testcoordinator start
