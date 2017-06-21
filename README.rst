|Build Status| |Coverage Status|

Liasis: Singular Enrichment Analysis
====================================

Actually one script is used: pbsea.py (for Pandas Based Singular Enrichment Analysis).
An enrichment analysis compares the occurrence of an entity in a list of interest 
to the occurence in a reference (for example the number of cat in one country compared 
to the number of cat in the world).

Two class are present:

#. EnrichmentAnalysis: to perform a Singular Enrichment Analysis on everything.
#. GOEnrichmentAnalysis: to perform a Singular Enrichment Analysis on GO terms.

Right now the analysis take two input files but it will accept pandas dataframe, 
with two columns (one for the interest values and one for the reference values).

Enrichment Analysis
===================

This workflow performs a Singular Enrichment Analysis. This analysis
takes a list of genes (for example differentially expressed genes) and
compute an enrichment term for each annotation term in this list. For a
better definition, read the `article writed by Huang et al.
(2009) <https://academic.oup.com/nar/article-lookup/doi/10.1093/nar/gkn923>`__.

The idea behind this workflow is to make a tool to analyze genome and
with few datas. Also, by using class it allows to use separately some of
its components (like enrichmentAnalysis class).

fileManagement.py manages the files to create counting files used by
enrichmentAnalysis.py.

enrichmentAnalysis.py is dividied in tow class. The first class
("EnrichmentAnalysis") is the basic method, which computes an
hypergeometric test for variables (now it works for GO terms, in the
future it will work for pathway) and calculates different multiple tests
corrections (Bonferroni, Holm, Sidak, Benjamini & Hochberg and SGoF).
The second class ("GOEnrichmentAnalysis") inherits from
"EnrichmentAnalysis" and overrides a function to add GO label to the
results.

workflow\_manager.py is the main script.

This workflow works with three directories (inputFiles, temporaryFiles
and outputFiles) :

-  inputFiles must have three files : queryResults.csv (a csv file
   resulting from queriyng on the Gene Ontology to have all the GO terms
   with their GO labels (it will be automated in the future),
   GOTermsPlasmoGenome.tsv (which contains all the GO terms from the
   genome of your species, it will also be automated) and your data (in
   .csv).

-  temporaryFiles : will contain files used during the script, it will
   be created during the analysis. It contains datas extracted from the
   external databases.

-  outputFiles : the results of the analysis in tsv, it will be created
   during the analysis.

Test used :

-  Hypergeometric test to compare the distribution of GO terms in your
   list and in the complete organism.

-  Normal approximation when using big numbers.

And multiple testing corrections :

-  `Bonferroni
   Correction <http://www.jstor.org/stable/2282330?seq=1#page_scan_tab_contents>`__
   Dunn, Olive Jean. “Multiple Comparisons Among Means.” Journal of the
   American Statistical Association, vol. 56, no. 293, 1961, pp. 52–64.

-  `Sidak <https://www.jstor.org/stable/2283989?seq=1#page_scan_tab_contents>`__
   Sidak, Zbynek. “Rectangular Confidence Regions for the Means of
   Multivariate Normal Distributions.” Journal of the American
   Statistical Association, vol. 62, no. 318, 1967, pp. 626–633.

-  `Holm <http://www.jstor.org/stable/4615733?seq=1#page_scan_tab_contents>`__
   Holm, Sture. “A Simple Sequentially Rejective Multiple Test
   Procedure.” Scandinavian Journal of Statistics, vol. 6, no. 2, 1979,
   pp. 65–70.

-  `Benjamini &
   Hochberg <https://www.jstor.org/stable/2346101?seq=1#page_scan_tab_contents>`__
   Benjamini, Yoav, and Yosef Hochberg. “Controlling the False Discovery
   Rate: A Practical and Powerful Approach to Multiple Testing.” Journal
   of the Royal Statistical Society. Series B (Methodological), vol. 57,
   no. 1, 1995, pp. 289–300.

-  `Benjamini &
   Yekutieli <http://www.jstor.org/stable/2674075?seq=1#page_scan_tab_contents>`__
   Benjamini, Yoav, and Daniel Yekutieli. “The Control of the False
   Discovery Rate in Multiple Testing under Dependency.” The Annals of
   Statistics, vol. 29, no. 4, 2001, pp. 1165–1188.

-  `SGoF <https://www.ncbi.nlm.nih.gov/pmc/articles/PMC2719628/>`__
   Carvajal-Rodríguez, Antonio, Jacobo de Uña-Alvarez, and Emilio
   Rolán-Alvarez. “A New Multitest Correction (SGoF) That Increases Its
   Statistical Power When Increasing the Number of Tests.” BMC
   Bioinformatics 10 (2009): 209.
