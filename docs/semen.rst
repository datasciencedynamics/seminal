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

.. code-block:: python

   from seminal import add_semen_percentile_cols

   scored = add_semen_percentile_cols(
       df, {"concentration": "conc", "progressive_motility": "pr", "normal_forms": "morph"}
   )
   # adds conc_pct, conc_below_lrl, pr_pct, pr_below_lrl, morph_pct, morph_below_lrl

Unparseable values become ``NaN`` in the percentile column and ``<NA>`` in the
flag column.

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
