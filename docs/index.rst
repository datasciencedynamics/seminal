Welcome to the seminal Python Library Documentation!
====================================================

.. note::

   This documentation is for ``seminal`` version |version_str|.

``seminal`` is a Python library of published risk equations in andrology and
male reproductive health, implemented with the coefficients exactly as printed
in the source papers and checked against the authors' own validation data.

It currently covers the two azoospermia prediction models of Tradewell et al.
(*World J Mens Health* 2022), a quadratic in serum FSH alone and a logistic
regression on age, FSH, LH, total testosterone and mean testis volume, and the
WHO 2021 semen reference distributions of Campbell et al. (*Andrology* 2021):
where a semen parameter sits among fertile men and whether it falls below the
lower reference limit.

The library scores single patients or entire cohorts, explains each patient's
risk term by term, and ships with the scripts and notebooks that rebuild the
paper's cohort from the public data deposit and reproduce its external
validation.

.. important::

   ``seminal`` is not affiliated with the original authors. It is an
   independent implementation of published equations, intended for research
   use. It is not a medical device and should not be used to make clinical
   decisions.

Prerequisites
-------------

- **Python**: 3.8 or higher
- **numpy**: 1.20 or higher
- **pandas**: 1.3 or higher

Installation
------------

.. code-block:: bash

   pip install seminal

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   getting_started
   _notebooks/00_quickstart

.. toctree::
   :maxdepth: 2
   :caption: Documentation

   usage_guide
   inputs
   model
   semen
   data
   _notebooks/01_reproduce_tradewell
   _notebooks/02_reproduce_campbell
   api

.. toctree::
   :maxdepth: 2
   :caption: About seminal

   contributors
   acknowledgements
   citing
   changelog
   references
