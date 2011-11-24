#!/usr/bin/env python

import matplotlib.pyplot as plt
from Copasi import CopasiSimulator

sim = CopasiSimulator("Hockin2002.xml")

for conc in [25, 20, 15, 10, 5, 1]:
    sim.setInitialConcentration({'TF' : conc * 1e-12})
    data = sim.doTimecourse(end=700, steps=350)
    plt.plot(data['Time'], data['IIa'] + 1.2 * data['mIIa'], label=str(conc) + " pM")

plt.legend(loc=2)
plt.xlabel("Time (sec)")
plt.ylabel("IIa+1.2mIIa (M)")
plt.xlim(0, 700)
plt.ylim(0, 6e-7)
plt.title("Total thrombin for varying TF concentrations")

plt.savefig("Hockin2002.png")
