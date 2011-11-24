#!/usr/bin/env python2.7
#
# SBMLCleanup converts names to IDs and reset meta-IDs
# - written by Michael Schubert, EMBL-EBI, 2011
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Usage: ./SBMLCleanup <infile> <outfile>
    Parameters are both mandatory but can be identical
    <infile>  : file name to be loaded and cleaned up
    <outfile> : file name to save the cleaned file

Examples:
    ./SBMLCleanup copasi.xml cleaned.xml
    Loads the file copasi.xml, performs standard cleanup operations, and 
    saves the resulting file under the name cleaned.xml.
"""

import sys, re
from libsbml import *


class SBMLCleanup:
    """
    """
    def __init__(self, filename):
        """
        Initialises the class and loads the model from the file name given
        """
        self.doc = SBMLReader().readSBMLFromFile(filename)
        self.model = self.doc.getModel()

    def get(self):
        """
        Returns references to the libSBML document and model classes

        Returns:
        doc -- the libSBML document class reference
        model -- the libSBML model class reference
        """
        return doc, model

    def save(self, filename):
        """
        Saves the currently loaded model under the file name specified
        """
        writeSBMLToFile(self.doc, filename)

    def cleanup(self, general=True, doRound=True, removeAnnotations=False, resetMetaIds=True):
        """
        Main cleanup method

        Takes:
        general -- flag to change the names to IDs for species, compartments, parameters,
            reactions, functions, events, and the formulas therein
        doRound -- flag to round all parameter values to 5 significant digits
        removeAnnotations -- flag to remove all annotations in the model
        resetMetaIds -- flag to reset all meta IDs by ascentding numbers after an underscore
        """
        if doRound:
            for species in self.model.getListOfSpecies():
                conc = "%e" % species.getInitialConcentration()
                species.setInitialConcentration(float(conc))

        if general:
            for species in self.model.getListOfSpecies():
                newId = self.__filterName2Id(species.getName())
                self.changeSpeciesId(species.getId(), newId)

            for comp in self.model.getListOfCompartments():
                newId = self.__filterName2Id(comp.getName())
                self.__changeFormulas(comp.getId(), newId)
                for species in self.model.getListOfSpecies():
                    if species.getCompartment() == comp.getId():
                        species.setCompartment(newId)
                comp.setId(newId)

            for param in self.model.getListOfParameters():
                newId = self.__filterName2Id(param.getName())
                self.changeParameterId(param.getId(), newId)

            for reaction in self.model.getListOfReactions():
                newId = self.__filterName2Id(reaction.getName())
                self.changeReactionId(reaction.getId(), newId)

            for function in self.model.getListOfFunctionDefinitions():
                newId = self.__filterName2Id(function.getName())
                self.__changeFormulas(function.getId(), newId)
                function.setId(newId)

            for evt in self.model.getListOfEvents():
                evt.setId(self.__filterName2Id(evt.getName()))

        if removeAnnotations:
            for elm in self.__getAllElements():
                elm.unsetAnnotation()

        if resetMetaIds:
            for i, elm in enumerate(self.__getAllElements()):
                elm.setMetaId("_" + str(i))

    def __filterName2Id(self, name):
        """
        Filters a given name of an entity to a valid ID string, ie. it removes
        all special characters therein

        Takes:
        name -- the entity name

        Returns:
        name -- the filtered name that can be used as ID
        """
        replace = {"+":"_plus_", "*":"_star", ".":"_", "/":"_", " ":"_"}
        for key, val in replace.items():
            name = name.replace(key, val)
        name = re.sub("[^\w]", "", name)
        if name[0] in "0123456789":
            name = "_" + name
        return name

    def changeCompartmentId(self, old, new):
        """
        Changes the ID of a parameter from old to new and also replaces references
        in the formulas.

        Takes:
        old -- the ID used currently in the model
        new -- the ID by which the old one should be replaced
        """
        curCompartment = self.model.getListOfCompartments().get(old)
        if curCompartment.setId(new) != 0:
            raise AssertionError("ERROR: could not replace " + old + " by " + new)
        self.__changeFormulas(old, new)

    def changeSpeciesId(self, old, new):
        """
        Changes the ID of a parameter from old to new and also replaces references
        in the formulas.

        Takes:
        old -- the ID used currently in the model
        new -- the ID by which the old one should be replaced
        """
        #print "::", original, "-->", modified
        # rename species, except on error
        curSpecies = self.model.getListOfSpecies().get(old)
        if curSpecies.setId(new) != 0:
            raise AssertionError("ERROR: could not replace " + old + " by " + new)

        # modify reaction entries
        for reaction in self.model.getListOfReactions():
            # rename species in all reactions
            for reference in reaction.getReactant(old), \
                    reaction.getProduct(old), \
                    reaction.getModifier(old):
                if reference:
                    reference.setSpecies(new)

        self.__changeFormulas(old, new)

    def changeParameterId(self, old, new):
        """
        Changes the ID of a parameter from old to new and also replaces references
        in the formulas.

        Takes:
        old -- the ID used currently in the model
        new -- the ID by which the old one should be replaced
        """
        curParam = self.model.getListOfParameters().get(old)
        if curParam.setId(new) != 0:
            raise AssertionError("ERROR: could not replace " + old + " by " + new)

        self.__changeFormulas(old, new)

    def changeReactionId(self, old, new):
        """
        Changes the ID of a reaction from old to new

        Takes:
        old -- the ID used currently in the model
        new -- the ID by which the old one should be replaced
        """
        curReaction = self.model.getListOfReactions().get(old)
        if curReaction.setId(new) != 0:
            raise AssertionError("ERROR: could not replace " + old + " by " + new)

    def __changeFormulas(self, old, new):
        """
        Changes the references of entities in formulas from old to new

        Takes:
        old -- the ID used currently in the model
        new -- the ID by which the old one should be replaced
        """
        for reaction in self.model.getListOfReactions():
            self.__replace(reaction.getKineticLaw(), old, new)

        for rule in self.model.getListOfRules():
            self.__replace(rule, old, new)
            if rule.getVariable() == old:
                rule.setVariable(new)

        for asgn in self.model.getListOfInitialAssignments():
            self.__replace(asgn, old, new)
            if asgn.getSymbol() == old:
                asgn.setSymbol(new)

        for evt in self.model.getListOfEvents():
            self.__replace(evt.getTrigger(), old, new)
            for asgn in evt.getListOfEventAssignments():
                if asgn.getVariable() == old:
                    asgn.setVariable(new)
                self.__replace(asgn, old, new)

        for cnst in self.model.getListOfConstraints():
            self.__replace(cnst, old, new)

    def __replace(self, objectWithMathAST, old, new):
        """
        Replaces the occurence of all references to old with references to new entity 
        IDs in the formula of a supplied object that holds a math AST.

        Takes:
        objectWithMathAST -- an object with a math AST, eg. a function or kineticLaw
        old -- the old reference ID
        new -- the new reference ID
        """
        fml = re.sub("(?<!\w)" + old + "(?!\w)", new, formulaToString(objectWithMathAST.getMath()))
        objectWithMathAST.setMath(parseFormula(fml))

    def __getAllElements(self):
        return [self.model] + \
            list(self.model.getListOfSpecies()) + \
            list(self.model.getListOfReactions()) + \
            list(self.model.getListOfParameters()) + \
            list(self.model.getListOfCompartments()) + \
            list(self.model.getListOfFunctionDefinitions()) + \
            list(self.model.getListOfEvents()) + \
            list(self.model.getListOfRules()) + \
            list(self.model.getListOfInitialAssignments()) + \
            list(self.model.getListOfConstraints())


if __name__ == "__main__":
    """
    Makes the script routines accessible to the command-line.
    """
    try:
        infile = sys.argv[1]
        outfile = sys.argv[2]

        tool = SBMLCleanup(infile)
        tool.cleanup(removeAnnotations=True)
        tool.save(outfile)
    except:
        print("Usage: ./SBMLTools <infile> <outfile>")
#    finally:
#        raise

