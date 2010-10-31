import tornado.web

import npsgd_model_parameters

#TODO: make this render from HTML file
class ParameterRenderer(tornado.web.UIModule):
    def render(self, parameter):
        if isinstance(parameter, npsgd_model_parameters.StringParameter):
            return "<label for='%s'>%s</label><input type='text' name='%s' />" % (parameter.name, parameter.description, parameter.name)
        elif isinstance(parameter, npsgd_model_parameters.IntegerParameter):
            return "<label for='%s'>%s</label><input type='text' name='%s' />" % (parameter.name, parameter.description, parameter.name)
        elif isinstance(parameter, npsgd_model_parameters.RangeParameter):
            return """
                <div class="rangeParameter">
                    <label for='%s'>%s</label>
                    <input type='text' name='%s' />
                    <input type='hidden' class='rangeStart' value='%s' />
                    <input type='hidden' class='rangeEnd' value='%s' />
                    <input type='hidden' class='step' value='%s' />
                    <div class="slider"></div>
                </div>
""" % (parameter.name, parameter.description, parameter.name, parameter.rangeStart, parameter.rangeEnd, parameter.step)

        return "Unimplemented parameter type"
