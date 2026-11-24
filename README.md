# BondScenarioLab

A fixed-income analyst work sample for comparing rate sensitivity across a small, synthetic multicurrency bond book. Open the [editable Excel grid](examples/Bond_Scenario_Grid.xlsx) or run the Python CLI. Excel users can change the blue position and shock cells to see the resulting price and local-currency P&L.

## An analyst question

How much would the two HKD positions lose if their yields rose 100 basis points? The sample book has a base market value of HKD 1,506,095.94. Full repricing gives a loss of HKD 48,564.24. The symmetric one-basis-point DV01 is HKD 498.50, so a linear estimate gives a loss of roughly HKD 49,850. The two estimates diverge because the fixed coupon cash flows have a curved price–yield relationship. The shorter and longer positions can be inspected separately in the position-level export.

## Run

Python 3.10+ suffices for the CLI and regression tests.

```sh
python bond_scenarios.py examples/synthetic_bonds.csv --shocks -100 -25 0 25 100 --output results
python -m unittest discover -s tests -v
```

The first command produces `positions.csv` with the base and stressed price per 100 of par, market value, scenario P&L, modified duration and DV01. The `by_currency.csv` export aggregates the positions separately in each denomination. [Example output](examples/output/by_currency.csv). To rebuild the Excel work sample, install XlsxWriter and run `python make_workbook.py`.

## Model and input conventions

- All examples are fictional holdings in CNY, HKD and USD. No live market data, issuer information or client records are used.
- Enter annual coupons and yields in percentage points. A yield entry of 4.5 means 4.5 percent. A shock of +25 means +0.25 percentage points.
- A position is a long, fixed-rate bullet bond valued immediately after a coupon payment, with regular annual, semiannual or quarterly cash flows. The next cash flow is one full period away. Face held is in local currency. Position prices are quoted per 100 of face value.
- Each period's coupon is discounted at the periodic yield, and the final period also returns principal. Modified duration is the present-value-weighted time to payment divided by one plus the periodic yield. DV01 is half of the market-value difference between down-one-basis-point and up-one-basis-point scenarios.
- Each scenario applies the same yield change to each instrument. P&L reflects revaluation at the same instant. The model excludes accrued interest between coupon dates, credit events, curve twists, optionality and currency translation. It does not estimate realized investment returns.

The test suite checks par pricing, an independently known zero-coupon solution, analytical versus finite-difference sensitivity, shock direction, convexity, negative yields, currency grouping and input validation. This is an AI-assisted portfolio work sample.
