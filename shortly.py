# -*- coding: utf-8 -*-
"""
    shortly
    ~~~~~~~

    A simple URL shortener using Werkzeug and redis.

    :copyright: 2007 Pallets
    :license: BSD-3-Clause
"""
import os

import redis

from db import get_url, insert_url
from utils import get_hostname, is_valid_url

from jinja2 import Environment
from jinja2 import FileSystemLoader
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound

from werkzeug.routing import Map
from werkzeug.routing import Rule
from werkzeug.utils import redirect
from werkzeug.wrappers import Request
from werkzeug.wrappers import Response


class Shortly(object):
    def __init__(self, config):
        self.redis = redis.Redis(config["redis_host"], config["redis_port"])
        template_path = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(
            loader=FileSystemLoader(template_path), autoescape=True
        )
        self.jinja_env.filters["hostname"] = get_hostname

        self.url_map = Map(
            [
                Rule("/", endpoint="home"),
                # TODO: Добавить ендпоинты на:
                # - создание шортката
                # - редирект по ссылке
                # - детальную информацию о ссылке
            ]
        )

    def render_template(self, template_name, **context):
        t = self.jinja_env.get_template(template_name)
        return Response(t.render(context), mimetype="text/html")

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return getattr(self, "on_" + endpoint)(request, **values)
        except NotFound:
            return self.error_404()
        except HTTPException as e:
            return e

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def on_home(self, request):
        return self.render_template("homepage.html")

    def on_new_url(self, request):
        error = None
        url = ""
        # TODO: Проверить что метод для создания новой ссылки "POST"
        # Проверить валидность ссылки используя is_valid_url
        # Если ссылка верна - создать запись в базе и
        # отправить пользователя на детальную информацию
        # Если неверна - написать ошибку

        return self.render_template("new_url.html", error=error, url=url)

    def on_follow_short_link(self, request, short_id):
        # TODO: Достать из базы запись о ссылке по ее ид (get_url)
        # если такого ид в базе нет то кинуть 404 (NotFount())
        # заинкрементить переход по ссылке (increment_url)
        link_target = "/"
        return redirect(link_target)

    def on_short_link_details(self, request, short_id):
        # TODO: Достать из базы запись о ссылке по ее ид (get_url)
        # если такого ид в базе нет то кинуть 404 (NotFount())
        link_target = "/"

        click_count = 0  # достать из базы кол-во кликов по ссылке (get_count)
        return self.render_template(
            "short_link_details.html",
            link_target=link_target,
            short_id=short_id,
            click_count=click_count,
        )

    def on_list_url(self, request):
        # TODO: ДЗ
        pass

    def error_404(self):
        response = self.render_template("404.html")
        response.status_code = 404
        return response

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
