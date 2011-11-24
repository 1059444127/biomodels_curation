#!/usr/bin/env python

from COPASI import *
import numpy as np


class CopasiSimulator:
    def __init__(self, sbmlfile):
        CCopasiRootContainer.init()
        self.dataModel = CCopasiRootContainer.addDatamodel()
        assert CCopasiRootContainer.getDatamodelList().size() == 1
        try:
            self.dataModel.importSBML(sbmlfile)
        except:
            raise IOError("Error while importing model from file \"" + sbmlfile + "\".")
        self.model = self.dataModel.getModel()

#    def reInitialize(self): # this should be in here somehow
#        pass

#TODO: also have get, not only set

    def setParameter(self, initDict): #TODO: to be replaced by setInit(conc, params, localParams)
        metabs = {}
        for i in range(self.model.getModelValues().size()):
            metab = self.model.getModelValue(i)
            metabs[metab.getObjectName()] = metab

        changedObjs = ObjectStdVector()
        for key, value in initDict.iteritems():
            metab = metabs[key]
            metab.setInitialValue(value)
            changedObjs.push_back(metab.getObject(CCopasiObjectName("Reference=InitialValue")))

        self.model.updateInitialValues(changedObjs)

    def setLocalParameter(self, reaction, name, value):
# s.model.getReactions()
# r = s.model.getReaction(i)
# r.getParameters().size()
# r.getParameter(i)
        pass

    def setInitialConcentration(self, initDict):
        metabs = {}
        for i in range(self.model.getMetabolites().size()):
            metab = self.model.getMetabolite(i)
            metabs[metab.getObjectName()] = metab

        changedObjs = ObjectStdVector()
        for key, value in initDict.iteritems():
            metab = metabs[key]
            metab.setInitialConcentration(value)
            changedObjs.push_back(metab.getObject(CCopasiObjectName("Reference=InitialConcentration")))
            # initial volume of compartments: "Reference=InitialVolume",
            # global parameters: "Reference=InitialValue", local: "Reference=Value"

        self.model.updateInitialValues(changedObjs)

    def doTimecourse(self, end=1, steps=10, watch=None):
        # create time course
        trajectoryTask = self.dataModel.getTask("Time-Course")
        if trajectoryTask == None:
            trajectoryTask = CTrajectoryTask()
            self.dataModel.getTaskList().addAndOwn(trajectoryTask)

        # set up parameters
        trajectoryTask.setMethodType(CCopasiMethod.deterministic)
        trajectoryTask.getProblem().setModel(self.model)
        trajectoryTask.setScheduled(True)
        problem = trajectoryTask.getProblem()
        problem.setStepNumber(steps)
        self.model.setInitialTime(0.0)
        problem.setDuration(end)
        method = trajectoryTask.getMethod()
        parameter = method.getParameter("Absolute Tolerance")
        assert parameter.getType() == CCopasiParameter.UDOUBLE
        parameter.setValue(1e-12)

        # run simulation
        try:
            if trajectoryTask.process(True) == False:# or timeSeries.getRecordedSteps() != steps+1:
                raise AssertionError
        except:
            raise RuntimeError("Error running the simulation")

        # return numpy array with data
        timeSeries = trajectoryTask.getTimeSeries()
        fieldNames = timeSeries.getTitles()
        data = {}
        for num, name in enumerate(fieldNames):
            data[name] = np.array(timeSeries.getConcentrationDataForIndex(num))
        return data
