# config.py

import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

TEXT_FILES = {
    'party_list': os.path.join(BASE_DIR, 'data', 'party_list.txt'),
    'region_list': os.path.join(BASE_DIR, 'data', 'region_list.txt'),
    'currency_names': os.path.join(BASE_DIR, 'data', 'currency_names.txt'),
    'sales_countries': os.path.join(BASE_DIR, 'data', 'sales_countries.txt'),
    'monthly_targets': os.path.join(BASE_DIR, 'data', 'monthly_targets.txt'),  # ✅ Add this line
    'last_month_overrides': os.path.join(BASE_DIR, 'data', 'last_month_overrides.txt'),
}
