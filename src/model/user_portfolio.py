from typing import List
from dataclasses import dataclass
import financedatabase as fd


@dataclass
class UserPortfolio:
    currencies: List[fd.Currencies]
    etf: List[fd.ETFs]
    equities: List[fd.Equities]
    funds: List[fd.Funds]
    cryptos: List[fd.Cryptos]
    moneymarkets: List[fd.Moneymarkets]
    indices: List[fd.Indices]
