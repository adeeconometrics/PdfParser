import sqlite3
from pathlib import Path
from dataclasses import dataclass, astuple
from argparse import ArgumentParser, ArgumentError
# from camelot.utils import strip_text

import tabula as tb

@dataclass
class CarSalesFields:
    No:int
    Model:int = None
    BrandAndVariant:str = None
    Transmission:str = None
    PlateNo:str = None
    Mileage:int = None
    Color:str = None
    SellingPrice:int = None

def create_db(db_path:Path) -> Path:
    conn = sqlite3.connect(db_path)
    curr = conn.cursor()
    curr.execute(
        """
        CREATE TABLE IF NOT EXISTS CarSales (
            No TEXT,
            Model TEXT,
            BrandAndVariant TEXT,
            Transmission TEXT,
            PlateNo TEXT,
            Mileage INTEGER,
            Color TEXT,
            SellingPrice INTEGER
        )
        """
    )
    conn.commit()
    conn.close()
    return db_path


def parse_pdf2db(pdf_path:Path, db_path:Path) -> Path:
    tables = tb.read_pdf(pdf_path, pages='3-last_page')
    conn = sqlite3.connect(db_path)
    curr = conn.cursor()
    for table in tables:
        table = table.dropna()
        for row in table.itertuples():
            if any(cell is None for cell in row):
                continue
            fields = CarSalesFields(*row[1:])
            fields_tuple = astuple(fields)
            print(f"Inserting data: {fields_tuple}")
            curr.execute(
                """
                INSERT INTO CarSales VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                fields_tuple
            )
    conn.commit()
    conn.close()
    return db_path

if __name__ == '__main__':
    parser = ArgumentParser(description='Parse PDF to SQLite')
    parser.add_argument('-pdf_path', required=True, type=Path, help='Path to PDF file')
    parser.add_argument('-db_path', required=True, type=Path, help='Path to SQLite file')

    args = parser.parse_args()


    try:
        create_db(args.db_path)
        parse_pdf2db(args.pdf_path, args.db_path)
    except ArgumentError as e:
        print(f'Error: {e}')