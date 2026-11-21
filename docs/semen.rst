WHO 2021 Semen Reference Distributions
======================================

The 6th edition of the WHO laboratory manual (2021) replaced the 2010
reference values with the distribution reported by Campbell et al. (2021):
semen parameters from 3,589 men in 12 countries whose partners conceived
within 12 months. ``seminal.semen`` carries that table exactly as printed and
answers two questions about a result: where it sits among fertile men, and
whether it is below the conventional lower reference limit (the 5th centile).

The paper is explicit that the 5th centile is not a threshold between fertile
and infertile men; it is the point below which only 5% of fertile men fall.

Where a value sits
------------------

.. code-block:: python

   from seminal import semen_percentile

   semen_percentile("concentration", 36)   # 25.0
   semen_percentile("progressive_motility", 55)   # 50.0
   semen_percentile("normal_forms", 2)     # 2.5  (below the lowest published centile)

The percentile is linearly interpolated between the nine published centiles
(2.5, 5, 10, 25, 50, 75, 90, 95, 97.5) and clipped to that range, since the
tails are not published. It is exact at the nine points and an approximation
between them.

Lower reference limits
----------------------

.. code-block:: python

   from seminal import lower_reference_limit, below_reference

   lower_reference_limit("concentration")             # 16
   lower_reference_limit("concentration", "who2010")  # 15
   below_reference("total_motility", 40)              # True (limit 42)

``edition="who2010"`` gives the 5th-edition limits (Cooper et al. 2010) for
labs that still report against them.

Cohorts
-------

``add_semen_percentile_cols`` takes a DataFrame with one row per semen
analysis and a mapping of parameter name to column name. For each mapped
column it adds a percentile column (``_pct``, 2.5 to 97.5) and a below-limit
flag (``_below_lrl``, below the WHO 5th centile).

.. code-block:: python

   from seminal import add_semen_percentile_cols

   df["tsc"] = df["vol_ml"] * df["conc"]        # total number, if not recorded

   scored = add_semen_percentile_cols(
       df,
       columns={
           "volume": "vol_ml",
           "concentration": "conc",
           "total_number": "tsc",
           "progressive_motility": "pr",
           "normal_forms": "morph",
       },
       edition="who2020",                       # or "2010_2020"
   )
   # adds vol_ml_pct, vol_ml_below_lrl, conc_pct, conc_below_lrl, ...
   scored["n_below_lrl"] = scored.filter(like="_below_lrl").sum(axis=1)

If the columns already carry the parameter names (``volume``,
``concentration``, ...) the mapping can be omitted.

What the call needs and what it adds, for every mapped parameter:

.. list-table::
   :header-rows: 1
   :widths: 24 22 30 24

   * - Parameter key
     - Input column (yours)
     - Unit expected
     - Columns added
   * - ``volume``
     - e.g. ``vol_ml``
     - mL
     - .. rst-class:: added-col

       ``vol_ml_pct``, ``vol_ml_below_lrl``
   * - ``concentration``
     - e.g. ``conc``
     - 10\ :sup:`6`/mL
     - .. rst-class:: added-col

       ``conc_pct``, ``conc_below_lrl``
   * - ``total_number``
     - e.g. ``tsc`` (volume × concentration)
     - 10\ :sup:`6` per ejaculate
     - .. rst-class:: added-col

       ``tsc_pct``, ``tsc_below_lrl``
   * - ``total_motility``
     - e.g. ``mot``
     - % (PR + NP), 0 to 100
     - .. rst-class:: added-col

       ``mot_pct``, ``mot_below_lrl``
   * - ``progressive_motility``
     - e.g. ``pr``
     - %
     - .. rst-class:: added-col

       ``pr_pct``, ``pr_below_lrl``
   * - ``nonprogressive_motility``
     - e.g. ``np``
     - %
     - .. rst-class:: added-col

       ``np_pct``, ``np_below_lrl``
   * - ``immotile``
     - e.g. ``im``
     - %
     - .. rst-class:: added-col

       ``im_pct``, ``im_below_lrl``
   * - ``vitality``
     - e.g. ``vit``
     - % live
     - .. rst-class:: added-col

       ``vit_pct``, ``vit_below_lrl``
   * - ``normal_forms``
     - e.g. ``morph``
     - % normal, strict criteria
     - .. rst-class:: added-col

       ``morph_pct``, ``morph_below_lrl``

``<col>_pct`` is a float from 2.5 to 97.5 (the man's centile among fertile
men); ``<col>_below_lrl`` is a nullable boolean, True below the WHO 5th
centile. Any subset of the nine parameters can be mapped; nothing else is
required of the DataFrame.

Whether the scored columns mean anything on a new dataset depends on three
things:

