#
# General tool and script paths
#
# COPASI: the Copasi command-line executable
# PYTHON: path to python
# TIDY  : html-tidy will that will be called for xml format
#
# CLEANUP, ANNOTATE, SBO:
#   Path to scripts written for these tasks
#
# VALIDATE: http://sbml.org/Community/Programs/validateSBML.py
#   Printing of warnings was removed
#
BASEDIR := /home/mschu/GitHub/biomodels_curation
COPASI := /usr/bin/CopasiSE
PYTHON := /usr/bin/python2.7
TIDY := /usr/bin/tidy

PYTHONPATH := $(BASEDIR):$(PYTHONPATH)
CLEANUP := $(BASEDIR)/SBMLCleanup.py
ANNOTATE := $(BASEDIR)/SBMLAnnotate.py
SPECIESFILE := $(BASEDIR)/annotateSpecies.txt
REACTIONFILE := $(BASEDIR)/annotateModifications.txt
SBO := $(BASEDIR)/expressionMapper.py
SBOFILE := $(BASEDIR)/MAMM.map
VALIDATE := $(BASEDIR)/validateSBML.py

#
# Get filenames to work on in variables
#   The advantage of a Makefile is that these variables are assigned when
#   needed, which means that we can declare in the root Makefile and they
#   will have the proper values in the branches
#
# FILES: all Copasi files in directory
# SBML: all SBML files if no Copasi files, else derived filenames from .cps
# ANN: annotation file names, derived from SBML names
#
FILES = $(wildcard *.cps)
SBML = $(wildcard *.xml) $(FILES:%.cps=%.xml)
READY = $(SBML:%.xml=%.xml.ready)

#
# Target: all
#
# (1) invoke needed conversion rules for the present files
# (2) plotting goes in visible subdir Makefiles
#
all: plot
	find . -mindepth 1 -type d \( ! -regex '.*/\..*' \) -exec $(MAKE) -C {} \;

#
# Target: clean
#
# (1) remove all .xml.ready files
# (2) remove all generated .xml files
#
clean:
	rm -f $(FILES:%.cps=%.xml)
	find . \( -name "*.ready" -o -name "*.png" \) -type f -exec rm -f {} \;
	find . \( -name "*.pyc" -o -name "*~" \) -exec rm -f {} \;

#
# Target: plot
#
# (1) call implicit conversion rules to prepare files
# (2) find and execute all plot*.py scripts
#
plot: $(READY)
	find . -type f -name 'plot*.py' -exec $(PYTHON) {} \;

# 
# Implicit conversion rule %.cps -> %.xml
#
# (1) for .cps file, use Copasi to convert them to SBML (.xml)
# (2) and for the generated SBML file, call the cleanup script
# (3) fix "time" instead of <csymbol ..> in formulas (this is a cleanup artefact)
#
%.xml: %.cps
	$(COPASI) --SBMLSchema L2V4 -e $@ $^
	$(PYTHON) $(CLEANUP) $@ $@
	sed -i 's|<ci> time </ci>|<csymbol encoding="text" definitionURL="http://www.sbml.org/sbml/symbols/time"> time </csymbol>|' $@

# 
# Implicit conversion rule %.xml -> %.xml.ready
#
# (1) use SBO mapping script
# (2) use annotation script
# (3) format xml
# (4) validate the resulting annotated SBML file
#
%.xml.ready: %.xml
	$(PYTHON) $(SBO) -load $(SBOFILE) -map $^ -out $@
	$(PYTHON) $(ANNOTATE) $@ $(SPECIESFILE) $(REACTIONFILE) $@
	$(TIDY) -m -i -xml -wrap 95 $@
	$(PYTHON) $(VALIDATE) $@
