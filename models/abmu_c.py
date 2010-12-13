import os
import sys
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from npsgd.standalone_task import StandaloneTask 
from npsgd.model_parameters import StringParameter, IntegerParameter, RangeParameter, FloatParameter

class ABMU(StandaloneTask): 
    short_name = 'abmu_c'
    full_name  = 'ABM-U'
    subtitle='Algorithmic BDF Model Unifacial'
    parameters = [
            IntegerParameter('nSamples', description="Number of Samples", 
                rangeStart=1000, rangeEnd=100000, step=1),
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
            FloatParameter('cuticleUndulationsAspectRatio', description="Cuticle Undulations Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5),
            FloatParameter('epidermisCellCapsAspectRatio', description="Epidermis Cell Caps Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5),
            FloatParameter('spongyCellCapsAspectRatio', description="Spongy Cell Caps Aspect Ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5)
    ]

    attachments   = ['spectral_distribution.csv', 'reflectance.png', 'transmittance.png', 'absorptance.png']

    executable = "/home/tdimson/public_html/npsg/abmb_abmu_cpp/abmu"

    def executableParameters(self):
        return [
            "-d", os.path.join(os.path.dirname(self.executable), "data"),
            "-n", str(self.nSamples.value),
            "-p", str(self.angleOfIncidence.value),
            "-s", str(5), #step
            "-w", str(self.wavelengths.value[0]),
            "-e", str(self.wavelengths.value[1]),
            "sample.json",
            "spectral_distribution.csv"
        ]

    def prepareExecution(self):
        with open(os.path.join(self.workingDirectory, "sample.json"), 'w') as f:
            f.write(json.dumps({
                "wholeLeafThickness": self.wholeLeafThickness.value,
                "cuticleUndulationsAspectRatio": self.cuticleUndulationsAspectRatio.value,
                "epidermisCellCapsAspectRatio": self.epidermisCellCapsAspectRatio.value,
                "spongyCellCapsAspectRatio": self.spongyCellCapsAspectRatio.value,
                "palisadeCellCapsAspectRatio": 0.0,
                "linginConcentration": self.linginConcentration.value,
                "proteinConcentration": self.proteinConcentration.value,
                "celluloseConcentration": self.celluloseConcentration.value,
                "chlorophyllAConcentration": self.chlorophyllAConcentration.value,
                "chlorophyllBConcentration": self.chlorophyllBConcentration.value,
                "carotenoidConcentration": self.carotenoidConcentration.value,
                "mesophyllFraction": self.mesophyllPercentage.value / 100
            }))

    def prepareGraphs(self):
        wavelengths, reflectance, transmittance, absorptance = ([], [], [], [])

        with open(os.path.join(self.workingDirectory, "spectral_distribution.csv"), 'r') as f:
            spectralReader = csv.reader(f)
            headers = [e.strip() for e in spectralReader.next()]
            wIndex = headers.index("wavelength")
            rIndex = headers.index("reflectance")
            tIndex = headers.index("transmittance")
            aIndex = headers.index("absorptance")

            for row in spectralReader:
                wavelengths.append(float(row[wIndex]))
                reflectance.append(float(row[rIndex]))
                transmittance.append(float(row[tIndex]))
                absorptance.append(float(row[aIndex]))
        
        plt.clf()
        plt.plot(wavelengths, [e*100 for e in reflectance])
        plt.title("Reflectance of Sample")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Reflectance (%)")
        plt.savefig(os.path.join(self.workingDirectory, "reflectance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "reflectance.png"))
        plt.clf()

        plt.plot(wavelengths, [e*100 for e in transmittance])
        plt.title("Transmittance of Sample")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Transmittance (%)")
        plt.savefig(os.path.join(self.workingDirectory, "transmittance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "transmittance.png"))
        plt.clf()

        plt.plot(wavelengths, [e*100 for e in absorptance])
        plt.title("Absorptance of Sample")
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Absorptance (%)")
        plt.savefig(os.path.join(self.workingDirectory, "absorptance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "absorptance.png"))
        plt.clf()


    def latexBody(self):
        return r"""
            This is the results of your model run of \textbf{ABM-U} for the 
            Natural Phenomenon Simulation Group (NPSG) at University of Waterloo.

            Reflectance, transmittance and absorptance curves will appear below followed
            by an appendix containing input parameters. 

            For more information on ABM-U, view \url{http://www.npsg.uwaterloo.ca/resources/docs/rse2006.pdf}. Thank you for trying out the model!

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
            %s
""" % self.latexParameterTable()
