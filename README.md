# Web Crawler and PDF Exporter

A Python script that crawls a website from a given starting URL, saves each page as a PDF, and optionally combines all PDFs into a single document. This script is especially useful for creating offline versions of documentation sites or other structured content. Additionally, it can now detect and download PDF files linked within the target website.

## Features

-   Crawls a website, following internal links up to a specified depth.
-   Saves each crawled page as a PDF using Headless Chrome.
-   Optionally combines all saved pages into a single PDF document.
-   Detects and downloads any PDF files linked on pages (optional).
-   Can operate in PDF-only mode to download only PDF files linked on the target domain.

## Prerequisites

-   **Python 3.x**
-   **Google Chrome** installed
-   **ChromeDriver** compatible with your Chrome version

## Installation

1.  **Clone this repository**:
    
     
2.  **Install required Python packages**:
    
        `pip install requests beautifulsoup4 selenium PyPDF2` 
    
3.  **Install ChromeDriver**:
    
    -   Use Homebrew (for macOS):
              
        `brew install chromedriver` 
        
    -   Or download manually from ChromeDriver official site.
4.  **Update the `chrome_driver_path`** in the script with your ChromeDriver’s location. For example:
    
 
    `chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # Adjust as necessary` 
    

## Usage

Run the script with the following command:

bash

Copy code

`python3 crawl_and_save.py <URL> [--depth DEPTH] [--single-pdf] [--download-pdfs] [--pdf-only]` 

### Arguments

-   `<URL>`: The starting URL to crawl (required).
-   `--depth DEPTH`: The maximum depth for recursive crawling (default is 2).
-   `--single-pdf`: Combine all saved pages into a single PDF file.
-   `--download-pdfs`: Download any PDF files linked on pages.
-   `--pdf-only`: Only download PDF files and ignore HTML pages.

### Example Commands

1.  **Save each page as a separate PDF**:
    
    bash
    
    Copy code
    
    `python3 crawl_and_save.py https://docs.example.com` 
    
2.  **Combine all pages into a single PDF**:
    
    bash
    
    Copy code
    
    `python3 crawl_and_save.py https://docs.example.com --single-pdf` 
    
3.  **Download PDFs linked on pages in addition to saving HTML pages as PDFs**:
    
    bash
    
    Copy code
    
    `python3 crawl_and_save.py https://docs.example.com --download-pdfs` 
    
4.  **PDF-Only Mode**: Crawl the site and download only PDFs linked on pages, ignoring HTML pages:
    
    bash
    
    Copy code
    
    `python3 crawl_and_save.py https://docs.example.com --pdf-only` 
    
5.  **Custom Crawling Depth**:
    
    bash
    
    Copy code
    
    `python3 crawl_and_save.py https://docs.example.com --depth 3` 
    

## How It Works

1.  **Crawling**: The script starts from the given URL and recursively finds internal links that match the target domain. It crawls up to the specified depth.
2.  **PDF Saving**: Each HTML page is loaded with Selenium, and the HTML content is converted to a PDF using Chrome’s DevTools print-to-PDF feature.
3.  **PDF Detection**: When `--download-pdfs` or `--pdf-only` is set, the script downloads any linked PDF files it encounters.
4.  **Combining PDFs**: If `--single-pdf` is specified, all generated PDFs are merged into a single document using `PyPDF2`.

## Debugging

The script outputs debug messages that include:

-   Timestamps
-   HTTP status codes for each request
-   Messages indicating when each page is processed and saved

## Requirements for Additional Libraries

-   **Selenium**: Used to control Chrome in headless mode and capture each page as a PDF.
-   **PyPDF2**: Needed if using the `--single-pdf` option to merge PDFs.

## Troubleshooting

1.  **ChromeDriver Errors**: Ensure `chromedriver` is compatible with your installed version of Chrome. You can check Chrome’s version under `chrome://settings/help`.
2.  **Permission Errors**: If you encounter permissions issues with ChromeDriver, try running `chmod +x /path/to/chromedriver` to make it executable.
3.  **Connection Issues**: If you get network errors (e.g., `ProtocolUnknownError`), ensure the target site is accessible and doesn't require authentication or other permissions.

## License

This project is licensed under the MIT License.