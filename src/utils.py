from typing import List, Dict, Optional
from pathlib import Path
from dataclasses import dataclass
from contextlib import contextmanager

import json
import logging

import tabula as tb

logger = logging.getLogger(__name__)


@contextmanager
def sqlachemy_available():
    try:
        from sqlalchemy.exc import SQLAlchemyError
        from flask_sqlalchemy import SQLAlchemy
        yield SQLAlchemy, SQLAlchemyError
    except ImportError:
        yield None


def pdf2json(pdf_path: Path) -> List[Dict[str, str]]:
    """Convert pdf to json"""
    tables = tb.read_pdf(pdf_path, pages="all")
    data: List[Dict[str, str]] = []
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


def read_pdf(pdf_path: Path) -> Optional[List]:
    """Read the pdf and return tables"""
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

with sqlachemy_available() as sqlachemy:
    if sqlachemy:
        from flask_sqlalchemy import Model
        SQLAlchemy, SQLAlchemyError = sqlachemy

        def db2json(db:SQLAlchemy, output_path:Path, t_model:Model) -> Optional[dict]:
            """Convert the database to JSON"""
            try:
                data = t_model.query.all()
                parsed_data = [d.to_dict() for d in data]
                with open(output_path, 'w', encoding='utf-8') as file:
                    json.dump(parsed_data, file, indent=4)
                return parsed_data
            except SQLAlchemyError as e:
                logger.error(f"An error occurred while converting the database to JSON: {e}", exec_info=True)
                return None