* **Units.** They must match ``PARAMETERS[name]["unit"]``: mL, 10\ :sup:`6`/mL,
  10\ :sup:`6` per ejaculate, and percentages on a 0 to 100 scale. A motility
  column stored as a fraction (0.55) scores as the 2.5th centile.
* **Morphology.** The reference was scored with strict (Tygerberg) criteria.
  Results under older WHO criteria run several times higher and are not
  comparable.
* **Missing values.** Unparseable values become ``NaN`` in the percentile
  column and ``<NA>`` in the flag column; do not fill them before scoring.

Two uses are worth naming. Describing a cohort against fertile men: the median
``_pct`` per parameter and the share ``_below_lrl``, which is about 5% in a
fertile reference population and far higher in an infertility clinic. And a
simple severity count, ``n_below_lrl`` (0 to 9). The percentiles are a
monotone transform of the raw values, so they add nothing to tree-based
models; they put the nine parameters on one scale for plots and linear
models.

Direction matters for ``immotile``: the flag fires when the immotile fraction
is *below* the 5th centile, the favourable end.

The quickstart notebook runs this on a toy export; section 7 of
:doc:`_notebooks/02_reproduce_campbell` scores the reference men themselves
(5% flag overall, with wide variation by study).

The table
---------

``semen_reference()`` returns every parameter; ``semen_reference("volume")``
one row. Columns: ``label``, ``n``, ``p2.5`` through ``p97.5``, and the 95%
confidence interval of the 5th centile.

.. list-table:: Campbell et al. 2021, Table 3 (WHO 2020, combined data)
   :header-rows: 1
   :widths: 30 8 8 12 8 8 8 8 8 8 8

   * - Parameter
     - n
     - 2.5
     - 5 (95% CI)
     - 10
     - 25
     - 50
     - 75
     - 90
     - 95
     - 97.5
   * - Semen volume (mL)
     - 3586
     - 1.0
     - 1.4 (1.3 to 1.5)
     - 1.8
     - 2.3
     - 3.0
     - 4.2
     - 5.5
     - 6.2
     - 6.9
   * - Sperm concentration (10⁶/mL)
     - 3587
     - 11
     - 16 (15 to 18)
     - 22
     - 36
     - 66
     - 110
     - 166
     - 208
     - 254
   * - Total sperm number (10⁶)
     - 3584
     - 29
     - 39 (35 to 40)
     - 58
     - 108
     - 210
     - 363
     - 561
     - 701
     - 865
   * - Total motility (%)
     - 3488
     - 35
     - 42 (40 to 43)
     - 47
     - 55
     - 64
     - 73
     - 83
     - 90
     - 92
   * - Progressive motility (%)
     - 3389
     - 24
     - 30 (29 to 31)
     - 36
     - 45
     - 55
     - 63
     - 71
     - 77
     - 81
   * - Non-progressive motility (%)
     - 3387
     - 1
     - 1 (1 to 1)
     - 2
     - 4
     - 8
     - 15
     - 26
     - 32
     - 38
   * - Immotile (%)
     - 2800
     - 15
     - 20 (19 to 20)
     - 23
     - 30
     - 37
     - 45
     - 53
     - 58
     - 65
   * - Vitality (%)
     - 1337
     - 45
     - 54 (50 to 56)
     - 60
     - 69
     - 78
     - 88
     - 95
     - 97
     - 98
   * - Normal forms (%)
     - 3335
     - 3
     - 4 (3.9 to 4.0)
     - 5
     - 8
     - 14
     - 23
     - 32
     - 39
     - 45

``edition="2010_2020"`` selects Table 2 of the same paper, the 2010 to 2020
studies without the 2010 reference data (n = 1,789 for most parameters).

Both tables are checked against the authors' deposit in
:doc:`_notebooks/02_reproduce_campbell`: every n matches, the 5th centiles
reproduce exactly, and 80 of 81 cells of Table 3 and 81 of 81 of Table 2
reproduce with the Weibull quantile definition (the remaining cell is a
median of 209.5 printed as 210).

Things to know
--------------

- The parameters are those of a standard semen analysis under the WHO manual:
  volume, concentration, total number, total and progressive motility,
  non-progressive, immotile, vitality (eosin or hypo-osmotic swelling) and
  strict-criteria normal morphology. pH, round cells and other measurements
  have no published distribution.
- The reference men are fertile by definition (time to pregnancy up to 12
  months), so the distribution describes fertile men, not the general
  population and not an infertility clinic.
- Methodological differences between contributing laboratories are part of
  the spread; Paffoni et al. (2022) argue the pooled studies cannot be treated
  as one population. The centiles are reported here as WHO adopted them.
- The library does not interpret results. A value at the 3rd centile is a
  value at the 3rd centile; what it means for a couple depends on everything
  else about them.
