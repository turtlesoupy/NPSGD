from npsgd.matlab_task import MatlabTask
from npsgd.model_parameters import StringParameter, IntegerParameter, RangeParameter, FloatParameter

class ExampleModel(MatlabTask): 
    short_name = 'example'
    subtitle   = 'A demo model'

    parameters = [
        StringParameter('test',      description="This a test string"),
        IntegerParameter('graphEnd', description="Graph end point"),
        RangeParameter('ranger',     description="Sample range parameter",\
                rangeStart=400, rangeEnd=700, step=1),
        FloatParameter('floater', description="Sample Float Parameter", rangeStart=10, rangeEnd=1000, step=1)
    ]

    matlabScript  = '/home/tdimson/public_html/npsg/npsgd/models/example/example.m'

    def latexBody(self):
        return r"""
            This is a test of including a figure. 
            \begin{figure}
            \caption{A nice looking function}
            \includegraphics[width=5in]{test_figure}
            \includegraphics[width=5in]{test_figure2222}
            \end{figure}

            \newpage\appendix\section{Parameter List}
            %s
""" % self.latexParameterTable()
