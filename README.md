BioModels curation scripts
==========================

This is a collection of scripts that were used to curate Blood Coagulation
models. Those were taken from various scientific articles and encoded in
the [Systems Biology Markup Language][sbml] (SBML) and subsequently annotated
with identifiers from e.g. [UniProt][uniprot], so that the model entities
could be linked to physical ones. Additionally, one or more figures from the 
original article were reproduced in order to validate the model and its
simulation results.

Note that the models deposited in the [BioModels database][bmdb] will always 
be more complete and up-to-date than the ones provided here. If plan on using 
the models instead of the curation framework, please use them from the database
directly.

All models published in the BioModels database are released without copyright
under a [CC0][cc0] license. The Framework is (c) [EMBL][embl], 2011 but may
be used under the terms of the [GPL][gpl] version 2 or later.

Usage
-----

The sample models are provided either as Copasi or unannotated SBML files.
Using the Make framework, they are transformed into annotated SBML files and
those are plotted using specific plotting scripts. To run, type:

    ./configure
    make

Upon which all model files and figures are created. Note that you can run
`make` in only one subdirectory as well, `configure` needs to be called before,
however.

Requirements
------------

The following software is required to successfully run the curation framework
with the sample models provided:

 * [Python][python]
                - A high-level scripting language that can be used for rapid
                  development and comes a lot of functionality included. Extra
                  libraries required are [NumPy][numpy] (for numerical data 
                  structures), [matplotlib][matplotlib] (for plotting), 
                  [libSBML][libsbml] (for manipulation of SBML files), 
                  [SymPy][sympy] (for matching of kinetic laws to 
                  [SBO terms][sbo]) and [SUDS][suds] (for interacting with the 
                  SBO webservice via [SOAP][soap]).
 * [Coapsi][copasi]
                - An application for simulation and analysis of biochemical
                  networks and their dynamics. It is a stand-alone application 
                  that comes with a command-line (CopasiSE) and GUI (CopasiUI) 
                  version and supports the [SBML][sbml] standard. The program
                  needs to be compiled with Python bindings enabled.
 * [HTML Tidy][tidy]
                - An application to clean up HTML and XML formatting. This
                  tool is used to format the SBML files nicely after 
                  annotation.

Sample models
-------------

In the course of the curation project, about 30 models were curated for the
BioModels database. Some from the following five articles are provided as
sample files for the framework here:

 * K. C. Jones and K. G. Mann. A model for the tissue factor pathway to 
   thrombin. II. a mathematical simulation. Journal of Biological Chemistry, 
   269(37):23367, 1994.
 * M. F. Hockin, K. C. Jones, S. J. Everse, and K. G. Mann. A model for the
   stoichiometric regulation of blood coagulation. Journal of Biological 
   Chemistry, 277(21):18322-18333, 2002.
 * S. D. Bungay, P. A. Gentry, and R. D. Gentry. A mathematical model of lipid-
   mediated thrombin generation. Mathematical Medicine and Biology, 20(1):105-
   129, 2003.
 * T. Wajima, G. K. Isbister, and S. B. Duffull. A comprehensive model for the
   humoral coagulation network in humans. Clinical Pharmacology and 
   Therapeutics, 86(3):290–298, 2009.
 * C. J. Lee, S. Wu, C. Eun, and L. G. Pedersen. A revisit to the one form 
   kinetic model of prothrombinase. Biophysical chemistry, 149(1-2):28–33, 2010.

[sbml]: http://sbml.org/Basic_Introduction_to_SBML
[uniprot]: http://www.uniprot.org/
[embl]: http://www.embl.de/
[bmdb]: http://www.ebi.ac.uk/biomodels-main/
[gpl]: http://www.gnu.org/licenses/gpl.html
[cc0]: http://creativecommons.org/publicdomain/zero/1.0/
[python]: http://python.org/
[copasi]: http://www.copasi.org/tiki-view_articles.php
[tidy]: http://tidy.sourceforge.net/
[numpy]: http://numpy.scipy.org/
[matplotlib]: http://matplotlib.sourceforge.net/
[libsbml]: http://sbml.org/Software/libSBML
[sympy]: http://code.google.com/p/sympy/
[sbo]: http://www.ebi.ac.uk/sbo/main/
[suds]: https://fedorahosted.org/suds/
[soap]: http://de.wikipedia.org/wiki/SOAP
