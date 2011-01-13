# Author: Thomas Dimson [tdimson@gmail.com]
# Date:   January 2011
# For distribution details, see LICENSE
"""Module containing all modules that are used for Tornado's UI rendering."""

import tornado.web
class ParameterRenderer(tornado.web.UIModule):
    """UI module to render parameter HTML."""

    def render(self, parameter):
        return parameter.asHTML()
