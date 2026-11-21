Changelog
=========

Version 0.0.1a1 (2026-11-21)
----------------------------

- New ``seminal.semen`` module: the WHO 2021 (6th edition) semen reference
  distributions of Campbell et al. (2021), carried exactly as printed for all
  nine parameters and nine centiles, with the 2010 to 2020 subset and the WHO
  2010 lower reference limits as options. ``semen_percentile``,
  ``lower_reference_limit``, ``below_reference``, ``semen_reference`` and
  ``add_semen_percentile_cols``.
- Tests check the table against the paper, the headline 6th-edition limits,
  interpolation and cohort behaviour.

Version 0.0.0a4 (2026-11-20)
----------------------------

- BibTeX citation in the README. No changes to the equations.

Version 0.0.0a3 (2026-11-20)
----------------------------

- Repository moved to datasciencedynamics/seminal; documentation at
  datasciencedynamics.com/seminal; Zenodo DOI in README and CITATION. No
  changes to the equations.

Version 0.0.0a2 (2026-11-20)
----------------------------

- README corrections: pre-release badge, install note, affiliation, the
  reproduced exclusion rule and the matching Chicago numbers.
- ``dcurves`` added to the ``data`` extras for the reproduction notebook.
- Full journal title in the package description.
- Documentation site and Zenodo archiving. No changes to the equations.

Version 0.0.0a1 (2026-11-20)
----------------------------

- First alpha release.
- ``azoospermia_fsh``: probability of azoospermia from serum FSH alone, the
  quadratic of Fig. 1 in Tradewell et al. (2022), clipped to [0, 1] by default.
- ``azoospermia_lr``: the five-variable logistic regression of Table 3, with
  ``explain=True`` returning the linear predictor and each input's log-odds
  contribution.
- ``add_azoospermia_risk_cols``: both probabilities for every row of a
  DataFrame, ``NaN`` for incomplete rows.
- ``data_gen.py`` and ``preprocessing.py`` rebuild the paper's three cohorts
  from the CC0 Dataverse deposit; the test suite checks the external AUCs
  against the paper when the data are present.
- Notebooks: quickstart, and a full reproduction of the paper (cohort,
  Table 1, refit, calibration, decision curves, recalibration).
- Tested on Python 3.8 to 3.13.
