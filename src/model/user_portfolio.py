from typing import List
from dataclasses import dataclass


@dataclass
class UserPortfolio:
    currencies: List[str]
    etf: List[str]
    equities: List[str]
    funds: List[str]
    cryptos: List[str]
    moneymarkets: List[str]
    indices: List[str]


@dataclass
class UserInfo:
    # Initial quantity of value add to be balanced in simulation
    initial_money_amount: int  # in cents
    # The best chance of become Rich, BET on finding a unicorn
    explosion_portfolio: UserPortfolio
    # Trying extract a big montant or return, keep Betting
    agressive_portfolio: UserPortfolio
    # Don't be stupid and create a reserve of value.
    conservative_portfolio: UserPortfolio
