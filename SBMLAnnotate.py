#!/usr/bin/env python2.7

from numpy import loadtxt, dtype
from libsbml import *
from copy import deepcopy
import re


class SBMLAnnotate:
    def __init__(self, filename):
        """
        loads sbml file, sets up some class variables
        """
        self.doc = SBMLReader().readSBMLFromFile(filename)
        self.model = self.doc.getModel()
        self.complexSeparator = "_"

        # CV types:
        self.parser = RDFAnnotationParser()
        self.bqbLookup = { "is" :  BQB_IS, "hasPart" : BQB_HAS_PART, 
            "isPartOf" : BQB_IS_PART_OF, "isVersionOf" : BQB_IS_VERSION_OF, 
            "hasVersion" : BQB_HAS_VERSION, "isHomologTo" : BQB_IS_HOMOLOG_TO, 
            "isDescribedBy" : BQB_IS_DESCRIBED_BY, "isEncodedBy" : BQB_IS_ENCODED_BY, 
            "encodes" : BQB_ENCODES, "occursIn" : BQB_OCCURS_IN, 
            "hasProperty" : BQB_HAS_PROPERTY, "isPropertyOf" : BQB_IS_PROPERTY_OF }

    def get(self):
        """
        returns sbml document and model objects
        """
        return doc, model

    def save(self, filename):
        """
        saves the sbml file to filename
        """
        writeSBMLToFile(self.doc, filename)

    def _combineQualifiers(self, q1, q2):
        """
        combines 2 qualifiers to yield a third one
        """
        if q1 == "is":
            return q2
        elif q2 == "is":
            return q1
        elif q1 == q2:
            return q1
        elif (q1 == "is" and q2 == "hasPart") or (q1 == "hasPart" and q2 == "is"):
            return "hasPart"
        elif (q1 == "isVersionOf" and q2 == "hasPart") or (q1 == "hasPart" and q2 == "isVersionOf"):
            return "hasPart"
        else:
            print "WARN: can't combine qualifiers:", q1, q2

    def _modifyQualifier(self, q):
        """
        given a qualifier, returns the modified version of it
        """
        if q == "is":
            return "isVersionOf"
        if q == "hasPart":
            return "hasVersion"
        else:
            print "WARN: no modification for qualifier:", q

    def annotateSpecies(self, specFile, modFile, complex=None):
        """
        main annotation method
        """
        specAnn = self._loadSpeciesFile(specFile)
        modAnn, idAnn = self._loadModificationFile(modFile)
        modSpecAnn = self._complementAnnotationList(specAnn, modAnn)

        def getMatchingTuples(sname):
            matches = []
            for ann in modSpecAnn:
                name, qual, urn = ann
                if self._equalsWithIdentities(idAnn, name, sname):
                    matches.append([qual, urn])
            return matches

        # annotate complexes and identities simultaneously (to not get n! annotations)
        for species in self.model.getListOfSpecies():
            sname = species.getName()
            matches = getMatchingTuples(sname)
            if complex in sname:
                subnames = sname.split(complex)
                for name in subnames:
                    for match in getMatchingTuples(name):
                        if match[1] not in [m[1] for m in matches]: # only if not annotated already w/ the same urn
                            matches.append(["hasPart"] + [match[1]])
            self._setCVTerms(species, matches)

        self.annotateReactions(modAnn)

    def annotateReactions(self, annList):
        """
        annotates reactions using the annotation list from the mod/reaction file
        """
        pass # call eqWithIds here # TODO
        # if reactant, product match r/p: set cv term
        # check for complex formation

    def _setCVTerms(self, sbobject, termList):
        """
        creates a cv term object and assigns it to the sbml object given
        """
        if termList:
            for terms in termList:
                qualifier, urns = terms[0], terms[1:]
                cv = CVTerm(BIOLOGICAL_QUALIFIER)
                cv.setBiologicalQualifierType(self.bqbLookup[qualifier])
                for urn in urns:
                    cv.addResource(urn)
                sbobject.addCVTerm(cv)#, newBag=True) # not supported by libsbml version at compneur
        else:
            print "*** WARN: *** Could not annotate", sbobject.getName()

    def _equalsWithIdentities(self, idList, name1, name2):
        """
        tests if 2 names are equal given the identity rules
        """
        for expr1, expr2 in idList:
            for n1, n2 in [(name1, name2), (name2, name1)]:
                if re.sub(expr1, expr2, n1) == n2:
                    return True
        return False

    def _complementAnnotationList(self, modSpecAnn, modAnn):
        """
        takes the speciesAnnotation list and applies modification rules to it
        returns the resulting list
        """
        for ma in modAnn:
            for sa in modSpecAnn:
                curSpec = deepcopy(sa)
                curAnn = deepcopy(ma)
                result = re.search(str(curAnn[0]), str(curSpec[0]))
                if result and result.group(0) == curSpec[0]:
                    curSpec[0] = re.sub(curAnn[0], curAnn[1], curSpec[0])
                    if curAnn[2] == "modification":
                        curSpec[1] = self._combineQualifiers(sa[1], "isVersionOf")
                        modSpecAnn.append(curSpec)
                    elif curAnn[2].startswith("addition"):
                        curSpec[1] = "hasPart"
                        modSpecAnn.append(sa)
                        for part in curAnn[2].split(";")[1:]:
                            curSpec[1:3] = ["hasPart", part]
                            modSpecAnn.append(curSpec)
                    elif curAnn[2].startswith("transport"):
                        modSpecAnn.append(curSpec) # for now, don't annotate transports
        return modSpecAnn

    def _loadSpeciesFile(self, fname):
        """
        parses the species annotation file into a list object
        """
        raw = loadtxt(fname, dtype=dtype("str"))
        speciesIds = set([s[0] for s in raw])
        speciesAnn = []
        for id, qualifier, uri in raw:
            if uri not in speciesIds:
                speciesAnn.append([id, qualifier, uri])
            else:
                for refId, refQualifier, refUri in raw:
                    if uri == refId:
                        newQualifier = self._combineQualifiers(qualifier, refQualifier)
                        if newQualifier != None:
                            speciesAnn.append([id, newQualifier, refUri])
        return speciesAnn

    def _loadModificationFile(self, fname):
        """
        parses the mod/reaction annotation file into a list object
        """
        raw = loadtxt(fname, dtype=dtype("str"), delimiter="\t")
        mods, ids = [], []
        for line in raw:
            if line[2] == "identity":
                ids.append(line[0:2].tolist())
            else:
                mods.append(line.tolist())
        return mods, ids


if __name__ == "__main__":
    ann = SBMLAnnotate(sys.argv[1])
    ann.annotateSpecies(sys.argv[2], sys.argv[3], complex="_")
    ann.save(sys.argv[4])

