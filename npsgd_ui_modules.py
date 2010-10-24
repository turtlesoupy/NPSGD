import tornado.web

import npsgd_model_parameters

#TODO: make this render from HTML file
class ParameterRenderer(tornado.web.UIModule):
    def render(self, parameter):
        if isinstance(parameter, npsgd_model_parameters.StringParameter):
            return "<label for='%s'>%s</label><input type='text' name='%s'>" % (parameter.name, parameter.description, parameter.name)

        return "Unimplemented parameter type"
