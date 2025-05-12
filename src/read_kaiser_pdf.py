#!/usr/bin/env python3
from pathlib import Path
import sys
import tabula as tb
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_pdf(pdf_path):
    """Read the pdf and return tables"""
    try:
        tables = tb.read_pdf(pdf_path, pages="all")
        cleaned_tables = []
        for table in tables:
            cleaned_tables.append(table)
        return cleaned_tables
    except Exception as e:
        logger.error(f"An error occurred while reading the PDF: {e}")
        return None


pdf_path = Path('../datasource/KaiserInternational.pdf')
tables = read_pdf(pdf_path)

if tables:
    print(f"Found {len(tables)} tables in the PDF")
    for i, table in enumerate(tables):
        print(f"\nTable {i+1} structure:")
        print(f"Columns: {table.columns.tolist()}")
        print(f"First few rows:")
        print(table.head())
else:
    print("Failed to read PDF or no tables found")
