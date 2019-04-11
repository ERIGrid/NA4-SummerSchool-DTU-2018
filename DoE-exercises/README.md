# Jupyter notebooks for learning the basics of Design of Experiments

The notebooks in this directory were made using Jupyter version 4.4.0, and Python 3.6. The requirements for running the notebook itself can be found in the file "requirements.txt". 

The requirements can be installed with pip through:

``pip install -r requirements.txt``

If you use Anaconda to manage your Python environment and don't want to mix the use of ``pip`` and ``conda``, you can install each package manually using, e.g.:

``conda install pandas``

Note: Mosaik is not on the Anaconda repository, you will have to install it from ``PyPI``, e.g. with ``pip``.

These educational notebooks have been developed by Daniel Esteban Morales Bondy and Tue Vissing Jensen (both at the Technical University of Denmark), as well as Cornelius Steinbrink (at OFFIS), with the support of the H2020 ERIGrid project, Grant Agreement No. 654113 

# Overview of the notebooks

The DoE exercises introduce the basic sampling and evaluation strategies of the  design of experiments zoo. 

The 'experiment' simulation is based on mosaik. To understand how this part works, run the mosaik tutorial first (also available at the ERIGrid website). 
For experimenting with DoE in these exercises, it is sufficient to understand that a simple simulation is 
set up to evaluate the system for the parameters you configure it for.

Exercises:
 I.   HEMS\_base\_case.ipynb (deterministic or stochastic simulation - where you vary over a range)
 II. Simple\_ANOVA.ipynb (carry out a simple one-way Analysis of Variance)
 III.  Blocking.ipynb (notebook on using the concept of blocking)
 IV. Modern\_DoE.ipynb (an example of how to generate a metamodel of a black box system)

