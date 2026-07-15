import sys
import pandas as pd
import os

# Add tools directory to sys.path so we can import validate_fai_sl
sys.path.append(os.path.abspath('tools'))
from validate_fai_sl import validate_fai_sl, get_license_details_byname

# Mapping for common ISO 3166-1 alpha-3 to IOC codes
# This is a subset. In a real scenario, we might want a more complete mapping.
ISO_TO_IOC = {
    'DEU': 'GER',
    'DNK': 'DEN',
    'USA': 'USA',
    'GBR': 'GBR',
    'FRA': 'FRA',
    'ESP': 'ESP',
    'ITA': 'ITA',
    'CZE': 'CZE',
    'POL': 'POL',
    'AUT': 'AUT',
    'BEL': 'BEL',
    'CHE': 'SUI',
    'NLD': 'NED',
    'FIN': 'FIN',
    'SWE': 'SWE',
    'NOR': 'NOR',
    'HRV': 'CRO',
    'ROU': 'ROU',
    'ESP': 'ESP',
    'HUN': 'HUN',
    'SVK': 'SVK',
    'CZE': 'CZE',
    'DNK': 'DEN',
    'ARG': 'ARG',
    'LTU': 'LTU',
    'EST': 'EST',
    'LVA': 'LVA',
}

def get_ioc(iso_code):
    return ISO_TO_IOC.get(iso_code.upper(), iso_code.upper())

def extract_numeric_id(lic_str):
    if pd.isna(lic_str) or lic_str == '':
        return None
    import re
    match = re.search(r'[\d.]+', str(lic_str))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def main():
    excel_file = 'egc2026-ENTRIES-01.07.2026.xlsx'
    if not os.path.exists(excel_file):
        print(f"Error: {excel_file} not found.")
        return

    df = pd.read_excel(excel_file)

    report = []

    print(f"Processing {len(df)} pilots from {excel_file}...\n")

    for idx, row in df.iterrows():
        first_name = str(row['first_name']).strip() if pd.notna(row['first_name']) else ''
        last_name = str(row['last_name']).strip() if pd.notna(row['last_name']) else ''
        country_iso = str(row['country_code']).strip() if pd.notna(row['country_code']) else ''
        fai_lic_raw = row['fai_licence_number']

        ioc_country = get_ioc(country_iso)
        pilot_name = f"{first_name} {last_name}".strip()

        if not pilot_name:
            continue

        status = ""
        details = ""

        # Case 1: License number is provided
        if pd.notna(fai_lic_raw) and str(fai_lic_raw).strip() != '':
            lic_str = str(fai_lic_raw).strip()

            # Try validating with the raw string first (in case it's a valid format)
            # But validate_fai_sl might fail if it's not numeric.
            # Let's try numeric extraction as a fallback or primary.

            valid = False
            # Try numeric match
            numeric_id = extract_numeric_id(lic_str)
            if numeric_id is not None:
                if validate_fai_sl(ioc_country, sl=numeric_id, prt=False):
                    valid = True

            # If numeric didn't work, try the raw string (some formats might be handled)
            if not valid:
                if validate_fai_sl(ioc_country, sl=lic_str, prt=False):
                    valid = True

            if valid:
                status = "VALID"
                details = f"License: {lic_str}"
            else:
                # Validation failed, try to find by name
                found_lic = get_license_details_byname(ioc_country, givenname=first_name, surname=last_name)
                if found_lic:
                    new_lic = found_lic.get('idlicencee')
                    status = "FOUND BY NAME"
                    details = f"Correct License: {new_lic} (Provided: {lic_str})"
                else:
                    status = "INVALID"
                    details = f"License {lic_str} not found in {ioc_country} records"

        # Case 2: No license number provided
        else:
            found_lic = get_license_details_byname(ioc_country, givenname=first_name, surname=last_name)
            if found_lic:
                new_lic = found_lic.get('idlicencee')
                status = "FOUND BY NAME"
                details = f"License: {new_lic}"
            else:
                status = "NO LICENSE PROVIDED"
                details = "No license number in entry and not found by name"

        report.append({
            'Name': pilot_name,
            'Country': ioc_country,
            'Status': status,
            'Details': details
        })
        print(f"{pilot_name:<25} | {ioc_country:<5} | {status:<20} | {details}")

    # Final Report Summary
    print("\n" + "="*80)
    print("FINAL VALIDATION REPORT")
    print("="*80)

    summary = {
        'VALID': 0,
        'FOUND BY NAME': 0,
        'INVALID': 0,
        'NO LICENSE PROVIDED': 0
    }

    for r in report:
        summary[r['Status']] = summary.get(r['Status'], 0) + 1

    for k, v in summary.items():
        print(f"{k:<25}: {v}")
    print("="*80)

if __name__ == "__main__":
    main()
