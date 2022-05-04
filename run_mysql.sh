#!/bin/bash

# /usr/sbin/mysqld --user=root --basedir=/usr --datadir=/var/lib/mysql --plugin-dir=/usr/lib/mysql/plugin --pid-file=/run/mysqld/mysqld.pid > /dev/null & 
# wait-for-it -t 0 localhost:3306
/etc/init.d/mysql restart