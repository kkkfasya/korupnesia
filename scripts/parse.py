import json
import sys
import os
import result
from pathlib import Path
from typing import Dict, Optional
from bs4 import BeautifulSoup

def scrape_korupedia_detail(file_path: str | Path) -> Optional[Dict[str, str]]:
    """
    Parses a Korupedia detail HTML page and extracts corruptor data.

    :param file_path: Path to the HTML file.

    return: A dictionary containing scraped data, or None if scraping fails.
    """
    soup: BeautifulSoup
    safe_read_text = result.as_result(UnicodeDecodeError)(Path.read_text)
    safe_bs = result.as_result(Exception)(BeautifulSoup)

    path = Path(file_path)
    if file_path == "" or not path.exists():
        print("error: file does not exist", file=sys.stderr)
        sys.exit(1)

    if not os.access(path, os.R_OK):
        print("error: file is not accessible", file=sys.stderr)
        sys.exit(1)

    r = safe_read_text(path, encoding="utf-8")
    if r.match_err(UnicodeDecodeError):
        print("error: failed to decode file to utf-8", file=sys.stderr)
        sys.exit(1)

    html_content = r.unwrap()

    s = safe_bs(html_content, "lxml")
    if s.is_err():
        s = safe_bs(html_content, "html.parser")

    soup = s.unwrap()

    scraped_data: Dict[str, str] = {}

    nama_elem = soup.select_one(".nama-hakim")
    scraped_data["nama"] = nama_elem.get_text().strip() if nama_elem else ""

    entry_title_elem = soup.select_one(".entry-title")
    deskripsi = ""
    if entry_title_elem:
        p_sibling = entry_title_elem.find_next_sibling("p")
        if p_sibling:
            deskripsi = p_sibling.get_text().strip()
    scraped_data["deskripsi"] = deskripsi

    table_rows = soup.select(".content-body table tbody tr")
    for row in table_rows:
        cells = row.find_all("td")
        if len(cells) == 2:
            key = cells[0].get_text().strip().replace(" ", "_").lower()
            value = cells[1].get_text().strip()
            scraped_data[key] = value

    print("Data scraped successfully:")
    print(json.dumps(scraped_data, indent=2, ensure_ascii=False))

    return scraped_data


if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else ""
    scrape_korupedia_detail(target_file)


