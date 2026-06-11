"""
Standalone import script for Table1.xlsx into the ICH Wards database.
Run from the project root:
    venv/bin/python import_records.py
"""
import sys
import os
import random
import pandas as pd
from datetime import datetime, date

# ── Bootstrap Flask app ────────────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from app import create_app, db
from app.models.models import (Patient, Race, MaritalStatus, Occupation,
                                ReferringDoctorHospital, Consultant, Pharmacy,
                                Ward)

app = create_app()

# ── Helpers ────────────────────────────────────────────────────────────────────

def parse_date_flexible(raw):
    """Try multiple date formats; return a date or None."""
    if pd.isna(raw):
        return None
    s = str(raw).strip()
    if not s or s in ('-', 'NIL', 'nil', 'N/A'):
        return None

    # Only a 4-digit year
    if s.isdigit() and len(s) == 4:
        try:
            return date(int(s), 1, 1)
        except ValueError:
            return None

    # Strip trailing garbage like 'YRS', 'yrs'
    s = s.upper().replace('YRS', '').replace('YR', '').strip()

    for fmt in (
        '%d/%m/%Y', '%d/%m/%y',  # 08/10/2012, 08/03/12
        '%Y-%m-%d',              # ISO
        '%d-%m-%Y', '%d-%m-%y',
        '%m/%d/%Y',
        '%d %b %Y', '%d %B %Y',
    ):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue

    # Last resort: pandas
    try:
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:
        return None


def normalise_sex(raw):
    """Map messy sex codes → 'Male' / 'Female' / 'Other'."""
    if pd.isna(raw):
        return 'Other'
    s = str(raw).strip().upper()
    # strip non-alpha suffixes
    s = s.split()[0] if s.split() else s
    if s in ('M', 'MALE'):
        return 'Male'
    if s in ('F', 'FEMALE', 'DF'):
        return 'Female'
    return 'Other'


def normalise_race(raw):
    """Map codes: A/AFRICAN → African, C/COLOURED → Coloured, E/EUROPEAN → European."""
    if pd.isna(raw):
        return 'Other'
    s = str(raw).strip().upper()
    first = s.split()[0] if s.split() else s
    if first in ('A', 'AFRICAN'):
        return 'African'
    if first in ('C', 'COLOURED'):
        return 'Coloured'
    if first in ('E', 'EUROPEAN'):
        return 'European'
    if first in ('M', 'MIXED'):
        return 'Mixed'
    if first in ('UNKNOWN', '-', '.', '`', '"', "'"):
        return 'Other'
    return 'Other'


def get_or_create_race(name):
    obj = Race.query.filter_by(name=name).first()
    if not obj:
        obj = Race(name=name)
        db.session.add(obj)
        db.session.flush()
    return obj


def ensure_defaults():
    """Make sure lookup tables have at least the default entries we need."""
    for ms in ('Single', 'Married', 'Divorced', 'Widowed', 'Unknown'):
        if not MaritalStatus.query.filter_by(name=ms).first():
            db.session.add(MaritalStatus(name=ms))

    for occ in ('Not Applicable', 'Unknown'):
        if not Occupation.query.filter_by(name=occ).first():
            db.session.add(Occupation(name=occ))

    if not ReferringDoctorHospital.query.filter_by(name='Not Applicable').first():
        db.session.add(ReferringDoctorHospital(name='Not Applicable', type='Hospital'))

    if not Consultant.query.filter_by(name='Not Applicable').first():
        db.session.add(Consultant(name='Not Applicable'))

    if not Pharmacy.query.filter_by(name='Not Applicable').first():
        db.session.add(Pharmacy(name='Not Applicable'))

    db.session.flush()


def get_or_create_occupation(raw):
    name = str(raw).strip().title() if (raw and not pd.isna(raw)) else 'Not Applicable'
    name = name[:100]
    obj = Occupation.query.filter_by(name=name).first()
    if not obj:
        obj = Occupation(name=name)
        db.session.add(obj)
        db.session.flush()
    return obj


def next_hospital_id():
    last = Patient.query.order_by(Patient.id.desc()).first()
    if last and last.hospital_id:
        try:
            return str(int(last.hospital_id) + 1).zfill(6)
        except ValueError:
            pass
    return '025000'


# ── Main import ────────────────────────────────────────────────────────────────

