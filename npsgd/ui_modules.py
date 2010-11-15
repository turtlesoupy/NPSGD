import tornado.web
class ParameterRenderer(tornado.web.UIModule):
    def render(self, parameter):
        return parameter.asHTML()
