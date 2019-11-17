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

from db import get_url, insert_url,get_count,increment_url,get_list_urls
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

        self.url_map = Map( # ROUTING
            [
                Rule("/", endpoint="home"),
                Rule("/new_url", endpoint="new_url"),
                Rule('/<short_id>/details',endpoint='short_link_details'),
                Rule('/<short_id>',endpoint='follow_short_link'),
                Rule('/list',endpoint='list_url'),
                Rule('/logout',endpoint='logout')
            ]
        )

    def on_logout(self, request):
        """logout user"""
        return Response("You was logout from Shortly",status=401)

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
        # LOGIN AND PASSWORD HERE
        if request.authorization and request.authorization.username == 'user' and request.authorization.password == '1234':
            response = self.dispatch_request(request)
            
        else:
            response = self.auth_required(request)
        return response(environ, start_response)

    def on_home(self, request):
        return self.render_template("homepage.html")

    def on_new_url(self, request):

        error = None
        url = ''

        if request.method == 'POST':
            url = request.form['url']

            if(is_valid_url(url) == False):
                error = 'Not valid url'
            else:           
                id = insert_url(self.redis,url)
                return redirect('%s'%id)

        return self.render_template("new_url.html", error=error, url=url)


    def auth_required(self, request):
        """asks user his username and password"""
        return Response(
            "Invalid password or login",
            401,
            {"WWW-Authenticate": 'Basic realm="login required"'},
        )

    def on_follow_short_link(self, request, short_id):

        url = get_url(self.redis,short_id)

        if(not url):
            return NotFound()
        
        increment_url(self.redis,short_id)

        link_target = url
        return redirect(link_target)

    def on_short_link_details(self, request, short_id):
        url = get_url(self.redis,short_id)

        if(not url):
            return NotFound()

        click_count = get_count(self.redis,short_id)
        
        return self.render_template(
            "short_link_details.html",
            link_target=url,
            short_id=short_id,
            click_count=click_count,
        )

    def on_list_url(self, request):
        """returns response with list of urls info"""
        return self.render_template(
            "list.html",
            short_ids = get_list_urls(self.redis)
        )

    def error_404(self):
        response = self.render_template("404.html")
        response.status_code = 404
        return response

    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)
