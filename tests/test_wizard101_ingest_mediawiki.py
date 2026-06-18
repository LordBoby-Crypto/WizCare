from scripts.wizard101_ingest_mediawiki import build_categorymembers_url


def test_categorymembers_url_contains_expected_query_parts():
    url = build_categorymembers_url("https://example.test/api.php", "Category:Any School Hats", 25)
    assert "action=query" in url
    assert "list=categorymembers" in url
    assert "cmtitle=Category%3AAny+School+Hats" in url
    assert "cmlimit=25" in url
