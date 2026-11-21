<img src="https://raw.githubusercontent.com/datasciencedynamics/seminal/main/assets/seminal_logo.svg" width="300" style="border: none; outline: none; box-shadow: none;" oncontextmenu="return false;">

<br>

[![PyPI](https://img.shields.io/pypi/v/seminal.svg?include_prereleases)](https://pypi.org/project/seminal/)
[![Docs](https://img.shields.io/badge/docs-datasciencedynamics.com%2Fseminal-1F6FB2)](https://datasciencedynamics.com/seminal/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24411154.svg)](https://doi.org/10.5281/zenodo.24411154)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/datasciencedynamics/seminal/tree/main?tab=MIT-1-ov-file)

`seminal` is a Python library of published risk equations in andrology and male reproductive health, implemented with the coefficients exactly as printed in the source papers and checked against the authors' own validation data.

The first release implements the two azoospermia prediction models of Tradewell et al. (World J Mens Health 2022): a quadratic in serum FSH alone, and a logistic regression on age, FSH, LH, total testosterone and mean testis volume. Both estimate the probability that a man presenting for infertility evaluation has no sperm in the ejaculate, without a semen analysis.

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

## Validation against the authors' data

The study data are public under CC0 on [Harvard Dataverse](https://doi.org/10.7910/DVN/EQFMCM). `make data_gen preprocess` downloads them into `data/` (gitignored) and the test suite then checks the implementation against the paper's external validation:

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

Both run against `data/processed/`, built by `make data_gen preprocess`. Notebooks are committed without outputs; the rendered versions are on the documentation site.

## Repository layout

```
seminal/
├── src/seminal/      the package (equations only; no data)
├── tests/              unit tests plus optional validation against data/
├── data_gen.py         download the Dataverse file into data/raw
├── preprocessing.py    harmonize sites into data/processed
├── notebooks/          quickstart and the reproduction of Tradewell et al.
└── Makefile            venv, install, test, data_gen, preprocess, build
```

## Citation

If you use `seminal`, please cite the software (see `CITATION.cff`) and the original paper:

Tradewell MB, Cazzaniga W, Pagani RL, et al. Algorithms for Predicting the Probability of Azoospermia from Follicle Stimulating Hormone: Design and Multi-Institutional External Validation. *World J Mens Health*. 2022;40(4):600-607. doi:10.5534/wjmh.210138

## License

MIT. The study data on Dataverse are CC0.

## Author

Leonid Shpaner, University of San Diego and Data Science Dynamics. [leonshpaner.com](https://www.leonshpaner.com)
