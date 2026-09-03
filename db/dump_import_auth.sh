#!/bin/bash
# Import the latest database backup file (taurus_auth.dump.sql -> taurus_auth.dump.{date}.sql)
# To import a specific date's backup, replace taurus_auth.dump.sql below with the specific filename

mysql -h127.0.0.1 -uroot -p123456 <<EOF
drop database if exists taurus_auth;
create database taurus_auth;
use taurus_auth;
source taurus_auth.dump.sql;
EOF