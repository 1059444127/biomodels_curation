#!/usr/bin/env python

import matplotlib.pyplot as plt
from Copasi import CopasiSimulator

sim = CopasiSimulator("Lee2010_OneForm_reduced.xml")

data = sim.doTimecourse(end=900, steps=250)

names = {"P":"Prothrombin", "T":"Thrombin", "M":"Meizothrombin", "P2":"Prethrombin-2"}
for name, label in names.items():
    plt.plot(data['Time'], data[name], label=label)

plt.legend(loc="center right")
plt.xlabel("Time (sec)")
plt.ylabel("Relative Concentration (uM)")
plt.xlim(0, 900)
plt.ylim(0, 1)
plt.title("Concentration profiles from the averaged data set")

plt.savefig("Lee2010_OneForm_reduced.png")
