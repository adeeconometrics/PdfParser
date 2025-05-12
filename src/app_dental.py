from typing import Dict, List
from pathlib import Path
import json
import logging
from dotenv import load_dotenv
import os

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

from dental_model import db, Region, Province, City, DentalClinic
from dental_utils import load_dental_json

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__, template_folder='templates')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../datasource/dentalclinics.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Load JSON data
json_path = Path('../datasource/dentalclinicslist.json')
clinics_data = load_dental_json(json_path)
if not clinics_data:
    logger.error(f"Failed to load data from {json_path}")

# Load environment variables from .env file
load_dotenv()

# Retrieve the Google Maps API key
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')


@app.context_processor
def inject_api_key():
    """Inject the API key into all templates."""
    return {'google_maps_api_key': GOOGLE_MAPS_API_KEY}


@app.route('/')
def index():
    return render_template('dental_clinics.html', title="Dental Clinics Directory")


@app.route('/api/data')
def data():
    """API endpoint for DataTables to fetch dental clinic data"""
    search = request.args.get('search[value]')
    if search:
        search_lower = search.lower()
        filtered_clinics = [
            clinic for clinic in clinics_data
            if any(search_lower in str(value).lower() if value else False
                   for value in clinic.values())
        ]
    else:
        filtered_clinics = clinics_data

    total_filtered = len(filtered_clinics)

    # Sorting
    order = []
    index = 0
    while True:
        col_index = request.args.get(f'order[{index}][column]')
        if col_index is None:
            break
        col_name = request.args.get(f'columns[{col_index}][data]')
        if col_name not in ('entry_no', 'dentist_name', 'clinic_name', 'address',
                            'city', 'province', 'region', 'contact_number', 'schedule'):
            break

        descending = request.args.get(f'order[{index}][dir]') == 'desc'
        order.append((col_name, descending))
        index += 1

    for col_name, descending in order:
        filtered_clinics.sort(
            key=lambda clinic: str(clinic.get(col_name, '')).lower(
            ) if clinic.get(col_name) else '',
            reverse=descending
        )

    # Pagination
    start = request.args.get('start', 0, type=int)
    length = request.args.get('length', -1, type=int)
    if length > 0:
        paginated_clinics = filtered_clinics[start:start+length]
    else:
        paginated_clinics = filtered_clinics

    # Response
    return {
        'data': paginated_clinics,
        'recordsTotal': len(clinics_data),
        'recordsFiltered': total_filtered,
        'draw': request.args.get('draw', 0, type=int)
    }


@app.route('/api/regions')
def get_regions():
    """API endpoint to get all regions"""
    regions_dict = {}

    # Group clinics by region
    for clinic in clinics_data:
        region = clinic.get('region')
        if region and region not in regions_dict:
            regions_dict[region] = {
                'name': region,
                'provinces': {}
            }

        province = clinic.get('province')
        if region and province:
            if province not in regions_dict[region]['provinces']:
                regions_dict[region]['provinces'][province] = {
                    'name': province,
                    'cities': set()
                }

        city = clinic.get('city')
        if region and province and city:
            regions_dict[region]['provinces'][province]['cities'].add(city)

    # Convert to list format
    regions_list = []
    for region_name, region_data in regions_dict.items():
        provinces_list = []
        for province_name, province_data in region_data['provinces'].items():
            provinces_list.append({
                'name': province_name,
                'cities': sorted(list(province_data['cities']))
            })

        regions_list.append({
            'name': region_name,
            'provinces': provinces_list
        })

    return jsonify(regions_list)


@app.route('/init_db')
def init_database():
    """Initialize database with data from JSON"""
    with app.app_context():
        db.create_all()

        # Clear existing data
        DentalClinic.query.delete()
        City.query.delete()
        Province.query.delete()
        Region.query.delete()

        # Dictionary to keep track of entities
        regions_dict = {}
        provinces_dict = {}
        cities_dict = {}

        # Process each clinic
        for clinic_data in clinics_data:
            # Create/get Region
            region_name = clinic_data.get('region')
            if not region_name:
                continue

            if region_name not in regions_dict:
                region = Region(name=region_name)
                db.session.add(region)
                db.session.flush()  # Get ID before commit
                regions_dict[region_name] = region
            else:
                region = regions_dict[region_name]

            # Create/get Province
            province_name = clinic_data.get('province')
            if not province_name:
                continue

            province_key = f"{region_name}:{province_name}"
            if province_key not in provinces_dict:
                province = Province(name=province_name, region_id=region.id)
                db.session.add(province)
                db.session.flush()
                provinces_dict[province_key] = province
            else:
                province = provinces_dict[province_key]

            # Create/get City
            city_name = clinic_data.get('city')
            if not city_name:
                continue

            city_key = f"{province_key}:{city_name}"
            if city_key not in cities_dict:
                city = City(name=city_name, province_id=province.id)
                db.session.add(city)
                db.session.flush()
                cities_dict[city_key] = city
            else:
                city = cities_dict[city_key]

            # Create Dental Clinic
            clinic = DentalClinic(
                entry_no=clinic_data.get('entry_no'),
                dentist_name=clinic_data.get('dentist_name', ''),
                clinic_name=clinic_data.get('clinic_name'),
                address=clinic_data.get('address'),
                contact_number=clinic_data.get('contact_number'),
                schedule=clinic_data.get('schedule'),
                city_id=city.id
            )
            db.session.add(clinic)

        db.session.commit()

        return jsonify({
            "success": True,
            "message": f"Database initialized with {len(clinics_data)} clinics",
            "counts": {
                "regions": len(regions_dict),
                "provinces": len(provinces_dict),
                "cities": len(cities_dict),
                "clinics": len(clinics_data)
            }
        })


@app.route('/clinic/<int:entry_no>')
def clinic_detail(entry_no):
    """Display detailed information for a specific clinic"""
    # Find the clinic by entry_no
    clinic = next((c for c in clinics_data if c.get(
        'entry_no') == entry_no), None)

    if not clinic:
        return render_template('404.html', message="Clinic not found"), 404

    # Process contact numbers for better display
    contact_numbers = []
    if clinic.get('contact_number'):
        contact_numbers = [c.strip()
                           for c in clinic['contact_number'].split('/') if c.strip()]

    clinic_data = {**clinic, 'contact_numbers': contact_numbers}

    return render_template('clinic_detail.html',
                           title=f"{clinic.get('clinic_name', 'Dental Clinic')} Details",
                           clinic=clinic_data)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(debug=True)
