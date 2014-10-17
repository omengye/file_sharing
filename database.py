# -*- coding: utf-8 -*-
import tornado.web
import math


class DataBase(tornado.web.RequestHandler):

    @property
    def database(self):
        return self.application.database

class Paginator(object):
    def page_renders(self, page, page_size, total):
        if total % page_size == 0:
            pages = int(math.ceil(total / page_size))
        else:
            pages = int(math.ceil(total / page_size)) + 1

        next = page + 1 if page < pages else None
        previous = page - 1 if page > 1 else None

        return  pages, next, previous

