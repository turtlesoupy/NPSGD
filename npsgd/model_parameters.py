import copy

class ValidationError(RuntimeError): pass

class ModelParameter(object):
    def __init__(self, name):
        self.name = name

    def withValue(self, value):
        """Instantiates a copy of the parameter with a value.
           It may be an idea to rethink this data model later"""

        ret = copy.copy(self)
        ret.setValue(value)
        return ret

    def asDict(self):
        return {
                "name" : self.name,
                "value": self.value
        }

    def fromDict(self, d):
        if d["name"] != self.name:
            raise ValidationError("Trying to instantiate the wrong parameter (called '%s' for '%s')",\
                    self.name, d["name"])

        return self.withValue(d["value"])

    def asMatlabCode(self):
        logging.warning("Unable to convert parameter '%s' to matlab code", self.name)
        return "%s='UNABLE TO CONVERT TO MATLAB';" % self.value

    def asHTML(self):
        return "No HTML for this parameter type"

    def hiddenHTML(self):
        return "No hidden HTML for this parameter type"

    def helpHTML(self):
        if self.helpText:
            img = "<img src='/static/images/question_mark_icon.gif' />"
            return "<a href='#' class='modelParameterHelp' data-helpText='%s'>%s</a>" \
                    % (htmlAttributeEscape(self.helpText), img)
        else:
            return ""

class BooleanParameter(ModelParameter):
    def __init__(self, name, description="", default=False, hidden=False, helpText=""):
        self.name        = name
        self.description = description
        self.units       = ""
        self.default     = default
        self.hidden      = hidden
        self.helpText    = helpText

        self.setValue(self.default)

    def setValue(self, value):
        self.value = bool(value)

    def asMatlabCode(self):
        if self.value:
            return "%s=1" % (self.name)
        else:
            return "%s=0" % (self.name)

    def asTextRow(self):
        return "%s: %s %s" % (self.description, self.value, self.units)

    def asLatexRow(self):
        return "%s & %s %s" % (self.description, latexEscape(self.valueString()), latexEscape(self.units))

    def valueString(self):
        return str(self.value)

    def hiddenHTML(self):
        return "<tr><td></td><td><input type='hidden' name='%s' value='%s' /></td></tr>" % (self.name, self.valueString())

    def asHTML(self):
        if self.hidden:
            return self.hiddenHTML()

        if self.value:
            checkedString = "checked='checked'"
        else:
            checkedString = ""

        return "<tr><td><label for='%s'>%s</label></td><td><input type='checkbox' name='%s' value='%s' %s/> %s</td></tr>" %\
                (self.name, self.description, self.name, self.valueString(), checkedString, self.helpHTML())

class StringParameter(ModelParameter):
    def __init__(self, name, description="", units="", default=None, hidden=False, helpText=""):
        self.name        = name
        self.description = description
        self.units       = units
        self.default     = default 
        self.value       = None
        self.hidden      = hidden
        self.helpText    = helpText
        if default != None:
            self.setValue(self.default)

    def setValue(self, value):
        self.value = str(value)

    def asMatlabCode(self):
        return "%s='%s';" % (self.name, matlabEscape(self.value))

    def asTextRow(self):
        return "%s: %s %s" % (self.description, self.value, self.units)

    def asLatexRow(self):
        return "%s & %s %s" % (self.description, latexEscape(self.valueString()), latexEscape(self.units))

    def valueString(self):
        if self.value == None:
            valueString = ""
        else:
            valueString = str(self.value)

        return valueString

    def hiddenHTML(self):
        return "<tr><td></td><td><input type='hidden' name='%s' value='%s' /></td></tr>" % (self.name, self.valueString())
    
    def asHTML(self):
        if self.hidden:
            return self.hiddenHTML()

        return "<tr><td><label for='%s'>%s</label></td><td><input type='text' name='%s' value='%s'/> %s</td></tr>" %\
                (self.name, self.description, self.name, self.valueString(), self.helpHTML())


