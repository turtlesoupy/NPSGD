"""Module containing all modules that are used for Tornado's UI rendering."""

import tornado.web
class ParameterRenderer(tornado.web.UIModule):
    """UI module to render parameter HTML."""

    def render(self, parameter):
        return parameter.asHTML()
