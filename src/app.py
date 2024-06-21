from pathlib import Path
from argparse import ArgumentParser, ArgumentError
from dataclasses import dataclass, astuple


from flask_sqlalchemy import SQLAlchemy
from flask import Flask, render_template, request

import tabula as tb

app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carsales.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class CarSalesFields(db.Model):
    __tablename__ = 'carsales'

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

def create_db(db_path:Path) -> Path:
    db.create_all()
    return db_path

def parse_pdf2db(pdf_path:Path) -> Path:
    """parse the pdf table to SQLAlchemy database
    """
    try:
        tables = tb.read_pdf(pdf_path, pages='3-')
        for table in tables:
            table = table.dropna()
            for row in table.itertuples():
                if any(cell is None for cell in row):
                    continue
                fields = CarSalesFields(*row[1:])
                db.session.add(fields)
        db.session.commit()
    except Exception as e:
        print(f"An error occurred: {e}")
        db.session.rollback()
    finally:
        db.session.close()
    return pdf_path

@app.route('/')
def index():
    cars = CarSalesFields.query
    return render_template('table_generator.html', title = "Cars ni Baby", cars=cars)

@app.route('/api/data')
def data():
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
        
    total_filtered:int = query.count()

    order = []
    index:int = 0

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

    args = parser.parse_args()

    try:
        with app.app_context():
            db.create_all()
            parse_pdf2db(args.pdf_path)
        
        app.run(debug=True)

    except ArgumentError as e:
        print(f'Error: {e}')
        