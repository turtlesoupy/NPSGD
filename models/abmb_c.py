import os
import sys
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from npsgd.standalone_task import StandaloneTask 
from npsgd.model_parameters import StringParameter, IntegerParameter, RangeParameter, FloatParameter
import abmu_c


class ABMB(abmu_c.ABMU): 
    short_name = 'abmb_c'
    full_name  = 'ABM-B'

    subtitle='Algorithmic BDF Model Bifacial'
    parameters = [
            IntegerParameter('nSamples', description="Number of Samples", 
                rangeStart=1000, rangeEnd=100000, step=1, default=10000),
            RangeParameter('wavelengths', description="Wavelengths",
                rangeStart=400, rangeEnd=2500, step=5, units="nm"),
            FloatParameter('angleOfIncidence', description="Incident Angle",
                default=8, rangeStart=0, rangeEnd=360, step=0.1, units="degrees"),
            FloatParameter('wholeLeafThickness', description="Leaf Thickness",
                default=1.66e-4, units="m"),
            FloatParameter('mesophyllPercentage', description="Mesophyll Percentage",
                default=50, units="%", rangeStart=0, rangeEnd=100, step=0.1),
            FloatParameter('proteinConcentration', description="Protein Concentration",
                default=78.059, units="kg/m^3"),
            FloatParameter('celluloseConcentration', description="Cellulose Concentration",
                default=37.7565, units="kg/m^3"),
            FloatParameter('linginConcentration', description="Lingin Concentration",
                default=10.7441, units="kg/m^3"),
            FloatParameter('chlorophyllAConcentration', description="Chlorophyll A Concentration",
                default=3.9775, units="kg/m^3"),
            FloatParameter('chlorophyllBConcentration', description="Chlorophyll B Concentration",
                default=1.1613, units="kg/m^3"),
            FloatParameter('carotenoidConcentration', description="Carotenoid Concentration",
                default=1.1323, units="kg/m^3"),
            FloatParameter('cuticleUndulationsAspectRatio', description="Cuticle Undulations Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5),
            FloatParameter('epidermisCellCapsAspectRatio', description="Epidermis Cell Caps Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5),
            FloatParameter('spongyCellCapsAspectRatio', description="Spongy Cell Caps Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5),
            FloatParameter('palisadeCellCapsAspectRatio', description="Palisade Cell Caps Aspect Ratio",
                default=1.0, rangeStart=1.0, rangeEnd=50.0, step=0.5)
    ]

    attachments   = ['spectral_distribution.csv', 'reflectance.png', 'transmittance.png', 'absorptance.png']

    executable = "/home/tdimson/public_html/npsg/abmb_abmu_cpp/abmb"

    
    def prepareExecution(self):
        with open(os.path.join(self.workingDirectory, "sample.json"), 'w') as f:
            f.write(json.dumps({
                "wholeLeafThickness": self.wholeLeafThickness.value,
                "cuticleUndulationsAspectRatio": self.cuticleUndulationsAspectRatio.value,
                "epidermisCellCapsAspectRatio": self.epidermisCellCapsAspectRatio.value,
                "spongyCellCapsAspectRatio": self.spongyCellCapsAspectRatio.value,
                "palisadeCellCapsAspectRatio": self.palisadeCellCapsAspectRatio.value,
                "linginConcentration": self.linginConcentration.value,
                "proteinConcentration": self.proteinConcentration.value,
                "celluloseConcentration": self.celluloseConcentration.value,
                "chlorophyllAConcentration": self.chlorophyllAConcentration.value,
                "chlorophyllBConcentration": self.chlorophyllBConcentration.value,
                "carotenoidConcentration": self.carotenoidConcentration.value,
                "mesophyllFraction": self.mesophyllPercentage.value / 100
            }))

    def latexBody(self):
        return r"""
            This is the results of your model run of \textbf{ABM-B} for the 
            Natural Phenomenon Simulation Group (NPSG) at University of Waterloo.

            Reflectance, transmittance and absorptance curves will appear below followed
            by an appendix containing input parameters. 

            For more information on ABM-B, view \url{http://www.npsg.uwaterloo.ca/resources/docs/rse2006.pdf}. Thank you for trying out the model!

            \begin{figure}
            \caption{Reflectance Curve}
            \includegraphics[width=5in]{reflectance}
            \end{figure}

            \begin{figure}
            \caption{Transmittance Curve}
            \includegraphics[width=5in]{transmittance}
            \end{figure}

            \begin{figure}
            \caption{Absorptance Curve}
            \includegraphics[width=5in]{absorptance}
            \end{figure}

            \newpage\appendix\section{Parameter List}
            dsds
            %s
""" % self.latexParameterTable()
