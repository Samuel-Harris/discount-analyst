from pathlib import Path

FIXTURE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "regulatory_data"


def test_regulatory_data_fixtures_exist() -> None:
    expected = [
        FIXTURE_DIR / "nasdaq" / "nasdaqlisted.txt",
        FIXTURE_DIR / "nasdaq" / "otherlisted.txt",
        FIXTURE_DIR / "lse" / "reports_issuers.html",
        FIXTURE_DIR / "lse" / "issuers_report.csv",
        FIXTURE_DIR / "sec" / "company_tickers.json",
        FIXTURE_DIR / "sec" / "companyfacts_cik_0000320193.json",
        FIXTURE_DIR / "sec" / "submissions_cik_0000320193.json",
        FIXTURE_DIR / "companies_house" / "companies.csv",
        FIXTURE_DIR / "companies_house" / "accounts_ifrs.xhtml",
        FIXTURE_DIR / "companies_house" / "accounts_ukgaap_filleted.xhtml",
    ]
    missing = [str(path) for path in expected if not path.is_file()]
    assert missing == []
