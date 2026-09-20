# sales-report-dashboard

A small Flask web app for recording sales invoices and generating a period report. Domestic sales are tracked per region against monthly targets, and export sales are tracked per currency, each compared with the previous month. An admin area lets you maintain the dropdown lists, targets and override values without touching the code.

## Features

- **Domestic entry**: invoice number, date, party (with autocomplete), region and value in INR.
- **Export entry**: the same fields plus country, currency and exchange rate. The INR value is calculated on save.
- **Report** for any date range:
  - domestic sales per region: last month, target, and the total so far
  - export sales per currency: value, INR value, and last month for each
  - all INR figures shown in lakhs
- **Last month values** come from the database by default. Admins can switch on **override mode** to use the values in `data/last_month_overrides.txt` instead, which is useful when the previous month's data isn't in the system.
- **Admin area** (password protected, auto-logout after 5 minutes idle) for editing the party, region, currency and country lists, monthly targets and override values.

## Tech stack

Python · Flask · MySQL (`mysql-connector-python`) · Bootstrap 5

## Project structure

```
sales-report-dashboard/
├── sales_report.py      # Flask app: entry, report and admin routes
├── config.py            # Paths to the editable text files
├── data/                # Dropdown lists, monthly targets, last-month overrides (sample data)
├── templates/           # Start, entry, admin, domestic, export and report pages
├── schema.sql           # MySQL database + table
└── requirements.txt
```

## Running it

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Create the database (MySQL):

   ```bash
   mysql -u root -p < schema.sql
   ```

3. Set the credentials as environment variables:

   ```
   DB_PASSWORD=your_mysql_password
   ADMIN_PASSWORD=choose-an-admin-password
   SECRET_KEY=any-random-string
   ```

   The database host and user are `localhost` / `root`; change them in `sales_report.py` if yours differ.

4. Run the app:

   ```bash
   python sales_report.py
   ```

   Open http://127.0.0.1:5000.

## Editing the data files

The files in `data/` hold sample values. Replace them with your own via the admin page or by editing them directly.

| File | Format |
|---|---|
| `region_list.txt`, `party_list.txt`, `currency_names.txt`, `sales_countries.txt` | one value per line |
| `monthly_targets.txt` | `Region=target`, in lakhs |
| `last_month_overrides.txt` | `Region=value` for domestic and keys like `INTL-USD` / `INTL-USD-INR` for export, in lakhs where INR |

## Known issues

- The admin "Edit" buttons open the file in **Notepad on the server machine**, so they only work when the app runs on Windows on the same computer you are using. Elsewhere, edit the files in `data/` by hand.
- "Last month" is worked out as roughly 30 days before the start date, so it can drift from the calendar month when the range doesn't start on the 1st.
- The entry routes share one long-lived database connection, which can time out on a server that stays up for days.
- Entry forms confirm with a plain text message, and there is no way to edit or delete an entry from the app.
- Only the admin area is protected. Anyone who can reach the app can enter data and view the report.
