#!/usr/bin/env python

import numpy as np
import matplotlib.pyplot as plt
from Copasi import CopasiSimulator

sim = CopasiSimulator("Bungay2003.xml")

def dosim(conc, end=500, steps=500, label=None):
    sim.setInitialConcentration({'LIPID' : conc * 4 * 10**2 * np.pi / 0.74})
    data = sim.doTimecourse(end, steps)
    plt.plot(data['Time'], data["IIa_f"], label=label)

# main plot
for conc in [5000, 500, 150, 100, 70, 50]:
    dosim(conc)
plt.xlabel("time (seconds)")
plt.ylabel("Thrombin concentration (nM)")
plt.xlim(0, 500)
plt.ylim(0, 50)
plt.title("The effect of vesicle concentration on the generation of free thrombin")
plt.legend(("5000 nM","500","150","100","70","50"), loc="upper right", bbox_to_anchor=(0.97,0.55))

# inset
a = plt.axes([.61, .61, .25, .25])
plt.title("")
dosim(30, end=1200, steps=1200, label="30")
plt.xlim(750, 1220)
plt.ylim(0, 5)
plt.setp(a, xticks=[750,900,1050,1200], yticks=[0,1,2,3,4,5])
plt.legend()
plt.xlabel("")
plt.ylabel("")

plt.savefig("Bungay2003.png")
