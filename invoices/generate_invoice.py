"""
Генератор "Счета на оплату" (стандарт РК) из шаблона template.xlsx.

Использование:
    python3 generate_invoice.py data.json output.xlsx

Формат data.json — см. example_data.py / README в конце файла.
"""
import json
import sys
import os
from datetime import date

import openpyxl

from num2words_ru import sum_in_words_tenge

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "template.xlsx")
COUNTER_PATH = os.path.join(HERE, "counter.json")

ITEM_FIRST_ROW = 27
ITEM_LAST_ROW = 34  # столько строк отформатировано в шаблоне под позиции


def _fmt_money(n):
    return f"{n:,.0f}".replace(",", " ")


def load_supplier(data):
    if data.get("supplier"):
        return data["supplier"]
    profile = data.get("supplier_profile", "default")
    path = os.path.join(HERE, f"supplier_{profile}.json")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def next_invoice_number():
    if os.path.exists(COUNTER_PATH):
        with open(COUNTER_PATH) as f:
            data = json.load(f)
        n = data.get("last", 0) + 1
    else:
        n = 1
    with open(COUNTER_PATH, "w") as f:
        json.dump({"last": n}, f)
    return n


def bump_counter(n):
    last = 0
    if os.path.exists(COUNTER_PATH):
        with open(COUNTER_PATH) as f:
            last = json.load(f).get("last", 0)
    if n > last:
        with open(COUNTER_PATH, "w") as f:
            json.dump({"last": n}, f)


def create_invoice(data: dict, out_path: str):
    wb = openpyxl.load_workbook(TEMPLATE_PATH)
    ws = wb["Счет на оплату"]

    supplier = load_supplier(data)
    buyer = data["buyer"]
    items = data["items"]

    if data.get("invoice_number"):
        invoice_number = data["invoice_number"]
        bump_counter(invoice_number)
    else:
        invoice_number = next_invoice_number()
    invoice_date = data.get("invoice_date") or date.today().strftime("%d.%m.%Y")

    supplier_line = f'{supplier["name"]}, {supplier["address"]}'

    # --- Образец платежного поручения (реквизиты поставщика/бенефициара) ---
    ws["B10"] = supplier_line
    ws["V10"] = supplier["iik"]
    ws["AF10"] = supplier["kbe"]
    ws["B11"] = f'БИН: {supplier["bin"]}'
    ws["B13"] = supplier["bank"]
    ws["V13"] = supplier["bik"]
    if "knp" in supplier:
        ws["AD13"] = supplier["knp"]

    # --- Заголовок счета ---
    ws["B16"] = f"Счет на оплату №{invoice_number} от {invoice_date}"

    # --- Поставщик / Покупатель / Договор ---
    ws["F20"] = supplier_line
    ws["F22"] = f'ИИН/БИН: {buyer["bin"]}, {buyer["name"]}, {buyer["address"]}'
    ws["F24"] = data.get("contract", "Без договора")

    # --- Позиции ---
    if len(items) > (ITEM_LAST_ROW - ITEM_FIRST_ROW + 1):
        raise ValueError(
            f"Шаблон поддерживает максимум {ITEM_LAST_ROW - ITEM_FIRST_ROW + 1} позиций, "
            f"передано {len(items)}. Нужно расширить шаблон."
        )

    for offset in range(ITEM_LAST_ROW - ITEM_FIRST_ROW + 1):
        row = ITEM_FIRST_ROW + offset
        if offset < len(items):
            item = items[offset]
            ws[f"B{row}"] = offset + 1
            ws[f"D{row}"] = item.get("code", "001")
            ws[f"I{row}"] = item["name"]
            ws[f"T{row}"] = item["qty"]
            ws[f"X{row}"] = item.get("unit", "шт")
            ws[f"AA{row}"] = item["price"]
            ws[f"AG{row}"] = f"=AA{row}*T{row}"
        else:
            for col in ("B", "D", "I", "T", "X", "AA", "AG"):
                ws[f"{col}{row}"] = None

    total = sum(item["qty"] * item["price"] for item in items)
    vat_rate = data.get("vat_rate", 0)
    vat_amount = round(total * vat_rate / (100 + vat_rate)) if vat_rate else 0

    ws["AG36"] = f"=SUM(AG{ITEM_FIRST_ROW}:AG{ITEM_LAST_ROW})"
    ws["AG37"] = vat_amount

    ws["B38"] = f"Всего наименований {len(items)}, на сумму {_fmt_money(total)} KZT"
    ws["B39"] = f"Всего к оплате: {sum_in_words_tenge(total)}"

    wb.save(out_path)
    return out_path, invoice_number, invoice_date, total


if __name__ == "__main__":
    data_path, out_path = sys.argv[1], sys.argv[2]
    with open(data_path, encoding="utf-8") as f:
        data = json.load(f)
    path, num, dt, total = create_invoice(data, out_path)
    print(f"Создан счёт №{num} от {dt} на сумму {total} KZT -> {path}")
