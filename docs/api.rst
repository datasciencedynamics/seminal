API Reference
=============

Single patient
--------------

.. autofunction:: seminal.azoospermia_fsh

.. autofunction:: seminal.azoospermia_lr

Cohorts
-------

.. autofunction:: seminal.add_azoospermia_risk_cols

WHO 2021 semen reference distributions
--------------------------------------

.. autofunction:: seminal.semen_percentile

.. autofunction:: seminal.lower_reference_limit

.. autofunction:: seminal.below_reference

.. autofunction:: seminal.semen_reference

.. autofunction:: seminal.add_semen_percentile_cols

Constants
---------

``seminal.azoospermia.LR_COEFS``
   Table 3 coefficients on the log-odds scale: ``intercept``, ``age``,
   ``fsh``, ``lh``, ``testosterone``, ``testis_volume``.

``seminal.azoospermia.FSH_QUAD``
   Fig. 1 quadratic in percent: ``a`` (FSH²), ``b`` (FSH), ``c`` (constant).

``seminal.semen.PARAMETERS``
   The nine semen parameters and their labels.

``seminal.semen.CENTILES``
   The nine published centiles: 2.5, 5, 10, 25, 50, 75, 90, 95, 97.5.

``seminal.azoospermia.REFERENCE_RANGES``
   Reference limits quoted in the paper for FSH, LH, total testosterone and
   mean testis volume. Informational only; the models do not threshold on
   them.
