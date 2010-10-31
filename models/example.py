import sys
from npsgd_model_task import NPSGDModelTask
from npsgd_matlab_task import NPSGDMatlabTask
from npsgd_model_parameters import StringParameter, IntegerParameter, RangeParameter

class ExampleModel(NPSGDMatlabTask): 
    short_name = 'example'
    subtitle   = 'A demo model'

    parameters = [
        StringParameter('test',      description="This a test string"),
        IntegerParameter('graphEnd', description="Graph end point"),
        RangeParameter('ranger',     description="Sample range parameter",\
                rangeStart=400, rangeEnd=700, step=1)
    ]

    matlabScript  = '/home/tdimson/public_html/npsg/npsgd/models/example/example.m'


    def latexBody(self):
        return """
            This is a test of including a figure. 
            \\begin{figure}
            \\caption{A nice looking function}
            \\includegraphics[width=5in]{test_figure}
            \\end{figure}

            \\newpage\\appendix\\section{Parameter List}
            %s
""" % self.latexParameterTable()
