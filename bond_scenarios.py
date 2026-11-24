"""Price synthetic fixed-rate bonds on coupon dates. Python 3.10+, standard library."""
import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

REPORT_FIELDS = ("bond_id", "currency", "shock_bp", "price_per_100", "shocked_price_per_100",
                 "market_value", "scenario_pnl", "modified_duration_years", "dv01")

@dataclass(frozen=True)
class Bond:
    bond_id: str
    currency: str
    face_held: float
    coupon_pct: float
    ytm_pct: float
    periods_left: int
    frequency: int

    def __post_init__(self):
        if not self.bond_id or len(self.currency) != 3 or not self.currency.isascii() or not self.currency.isalpha() or self.currency.upper() != self.currency:
            raise ValueError("Provide a bond ID and three uppercase currency letters.")
        if not all(math.isfinite(n) for n in (self.face_held, self.coupon_pct, self.ytm_pct)):
            raise ValueError("Position and rates must be finite.")
        if self.face_held <= 0 or self.coupon_pct < 0 or self.periods_left < 1 or self.frequency not in (1, 2, 4):
            raise ValueError("Invalid face held, coupon, periods left or coupon frequency.")

    def price_duration(self, shock_bp=0):
        rate = (self.ytm_pct / 100 + shock_bp / 10000) / self.frequency
        if not math.isfinite(rate) or rate <= -1:
            raise ValueError(f"{self.bond_id}: yield plus shock invalid for discounting")
        pv_flows = []
        for period in range(1, self.periods_left + 1):
            coupon = self.coupon_pct / self.frequency
            cash_flow = coupon + (100 if period == self.periods_left else 0)
            pv_flows.append(cash_flow / (1 + rate) ** period)
        price = math.fsum(pv_flows)
        weighted_time = math.fsum(t * pv / self.frequency for t, pv in enumerate(pv_flows, start=1))
        return price, weighted_time / price / (1 + rate)

    def scenario(self, shock):
        base, duration = self.price_duration()
        shocked, _ = self.price_duration(shock)
        down, _ = self.price_duration(-1)
        up, _ = self.price_duration(1)
        units = self.face_held / 100
        return dict(zip(REPORT_FIELDS, (self.bond_id, self.currency, shock, base, shocked, base * units,
                                         (shocked - base) * units, duration, (down - up) * units / 2)))


def read_positions(source):
    bonds = []
    seen = set()
    for row_number, row in enumerate(csv.DictReader(source), start=2):
        try:
            bond = Bond(row["bond_id"].strip(), row["currency"].strip(), float(row["face_held"]),
                        float(row["coupon_pct"]), float(row["ytm_pct"]), int(row["periods_left"]), int(row["frequency"]))
            if bond.bond_id in seen:
                raise ValueError(f"duplicate ID {bond.bond_id}")
        except (KeyError, TypeError, AttributeError, ValueError) as exc:
            raise ValueError(f"CSV row {row_number}: {exc}") from exc
        bonds.append(bond)
        seen.add(bond.bond_id)
    if not bonds:
        raise ValueError("Positions file is empty.")
    return bonds


def aggregate(rows):
    totals = defaultdict(lambda: defaultdict(float))
    for row in rows:
        group = totals[row["currency"], row["shock_bp"]]
        for key in ("market_value", "scenario_pnl", "dv01"):
            group[key] += row[key]
    return [dict(currency=ccy, shock_bp=shock, **values) for (ccy, shock), values in sorted(totals.items())]


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: round(v, 8) if isinstance(v, float) else v for k, v in row.items()})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("positions", type=Path)
    parser.add_argument("--shocks", nargs="+", type=int, default=[-100, -25, 0, 25, 100], metavar="BP")
    parser.add_argument("--output", type=Path, default=Path("results"))
    args = parser.parse_args()
    try:
        with args.positions.open(encoding="utf-8-sig", newline="") as source:
            bonds = read_positions(source)
        rows = [bond.scenario(bp) for bond in bonds for bp in sorted(set(args.shocks))]
    except (OSError, ValueError, OverflowError) as exc:
        parser.exit(2, f"Input error: {exc}\n")
    args.output.mkdir(exist_ok=True, parents=True)
    write_csv(args.output / "positions.csv", REPORT_FIELDS, rows)
    write_csv(args.output / "by_currency.csv", ("currency", "shock_bp", "market_value", "scenario_pnl", "dv01"), aggregate(rows))


if __name__ == "__main__":
    main()
