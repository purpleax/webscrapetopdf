Web Crawler and PDF Exporter
A Python script that crawls a website from a given starting URL, saves each page as a PDF, and optionally combines all PDFs into a single document. This script is especially useful for creating offline versions of documentation sites or other structured content.

Features
Crawls a website, following internal links up to a specified depth.
Saves each crawled page as a PDF using Headless Chrome.
Optionally combines all PDFs into a single file.
Includes detailed debug messages with timestamps, HTTP status codes, and save confirmations.
Prerequisites
Python 3.x
Google Chrome installed
ChromeDriver compatible with your Chrome version

Installation
Clone this repository:
Install required Python packages:

bash
Copy code
pip install requests beautifulsoup4 selenium PyPDF2


Install ChromeDriver:

Use Homebrew (for macOS):
bash
Copy code
brew install chromedriver
Or download manually from ChromeDriver official site.
Update the chrome_driver_path in the script with your ChromeDriver’s location. For example:

python
Copy code
chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # Adjust as necessary
Usage
Run the script with the following command:

bash
Copy code
python3 scrapeChrome.py <URL> [--depth DEPTH] [--single-pdf]
Arguments
<URL>: The starting URL to crawl (required).
--depth DEPTH: The maximum depth for recursive crawling (default is 2).
--single-pdf: Combine all saved pages into a single PDF file.
Example Commands
Save each page separately:

bash
Copy code
python3 scrapeChrome.py https://www.website.com/manual
Combine all pages into a single PDF:

bash
Copy code
python3 scrapeChrome.py https://www.website.com/manual --single-pdf
Set a custom crawling depth:

bash
Copy code
python3 scrapeChrome.py https://www.website.com/manual --depth 3
How It Works
Crawling: The script starts from the given URL and recursively finds internal links that match the target domain and URL path, up to the specified depth.
PDF Saving: Each page is loaded with Selenium, and the HTML content is converted to a PDF using Chrome’s DevTools print-to-PDF feature.
Combining PDFs: If the --single-pdf option is specified, all generated PDFs are merged into a single file using PyPDF2.
Debugging
The script outputs debug messages that include:

Timestamps
HTTP status codes for each request
Messages indicating when each page is processed and saved
Requirements for Additional Libraries
Selenium: Used to control Chrome in headless mode and capture each page as a PDF.
PyPDF2: Needed if using the --single-pdf option to merge PDFs.
Troubleshooting
ChromeDriver Errors: Ensure chromedriver is compatible with your installed version of Chrome. You can check Chrome’s version under chrome://settings/help.
Permission Errors: If you encounter permissions issues with ChromeDriver, try running chmod +x /path/to/chromedriver to make it executable.
Connection Issues: If you get network errors (e.g., ProtocolUnknownError), ensure the target site is accessible and doesn't require authentication or other permissions.
License
This project is licensed under the MIT License.