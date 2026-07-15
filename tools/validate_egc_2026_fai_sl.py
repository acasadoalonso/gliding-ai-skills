#!/usr/bin/python3
# -*- coding: UTF-8 -*-

"""
Validate FAI sporting licenses for EGC 2026 pilots against FAI records.
Uses the same logic as validate-fai-sporting-license-for-pilots.md memory file.
"""

import sys
import json
import urllib.request, urllib.error, urllib.parse
import datetime
import os
import math
import pycountry
import pandas as pd

# FAI password (base64-encoded) - hardcoded for standalone use
FAIPWD = 'M1g5RnRPMmNMNg=='


def get_licenses_per_country(country, prt=False):
    """Fetch all gliding licenses for a country from FAI extranet API."""
    licenses = []
    start = 0
    nl = 100

    while nl == 100:
        url = "https://extranet.fai.org/api/v1/licences?auth_username=FAIOrganizer&auth_password=" + FAIPWD \
              + "&discipline=Gliding&country=" + country + "&limit_length=100&limit_start=" + str(start)

        if prt:
            print(url, "\n\n")

        j = urllib.request.urlopen(url)
        rr = j.read().decode('UTF-8')
        j_obj = json.loads(rr)
        nl = len(j_obj)

        for lic in j_obj:
            if lic["Sport"] == 'Gliding':
                licenses.append(lic)

        if prt:
            print("NL:", nl, "Start", start, "Lics", len(licenses))

        start += nl

    return (licenses)


def validate_fai_sl(country, sl=0, name=' ', prt=True):
    """Validate a FAI license number or match by name."""
    lpc = get_licenses_per_country(country, prt)

    if sl != 0:
        for lic in lpc:
            try:
                # Try numeric comparison first (most common format)
                if float(sl) == float(lic['idlicencee']):
                    return(True)
            except ValueError:
                pass

        # Fall back to string comparison for non-numeric formats
        str_sl = str(sl).strip()

        # Try to match the license number string against any ID in FAI records
        found_match = False
        for lic_id_str in lpc:
            try:
                if float(sl) == float(lic_id_str['idlicencee'].replace('.', '')):
                    return(True, lic_id_str)  # Return license details on match
            except ValueError:
                pass

    else:
        # Name-based lookup - find pilot by surname (and givenname if provided)
        for lic in lpc:
            last_name_upper = name.upper()
            first_name_lower = ''

            try:
                first_name_lower = str(name).strip().lower()[:30]  # Limit to avoid full name match issues
            except:
                pass

            if lic['surname_lip'].upper() == last_name_upper:
                givenname_match = True
                if len(first_name_lower) > 1 and ' ' in first_name_lower:
                    parts = first_name_lower.split(' ')
                    expected_givenname = f"{parts[0]}{parts[1] if len(parts) > 1 else ''}".lower()
                    givenname_match = lic['givenname_lip'].strip().lower() == expected_givenname

                return (True, lic)  # Return license details on match


def get_full_license_details(idlicence, prt=False):
    """Get full license details from FAI API."""
    l = str(idlicence)
    url = "https://extranet.fai.org/api/v1/licence/" + l + "?auth_username=FAIOrganizer&auth_password=" + FAIPWD

    if prt:
        print(url, "\n\n")

    j = urllib.request.urlopen(url)
    rr = j.read().decode('UTF-8')
    j_obj = json.loads(rr)

    return(j_obj)


def parse_license_number(ln):
    """Parse license number to extract country and numeric ID."""
    if pd.isna(ln):
        return None, None

    ln_str = str(ln).strip()

    # Handle formats like "GER-5532", "POL-110/06", etc.
    parts = ln_str.split('-')
    if len(parts) >= 2:
        country_code = parts[0].upper()
        try:
            numeric_id = float(ln_str.replace('-', '').replace('/', ''))
            return country_code, numeric_id
        except ValueError:
            pass

    # Try to extract just the number from various formats
    import re
    match = re.search(r'[\d.]+', ln_str)
    if match:
        try:
            numeric_id = float(match.group())
            return None, numeric_id  # Country unknown but have ID
        except ValueError:
            pass

    return None, None


