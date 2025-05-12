#!/usr/bin/env python3
from pathlib import Path
import logging
import pandas as pd

from dental_utils import dental_pdf_to_json, save_dental_json

# Setup logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    # Define paths
    pdf_path = Path('../datasource/KaiserInternational.pdf')
    json_path = Path('../datasource/dentalclinicslist.json')

    # Check if PDF exists
    if not pdf_path.exists():
        logger.error(f"PDF file not found: {pdf_path}")
        return

    # Convert PDF to JSON
    logger.info(f"Converting {pdf_path} to JSON...")
    clinics = dental_pdf_to_json(pdf_path)
    logger.info(f"Extracted {len(clinics)} dental clinics")

    # Save to JSON
    save_dental_json(clinics, json_path)
    logger.info(f"Saved dental clinics to {json_path}")

    # Print sample
    if clinics:
        logger.info("Sample clinic data:")
        sample = pd.DataFrame(clinics[:5])
        print(sample)
    else:
        logger.warning("No clinic data found")


if __name__ == "__main__":
    main()
