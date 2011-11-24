#!/usr/bin/env python

import matplotlib.pyplot as plt
from Copasi import CopasiSimulator

sim = CopasiSimulator("Jones1994.xml")

concs = [5000, 500, 50, 10, 5]
labels = ['5 nM', '500 pM', '50 pM', '10 pM', '5 pM']

for conc, label in zip(concs, labels):
    sim.setInitialConcentration({'TF_VIIa' : conc * 1e-12})
    data = sim.doTimecourse(end=250, steps=250)
    plt.plot(1e6 * data['Time'], 1e6 * (data["IIa"] + 1.2 * data["mIIa"]), label=label)

plt.legend(loc=4)
plt.xlabel("Time (seconds)")
plt.ylabel("IIa+1.2mIIa (uM)")
plt.ylim(0, 1.6)
plt.title("The effect of TF-VIIa concentration")

plt.savefig("Jones1994.png")
