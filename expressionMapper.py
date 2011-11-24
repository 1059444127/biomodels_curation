#!/usr/bin/env python2.7
#
# ExpressionMapper automatically annotates SBML rate laws with SBO Ids.
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
Usage: ./expressionMapper -param value
    Parameters should be combined and are
    -load <file>    : file to load lookup dictionary
    -query <idList> : comma-separated list of SBO Ids to query from webservice
    -save <file>    : file to save state of lookup dictionary
    -map <SBML.xml> : filename of SBML file to map
    -out <SBML.xml> : filename to save the mapped result
    -initialise <f> : load a standard set of SBO Ids and save in file f;
                      if used, this needs to be the first and only parameter

Examples:
    ./expressionMapper.py -initialise MAMM.map
    Load a standard set of rate laws, namely all irreversible and reversible
    Mass Action kinetics, and Briggs-Haldane. Save them to the file MAMM.map.

    ./expressionMapper.py -load MAMM.map -map SBML.xml -out SBML.sbo.xml
    Load set of rate laws saved in MAMM.map and assign SBO Terms in the SBML
    file SBML.xml matching these.

    ./expressionMapper.py -query 260,455,387 -map SBML.xml -out SBML.sbo.xml
    Load rate laws for simple competitive inhibition, substrate inhibition,
    and product inhibition, and assign SBO Terms in the file SBML.xml.
    If spaces are used between query Ids, they must be enclosed in quotes.

    ./expressionMapper.py -load MAMM.map -query 260,455,387 -save MAMM.map
    Update the MAMM.map file with simple competitive, substrate and
    product inhibition.
