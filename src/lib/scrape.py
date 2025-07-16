from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import Firefox, Chrome, Safari, Edge

"""
API HIT: GET https://korupedia.transparansi.id/detail-koruptor/?key=6&no=267

KEY: 6
NO: 11 MIN
NO: 360 MAX

h1 .entry-title nama-hakim untuk nama koruptor
.tbl-clean->tbody->tr->td widht='20%' foto koruptor
.content-body parse aja nnti datanya di pick lagi

"""

# CSR LMFAOO GIMME SSR PAGE THIS STUFF DONT NEED TO BE DYNAMIC ITS NOT EVEN UP-TO-DATE
URL = "https://korupedia.transparansi.id/detail-koruptor/?key=6&no=155"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}

type WebDriver = Firefox | Chrome | Safari | Edge

def korupedia_parse_data_and_save(
    webdriver: WebDriver,
    savedir: str,
    min: int = 11,
    max: int = 360,
):
    """Fetch and save HTML detail pages from the Korupedia website.

    This iterates over a range of corruption case indices and downloads
    the associated HTML detail pages using the given Selenium WebDriver
    instance. The page contents are saved as `.html` files into the
    specified directory.

    The function requires an initialized and open WebDriver instance.
    It uses a hardcoded URL format from Korupedia's detail view and assumes
    that the page is fully loaded when the `<body>` tag becomes present.
    Each downloaded page is saved as `data_<i>.html` where `i` is the
    current index in the loop.

    The WebDriver will be automatically closed after the operation.

    :param webdriver: A Selenium WebDriver instance such as Firefox,
        Chrome, Safari, or Edge. It must be ready to make HTTP requests.
    :param savedir: Filesystem path to the directory where HTML files
        will be saved. Must already exist.
    :param min: Starting index of the page range to fetch
        Defaults to 11. (inclusive)
    :param max: Ending index of the page range to fetch
        Defaults to 360. (inclusive)

    :raises TimeoutException: If the page fails to load the `<body>`
        element within 10 seconds.
    """

    for i in range(min, max+1):
        url = f"https://korupedia.transparansi.id/detail-koruptor/?key=6&no={i}"
        webdriver.get(url)

        # Wait for the page to load completely
        WebDriverWait(webdriver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )

        # Get the page source (HTML content)
        page_source = webdriver.page_source

        # Save to a file
        with open(f"{savedir}/data_{i}.html", "w", encoding="utf-8") as file:
            file.write(page_source)
            print(f"HTML data_{i}.html saved successfully.")

    webdriver.quit()
