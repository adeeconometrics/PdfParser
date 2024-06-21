from typing import List, Optional
from pathlib import Path
from argparse import ArgumentParser, ArgumentError
from dataclasses import dataclass

import json

import logging


from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, render_template, request

import tabula as tb

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carsales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

logger = logging.getLogger(__name__)

@dataclass
class CarSalesFields(db.Model):
    __tablename__ = 'carsales'

    def __init__(self, No, Model, BrandAndVariant, Transmission, PlateNo, Mileage, Color, SellingPrice) -> None:
        self.No = No
        self.Model = Model
        self.BrandAndVariant = BrandAndVariant
        self.Transmission = Transmission
        self.PlateNo = PlateNo
        self.Mileage = Mileage
        self.Color = Color
        self.SellingPrice = SellingPrice

    No = db.Column(db.Integer)
    Model = db.Column(db.Integer)
    BrandAndVariant = db.Column(db.String)
    Transmission = db.Column(db.String)
    PlateNo = db.Column(db.String, primary_key=True)
    Mileage = db.Column(db.Integer)
    Color = db.Column(db.String)
    SellingPrice = db.Column(db.Integer)

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

def read_pdf(pdf_path: Path) -> Optional[List]:
    """Read the pdf and return tables
    """
    try:
        tables = tb.read_pdf(pdf_path, pages="all")
        cleaned_tables = []
        for table in tables:
            if len(table.columns) < 8:
                continue
            table = table.dropna()
            cleaned_tables.append(table)
        return cleaned_tables
    except Exception as e:
        logger.error(f"An error occurred while reading the PDF: {e}", exec_info=True)
        return None


def parse_pdf2db(tables: Optional[List]) -> Optional[SQLAlchemy]:
    """parse the pdf table to SQLAlchemy database
    """
    if tables is None:
        return None
    try:
        with db.session.begin():
            for table in tables:
                for row in table.itertuples():
                    if any(cell is None for cell in row):
                        continue
                    fields = CarSalesFields(*row[1:])
                    db.session.add(fields)
            db.session.commit()
        return db
    except SQLAlchemyError as e:
        logger.error(f"An error occurred while updating the database: {e}", exec_info=True)
        db.session.rollback()
        return None


def db2json(db: SQLAlchemy, output_path:Path) -> dict:
    """Convert the database to JSON
    """
    try:
        data = CarSalesFields.query.all()

        car_data = [car.to_dict() for car in data]
        with open(output_path, 'w') as f:
            json.dump(car_data, f, indent=4)
        return car_data
    except SQLAlchemyError as e:
        logger.error(f"An error occurred while converting the database to JSON: {e}", exec_info=True)
        return {}

@app.route('/')
def index() -> str:
    cars = CarSalesFields.query
    return render_template('table_generator.html', title="Car Selection", cars=cars)


@app.route('/api/data')
def data() -> dict:
    query = CarSalesFields.query

    search = request.args.get('search[value]')
    if search:
        query = query.filter(
            db.or_(
                CarSalesFields.No.like(f'%{search}%'),
                CarSalesFields.Model.like(f'%{search}%'),
                CarSalesFields.BrandAndVariant.like(f'%{search}%'),
                CarSalesFields.Transmission.like(f'%{search}%'),
                CarSalesFields.PlateNo.like(f'%{search}%'),
                CarSalesFields.Mileage.like(f'%{search}%'),
                CarSalesFields.Color.like(f'%{search}%'),
                CarSalesFields.SellingPrice.like(f'%{search}%')
            ))

    total_filtered: int = query.count()

    order = []
    index: int = 0

    while True:
        col_index = request.args.get(f'order[{index}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if col_name not in ('No', 'Model', 'BrandAndVariant', 'Transmission', 'PlateNo', 'Mileage', 'Color', 'SellingPrice'):
            break

        descending = request.args.get(f'order[{index}][dir]') == 'desc'
        col = getattr(CarSalesFields, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        index += 1

    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', type=int)
    query = query.offset(start).limit(length)

    # response
    return {
        'data': [car.to_dict() for car in query],
        'recordsTotal': CarSalesFields.query.count(),
        'recordsFiltered': total_filtered,
        'draw': request.args.get('draw', 0, type=int)
    }


if __name__ == '__main__':
    parser = ArgumentParser(description='Parse PDF to SQLite')
    parser.add_argument('-pdf_path', required=True,
                        type=Path, help='Path to PDF file')
    parser.add_argument('--json_path', default=None,
                        type=Path, help='Path to JSON file')

    args = parser.parse_args()

    try:
        if args.json_path is not None:
            with app.app_context():
                db.drop_all()
                db.create_all()
                tables = read_pdf(args.pdf_path)
                parse_pdf2db(tables)
                db2json(db, args.json_path)
            print(f"Data has been converted to JSON and saved to {args.json_path}")
        else:
            with app.app_context():
                db.drop_all()
                db.create_all()
                tables = read_pdf(args.pdf_path)
                parse_pdf2db(tables)

            app.run(debug=True)

    except ArgumentError as e:
        print(f'Error: {e}')
