from typing import List,Dict, Optional

from pathlib import Path
from argparse import ArgumentParser, ArgumentError
from dataclasses import dataclass

import json
import logging


import tabula as tb

@dataclass
class CarSalesModel:
    No:int
    Model:int = None
    BrandAndVariant:str = None
    Transmission:str = None
    PlateNo:str = None
    Mileage:int = None
    Color:str = None
    SellingPrice:int = None

    def to_dict(self) -> dict:
        return {
            'id': self.No,
            'model': self.Model,
            'brand': self.BrandAndVariant,
            'transmission': self.Transmission,
            'plate_no': self.PlateNo,
            'mileage': self.Mileage,
            'color': self.Color,
            'price': self.SellingPrice
        }

def pdf2json(pdf_path:Path)-> List[Dict[str, str]]:
    tables = tb.read_pdf(pdf_path, pages="all")
    data:List[Dict[str,str]] = []
    for table in tables:
        if len(table.columns) < 8:
            continue
        table = table.dropna()
        for row in table.itertuples():
            if any(cell is None for cell in row):
                continue
            fields = CarSalesModel(*row[1:])
            data.append(fields.to_dict())
    return data


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('-pdf_path', type=Path, help='Path to the PDF file')
    parser.add_argument('-json_path', type=Path, help='Path to the JSON file')
    args = parser.parse_args()
    data = pdf2json(args.pdf_path)

    try:
        with open(args.json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)

        print(f"Data saved to {args.json_path}")
    except ArgumentError as e:
        logging.error(f"An error occurred while saving the data: {e}", exc_info=True)