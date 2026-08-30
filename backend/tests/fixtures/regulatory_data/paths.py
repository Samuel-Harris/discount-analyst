from pathlib import Path

REGULATORY_DATA_FIXTURES = Path(__file__).resolve().parent

NASDAQ_LISTED_FIXTURE = REGULATORY_DATA_FIXTURES / "nasdaq" / "nasdaqlisted.txt"
NASDAQ_OTHER_LISTED_FIXTURE = REGULATORY_DATA_FIXTURES / "nasdaq" / "otherlisted.txt"
LSE_REPORTS_PAGE_FIXTURE = REGULATORY_DATA_FIXTURES / "lse" / "reports_issuers.html"
LSE_ISSUERS_REPORT_FIXTURE = REGULATORY_DATA_FIXTURES / "lse" / "issuers_report.csv"
SEC_COMPANY_TICKERS_FIXTURE = REGULATORY_DATA_FIXTURES / "sec" / "company_tickers.json"
SEC_COMPANYFACTS_AAPL_FIXTURE = (
    REGULATORY_DATA_FIXTURES / "sec" / "companyfacts_cik_0000320193.json"
)
SEC_SUBMISSIONS_AAPL_FIXTURE = (
    REGULATORY_DATA_FIXTURES / "sec" / "submissions_cik_0000320193.json"
)
CH_COMPANIES_CSV_FIXTURE = (
    REGULATORY_DATA_FIXTURES / "companies_house" / "companies.csv"
)
CH_IFRS_ACCOUNTS_FIXTURE = (
    REGULATORY_DATA_FIXTURES / "companies_house" / "accounts_ifrs.xhtml"
)
CH_FILLETED_ACCOUNTS_FIXTURE = (
    REGULATORY_DATA_FIXTURES / "companies_house" / "accounts_ukgaap_filleted.xhtml"
)
