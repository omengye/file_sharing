# -*- coding: utf-8 -*-
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import torndb
import os
import qiniu.conf
import qiniu.io
import qiniu.rs
import qiniu.fop
from database import DataBase, Paginator
import datetime
import time
import sys

from tornado.options import define, options
define("port", default=8000, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="demo database host")  # 修改mysql ip及端口
define("mysql_database", default="***", help="demo database name")  # 填入数据库名称
define("mysql_user", default="***", help="demo database user") # 填入mysql用户名
define("mysql_password", default="***", help="demo database password")  # 填入mysql密码

period = 2 * 7 * 24 * 60 * 60 * 1000   # 每两周定时删除两周前文件


class Application(tornado.web.Application):

    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/file", UploadFileHandler),
        ]
        settings = dict(
            blog_title=u"Tornado Blog",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            qiniu_access_key="***", # 填入qiniu_access_key
            qiniu_secret_key="***", # 填入qiniu_secret_key
            qiniu_policy="***", # 填入qiniu bucket空间名称
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        self.database = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)


def qiniu_path(key):
    bucket = Application().settings['qiniu_policy']
    bucket = unicode(bucket)
    return qiniu.rs.EntryPath(bucket, key)


def del_cron():
    now = datetime.datetime.now()
    before = now + datetime.timedelta(days=-14)  # 设定时间至两周前
    before_mktime = time.mktime(before.timetuple())  # 把设定时间转换成Epoch秒数
    keys = Application().database.query(
        "SELECT file_name FROM files WHERE mktime < %s", before_mktime)
    all_key = [x['file_name'] for x in keys]
    path = map(qiniu_path, all_key)
    Application().database.execute(
        "DELETE FROM files WHERE mktime < %s", before_mktime)
    qiniu.conf.ACCESS_KEY = Application().settings['qiniu_access_key']
    qiniu.conf.SECRET_KEY = Application().settings['qiniu_secret_key']
    rets, err = qiniu.rs.Client().batch_delete(path)
    if not [ret['code'] for ret in rets] == [200, 200]:
        sys.stderr.write('error: %s ' % "删除失败")


class HomeHandler(DataBase):

    def get(self):
        p = self.get_argument('p', 1)
        p = int(p)
        number = self.database.query("select count(*) from files")
        total = int(number[0]['count(*)'])
        detail = None
        if total == 0:
            self.redirect("/file")
            return
        elif p > 0:
            paginator = Paginator()
            page_size = 10  # 每页显示10条信息
            pages, next, previous = paginator.page_renders(
                page=p, page_size=page_size, total=total)
            files = self.database.query("SELECT * FROM files ORDER BY published DESC "
                                        "LIMIT %s, %s", (p - 1) * page_size, p * page_size)
            self.render("files.html", files=files, pages=pages,
                        next=next, previous=previous, page=p, detail=detail)


class UploadFileHandler(DataBase):

    def get(self):
        self.render("uploadfile.html")

    def post(self):
        file_title = self.get_argument("file_title", None)
        file_title = unicode(file_title)  # 文件题目
        qiniu.conf.ACCESS_KEY = self.settings['qiniu_access_key']
        qiniu.conf.SECRET_KEY = self.settings['qiniu_secret_key']
        bucket = self.settings['qiniu_policy']
        tokenObj = qiniu.rs.PutPolicy(bucket)
        extra = qiniu.io.PutExtra()
        extra.mime_type = "application/octet-stream"

        file_metas = self.request.files['file'][0]  # 提取表单中'name'为'file'的文件元数据
        filename = file_metas['filename']
        filename = unicode(filename)  # 文件名
        file = file_metas['body']
        upload_token = tokenObj.token()
        ret, err = qiniu.io.put(upload_token, filename, file, extra)
        if err is not None:
            self.write('error: ' + err)
        else:
            file_exist = self.database.query(
                "SELECT * from files WHERE file_hash=%s", ret['hash'])
            if file_exist:
                self.render('files.html', files=file_exist, pages=None,
                            next=None, previous=None, page=None, detail='对不起,文件已存在或文档为0字节')
            else:
                t = datetime.datetime.now()
                mktime = time.mktime(t.timetuple())  # 把当前时间转换成Epoch秒数
                self.database.execute(
                    "INSERT INTO files (bucket,file_title,file_name,mktime,file_hash,"
                    "published) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                    bucket, file_title, ret['key'], mktime, ret['hash'])
                self.redirect('/')


def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    tornado.ioloop.PeriodicCallback(del_cron, period).start()   # 附加一个定时删除的任务
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
