#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import json
import logging
from math import ceil

import tornado.web

from ..const import OK, LOG_NAME, N_POST_PER_PAGE
from ..utils import TemplateRendering


log = logging.getLogger(LOG_NAME)
__all__ = ['BaseHandler']


class BaseHandler(tornado.web.RequestHandler, TemplateRendering):

    def get(self, url=None):
        url = url.strip(' /')
        super().get(url)

    @property
    def db(self):
        return self.application.db

    @property
    def ip(self):
        return self.request.headers.get('X-Real-IP', self.request.remote_ip)

    def write_json(self, *, status=OK, msg='', data={}):
        self.write(json.dumps({
            'status': status,
            'msg': msg,
            'data': data
        }))

    @property
    def is_ajax(self):
        return self.request.headers.get('X-Requested-With') == "XMLHttpRequest"

    @property
    def is_https(self):
        return self.request.headers.get('X-Scheme') == "https"

    def redirect_404(self):
        self.redirect('/404.html')

    def render2(self, template_name, **kwargs):
        """
        This is for making some extra context variables available to
        the template
        """
        def static_url(path):
            prefix = self.settings.get('static_url_prefix')
            return os.path.join(prefix, path)

        kwargs.update({
            'settings': self.settings,
            'static_url': static_url,
            'request': self.request,
            'xsrf_token': self.xsrf_token,
            'xsrf_form_html': self.xsrf_form_html,
            'max': max,
            'min': min,
            'is_ajax': self.is_ajax,
            'is_https': self.is_https,
        })
        content = self.render_template(template_name, **kwargs)
        self.write(content)

    @tornado.gen.coroutine
    def prepare(self):
        super().prepare()
        cursor = self.db.posts.find()
        self.post_count = yield cursor.count()
        self.max_page = ceil(self.post_count / N_POST_PER_PAGE)
        log.debug('prepare for post_count {}, max_page {}'
                  .format(self.post_count, self.max_page))

    def render_post(self, template_name, **kwargs):
        kwargs.update({
            'max_page': self.max_page,
        })
        self.render2(template_name, **kwargs)