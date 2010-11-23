%nSamples
%wavelength
%angleOfIncidence
%wholeLeafThickness
%mesophyllPercentage
%proteinConcentration
%celluloseConcentration
%linginConcentration
%chlorophyllAConcentration
%chlorophyllBConcentration
%carotenoidConcentration
%bifiacial

path('/home/tdimson/public_html/npsg/matlab_plant', path);

sample = abm_sample();
sample.wholeLeafThickness        = wholeLeafThickness;
sample.proteinConcentration      = proteinConcentration;
sample.celluloseConcentration    = celluloseConcentration;
sample.linginConcentration       = linginConcentration;
sample.chlorophyllAConcentration = chlorophyllAConcentration;
sample.chlorophyllBConcentration = chlorophyllBConcentration;
sample.carotenoidConcentration   = carotenoidConcentration;
sample.mesophyllFraction         = mesophyllPercentage / 100;
sample.bifacial                  = bifacial;

for n=1:length(wavelengths)
    fprintf('Wavelength %d\n', wavelengths(n));
    interfaces = build_interfaces(sample, wavelengths(n) * 10^(-9));
    [r,t,a] = ABM(0, angleOfIncidence * pi / 180, interfaces, nSamples);
    reflectance(n)   = r;
    transmittance(n) = t;
    absorptance(n)   = a; 
end

plot(wavelengths, reflectance * 100);
title('Reflectance');
xlabel('Wavelength (nm)');
ylabel('Percentage');
print -dpdf reflectancecurve
print -dpng reflectancecurve

plot(wavelengths, transmittance * 100);
title('Transmittance');
xlabel('Wavelengths (nm)');
ylabel('Percentage');
print -dpdf transmittancecurve
print -dpng transmittancecurve

plot(wavelengths, absorptance * 100);
title('Absorptance');
xlabel('Wavelengths (nm)');
ylabel('Percentage');
print -dpdf absorptancecurve
print -dpng absorptancecurve

reflectanceTrans(:, 1)   = wavelengths * 10^(-9);
transmittanceTrans(:, 1) = wavelengths * 10^(-9);
absorptanceTrans(:, 1)   = wavelengths * 10^(-9);
reflectanceTrans(:,2)    = reflectance';
transmittanceTrans(:,2)  = transmittance';
absorptanceTrans(:,2)    = absorptance';

save('reflectance.txt',   'reflectanceTrans',   '-ASCII');
save('transmittance.txt', 'transmittanceTrans', '-ASCII');
save('absorptance.txt',   'absorptanceTrans',   '-ASCII');