def validate_pilot(pilots_df):
    """Validate all pilots in the dataframe against FAI records."""

    results = {
        'total': len(pilots_df),
        'with_license_numbers': 0,
        'without_license_numbers': 0,
        'valid_licenses': [],
        'invalid_licenses': []
    }

    print(f"\n{'='*60}")
    print("EGC 2026 FAI License Validation Report")
    print(f"{'='*60}\n")

    for idx, row in pilots_df.iterrows():
        first_name = str(row['first_name']).strip() if pd.notna(row['first_name']) else ''
        last_name = str(row['last_name']).strip().upper() if pd.notna(row['last_name']) else ''
        country_code = str(row['country_code']).strip().upper() if pd.notna(row['country_code']) else ''
        fai_license_number = row.get('fai_licence_number')

        # Parse license number to get numeric ID and country
        lic_country, lic_id = parse_license_number(fai_license_number)

        pilot_name = f"{first_name} {last_name}" if first_name and last_name else str(row['first_name'])

        print(f"\n--- Pilot: {pilot_name} ({country_code}) ---")
        print(f"FAI License Number from entry: {fai_license_number}")

        # Check for FAI license number
        has_fai_number = pd.notna(fai_license_number) and fai_license_number != 'NaN'

        if not has_fai_number:
            results['without_license_numbers'] += 1
            print("Status: NO FAI LICENSE NUMBER PROVIDED")

            # Try to find by name anyway (for pilots who might have valid licenses but no number on entry)
            found_by_name = False
            for lic in get_licenses_per_country(country_code):
                if last_name.upper() == lic['surname_lip'].upper():
                    givenname = ''
                    if pd.notna(row.get('first_name')):
                        try:
                            givenname = str(row['first_name']).strip().lower()
                        except:
                            pass

                    # Check for exact match or partial name match
                    found_by_name = True
                    print(f"  Found in FAI records (surname only): {lic.get('givenname_lip', '')} {last_name}")

            if not found_by_name and lic_country is None:
                results['invalid_licenses'].append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'country_code': country_code,
                    'fai_license_number': fai_license_number or str(row.get('registration_mark', '')),
                    'reason': f'No FAI license number provided; name not found in {country_code} records'
                })
            else:
                results['valid_licenses'].append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'country_code': country_code or str(row.get('registration_mark', '')),
                    'fai_license_number': fai_license_number or str(row.get('registration_mark', '')) if not found_by_name else None,
                    'reason': f'Found in FAI records by name match (surname: {last_name})'
                })
            continue

        # Has a license number - validate it against FAI database
        lic_country = country_code  # Use the country from entry for validation lookup

        print("Validating license...")

        found, details = None, None

        try:
            if lic_id is not None and lic_country:
                # Try numeric match first (most common format)
                float(lic_id) == float(details['idlicencee']) or str(lic_id).strip() == str(details['idlicencee']).strip()

                found = True

        except ValueError as e:
            print(f"  Error parsing license number for comparison")

        if not (found and details):
            # Try string match first, then numeric
            try:
                if float(lic_id) == float(details['idlicencee']) or str(lic_id).strip() == str(details['idlicencee']).strip():
                    found = True

            except ValueError as e:
                print(f"  Error parsing license number for comparison")

        if not (found and details):
            # Fall back to name-based lookup
            givenname = ''
            try:
                givenname = str(row.get('first_name', '')).strip().lower()
            except:
                pass

            found, details = False, None
            for lic in get_licenses_per_country(lic_country):
                if last_name.upper() == lic['surname_lip'].upper():
                    # Check full name match or surname-only match
                    givenname_match = (givenname and givenname.lower() == lic['givenname_lip'].lower()) \
                                     or not givenname

                    found, details = True, lic

            if not found:
                results['invalid_licenses'].append({
                    'first_name': first_name,
                    'last_name': last_name,
                    'country_code': country_code,
                    'fai_license_number': fai_license_number,
                    'reason': f'License number {lic_id} not found in FAI records for {country_code}'
                })

        if details:
            # Get full license details to check validity dates
            lic_details = get_full_license_details(details['idlicencee'], prt=False)

            issue_date = datetime.datetime.strptime(lic_details.get('dateissue', '1900-01-01'), '%Y-%m-%d') if lic_details.get('dateissue') else None

            # Check validity period (FAI licenses are typically 4 years, renewable)
            current_year = datetime.datetime.now().year
            expiry_date_str = str(lic_details.get('validite', '2099-12-31')) if lic_details.get('validite') else None

            # Parse expiry date - handle various formats
            try:
                expiry_parts = expiry_date_str.split('.')
                year, month, day = int(expiry_parts[0]), int(expiry_parts[1]) or 15, int(expiry_parts[2]) if len(expiry_parts) > 2 else (30, None)
                expiry_date = datetime.datetime(year, month, day)
            except:
                # Default to very far future for unknown formats
                expiry_date = datetime.datetime(current_year + 15, 12, 31)

            is_valid_until_2026 = current_year <= year

            results['valid_licenses'].append({
                'first_name': first_name,
                'last_name': last_name,
                'country_code': country_code,
                'fai_license_number': fai_license_number,
                'issue_date': issue_date.strftime('%Y-%m-%d') if issue_date else None,
                'expiry_year': year,
                'is_valid_until_2026': is_valid_until_2026,
            })
        else:
            results['invalid_licenses'].append({
                'first_name': first_name,
                'last_name': last_name,
                'country_code': country_code,
                'fai_license_number': fai_license_number,
                'reason': f'License number {lic_id} not found in FAI records for {country_code}'
            })

    # Summary statistics
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}\n")
    print(f"Total pilots: {results['total']}")
    print(f"Pilots with FAI license numbers: {results['with_license_numbers']}")
    print(f"Pilots without FAI license numbers: {results['without_license_numbers']}")

    if results['valid_licenses']:
        valid_count = len(results['valid_licenses'])
        invalid_count = len(results['invalid_licenses'])

        # Check for expired licenses (expired before 2026-12-31)
        expired_before_2026 = [p for p in results['valid_licenses'] if not p.get('is_valid_until_2026', True)]

        print(f"\nValid FAI license numbers: {valid_count}")
        print(f"Invalid/Not found in records: {invalid_count}")

        # Check expired licenses (before 2026-12-31)
        if expired_before_2026:
            print(f"Expired before end of competition period: {len(expired_before_2026)}")

    else:
        print("\nNo valid FAI license numbers found!")

    # Write results to file
    output_file = '/home/angel/tools/EGC_2026_fai_license_validation.txt'
    with open(output_file, 'w') as f:
        f.write("EGC 2026 FAI License Validation Report\n")
        f.write("="*50 + "\n\n")

        # Summary section
        f.write(f"Total pilots: {results['total']}\n")
        f.write(f"Pilots with FAI license numbers: {results['with_license_numbers']}\n")
        f.write(f"Pilots without FAI license numbers: {results['without_license_numbers']}\n\n")

        if results['valid_licenses']:
            valid_count = len(results['valid_licenses'])
            invalid_count = len(results['invalid_licenses'])

            expired_before_2026 = [p for p in results['valid_licenses'] if not p.get('is_valid_until_2026', True)]

            f.write(f"Valid FAI license numbers: {valid_count}\n")
            f.write(f"Invalid/Not found in records: {invalid_count}\n\n")

        # List of valid pilots with details
        if results['valid_licenses']:
            f.write("\n--- VALID LICENSES ---\n")
            for p in sorted(results['valid_licenses'], key=lambda x: (x.get('country_code', ''), x.get('last_name', ''))):
                expiry_year = p.get('expiry_year') or 2099
                is_valid_until_2026 = p.get('is_valid_until_2026', True)

                status = "VALID" if is_valid_until_2026 else f"EXPIRED (before {current_year})"
                lic_num = str(p['fai_license_number']) or 'N/A'

                f.write(f"{p.get('first_name')} {p.get('last_name', '')} ({lic_num}): {status}\n")

        # List of invalid pilots with details
        if results['invalid_licenses']:
            f.write("\n--- INVALID LICENSES (not found in FAI records) ---\n")
            for p in sorted(results['invalid_licenses'], key=lambda x: (x.get('country_code', ''), x.get('last_name', ''))):
                lic_num = str(p['fai_license_number']) or 'N/A'

                f.write(f"{p.get('first_name')} {p.get('last_name', '')} ({lic_num}): Not found in FAI records\n")

        # List of pilots without license numbers
        if results['without_license_numbers']:
            f.write("\n--- NO LICENSE NUMBER PROVIDED ---\n")
            for p in sorted(results['valid_licenses'], key=lambda x: (x.get('country_code', ''), x.get('last_name', ''))):
                lic_num = str(p['fai_license_number']) or 'N/A'

                f.write(f"{p.get('first_name')} {p.get('last_name', '')} ({lic_num}): Found in FAI records by name match\n")

    print(f"\nResults written to: {output_file}")


if __name__ == '__main__':
    # Load the EGC 2026 entries from Excel file
    excel_path = '/home/angel/egc2026-ENTRIES-01.07.2026.xlsx'

    try:
        df = pd.read_excel(excel_path)

        # Get unique countries for reference (optional, could be printed separately)
        print(f"Reading pilot data from {excel_path}")
        print(f"Total pilots in entry list: {len(df)}\n")

        validate_pilot(df)

    except Exception as e:
        print(f"Error reading Excel file: {e}")
        sys.exit(1)
