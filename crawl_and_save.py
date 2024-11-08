import os
import requests
import base64
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from datetime import datetime
from PyPDF2 import PdfMerger
import time

visited_urls = set()

def debug_message(message):
    """Prints a debug message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_internal_links(url, base_domain, target_url):
    """Fetch internal links from a page that are under the target URL path, with debugging information."""
    internal_links = set()
    try:
        response = requests.get(url)
        debug_message(f"Started extracting links from: {url} | HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            debug_message(f"Failed to retrieve page: {url} | HTTP Status: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(url, href)
            link_domain = urlparse(full_url).netloc
            
            # Check if the link is within the same domain and starts with the target URL
            if link_domain == base_domain and full_url.startswith(target_url) and full_url not in visited_urls:
                internal_links.add(full_url)
                
    except Exception as e:
        debug_message(f"Error fetching links from {url}: {e}")
    
    return internal_links

def save_page_to_pdf(url, file_name, driver):
    """Fetch page content and save it as a PDF using Headless Chrome, with detailed debugging information."""
    try:
        # Use Selenium to fetch and save the PDF
        driver.get(url)
        debug_message(f"Started processing URL: {url}")
        
        # Save page as PDF (using Chrome's DevTools PDF functionality)
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})
        
        # Decode base64 data to binary and write to a PDF file
        with open(f"{file_name}.pdf", "wb") as f:
            f.write(base64.b64decode(pdf['data']))
        
        debug_message(f"Saved {url} to {file_name}.pdf")
        
        return f"{file_name}.pdf"  # Return the PDF file name
    
    except Exception as e:
        debug_message(f"Error saving {url} to PDF: {e}")
        return None

def crawl_and_save(url, base_domain, driver, target_url, depth=2):
    """Recursively crawl internal links and save each page as a PDF."""
    if depth == 0:
        return []
    
    # Normalize URL and add it to visited URLs
    url = url.rstrip('/')
    visited_urls.add(url)
    
    # Save the page to a PDF file
    page_name = url.replace("https://", "").replace("http://", "").replace("/", "_")
    pdf_file = save_page_to_pdf(url, page_name, driver)
    
    # Initialize list of PDFs with the current PDF file if saved successfully
    pdf_files = [pdf_file] if pdf_file else []
    
    # Recursively find and process internal links
    internal_links = get_internal_links(url, base_domain, target_url)
    for link in internal_links:
        if link not in visited_urls:
            pdf_files.extend(crawl_and_save(link, base_domain, driver, target_url, depth=depth - 1) or [])
            time.sleep(1)  # Pause briefly to respect server load

    return pdf_files

def combine_pdfs(pdf_files, output_filename="combined_document.pdf"):
    """Combine a list of PDF files into a single PDF."""
    merger = PdfMerger()
    for pdf in pdf_files:
        merger.append(pdf)
    merger.write(output_filename)
    merger.close()
    debug_message(f"Combined PDF saved as {output_filename}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Crawl a website and save pages as PDFs.")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Depth of crawling")
    parser.add_argument("--single-pdf", action="store_true", help="Combine all pages into a single PDF")
    args = parser.parse_args()
    
    target_url = args.url
    base_domain = urlparse(target_url).netloc
    chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # Replace with your actual ChromeDriver path

    # Set up Selenium WebDriver with a Service object
    service = Service(chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)
    
    # Crawl and save pages
    pdf_files = crawl_and_save(target_url, base_domain, driver, target_url, depth=args.depth)
    
    # Combine PDFs if requested
    if args.single_pdf:
        combine_pdfs(pdf_files)
    else:
        debug_message("Saved each page as a separate PDF file.")

    # Close the driver when done
    driver.quit()

if __name__ == "__main__":
    main()
