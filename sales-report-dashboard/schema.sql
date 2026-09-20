-- Reconstructed from the INSERT / SELECT statements in sales_report.py.
-- Column types are inferred; adjust them if your data needs it.
CREATE DATABASE IF NOT EXISTS sales_report;
USE sales_report;

CREATE TABLE sales_report (
  id                INT NOT NULL AUTO_INCREMENT,
  invoice_no        VARCHAR(50)   NOT NULL,
  invoice_date      DATE          NOT NULL,
  party_name        VARCHAR(100)  NOT NULL,
  region_name       VARCHAR(100)  NOT NULL,  -- region (domestic) or country (export)
  product_value     DECIMAL(15,2) NOT NULL,  -- in the invoice currency
  exchange_rate     DECIMAL(10,4) NOT NULL,  -- 1.0 for domestic
  product_value_inr DECIMAL(18,2) NOT NULL,
  currency_name     VARCHAR(10)   NOT NULL,  -- INR for domestic
  invoice_type      VARCHAR(20)   NOT NULL,  -- 'domestic' | 'export_xlnt' | 'international'
  PRIMARY KEY (id),
  KEY idx_type_date (invoice_type, invoice_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
