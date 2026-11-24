"""Regenerate the optional Excel scenario grid: pip install XlsxWriter."""
from pathlib import Path
from xlsxwriter import Workbook
from xlsxwriter.utility import xl_col_to_name
from bond_scenarios import read_positions

ROOT = Path(__file__).resolve().parent
with (ROOT / "examples/synthetic_bonds.csv").open() as stream:
    bonds = read_positions(stream)
with Workbook(ROOT / "examples/Bond_Scenario_Grid.xlsx") as book:
    sheet = book.add_worksheet("Stress")
    title = book.add_format({"bold": True, "font_size": 18, "font_color": "#164455"})
    label = book.add_format({"bold": True, "font_color": "white", "bg_color": "#164455", "text_wrap": True})
    inputs = book.add_format({"font_color": "#105AC5", "num_format": "#,##0.00"})
    number = book.add_format({"num_format": "#,##0.00;[Red](#,##0.00);0.00"})
    sheet.merge_range("A1:N1", "Fixed-rate bond scenario grid", title)
    sheet.merge_range("A2:N2", "Synthetic positions | blue cells are editable | coupon-date valuation | P&L in the row currency")
    sheet.write("A4", "Yield shock (bp)")
    shocks = [-100, -25, 0, 25, 100]
    for column, shock in enumerate(shocks, 9):
        sheet.write(3, column, shock, inputs)
    sheet.write_row(4, 0, ["Position", "Currency", "Face held", "Annual coupon (%)", "Annual yield (%)",
                            "Periods left", "Payments/year", "Price / 100", "Market value"] + ["Scenario P&L"] * 5, label)
    for row, bond in enumerate(bonds, 5):
        n = row + 1
        sheet.write_row(row, 0, [bond.bond_id, bond.currency])
        sheet.write_row(row, 2, [bond.face_held, bond.coupon_pct, bond.ytm_pct, bond.periods_left, bond.frequency], inputs)
        price, _ = bond.price_duration()
        sheet.write_formula(row, 7, f"=-PV(E{n}/100/G{n},F{n},D{n}/G{n},100)", number, price)
        sheet.write_formula(row, 8, f"=H{n}*C{n}/100", number, price*bond.face_held/100)
        for column, shock in enumerate(shocks, 9):
            letter = xl_col_to_name(column)
            formula = f"=(-PV(($E{n}/100+{letter}$4/10000)/$G{n},$F{n},$D{n}/$G{n},100)-$H{n})*$C{n}/100"
            sheet.write_formula(row, column, formula, number, bond.scenario(shock)["scenario_pnl"])
    sheet.freeze_panes(5, 2)
    sheet.autofilter(4, 0, 4 + len(bonds), 13)
    sheet.set_column("A:A", 22)
    sheet.set_column("B:N", 16)
    sheet.set_row(4, 34)
