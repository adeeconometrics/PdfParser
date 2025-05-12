from typing import Optional, Dict, List
from dataclasses import dataclass, field
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()

# Base Models


class Region(db.Model):
    __tablename__ = 'region'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)

    provinces = relationship('Province', back_populates='region')

    def __repr__(self):
        return f"<Region {self.name}>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name
        }


class Province(db.Model):
    __tablename__ = 'province'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    region_id = Column(Integer, ForeignKey('region.id'), nullable=False)

    region = relationship('Region', back_populates='provinces')
    cities = relationship('City', back_populates='province')

    def __repr__(self):
        return f"<Province {self.name}>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'region_id': self.region_id
        }


class City(db.Model):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    province_id = Column(Integer, ForeignKey('province.id'), nullable=False)

    province = relationship('Province', back_populates='cities')
    dental_clinics = relationship('DentalClinic', back_populates='city')

    def __repr__(self):
        return f"<City {self.name}>"

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'province_id': self.province_id
        }


class DentalClinic(db.Model):
    __tablename__ = 'dental_clinic'

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_no = Column(Integer, nullable=True)  # Original # from PDF
    dentist_name = Column(String(200), nullable=False)
    clinic_name = Column(String(200), nullable=True)
    address = Column(String(500), nullable=True)
    contact_number = Column(String(200), nullable=True)
    schedule = Column(String(200), nullable=True)
    city_id = Column(Integer, ForeignKey('city.id'), nullable=False)

    city = relationship('City', back_populates='dental_clinics')

    def __repr__(self):
        return f"<DentalClinic {self.clinic_name} - {self.dentist_name}>"

    def to_dict(self) -> dict:
        province_name = self.city.province.name if self.city and self.city.province else None
        region_name = self.city.province.region.name if self.city and self.city.province and self.city.province.region else None

        return {
            'id': self.id,
            'entry_no': self.entry_no,
            'dentist_name': self.dentist_name,
            'clinic_name': self.clinic_name,
            'address': self.address,
            'city': self.city.name if self.city else None,
            'province': province_name,
            'region': region_name,
            'contact_number': self.contact_number,
            'schedule': self.schedule
        }

# Data class for non-database use (parsing)


@dataclass
class DentalClinicModel:
    entry_no: int
    dentist_name: str
    clinic_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    region: Optional[str] = None
    contact_number: Optional[str] = None
    schedule: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            'entry_no': self.entry_no,
            'dentist_name': self.dentist_name,
            'clinic_name': self.clinic_name,
            'address': self.address,
            'city': self.city,
            'province': self.province,
            'region': self.region,
            'contact_number': self.contact_number,
            'schedule': self.schedule
        }
