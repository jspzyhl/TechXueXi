#!/bin/bash

/etc/init.d/mysql start
echo "开始运行"
/usr/local/bin/python /xuexi/pandalearning.py
