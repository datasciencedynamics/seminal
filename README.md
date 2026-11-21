<img src="https://raw.githubusercontent.com/datasciencedynamics/seminal/main/assets/seminal_logo.svg" width="300" style="border: none; outline: none; box-shadow: none;" oncontextmenu="return false;">

<br>

[![PyPI](https://img.shields.io/pypi/v/seminal.svg?include_prereleases)](https://pypi.org/project/seminal/)
[![Docs](https://img.shields.io/badge/docs-datasciencedynamics.com%2Fseminal-1F6FB2)](https://datasciencedynamics.com/seminal/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24411154.svg)](https://doi.org/10.5281/zenodo.24411154)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/datasciencedynamics/seminal/tree/main?tab=MIT-1-ov-file)

`seminal` is a Python library of published risk equations in andrology and male reproductive health, implemented with the coefficients exactly as printed in the source papers and checked against the authors' own validation data.

It currently covers:

- **Azoospermia probability** from Tradewell et al. (World J Mens Health 2022): a quadratic in serum FSH alone, and a logistic regression on age, FSH, LH, total testosterone and mean testis volume. Both estimate the probability that a man presenting for infertility evaluation has no sperm in the ejaculate, without a semen analysis.
- **WHO 2021 semen reference distributions** from Campbell et al. (Andrology 2021), the fertile-man centiles adopted by the 6th edition of the WHO laboratory manual: where a semen parameter sits among fertile men, and whether it falls below the lower reference limit. The table is checked against the authors' public deposit (3,589 men): all 81 cells reproduce.

> **Not affiliated with the original authors.** This is an independent implementation of published equations, intended for research use. It is not a medical device and should not be used to make clinical decisions.

## Installation

```bash
pip install seminal
```

Requires Python 3.8+, numpy 1.20+ and pandas 1.3+. Full documentation: [datasciencedynamics.com/seminal](https://datasciencedynamics.com/seminal/).

## Usage

### FSH alone

```python
from seminal import azoospermia_fsh

azoospermia_fsh(20)
# 0.439
```

The published curve is U-shaped: 10.1% at undetectable FSH, a minimum of about 8.4% at FSH 3.6 IU/L, and 100% from about 30 IU/L. Output is clipped to [0, 1]; pass `clip=False` to reproduce the paper's unbounded quadratic.

### Full logistic model

```python
from seminal import azoospermia_lr

azoospermia_lr(age=36, fsh=5.7, lh=4.5, testosterone=429, testis_volume=15)
# 0.086
```

Pass `explain=True` to also get the linear predictor and each input's contribution to the log-odds, largest first.

### A whole cohort

```python
from seminal import add_azoospermia_risk_cols

scored = add_azoospermia_risk_cols(
    df, age_col="age", fsh_col="fsh", lh_col="lh",
    testosterone_col="testosterone", testis_volume_col="testis_volume",
)
scored[["azoo_fsh", "azoo_lr"]]
```

Rows missing any logistic-model input get `NaN` in `azoo_lr`; `azoo_fsh` needs only FSH.

### Semen parameters against the WHO reference distribution

```python
from seminal import semen_percentile, lower_reference_limit, below_reference

semen_percentile("concentration", 36)      # 25.0  (25th centile of fertile men)
lower_reference_limit("progressive_motility")   # 30  (WHO 2021; 32 under edition="who2010")
below_reference("normal_forms", 3)         # True
```

`semen_reference()` returns the full published table (2.5th to 97.5th centiles, with the 95% CI of the 5th), and `add_semen_percentile_cols(df, {"concentration": "conc", ...})` adds a percentile and a below-limit flag per parameter for a cohort. Percentiles are interpolated between the nine published centiles and clipped to [2.5, 97.5].

## The equations

**FSH-only quadratic** (Fig. 1): `p(%) = 0.133·FSH² − 0.965·FSH + 10.1`, fit to binned Miami probabilities, R² = 0.95.

**Logistic regression** (Table 3): `p = 1 / (1 + exp(−η))` where

| Term | Units | Coefficient |
|---|---|---|
| Intercept | | −1.9 |
| Age | years | 0.02 |
| FSH | IU/L | 0.13 |
| LH | IU/L | 0.03 |
| Total testosterone | ng/dL | −0.002 |
| Mean testis volume | cm³ (Prader orchidometer) | −0.08 |

The paper prints the model form as `1/exp[−(b₀ + bᵢXᵢ)]`, which is a typesetting error (it exceeds 1); the standard logistic form is used here.

**WHO 2021 reference distribution** (Campbell et al. 2021, Table 3; 5th centile with 95% CI):

| Parameter | n | 5th | 50th | 95th |
|---|---|---|---|---|
| Semen volume (mL) | 3,586 | 1.4 (1.3 to 1.5) | 3.0 | 6.2 |
| Sperm concentration (10⁶/mL) | 3,587 | 16 (15 to 18) | 66 | 208 |
| Total sperm number (10⁶) | 3,584 | 39 (35 to 40) | 210 | 701 |
| Total motility (%) | 3,488 | 42 (40 to 43) | 64 | 90 |
| Progressive motility (%) | 3,389 | 30 (29 to 31) | 55 | 77 |
| Vitality (%) | 1,337 | 54 (50 to 56) | 78 | 97 |
| Normal forms (%) | 3,335 | 4 (3.9 to 4.0) | 14 | 39 |

All nine centiles for all nine parameters are in the package, as printed, for both the combined WHO 2020 table and the 2010 to 2020 studies alone. `notebooks/02_reproduce_campbell.ipynb` recomputes both tables from the authors' deposit (`Fertile_Man_2020.xlsx`, University of Dundee, CC BY): every n matches, the 5th centiles reproduce exactly, and 80 of 81 cells of Table 3 match (the median total sperm number is 209.5, printed as 210).

## Validation against the authors' data

The Tradewell study data are public under CC0 on [Harvard Dataverse](https://doi.org/10.7910/DVN/EQFMCM) and the Campbell reference men under CC BY on the [University of Dundee portal](https://doi.org/10.15132/10000163). `make data_gen preprocess` downloads both into `data/` (gitignored) and the test suite then checks the implementation against the paper's external validation and the WHO table against the deposit:

| Site | n | AUC, logistic (paper) | AUC, FSH-only (paper) |
|---|---|---|---|
| Milan | 1,955 | 0.786 (0.79) | 0.786 (0.78) |
| Chicago | 596 | 0.718 (0.72) | 0.707 (0.71) |

### Things to know about the data

- The deposit contains all three sites as separate sheets. Miami (1,070 rows) and Chicago (643) are pre-exclusion. Applying the exclusions exactly as the paper states them (prior vasectomy, Y microdeletion, solitary testis, testosterone or steroid use) gives 943 and 614, not the paper's 946 and 596. The paper's counts are recovered exactly by not excluding Y microdeletions, reading solitary testis from the absence codes (Miami) or a zero volume (Chicago), and defining azoospermia as concentration below 0.01 M/mL. `preprocessing.py` applies that reproduced rule by default (`--exclusions stated` gives the literal one); the choice does not change the AUCs. Milan (1,955) matches either way.
- Chicago testis volumes are ultrasound long-axis measurements in cm (median 4.5), not orchidometer volumes in mL (median 14 to 15 at Miami and Milan). The paper does not address this; `preprocessing.py` labels the measurement method per site.
- The logistic coefficients are printed to one or two significant figures. At the extremes of testosterone and age this rounding alone can move the log-odds by several tenths. A refit on the Miami data recovers full-precision values; that is planned for a later release and kept separate from the as-published model.
- Azoospermia was confirmed on at least two semen analyses. The outcome in the Miami and Chicago sheets is sperm concentration = 0; Milan carries an explicit flag plus obstructive/non-obstructive type.

## Notebooks

- [`00_quickstart.ipynb`](notebooks/00_quickstart.ipynb): one patient, the FSH curve, scoring the validation cohorts, ROC / PR / calibration per site, explaining a prediction.
- [`01_reproduce_tradewell.ipynb`](notebooks/01_reproduce_tradewell.ipynb): rebuild the paper's cohort and Table 1 from the deposit, refit the logistic model on Miami, calibration-in-the-large and slope per site, decision curves, intercept-only recalibration.
- [`02_reproduce_campbell.ipynb`](notebooks/02_reproduce_campbell.ipynb): recompute the WHO 2021 reference centiles from the Fertile Man deposit, identify the 2010 to 2020 studies, bootstrap the 5th-centile CIs, between-laboratory heterogeneity, accuracy of the interpolated percentile.

Both run against `data/processed/`, built by `make data_gen preprocess`. Notebooks are committed without outputs; the rendered versions are on the documentation site.

## Repository layout

```
seminal/
├── src/seminal/      the package (equations and reference tables; no data)
├── tests/              unit tests plus optional validation against data/
├── data_gen.py         download the Dataverse and Dundee files into data/raw
├── preprocessing.py    harmonize both datasets into data/processed
├── notebooks/          quickstart and the reproduction of Tradewell et al.
└── Makefile            venv, install, test, data_gen, preprocess, build
```

## Citation

If you use `seminal`, please cite the software and the original paper.

```bibtex
@software{shpaner_2026_24411154,
   author       = {Shpaner, Leonid},
   title        = {seminal: published risk equations in andrology and male reproductive health},
   month        = nov,
   year         = 2026,
   publisher    = {Zenodo},
   version      = {0.0.1a1},
   doi          = {10.5281/zenodo.24411154},
   url          = {https://doi.org/10.5281/zenodo.24411154}
}
```

`CITATION.cff` carries the same metadata (GitHub shows it as "Cite this repository"). The original paper:

Tradewell MB, Cazzaniga W, Pagani RL, et al. Algorithms for Predicting the Probability of Azoospermia from Follicle Stimulating Hormone: Design and Multi-Institutional External Validation. *World J Mens Health*. 2022;40(4):600-607. doi:10.5534/wjmh.210138

Campbell MJ, Lotti F, Baldi E, et al. Distribution of semen examination results 2020 - A follow up of data collated for the WHO semen analysis manual 2010. *Andrology*. 2021;9(4):817-822. doi:10.1111/andr.12983

World Health Organization. *WHO laboratory manual for the examination and processing of human semen*, 6th ed. Geneva: WHO; 2021. ISBN 978-92-4-003078-7.

## License

MIT. The Tradewell data on Dataverse are CC0; the Fertile Man deposit is CC BY 4.0. The Dundee portal refuses scripted downloads, so `data_gen.py` falls back to a verbatim copy of the deposit attached to the GitHub release (sha256 checked); the original is at https://doi.org/10.15132/10000163.

## Author

Leonid Shpaner, University of San Diego and Data Science Dynamics. [leonshpaner.com](https://www.leonshpaner.com)
