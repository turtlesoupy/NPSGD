import copy

class ValidationError(RuntimeError): pass

def replaceAll(replacee, replaceList):
    for find, replace in replaceList:
        replacee = replacee.replace(find, replace)

    return replacee

def matlabEscape(string):
    return string.replace("'", "\\'")\
            .replace("%", "%%")\
            .replace("\\", "\\\\")

def latexEscape(string):
    return replaceAll(string,
            [("<", r"\textless{}"),
             (">", r"\textgreater{}"),
             ("~", r"\texasciitilde{}"),
             ("^", r"\testasciicircum{}"),
             ("&", r"\&"),
             ("#", r"\#"),
             ("_", r"\_"),
             ("$", r"\$"),
             ("%", r"\%"),
             ("|", r"\docbooktolatexpipe{}"),
             ("{", r"\{"),
             ("}", r"\}"),
             ("\\",r"\textbackslash ")])

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



class StringParameter(ModelParameter):
    def __init__(self, name, description=""):
        self.name        = name
        self.description = description

    def setValue(self, value):
        self.value = str(value)

    def asMatlabCode(self):
        return "%s='%s';" % (self.name, matlabEscape(self.value))

    def asLatexRow(self):
        return "%s & %s & %s" % (self.name, self.description, latexEscape(self.value))

class RangeParameter(ModelParameter):
    def __init__(self, name, description="", rangeStart=1.0, rangeEnd=10.0, step=1.0):
        self.name        = name
        self.description = description
        self.rangeStart  = rangeStart
        self.rangeEnd    = rangeEnd
        self.step        = step

    def setValue(self, value):

        if isinstance(value, basestring):
            start, end = [float(e.strip()) for e in value.split("-")]
        else:
            start, end = map(float, value)

        self.value = (start, end)

    def asMatlabCode(self):
        start, end = self.value
        return "%sStart=%s;\n%sEnd=%s;" % (self.name, start, self.name, end)

    def asLatexRow(self):
        return "%s & %s & %s-%s" % (self.name, self.description, self.value[0], self.value[1])

class IntegerParameter(ModelParameter):
    def __init__(self, name, description=""):
        self.name        = name
        self.description = description

    def setValue(self, value):
        self.value = int(value)

    def asMatlabCode(self):
        return "%s=%s;" % (self.name, self.value)

    def asLatexRow(self):
        return "%s & %s & %s" % (self.name, self.description, self.value)
