from typing import List, Dict, Optional, Tuple
from pathlib import Path
import json
import logging
import re
import pandas as pd
import tabula as tb

from dental_model import DentalClinicModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_pdf(pdf_path: Path) -> Optional[List]:
    """Read the pdf and return tables"""
    try:
        tables = tb.read_pdf(pdf_path, pages="all")
        return tables
    except Exception as e:
        logger.error(f"An error occurred while reading the PDF: {e}")
        return None


def clean_text(text: str) -> str:
    """Clean text by removing extra spaces and newlines"""
    if not isinstance(text, str):
        return str(text) if text is not None else ""

    # Replace multiple spaces, tabs and newlines with a single space
    cleaned = re.sub(r'\s+', ' ', text).strip()
    # Replace '\r' with space
    cleaned = cleaned.replace('\r', ' ').strip()
    return cleaned


def extract_columns(row, columns):
    """Extract column values from a row, handling different formats"""
    result = {}
    for col in columns:
        if col in row:
            result[col] = clean_text(row[col])
        else:
            result[col] = None
    return result


def dental_pdf_to_json(pdf_path: Path) -> List[Dict]:
    """Convert dental clinic PDF to JSON data"""
    tables = read_pdf(pdf_path)
    if not tables:
        logger.error("Failed to read PDF or no tables found")
        return []

    all_clinics = []
    standard_columns = ['#', 'DENTIST NAME', 'CLINIC NAME', 'ADDRESS',
                        'CITY/TOWN', 'PROVINCE', 'REGION', 'CONTACT NUMBER', 'SCHEDULE']

    for table_index, table in enumerate(tables):
        logger.info(f"Processing table {table_index+1}")

        # Skip tables with inconsistent structure
        if len(table.columns) < 8:
            logger.warning(
                f"Table {table_index+1} has less than 8 columns, skipping")
            continue

        # Map columns to standard names when possible
        col_mapping = {}
        for std_col in standard_columns:
            for col in table.columns:
                if std_col in str(col):
                    col_mapping[std_col] = col
                    break

        # Process rows
        for _, row in table.iterrows():
            entry_data = {}

            # For standard column tables
            if len(col_mapping) >= 7:  # If we have most standard columns
                for std_col, df_col in col_mapping.items():
                    if std_col == '#':
                        try:
                            entry_data['entry_no'] = int(
                                float(row[df_col])) if pd.notna(row[df_col]) else None
                        except (ValueError, TypeError):
                            entry_data['entry_no'] = None
                    else:
                        entry_data[std_col.lower().replace('/', '_').replace(' ', '_')
                                   ] = clean_text(row[df_col]) if pd.notna(row[df_col]) else None

            # For non-standard tables, try to extract data from any column
            else:
                row_data = {str(col): str(row[col]) if pd.notna(
                    row[col]) else "" for col in table.columns}
                combined_data = " ".join(row_data.values())

                # Skip empty rows
                if not combined_data.strip():
                    continue

                # Try to extract entry number
                entry_match = re.search(r'^\s*(\d+)', combined_data)
                if entry_match:
                    entry_data['entry_no'] = int(entry_match.group(1))

                # Extract other fields based on patterns
                # This is a simplified approach and might need refinement
                name_match = re.search(r'DR\.\s+([A-Z\s]+)', combined_data)
                if name_match:
                    entry_data['dentist_name'] = name_match.group(0)

            # Only add if we have a dentist name
            if 'dentist_name' in entry_data and entry_data['dentist_name']:
                try:
                    clinic = DentalClinicModel(
                        entry_no=entry_data.get('entry_no', None),
                        dentist_name=entry_data.get('dentist_name', ""),
                        clinic_name=entry_data.get('clinic_name', None),
                        address=entry_data.get('address', None),
                        city=entry_data.get('city_town', None),
                        province=entry_data.get('province', None),
                        region=entry_data.get('region', None),
                        contact_number=entry_data.get('contact_number', None),
                        schedule=entry_data.get('schedule', None),
                    )
                    all_clinics.append(clinic.to_dict())
                except Exception as e:
                    logger.error(f"Error creating clinic model: {e}")

    return all_clinics


def save_dental_json(clinics: List[Dict], output_path: Path) -> None:
    """Save dental clinic data as JSON"""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(clinics, f, indent=4)
        logger.info(f"Saved {len(clinics)} clinics to {output_path}")
    except Exception as e:
        logger.error(f"Error saving JSON: {e}")


def load_dental_json(json_path: Path) -> List[Dict]:
    """Load dental clinic data from JSON"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        return []
