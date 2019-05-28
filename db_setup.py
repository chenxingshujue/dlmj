#coding=utf-8
# 导入pymysql模块
import pymysql
 
# 连接database
conn = pymysql.connect(
    host="127.0.0.1",
    user="root",password="Chenxing0320!",
    database = 'shaoyou',
    charset = 'utf8')
 
# 得到一个可以执行SQL语句的光标对象
cursor = conn.cursor() 
def executeScriptsFromFile(filename,cursor):
	fd = open(filename, 'r',encoding='utf-8')
	sqlFile = fd.read()
	fd.close()
	sqlCommands = sqlFile.split(';') 
	for command in sqlCommands:
		try:
		    cursor.execute(command)
		except Exception as msg:
		    print(msg)
		print('sql执行完成')
	 
# 执行SQL语句
executeScriptsFromFile('db_setup.sql',cursor)
# cursor.execute(sql)
# sql = "select * from players where username = 'shujue';"
# cursor.execute(sql)
# a = cursor.fetchone()
# print("1",a)
# for c in cursor:
# 	print(c)
# print(dir(cursor))
# 关闭光标对象
cursor.close()
 
# 关闭数据库连接
conn.close()