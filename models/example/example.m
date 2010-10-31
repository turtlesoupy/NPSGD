x = rangerStart:1:rangerEnd;
y = x.^2;

plot(x,y)
title('Plot of y = x^2')
print -dpng test_figure