"""

import sys
import itertools
import re
import cPickle as pickle
from libsbml import *
from sympy import Symbol
from xml.etree.ElementTree import ElementTree, fromstring, tostring
from suds.client import Client


class ExpressionMatcher():
    def __init__(self):
        """
        Sets up the needed variables for XML namespaces, webservice client, and SBO Id to content
        dictionary and returns and ExpressionMatcher instance.

        Takes:
        sboIdList -- a list of SBO Ids whose formulas are checked against the rate laws in a
            test SBML file
        """
        self.sbons = "{http://www.biomodels.net/sbo}"
        self.mathns = "{http://www.w3.org/1998/Math/MathML}"
        self.types = ("reactant", "product", "modifier", "parameter")
        # map SBO Term Ids to a primitive data structure of their contents once fetched from server
        self.sboLookup = []
        # also save concentration->participant lookups so we query only once
        self.childLookup = {}

    def load(self, fname):
        """ Loads a rate law lookup dictionary from a given file """
        newLookup = pickle.load(open(fname, "rb"))
        self.sboLookup += newLookup
#        self.sboLookup.update(newLookup) # TODO: fix

    def save(self, fname):
        """ Saves the lookup dictionary of rate laws to the given filename """
        pickle.dump(self.sboLookup, open(fname, "wb"))

    def query(self, sboIdList):
        """ Queries the SBO webservice for Ids """
        client = Client("http://www.ebi.ac.uk/sbo/main/services/SBOQuery?wsdl")
        self.SBO = client.service
        for id in sboIdList:
            self.sboLookup.append(self._sboId2expression(id))

    def addLaw(self, id, expr, termDict):
        """
        Adds a custom rate law to the ExpressionMatcher instance.

        Takes:
        id -- an SBO Id that should be used to annotate the model with
        expr -- a string of the mathematical expression
        termDict -- a dictionary identifier:(type, parameter, participantRole)
        """
        self.sboLookup.append((id, expr, termDict))

    def match(self, testSet, testExpr):
        """
        Public matching function that takes an infix expression of an SBML kinetic law including
        a set that describes the role of the individual terms (reactant, product, modifier) and
        matches this expression to all the ones gotten from the SBO Ids supplied earlier.

        Takes
        testSet -- a tuple of referenced terms and their role in the kinetic law, e.g. reactant,
            product, or modifier.
        testExpr -- an infix expression of the kinetic law with all its terms

        Returns: tuple of
        kineticLaw -- the SBO Id that was successfully mapped
        finalMap -- a dictionary of variable_name -> ("type", concentration, participant_role)
        or None if no mapping was found
        """
        for kineticLaw, refExpr, termDict in self.sboLookup:
            refSet = (set(), set(), set(), set())
            for key, term in termDict.items():
                for t in term[0].split(","):
                    refSet[self.types.index(t)].add(key)

            mapping = self._match(testSet, testExpr, refSet, refExpr) 
            if mapping:
                finalMap = {}
                for key, value in mapping.items():
                    finalMap[value] = termDict[key]
                return kineticLaw, finalMap

        return None

    def _match(self, (Rt,Pt,Mt,Kt), testExpr, (Rr,Pr,Mr,Kr), refExpr):
        """
        Private matching function that takes two expressions (test, defined in the SBML file 
        that should be annotated, and ref, the rate laws gotten from SBO Ids from the 
        webservice). Additionally, the sets describe which parameters are reactants, products,
        modifiers, or parameters. The method returns the mapping that is found, or None
        if it could not be matched to any rate law in the list.

        Takes:
        RPMKt -- reactants, products, modifiers, and parameters of the expression to be tested
        RPMKr -- reactants, products, modifiers, and parameters of the reference expression
        testExpr -- the infix notation of the kinetic law formula, with terms defined in RPMKt
        refExpr -- the formula derived from an SBO term with terms defined in RPMKr

        Returns:
        varMap -- a dictionary mapping reference variables to test variables or None if no valid
            mapping is found
        """
        varMap = {}
        symbolNamespace = {}

        #test for equal amount of tokens with each type, otherwise return None right away
        for test,ref in zip((Rt,Pt,Mt,Kt), (Rr,Pr,Mr,Kr)):
            if len(test) != len(ref):
                return None

        # get all tokens in reference expression
        for token in re.findall("[A-Za-z_]\w*", refExpr):
            symbolNamespace[token] = Symbol(token)

        # subroutine to assign current test permutation to ref vars
        def mapVars(testSymbols, refSymbols):
            for testSymbol, refSymbol in zip(testSymbols, refSymbols):
                symbolNamespace[testSymbol] = symbolNamespace[refSymbol]
                varMap[refSymbol] = testSymbol

        # test for expression equality under permutations
        for r in itertools.permutations(Rt): # most for-loops should degrade
            mapVars(r, Rr)
            for p in itertools.permutations(Pt): # or constist of very few items
                mapVars(p, Pr)
                for m in itertools.permutations(Mt):
                    mapVars(m, Mr)
                    for k in itertools.permutations(Kt):
                        mapVars(k, Kr)
                   #    assert(eval(testExpr + "==" + testExpr, symbolNamespace)) # debug
                   #    assert(eval(refExpr + "==" + refExpr, symbolNamespace)) # debug
                        if eval(testExpr + "==" + refExpr, symbolNamespace):
                            return varMap

        return None

    def _sboId2expression(self, id):
        """
        Using an SBO Id, queries the SBO webservice to get the Term in XML format. From that, find all
        variables names used in the formula and their corresponding SBO Ids. Look up the parameter
        meaning (e.g. concentration) and participant role from self._getRole() as a tuple and
        save it in termDict with the original Id is key.

        Takes:
        id -- an integer SBO Id

        Returns:
        expr -- the mathematical expression contained in the term with corresponding Id
        termDict -- a dictionary linking the SBO Id used for the query to the participant
            type, type id, and role (see _getRole() for details)
        """
        # root nodes for compartments, reactants, products, modifiers, and constants
        termDict = {}

        # get term definition from SBO webservice
        xml = fromstring(self.SBO.getStringTermById(id))

        # get math part and convert it to infix
        math = xml.find(self.mathns + "math")
        fd = FunctionDefinition(2, 4)
        fd.setMath(readMathMLFromString(tostring(math)))
        expr = formulaToString(fd.getBody())
        expr = expr.replace("()", "") # fix for k() in mass-action (bug in libSBML?)

        # look through all variables defined in sbo term formula
        for var in math.findall("*//" + self.mathns + "bvar/" + self.mathns + "ci"):
            sboid = int(re.search("[0-9]+$", var.attrib["definitionURL"]).group(0))
            termDict[var.text] = self._getRole(sboid)
            
        return id, expr, termDict

    def _getRole(self, childId):
        """
        Gets additional information from an SBO Id referenced in a rate law. This is needed in order
        to know if the referenced concentration or parameter has the participant role a substrate, 
        product, modifier, or parameter. From this information a tuple is contructed that is then 
        returned for further processing. This method assumes that the role is referenced in the 
        defstr of the concentration and will fail if it is not.

        Takes:
        childId -- the SBO Id referenced in the kinetic law (e.g. substrate concentration)

        Returns: tuple of
        type -- a string describing on whether the current SBO term is a "reactant", "product", 
            "modifier", or "parameter"; this can contain multiple, comma-separated values
        childId -- the SBO Id of the parameter, e.g. substrate/enzyme concentration, or quantitative parameter
        childRole -- the SBO Id of the parameter role, e.g. substrate/enzyme, or quantitative parameter
        """
        parameterRoots = (509, 512, 518, 2) # entities: concentrations of (reactant, product, modifier), parameter
        participantRoleRoots = (10, 11, 19) # references: r, p, m; mainly for debugging
        childRole = childId # role = id when there is no extra role

        for num, param in enumerate(parameterRoots):
            if childId == param or self.SBO.isChildOf(childId, param):
                if num < 3: # do derived lookup
                    childxml = fromstring(self.SBO.getStringTermById(childId))
                    defstr = childxml.find(self.sbons + "def/" + self.sbons + "defstr").text
                    childRole = int(re.search("(?<=SBO:)[0-9]+", defstr).group(0))
                    assert(childRole == participantRoleRoots[num] or \
                        self.SBO.isChildOf(childRole, participantRoleRoots[num]))
                break #TODO: this probably needs rewriting for multiple references

        return (self.types[num], childId, childRole)

    def resolveFunction(self, lawExpr, function):
        """
        Applies a function to an infix expression and returns the expression with the function
        applied. E.g., when the lawExpr is "2 * function_x(x, y)" and the function_x(a,b) = "a * b"
        it yields "2 * x * y"

        Takes:
        lawExpr -- the infix expression of a kinetic law that calls a function
        function -- the object of the function that should be applied

        Returns:
        expr -- a mathematical expression where the function has been applied to the original one
        """
        # replace function calls by their actual math (regex madness!)
        for expr in re.findall("(?<=" + function.getId() + "\()[^)]+", lawExpr):
            klmath, klbody = KineticLaw(2, 4), KineticLaw(2, 4)
            klmath.setMath(function.getMath())
            klbody.setMath(function.getBody())
            functionVars = klmath.getFormula().replace(", " + klbody.getFormula(), "")
            functionVars = re.search("(?<=lambda\()[^)]+", functionVars).group(0).split(", ")
            newFunctionFormula = klbody.getFormula()
            for repl, orig in zip(expr.split(", "), functionVars):
                newFunctionFormula = re.sub("(?<!\w)" + orig + "(?!\w)", repl, newFunctionFormula)
            lawExpr = lawExpr.replace(function.getId() + "(" + expr + ")", newFunctionFormula)
        # return resolved expression
        return lawExpr


def simpletest():
    """
    Tests the expression mapper by mapping the Briggs-Haldane rate law to a given expression 
    and prints out the result.
    """
    testSet = (set(["substrate"]), set(), set(["enzyme"]), set(["kcat", "km"])) # reactants, products, modifiers, params
    testExpr = "kcat * enzyme * substrate / (km + substrate)"
    refLaws = [31]
    em = ExpressionMatcher()
    em.query(refLaws)
    varMap = em.match(testSet, testExpr)
    print "Matching '", testExpr, "' to Briggs-Haldane", refLaws, "; resulting mapping:"
    print varMap

def annotateSBML(model, em):
    """
    General function to annotate a model using an instantiated ExpressionMapper class with all 
    the formulas of rate laws it holds. It goes through all reactions, resolves function
    calls and thereby constructs a mathematical expression that can be compared to the ones defined
    in SBO. Compartments are disregarded (set to "1" in the formula as they are multiplied with the
    rest to yield a rate law for the number of species instead of concentrations).
    It does not annotate functions themselves as they do not define the participant roles of the
    given parameters and could be used in a variety of contexts, e.g. a Michaelis-Menten function
    could be used for any rectangular parabola.

    Takes:
    model -- a libsbml model object that is updated with SBOTerms
    em -- an ExpressionMapper instance
    """
    # get list of compartments and functions for formula replacements
    compartments = model.getListOfCompartments()
    functions = model.getListOfFunctionDefinitions()

    for reaction in model.getListOfReactions():
        law = reaction.getKineticLaw()
        testExpr = law.getFormula()

        # as we are not interested in compartments when matching formulas, replace all occurences by "1"
        for c in compartments:
            testExpr = testExpr.replace(c.getId(), "1")

        # replace function calls by their actual math
        for f in functions:
            testExpr = em.resolveFunction(testExpr, f)

        # get all variables that are referenced in the final formula
        inFormula = set(re.findall("[A-Za-z_]\w*", testExpr))

        # create a list of participant sets (reactants, products, modifiers, parameters)
        reactionRPM = reaction.getListOfReactants, reaction.getListOfProducts, reaction.getListOfModifiers
        testSet = []
        for func in reactionRPM:
            testSet.append(set([elm.getSpecies() for elm in func()]) & inFormula)
        testSet.append(inFormula ^ (testSet[0] | testSet[1] | testSet[2]))

        # do matching
        result = em.match(testSet, testExpr)
#        print reaction.getName(), result
        if result == None: 
            # warn if no match obtained
            print "*** WARN: *** Could not map:", reaction.getId(), testExpr, testSet
        else:
            # otherwise, set corresponding SBO term to rate law...
            law.setSBOTerm(result[0])
            # ...and reactants, products, modifers, and...
            for identifier, (type, conc, role) in result[1].items():
                for currentType, method in zip(("reactant", "product", "modifier"), reactionRPM):
                    for elm in method():
                        if elm.getSpecies() == identifier and currentType in type:
                            elm.setSBOTerm(role)
                # ...parameters.
                if "parameter" in type:
                    param = law.getParameter(identifier) # getLocalParameter()?
                    if param == None:
                        oldTerm = model.getParameter(identifier).getSBOTerm()
                        if oldTerm != -1 and oldTerm != role:
                            print "*** WARN: *** overwriting", oldTerm, "with", role # not sure if it should get LCA here
                        model.getParameter(identifier).setSBOTerm(role)
                    else:
                        param.setSBOTerm(role)

        # for all reactants, products, modifiers that were not mapped use generic terms
        for term, method in zip((10,11,19), reactionRPM): # (10,11,19) are general SBOTerms for (reac,prod,mod)
            for elm in method():
                if elm.getSBOTerm() == -1:
                    elm.setSBOTerm(term)

if __name__ == "__main__":
    """
    Makes the script routines accessible to the command-line via the annotateSBML() function.
    """
    em = ExpressionMatcher()

    try:
        if sys.argv[1] == "-test":
            simpletest()
            sys.exit(0)

        params = {'-load':[], '-query':[], '-save':[], '-map':[], '-out':[]}
        if len(sys.argv) < 3:
            raise AssertionError

        if sys.argv[1] == "-initialise":
            # TODO: add all custom terms that you want to use here
            # michaelis-menten w/ briggs-haldane appx (NLN's definition)
            em.addLaw(28, "kcat * E * S / (Km + S)", { \
                "kcat" : ("parameter", 25, 25), \
                "E" : ("modifier", 524, 461), \
                "S" : ("reactant", 509, 10), \
                "Km" : ("parameter", 371, 371)})
            # michaelis-menten with vmax instead of kcat
            em.addLaw(28, "Vmax * S / (Km + S)", { \
                "Vmax" : ("parameter", 324, 324), \
                "S" : ("reactant", 509, 10), \
                "Km" : ("parameter", 371, 371)})
            # mass action with constant in denominator
            em.addLaw(28, "R1 * R2 / c", { \
                "R1" : ("reactant", 509, 10), \
                "R2" : ("reactant", 509, 10), \
                "c" : ("parameter", 36, 36)})
            # enzymatic rate law with Km + E in denominator
            em.addLaw(28, "kcat * E * S / (Km + E)", { \
                "kcat" : ("parameter", 25, 25), \
                "E" : ("modifier", 524, 461), \
                "S" : ("reactant", 509, 10), \
                "Km" : ("parameter", 371, 371)})
            # mass action with modifier -> A; B
            em.addLaw(49, "k * M", { \
                "k" : ("parameter", 35, 35), \
                "M" : ("modifier", 524, 461)})
            # mass action with modifier A+B -> A+C
            em.addLaw(45, "k * M * R", { \
                "R" : ("reactant", 509, 10), \
                "M" : ("reactant,product", 524, 461), \
                "k" : ("parameter", 36, 36)})
            # all mass action
            params['-query'].append("""47, 70, 72, 73, 75, 76, 77,
                                       49, 79, 80, 82, 83, 85, 86, 87,
                                       52, 90, 91, 93, 94, 96, 97, 98,
                                       54, 100, 101, 103, 104, 106, 107, 108,
                                       57, 131, 132, 134, 135, 137, 138, 139,
                                       59, 111, 112, 114, 115, 117, 118, 119,
                                       61, 121, 122, 124, 125, 127, 128, 129""")
            params['-save'].append(sys.argv[2])
        else:
            for i in range(1, len(sys.argv), 2):
                params[sys.argv[i]].append(sys.argv[i+1])
    except Exception:
        print __doc__
        sys.exit(1)

    for load in params['-load']:
        em.load(load)
    for query in params['-query']:
        em.query([int(id.strip()) for id in query.split(",")])
    for save in params['-save']:
        em.save(save)
    for map in params['-map']:
        doc = SBMLReader().readSBMLFromFile(map)
        model = doc.getModel()
        annotateSBML(model, em)
    for out in params['-out']:
        writeSBMLToFile(doc, out)

