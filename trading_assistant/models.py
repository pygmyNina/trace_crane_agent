"""Data models for the options trading assistant."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class StopLossType(str, Enum):
    """Strategy for calculating stop loss."""
    PERCENTAGE = "percentage"       # Fixed % of premium paid
    ATR_BASED = "atr_based"         # Based on Average True Range of underlying
    DELTA_BASED = "delta_based"     # Exit when delta drops below threshold
    PREMIUM_FLOOR = "premium_floor" # Exit when premium drops to floor value


class OptionContract(BaseModel):
    """Represents a single option contract."""
    symbol: str                             # Underlying ticker (e.g. AAPL)
    option_type: OptionType
    strike: float
    expiration: date
    contracts: int = 1                      # Number of contracts

    # Pricing
    entry_premium: float                    # Premium paid per share
    current_premium: Optional[float] = None
    bid: Optional[float] = None
    ask: Optional[float] = None

    # Greeks (optional, fetched from broker)
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    iv: Optional[float] = None              # Implied volatility

    @property
    def total_cost(self) -> float:
        """Total premium paid (each contract = 100 shares)."""
        return self.entry_premium * 100 * self.contracts

    @property
    def current_value(self) -> Optional[float]:
        if self.current_premium is None:
            return None
        return self.current_premium * 100 * self.contracts

    @property
    def pnl(self) -> Optional[float]:
        if self.current_value is None:
            return None
        return self.current_value - self.total_cost

    @property
    def pnl_percent(self) -> Optional[float]:
        if self.pnl is None or self.total_cost == 0:
            return None
        return (self.pnl / self.total_cost) * 100

    @property
    def days_to_expiration(self) -> int:
        return (self.expiration - date.today()).days

    @property
    def osi_symbol(self) -> str:
        """OCC Options Symbology Initiative format."""
        exp = self.expiration.strftime("%y%m%d")
        cp = "C" if self.option_type == OptionType.CALL else "P"
        strike_str = f"{int(self.strike * 1000):08d}"
        return f"{self.symbol:<6}{exp}{cp}{strike_str}"


class StopLossOrder(BaseModel):
    """A stop loss configuration for an option position."""
    contract: OptionContract
    stop_type: StopLossType
    trigger_price: float                    # Premium at which to exit
    reason: str = ""                        # Human-readable explanation

    # For tracking
    created_at: datetime = Field(default_factory=datetime.now)
    triggered: bool = False

    @property
    def max_loss(self) -> float:
        """Maximum loss if stop is hit (per contract, x100 shares)."""
        return (self.contract.entry_premium - self.trigger_price) * 100 * self.contract.contracts

    @property
    def max_loss_percent(self) -> float:
        if self.contract.total_cost == 0:
            return 0
        return (self.max_loss / self.contract.total_cost) * 100

    def is_triggered(self, current_premium: float) -> bool:
        return current_premium <= self.trigger_price


class RiskProfile(BaseModel):
    """User's risk parameters."""
    account_size: float = 10000.0
    max_risk_per_trade_pct: float = 2.0     # % of account to risk per trade
    max_portfolio_risk_pct: float = 10.0    # Max total portfolio risk
    default_stop_type: StopLossType = StopLossType.PERCENTAGE
    default_stop_pct: float = 50.0          # Default: stop at 50% loss of premium

    @property
    def max_risk_per_trade(self) -> float:
        return self.account_size * (self.max_risk_per_trade_pct / 100)

    def max_contracts(self, premium_per_share: float, stop_loss_pct: float) -> int:
        """How many contracts you can buy within risk limits."""
        risk_per_contract = premium_per_share * 100 * (stop_loss_pct / 100)
        if risk_per_contract <= 0:
            return 0
        return int(self.max_risk_per_trade / risk_per_contract)
