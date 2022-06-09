#!/bin/bash
yum update -y
yum install httpd -y
systemctl start httpd
systemctl enable httpd
cd /var/www/html
EC2AZ=$(curl -s http://"ip address"/latest/meta-data/hostname)
echo "Test  #EC2AZ" > index.html
