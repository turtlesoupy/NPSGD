import sys
from npsgd.model_task  import ModelTask
from npsgd.matlab_task import MatlabTask
from npsgd.model_parameters import StringParameter, IntegerParameter, RangeParameter, FloatParameter

class ABMB(MatlabTask): 
    short_name = 'abmb'
    full_name  = 'ABMB'
    subtitle='Algorithmic BDF Model, Bifacial'
    parameters = [
            IntegerParameter('nSamples', description="Number of Samples", 
                rangeStart=100, rangeEnd=10000, step=1),
            RangeParameter('wavelengths', description="Wavelengths",
                rangeStart=400, rangeEnd=2500, step=5, units="nm"),
            FloatParameter('angleOfIncidence', description="Incident Angle",
                default=8, rangeStart=0, rangeEnd=360, step=0.1, units="degrees"),
            FloatParameter('wholeLeafThickness', description="Leaf Thickness",
                default=2.04e-4, units="m"),
            FloatParameter('mesophyllPercentage', description="Mesophyll Percentage",
                default=80, units="%", rangeStart=0, rangeEnd=100, step=0.1),
            FloatParameter('proteinConcentration', description="Protein Concentration",
                default=53.08714, units="kg/m^3"),
            FloatParameter('celluloseConcentration', description="Cellulose Concentration",
                default=0.0, units="kg/m^3"),
            FloatParameter('linginConcentration', description="Lingin Concentration",
                default=59.245619, units="kg/m^3"),
            FloatParameter('chlorophyllAConcentration', description="Chlorophyll A Concentration",
                default=2.895146, units="kg/m^3"),
            FloatParameter('chlorophyllBConcentration', description="Chlorophyll B Concentration",
                default=0.79866, units="kg/m^3"),
            FloatParameter('carotenoidConcentration', description="Carotenoid Concentration",
                default=0.658895, units="kg/m^3"),
            IntegerParameter('bifacial', description="Hidden bifacial parameter", default=1, hidden=True)
    ]

    attachments   = ['reflectance.txt', 'transmittance.txt', 'absorptance.txt',
            'reflectancecurve.png', 'transmittancecurve.png', 'absorptancecurve.png']

    matlabScript  = '/home/tdimson/public_html/npsg/npsgd/models/abm.m'

    def latexBody(self):
        return """
            This is the results of your model run of \\textbf{ABMB} for the 
            Natural Phenomenon Simulation Group (NPSG) at University of Waterloo.

            Reflectance, transmittance and absorptance curves will appear below followed
            by an appendix containing input parameters. 

            For more information on ABM-B, view \\url{http://www.npsg.uwaterloo.ca/resources/docs/rse2006.pdf}. Thank you for trying out the model!

            \\begin{figure}
            \\caption{Reflectance Curve}
            \\includegraphics[width=5in]{reflectancecurve}
            \\end{figure}

            \\begin{figure}
            \\caption{Transmittance Curve}
            \\includegraphics[width=5in]{transmittancecurve}
            \\end{figure}

            \\begin{figure}
            \\caption{Absorptance Curve}
            \\includegraphics[width=5in]{absorptancecurve}
            \\end{figure}

            \\newpage\\appendix\\section{Parameter List}
            %s
""" % self.latexParameterTable()