def run_import(filepath='Table1.xlsx'):
    df = pd.read_excel(filepath)
    df.columns = [c.strip() for c in df.columns]

    success = 0
    skipped = 0
    errors = 0

    with app.app_context():
        ensure_defaults()
        db.session.commit()

        for idx, row in df.iterrows():
            try:
                # ── Hospital ID ──────────────────────────────────────────────
                raw_hid = row.get('HOSPITAL NUMBER')
                if pd.isna(raw_hid) or str(raw_hid).strip() == '':
                    skipped += 1
                    continue

                hospital_id = str(raw_hid).strip().zfill(6)

                # Skip duplicates
                if Patient.query.filter_by(hospital_id=hospital_id).first():
                    skipped += 1
                    continue

                # ── Names ────────────────────────────────────────────────────
                first_names = str(row.get('NAME', '') or '').strip() or 'Unknown'
                surname     = str(row.get('SURNAME', '') or '').strip() or 'Unknown'
                first_names = first_names[:100]
                surname     = surname[:100]

                # ── Dates ────────────────────────────────────────────────────
                dob           = parse_date_flexible(row.get('DATE OF BIRTH'))
                admission_dt  = parse_date_flexible(row.get('DATE OF ADMISSION'))
                discharge_dt  = parse_date_flexible(row.get('DATE OF DISCHARGE'))

                if dob is None:
                    dob = date(1970, 1, 1)
                if admission_dt is None:
                    admission_dt = datetime.now()
                else:
                    admission_dt = datetime(admission_dt.year, admission_dt.month, admission_dt.day)

                if discharge_dt is not None:
                    discharge_dt = datetime(discharge_dt.year, discharge_dt.month, discharge_dt.day)

                # Age from DOB
                today = date.today()
                age = today.year - dob.year
                if (today.month, today.day) < (dob.month, dob.day):
                    age -= 1
                age = max(0, min(age, 150))

                # ── Demographics ─────────────────────────────────────────────
                sex  = normalise_sex(row.get('SEX'))
                race = normalise_race(row.get('RACE'))
                race_obj = get_or_create_race(race)

                occ_raw = row.get('OCCUPATION')
                occ_obj = get_or_create_occupation(occ_raw)

                religion = str(row.get('RELIGION', '') or 'Not Applicable').strip()[:50]
                if not religion or religion in ('-', 'nan', 'NIL'):
                    religion = 'Not Applicable'

                # ── Address / Next of Kin ────────────────────────────────────
                address = str(row.get('ADDRESS', '') or 'Not Provided').strip()[:500] or 'Not Provided'

                nok_name = str(row.get('NEXT OF KIN AND NAME', '') or 'Not Provided').strip()[:100] or 'Not Provided'
                nok_addr = str(row.get('NEXT OF KIN ADDRESS', '') or 'Not Provided').strip()[:500] or 'Not Provided'

                # ── Medical ──────────────────────────────────────────────────
                diagnosis = str(row.get('DIAGNOSIS', '') or 'Not Provided').strip()[:2000] or 'Not Provided'

                # ── Status ───────────────────────────────────────────────────
                status = 'Discharged' if discharge_dt else 'Admitted'

                # ── Build Patient ────────────────────────────────────────────
                patient = Patient(
                    hospital_id=hospital_id,
                    first_names=first_names,
                    surname=surname,
                    date_of_birth=dob,
                    age=age,
                    sex=sex,
                    race=race_obj.name,
                    marital_status='Unknown',
                    occupation=occ_obj.name,
                    religion=religion,
                    residential_address=address,
                    contact_number='Not Provided',
                    next_of_kin_name=nok_name,
                    next_of_kin_address=nok_addr,
                    next_of_kin_relationship='Other',
                    admission_datetime=admission_dt,
                    referring_doctor_hospital='Not Applicable',
                    diagnosis=diagnosis,
                    doctor_name='Not Provided',
                    consultant_name='Not Applicable',
                    pharmacy_name='Not Applicable',
                    discharge_datetime=discharge_dt,
                    status=status,
                )
                db.session.add(patient)
                db.session.commit()
                success += 1

                if success % 200 == 0:
                    print(f'  ... {success} records imported so far')

            except Exception as e:
                db.session.rollback()
                errors += 1
                if errors <= 10:
                    print(f'  Row {idx}: ERROR — {e}')

        print(f'\n✅ Done.')
        print(f'   Imported : {success}')
        print(f'   Skipped  : {skipped}  (missing hospital ID or duplicate)')
        print(f'   Errors   : {errors}')


if __name__ == '__main__':
    filepath = sys.argv[1] if len(sys.argv) > 1 else 'Table1.xlsx'
    print(f'Importing from {filepath} …')
    run_import(filepath)