class RangeParameter(ModelParameter):
    def __init__(self, name, description="", rangeStart=1.0, rangeEnd=10.0, \
            step=1.0, units="", default=None, hidden=False, helpText=""):
        self.name        = name
        self.description = description
        self.rangeStart  = rangeStart
        self.rangeEnd    = rangeEnd
        self.step        = step
        self.default     = None
        self.units       = units
        self.hidden      = hidden
        self.helpText    = helpText
        self.value = None

        if default != None:
            self.setValue(self.default)

    def setValue(self, value):
        if isinstance(value, basestring):
            start, end = [float(e.strip()) for e in value.split("-")]
        else:
            start, end = map(float, value)

        if start > end:
            raise ValidationError("%s starts after it ends (%s-%s)" % 
                    (self.name, start, end))
            
        if start < self.rangeStart:
            raise ValidationError("%s start value of '%s' less than minimum '%s'" % 
                    (self.name, start, self.rangeStart))

        if end > self.rangeEnd:
            raise ValidationError("%s end value of '%s' greater than maximum '%s'" % 
                    (self.name, end, self.rangeEnd))


        self.value = (start, end)

    def asMatlabCode(self):
        start, end = self.value
        return "%sStart=%s;\n%sEnd=%s;\n%s=%s:%s:%s;" % (self.name, start, self.name, end, self.name, start, self.step, end)

    def asTextRow(self):
        return "%s: %s-%s %s" % (self.description, self.value[0], self.value[1], self.units)

    def asLatexRow(self):
        return "%s & %s-%s %s" % (latexEscape(self.description), self.value[0], self.value[1], latexEscape(self.units))

    def valueString(self):
        if self.value == None:
            valueString = ""
        else:
            valueString = "%s-%s" % (self.value[0], self.value[1])

        return valueString


    def hiddenHTML(self):
        return """
                <tr>
                    <td></td>
                    <td>
                        <input type='hidden' name='%s' value='%s' /> %s
                    </td>
                </tr>
""" % (self.name, self.valueString())


    def asHTML(self):
        if self.hidden:
            return self.hiddenHTML()

        return """
                <tr class="rangeParameter">
                    <td>
                        <label for='%s'>%s</label> 
                    </td>
                    <td>
                        <input type='text' class="npsgdRange" name='%s' value='%s' data-rangeStart='%s' data-rangeEnd='%s' data-step='%s' /> %s %s
                        <div class="slider"></div>
                    </td>
                </tr>
""" % (self.name, self.description, self.name, self.valueString(), self.rangeStart, self.rangeEnd, self.step, self.units, self.helpHTML())

class FloatParameter(ModelParameter):
    def __init__(self, name, description="", rangeStart=None, rangeEnd=None, \
            step=None, units="", default=None, hidden=False, helpText=""):
        self.name        = name
        self.description = description
        self.rangeStart  = rangeStart
        self.rangeEnd    = rangeEnd
        self.step        = step
        self.default     = default
        self.units       = units
        self.value       = None
        self.hidden      = hidden
        self.helpText    = helpText
        self.htmlClassBase = "npsgdFloat"
        if default != None:
            self.setValue(self.default)

    def setValue(self, inVal):
        value = float(inVal)
        
        if self.rangeStart != None and value < self.rangeStart:
            raise ValidationError("%s value (%s) out of range" % 
                    (self.name, value))

        if self.rangeEnd != None and value > self.rangeEnd:
            raise ValidationError("%s value (%s) out of range" % 
                    (self.name, value))

        self.value = value

    def asMatlabCode(self):
        return "%s=%s;" % (self.name, self.value)

    def asTextRow(self):
        return "%s: %s %s" % (self.description, self.value, self.units)

    def asLatexRow(self):
        return "%s & %s %s" % (latexEscape(self.description), self.valueString(), latexEscape(self.units))

    def valueString(self):
        if self.value == None:
            valueString = ""
        else:
            valueString = str(self.value)

        return valueString

    def hiddenHTML(self):
        return "<tr><td></td><td><input type='hidden' name='%s' value='%s'/></td></tr>" \
            % (self.name, self.valueString())

    def asHTML(self):
        if self.hidden:
            return self.hiddenHTML()

        if self.rangeStart != None and self.rangeEnd != None and self.step != None:
            return """
                    <tr class="floatSliderParameter">
                        <td>
                            <label for='%s'>%s</label>
                        </td>
                        <td>
                            <input type='text' class='%sRange' name='%s' value='%s' 
                            data-rangeStart='%s' data-rangeEnd='%s' data-step='%s' /> %s %s
                            <div class="slider"></div>
                        </td>
                    </tr>
    """ % (self.name, self.description, self.htmlClassBase, self.name, self.valueString(), self.rangeStart, self.rangeEnd, self.step, self.units, self.helpHTML())
        else:
            return "<tr><td><label for='%s'>%s</label></td><td><input type='text' class='%s' name='%s' value='%s'/> %s %s</td></tr>" \
                % (self.name, self.description, self.htmlClassBase, self.name, self.valueString(), self.units, self.helpHTML())

class IntegerParameter(FloatParameter):
    def __init__(self, *args, **kwargs):
        FloatParameter.__init__(self, *args, **kwargs)
        self.htmlClassBase = "npsgdInteger"

    def setValue(self, value):
        self.value = int(value)


#Some helpers
def replaceAll(replacee, replaceList):
    for find, replace in replaceList:
        replacee = replacee.replace(find, replace)

    return replacee

def matlabEscape(string):
    return string.replace("'", "\\'")\
            .replace("%", "%%")\
            .replace("\\", "\\\\")

def htmlAttributeEscape(string):
    return string.replace("'", "\\'")

def latexEscape(string):
    return replaceAll(string,
            [("\\",r"\textbackslash "),
             ("<", r"\textless "),
             (">", r"\textgreater "),
             ("~", r"\texasciitilde "),
             ("^", r"\textasciicircum "),
             ("|", r"\docbooktolatexpipe "),
             ("&", r"\&"),
             ("#", r"\#"),
             ("_", r"\_"),
             ("$", r"\$"),
             ("%", r"\%"),
             ("{", r"\{"),
             ("}", r"\}")])
