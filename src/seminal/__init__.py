import sys
import builtins
from .logo import *

from .azoospermia import *
from .semen import *

detailed_doc = """
seminal: Male Reproductive Risk Equations in Python
========================================================================================

`seminal` implements published risk equations in andrology and male reproductive health,
with coefficients taken exactly as printed in the source papers.

Currently included (Tradewell et al., World J Mens Health 2022):
  * azoospermia_fsh   probability of azoospermia from serum FSH alone (quadratic)
  * azoospermia_lr    probability of azoospermia from age, FSH, LH, testosterone
                      and mean testis volume (logistic regression)
  * add_azoospermia_risk_cols   score a whole cohort in a DataFrame

WHO 2021 semen reference distributions (Campbell et al., Andrology 2021):
  * semen_percentile      where a value sits among fertile men
  * lower_reference_limit the 5th centile for a parameter (WHO 2020 or 2010)
  * below_reference       flag values under the lower reference limit
  * semen_reference       the published centile table as a DataFrame
  * add_semen_percentile_cols   percentiles and flags for a whole cohort

Not affiliated with the original authors. For research use only.

PyPI: https://pypi.org/project/seminal/
GitHub: https://github.com/datasciencedynamics/seminal
Docs: https://datasciencedynamics.com/seminal

Version: 0.0.1a1

"""

__author__ = "Leonid Shpaner"
__email__ = "lshpaner@ucla.edu"
__version__ = "0.0.1a1"


def custom_help(obj=None):
    """Custom help function to include the ASCII logo in help() output."""
    if obj is None or obj is sys.modules[__name__]:
        print(seminal_logo)
        print(detailed_doc)
    else:
        original_help(obj)


original_help = builtins.help
builtins.help = custom_help
