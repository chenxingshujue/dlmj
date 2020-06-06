#!/usr/bin/python
# -*- coding: UTF-8 -*- 
 
import re
print(re.search('www', 'www.runoob.com'))  # 在起始位置匹配
print(re.search('com', 'www.runoob.com'))         # 不在起始位置匹配