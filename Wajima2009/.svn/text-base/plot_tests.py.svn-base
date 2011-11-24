#!/usr/bin/env python

import os
dir = os.getcwd()
import numpy as np
import matplotlib.pyplot as plt
import pysces

models = [("PT test", "Wajima2009_PTtest.xml", 0, 7), \
    ("aPTT test", "Wajima2009_aPTTtest.xml", 2, 6)]
figure = "Wajima2009_tests.png"

for model in models:
    pysces.PyscesInterfaces.Core2interfaces().convertSBML2PSC(sbmlfile=model[1], sbmldir=dir, pscfile=model[1], pscdir=dir)
    mod = pysces.model(model[1], dir=dir)
    os.chdir(dir)
    
    mod.doSim(end=0.025, points=500)
    x = mod.data_sim.getSpecies()
    x[0] = x[1] # we don't want pre-dilution concentration in the time course plot
    x[0,-1] = 0 # start the time at 0
    x = x.transpose()
    
    data = lambda name: x[mod.data_sim.species_labels.index(name)+1]
    time = mod.data_sim.getTime() * 3600 # we want seconds here, not hours
    plot = lambda species, norm: plt.plot(time, data(species)/max(data(norm))*100)
    
    plt.subplot(221 + model[2]) # rows, cols, num
    pdict = {"Fg":"F", "II":"IIa", "X":"Xa"}
    for key in pdict.keys():
        plot(pdict[key], key)
        plot(key, key)
    
    plt.title(model[0])
    plt.legend(["Fibrinogen", "Fibrin", "Prothrombin", "Thrombin", "Factor X", "Factor Xa"][::-1], loc=model[3]) #FIXME
    plt.xlabel("Time (s)")
    plt.ylabel("% of initial inactive factor conc.")
    
    data = lambda name: mod.data_sim.rules.transpose()[mod.data_sim.rules_labels.index(name)]
    plt.subplot(222 + model[2])
    plt.plot(time, data("Integral_Fibrin")*3600)
    plt.gca().set_yscale("log")
    plt.ylim(0.1, 1e6)
    plt.title(model[0])
    plt.xlabel("Time (s)")
    plt.ylabel("Integral of Fibrin (nmol/l.s)")
    
    coag_y = 1.5e3
    coag_x = time[list(data("Integral_Fibrin")*3600 > coag_y).index(1)]
    plt.plot([0, coag_x, coag_x], [coag_y, coag_y, 0.1], "k--")

plt.savefig(figure)
