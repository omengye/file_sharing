##基于tornado和mysql的文件分享web应用

**demo放在了[coding演示](http://simplefilesharing.coding.io/)**上  

之所以选择tornado这个框架是因为最近一直在学习tornado，对它还是比较熟悉的，所以会有点取巧的感觉。这个web应用还用到了七牛的云储存，所以上传文件和下载文件还是比较迅速的。多亏有bootstrap，要不然我做不出能看的页面来。  

主要的功能就是上传文件和下载文件，并含有一个input输入框来返回上传的文件链接，google了下加入了一个tornado的PeriodicCallback属性，来自动在两周后删除数据库以及批量删除七牛云中存储的两周前的数据  

细节方面，加入了一个自定义文件名和超过10个数据则分页的功能  

由于时间关系就只能做到这个程度了

####Todo
可以配置上传文件类型, 大小  
提供简单的接口供命令行或其他语言调用该功能, 如使用curl命令直接上传文件  
其他有趣的功能,想到的有可以划分标签来标记文件；可以查询文件；创建注册用户，可以修改自己的文件，等等

####requirements

	tornado==4.0.2
	torndb==0.3
	MySQL-python==1.2.5
	qiniu==6.1.8

####部署步骤
1，按照requirements配置环境  
2，mysql数据库中创建表

		CREATE TABLE files (
		id INT(11) NOT NULL AUTO_INCREMENT,
		bucket VARCHAR(50) NOT NULL,
		file_title MEDIUMTEXT NULL,
		file_name MEDIUMTEXT NOT NULL,
		mktime FLOAT NOT NULL,
		file_hash VARCHAR(50) NOT NULL,
		published DATETIME NOT NULL,
		PRIMARY KEY (id),
		UNIQUE INDEX file_hash (file_hash)
	)

3，在 index.py 中按要求填写

	define("port", default=8000, help="run on the given port", type=int)
	define("mysql_host", default="127.0.0.1:3306", help="demo database host")  # 修改mysql ip及端口
	define("mysql_database", default="***", help="demo database name")  # 填入数据库名称
	define("mysql_user", default="***", help="demo database user") # 填入mysql用户名
	define("mysql_password", default="***", help="demo database password")  # 填入mysql密码

	qiniu_access_key="***", # 填入qiniu_access_key
    qiniu_secret_key="***", # 填入qiniu_secret_key
    qiniu_policy="***", # 填入qiniu bucket空间名称

4，可以使用Supervisor和Nginx搭配来让tornado app运作起来

	python index.py --port=8000
