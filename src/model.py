
from typing import Optional, Dict
from dataclasses import dataclass

from contextlib import contextmanager

from flask import Flask, render_template, request

@contextmanager
def sqlachemy_available():
    try:
        from sqlalchemy.exc import SQLAlchemyError
        from flask_sqlalchemy import SQLAlchemy
        yield SQLAlchemy, SQLAlchemyError
    except ImportError:
        yield None

with sqlachemy_available() as sqlachemy:
    if sqlachemy:
        SQLAlchemy, SQLAlchemyError = sqlachemy
        app = Flask(__name__, template_folder='templates')
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///carsales.db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db = SQLAlchemy(app)

        @dataclass
        class CarSalesFields(db.Model):
            __tablename__ = 'carsales'

            def __init__(self, 
                         t_No:int, 
                         t_Model:int, 
                         t_BrandAndVariant:str, 
                         t_Transmission:str, 
                         t_PlateNo:str, 
                         t_Mileage:int, 
                         t_Color:str, 
                         t_SellingPrice:int) -> None:
                self.No = t_No
                self.Model = t_Model
                self.BrandAndVariant = t_BrandAndVariant
                self.Transmission = t_Transmission
                self.PlateNo = t_PlateNo
                self.Mileage = t_Mileage
                self.Color = t_Color
                self.SellingPrice = t_SellingPrice

            No = db.Column(db.Integer)
            Model = db.Column(db.Integer)
            BrandAndVariant = db.Column(db.String)
            Transmission = db.Column(db.String)
            PlateNo = db.Column(db.String, primary_key=True)
            Mileage = db.Column(db.Integer)
            Color = db.Column(db.String)
            SellingPrice = db.Column(db.Integer)

            def to_dict(self) -> dict:
                """Convert the fields to dictionary"""
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
