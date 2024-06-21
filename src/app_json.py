from typing import List,Dict

from pathlib import Path
from argparse import ArgumentParser, ArgumentError
from dataclasses import dataclass

import json
import logging

from flask import Flask, render_template, request
import tabula as tb

app = Flask(__name__, template_folder='templates')
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


@app.route('/')
def index() -> str:
    return render_template('table_generator.html', title="Car Selection")


@app.route('/api/data')
def data() -> dict:
    search = request.args.get('search[value]')
    if search:
        search_lower = search.lower()
        filtered_cars = [
            car for car in cars if any(search_lower in str(value).lower() for value in car.values())
        ]
    else:
        filtered_cars = cars

    total_filtered = len(filtered_cars)

    # Sorting
    order = []
    index = 0
    while True:
        col_index = request.args.get(f'order[{index}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if col_name not in ('id', 'model', 'brand', 'transmission', 'plate_no', 'mileage', 'color', 'price'):
            break

        descending = request.args.get(f'order[{index}][dir]') == 'desc'
        order.append((col_name, descending))
        index += 1

    for col_name, descending in order:
        if col_name in ('transmission', 'model', 'color'):
            filtered_cars.sort(
                key=lambda car: str(car[col_name]), reverse=descending)
        elif col_name == 'mileage':
            filtered_cars.sort(
                key=lambda car: float('inf') if str(car[col_name]).replace(
                    ',', '') == '-' else int(str(car[col_name]).replace(',', '')),
                reverse=descending)
        elif col_name == 'price':
            filtered_cars.sort(
                key=lambda car: float(car[col_name].replace(',', '')),
                reverse=descending)
        else:
            filtered_cars.sort(key=lambda car: car[col_name], reverse=descending)

    # Pagination
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', type=int)
    paginated_cars = filtered_cars[start:start+length]

    # Response
    return {
        'data': paginated_cars,
        'recordsTotal': len(cars),
        'recordsFiltered': total_filtered,
        'draw': request.args.get('draw', 0, type=int)
    }

if __name__ == '__main__':
    try:
        json_path = Path('./datasource/carsaleslist.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            cars = json.load(f)
        app.run(debug=True)

    except ArgumentError as e:
        logging.error(f"An error occurred while saving the data: {e}", exc_info=True)