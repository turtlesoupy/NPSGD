import os
import sys
import csv
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from npsgd.standalone_task import StandaloneTask 
from npsgd.model_parameters import *

class ABMU(StandaloneTask): 
    short_name = 'abmu_c'
    full_name  = 'ABM-U'

    subtitle='Algorithmic BDF Model Unifacial'
    parameters = [
            IntegerParameter('nSamples', description="Number of samples", 
                rangeStart=1000, rangeEnd=100000, step=1, default=10000),
            RangeParameter('wavelengths', description="Wavelengths",
                rangeStart=400, rangeEnd=2500, step=5, units="nm", helpText="Output will generated in steps of 5nm."),
            FloatParameter('angleOfIncidence', description="Incident angle",
                default=8, rangeStart=0, rangeEnd=90, step=0.1, units="degrees"),
            SelectParameter('surfaceOfIncidence', description="Surface of incidence",
                options=["Adaxial", "Abaxial"], default="Abaxial",
                helpText="Adaxial is the top epidermal layer of the leaf, abaxial is the bottom epidermal layer of the leaf."),
            FloatParameter('wholeLeafThickness', description="Leaf thickness",
                default=2.04e-4, units="m"),
            FloatParameter('mesophyllPercentage', description="Mesophyll percentage",
                default=80, units="%", rangeStart=0, rangeEnd=100, step=0.1,
                helpText="Percentage of the total leaf thickness occupied by the mesophyll tissue."),
            FloatParameter('proteinConcentration', description="Protein concentration",
                default=0.05308714, units="g/cm^3", rangeStart=0.0),
            FloatParameter('celluloseConcentration', description="Cellulose concentration",
                default=0.05318708961, units="g/cm^3", rangeStart=0.0),
            FloatParameter('linginConcentration', description="Lingin concentration",
                default=0.006058529380, units="g/cm^3", rangeStart=0.0),
            FloatParameter('chlorophyllAConcentration', description="Chlorophyll A concentration",
                default=0.002895146, units="g/cm^3", rangeStart=0.0),
            FloatParameter('chlorophyllBConcentration', description="Chlorophyll B concentration",
                default=0.00079866, units="g/cm^3", rangeStart=0.0),
            FloatParameter('carotenoidConcentration', description="Carotenoid concentration",
                default=0.000658895, units="g/cm^3", rangeStart=0.0),
            FloatParameter('cuticleUndulationsAspectRatio', description="Cuticle undulations aspect ratio",
                default=10.0, rangeStart=1.0, rangeEnd=50.0, step=0.5,
                helpText="Lower values result in more roughness and a more diffuse behaviour."),
            FloatParameter('epidermisCellCapsAspectRatio', description="Epidermis cell caps aspect ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5,
                helpText="Lower values correspond to more prolate (or rough) cell caps. This results in more diffusion of the propegated light."),
            FloatParameter('spongyCellCapsAspectRatio', description="Spongy cell caps aspect ratio",
                default=5.0, rangeStart=1.0, rangeEnd=50.0, step=0.5,
                helpText="Lower values correspond to more prolate (or rough) cell caps. This results in more diffusion of the propegated light."),
            BooleanParameter('sieveDetourEffects', description="Simulate sieve and detour effects",
                default=True, helpText="To account for the non-homogeneous distribution of pigments (for details, please refer to our related publications).")
    ]

    attachments   = ['spectral_distribution.csv', 'reflectance.png', 'transmittance.png', 'absorptance.png']

    executable = "/home/tdimson/public_html/npsg/abmb_abmu_cpp/abmu"

    def executableParameters(self):
        if self.surfaceOfIncidence.value == "Adaxial":
            angleIn = 180 - self.angleOfIncidence.value
        else:
            angleIn = self.angleOfIncidence.value

        params = [
            "-d", os.path.join(os.path.dirname(self.executable), "data"),
            "-n", str(self.nSamples.value),
            "-p", str(angleIn),
            "-s", str(5), #step
            "-w", str(self.wavelengths.value[0]),
            "-e", str(self.wavelengths.value[1]),
        ]

        if not self.sieveDetourEffects.value:
            params.append("-q")

        params += ["sample.json",
                   "spectral_distribution.csv"
        ]
        
        return params

    def readDataTable(self):
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

        return wavelengths, reflectance, transmittance, absorptance


    def latexDataTable(self):
        wavelengths, reflectance, transmittance, absorptance = self.readDataTable()
        latex = r"""
        \begin{centering}
        \begin{longtable}{l l l l}
        \textbf{Wavelength} & \textbf{Reflectance} & \textbf{Transmittance} & \textbf{Absorptance} \\
        \hline
        \endhead
        %s
        \end{longtable}
        \end{centering}
        """ % "\n".join("%snm & %s & %s & %s\\\\" % (w,r,t,a) for (w,r,t,a) in zip(wavelengths,reflectance, transmittance, absorptance))

        return latex

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
        wavelengths, reflectance, transmittance, absorptance = self.readDataTable()
        axisWavelengthStart = wavelengths[0]
        axisWavelengthEnd   = wavelengths[-1]
        plotCommand = plt.plot
        if len(wavelengths) == 1:
            axisWavelengthStart = wavelengths[0] - 100
            axisWavelengthEnd   = wavelengths[0] + 100
            plotCommand = plt.scatter
    

        plt.clf()
        plotCommand(wavelengths, [e*100 for e in reflectance])
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Reflectance (%)")
        plt.title(self.full_name)
        plt.axis([axisWavelengthStart, axisWavelengthEnd, 0, max(reflectance) * 100 + 5])
        plt.savefig(os.path.join(self.workingDirectory, "reflectance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "reflectance.png"))
        plt.clf()

        plotCommand(wavelengths, [e*100 for e in transmittance])
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Transmittance (%)")
        plt.title(self.full_name)
        plt.axis([axisWavelengthStart, axisWavelengthEnd, 0, max(transmittance) * 100 + 5])
        plt.savefig(os.path.join(self.workingDirectory, "transmittance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "transmittance.png"))
        plt.clf()

        plotCommand(wavelengths, [e*100 for e in absorptance])
        plt.xlabel("Wavelength (nm)")
        plt.ylabel("Absorptance (%)")
        plt.title(self.full_name)
        plt.axis([axisWavelengthStart, axisWavelengthEnd, 0, max(absorptance) * 100 + 5])
        plt.savefig(os.path.join(self.workingDirectory, "absorptance.pdf"))
        plt.savefig(os.path.join(self.workingDirectory, "absorptance.png"))
        plt.clf()


    def latexBody(self):
        return r"""
            These are the results of your model run of \textbf{ABM-U} for the 
            Natural Phenomenon Simulation Group (NPSG) at the University of Waterloo.

            The ABM-U employs an algorithmic Monte Carlo formulation 
            to simulate light interactions with unifacial plant leaves 
            (e.g., corn and sugar cane). More specifically, radiation propagation 
            is treated as a random walk process whose states correspond 
            to the main tissue interfaces found in these leaves. For more
            details about this model, please refer to our related publications~\cite{Ba06,Ba07}. 
            Although the ABM-U provides bidirectional readings,
            directional-hemispherical quantities (provided by our online system) 
            can be obtained by integrating the outgoing light (rays) with respect 
            to the outgoing (collection) 
            hemisphere. Similarly, bihemispherical quantities can be calculated 
            by integrating the BDF (bidirectional scattering distribution function) 
            values with respect to incident and collection hemispheres.

            The provided spectral curves (directional-hemispherical, reflectance,
            transmittance and absorptance) were obtained considering an angle of incidence
            measured with respect to the specimen's normal (zenith). The curves
            were obtained using a virtual spectrophotometer~\cite{Ba01}.
            The researcher interested in BDF
            (bidirectional scattering distribution function)
            plots is referred to a publication describing the implementation of virtual
            goniophotometers~\cite{Kr04}. These publications can be found at:
            \url{http://www.npsg.uwaterloo.ca/pubs/measurement.php}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{reflectance}
            \caption{Directional-hemispherical reflectance}
            \end{centering}
            \end{figure}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{transmittance}
            \caption{Directional-hemispherical transmittance}
            \end{centering}
            \end{figure}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{absorptance}
            \caption{Directional-hemispherical absorptance}
            \end{centering}
            \end{figure}

            \newpage
            \begin{thebibliography}{9}
            \bibitem{Ba01}
            Baranoski,G.V.G.; Rokne,J.G.; Xu,G.
            Virtual spectrophotometric Measurements for biologically and physically-based rendering.
            \textit{The Visual Computer}, Volume 17, Issue 8, pp. 506-518, 2001.

            \bibitem{Ba06}
            Baranoski G.V.G.
            Modeling the interaction of infrared radiation (750 to 2500 nm) with bifacial and unifacial plant leaves.
            \textit{Remote Sensing of Environment}, 100(3):335-347, 2006.

            \bibitem{Ba07}
            Baranoski G.V.G.; Eng D.
            An investigation on sieve and detour effects affecting the interaction of collimated and diffuse infrared radiation (750 to 2500 nm) with plant leaves.
            \textit{IEEE Transactions on Geoscience and Remote Sensing}, 45 (8):2593-2599, 2007.

            \bibitem{Kr04}
            Krishnaswamy,A.; Baranoski,G.V.G.; Rokne,J.G.
            Improving the reliability/cost ratio of goniophotometric comparisons.
            \textit{Journal of Graphics Tools}, Volume 9, Number 3, pp. 1-20, 2004.
            \end{thebibliography}

            \appendix
            \section{Parameter List}
            %s
            \section{Data List}
            %s
""" % (self.latexParameterTable(), self.latexDataTable())
