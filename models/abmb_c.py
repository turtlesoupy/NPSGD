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

            The ABM-B employs an algorithmic Monte Carlo formulation 
            to simulate light interactions with bifacial plant leaves 
            (e.g., soybean and maple). More specifically, radiation propagation 
            is treated as a random walk process whose states correspond 
            to the main tissue interfaces found in these leaves. 
            For more details about this model, please refer to our 
            related publications~\cite{Ba06,Ba07}. Although the ABM-B provides bidirectional readings,
            directional-hemispherical quantities (provided by our online system) 
            can be obtained by integrating 
            the outgoing light (rays) with respect to the outgoing (collection) 
            hemisphere. Similarly, bihemispherical quantities can be calculated 
            by integrating the BDF (bidirectional scattering distribution function) 
            values with respect to incident and collection hemispheres.

            The provided spectral curves (directional-hemispherical 
            reflectance, transmittance and 
            absorptance) were obtained considering light incident on the adaxial 
            surface of the specimens, and angles of incidence measured with 
            respect to the specimens' normal (zenith). The curves  
            were obtained using a virtual spectrophotometer~\cite{Ba01}. 
            The researcher interested in BDF 
            (bidirectional scattering distribution function)
            plots is referred to a publication describing the implementation of virtual
            goniophotometers~\cite{Kr04}. These publications can be found at:
            \url{http://www.npsg.uwaterloo.ca/pubs/measurement.php}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{reflectance}
            \caption{Directional-hemispherical Reflectance}
            \end{centering}
            \end{figure}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{transmittance}
            \caption{Directional-hemispherical Transmittance}
            \end{centering}
            \end{figure}

            \begin{figure}
            \begin{centering}
            \includegraphics[width=5in]{absorptance}
            \caption{Directional-hemispherical Absorptance}
            \end{centering}
            \end{figure}

            \newpage\appendix\section{Parameter List}
            %s

            \begin{thebibliography}{9}
            \bibitem{Ba01}
            Baranoski,G.V.G.; Rokne,J.G.; Xu,G.
            Virtual Spectrophotometric Measurements for Biologically and Physically-Based Rendering
            The Visual Computer, Volume 17, Issue 8, pp. 506-518, 2001.

            \bibitem{Ba06}
            Baranoski G.V.G. 
            Modeling the interaction of infrared radiation (750 to 2500 nm) with bifacial and unifacial plant leaves
            Remote Sensing of Environment, 100(3):335-347, 2006

            \bibitem{Ba07}
            Baranoski G.V.G.; Eng D.
            An investigation on sieve and detour effects affecting the interaction of collimated and diffuse infrared radiation (750 to 2500 nm) with plant leaves 
            IEEE Transactions on Geoscience and Remote Sensing, 45 (8):2593-2599, 2007

            \bibitem{Kr04}
            Krishnaswamy,A.; Baranoski,G.V.G.; Rokne,J.G.
            Improving the Reliability/Cost Ratio of Goniophotometric Comparisons 
            Journal of Graphics Tools, Volume 9, Number 3, pp. 1-20, 2004.
            \end{thebibliography}

""" % self.latexParameterTable()
