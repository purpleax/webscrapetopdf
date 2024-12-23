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

def get_internal_links(url, base_domain):
    """Fetch internal links and PDF links from a page within the same domain."""
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
            
            # Check if the link is within the same domain
            if link_domain == base_domain and full_url not in visited_urls:
                internal_links.add(full_url)
                
    except Exception as e:
        debug_message(f"Error fetching links from {url}: {e}")
    
    return internal_links

def download_pdf(url, output_dir):
    """Download a PDF file from a URL and save it to the specified directory."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            file_name = os.path.join(output_dir, url.split("/")[-1])
            with open(file_name, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            debug_message(f"Downloaded PDF: {file_name}")
        else:
            debug_message(f"Failed to download PDF: {url} | HTTP Status: {response.status_code}")
    except Exception as e:
        debug_message(f"Error downloading PDF {url}: {e}")

def save_page_to_pdf(url, file_name, driver):
    """Fetch page content and save it as a PDF using Headless Chrome, with detailed debugging information."""
    try:
        # Use Selenium to fetch and save the PDF
        driver.get(url)
        debug_message(f"Started processing URL: {url}")
        
        # Save page as PDF (using Chrome's DevTools PDF functionality)
        pdf = driver.execute_cdp_cmd("Page.printToPDF", {"printBackground": True})
        
        # Decode base64 data to binary and write to a PDF file
        with open(file_name, "wb") as f:
            f.write(base64.b64decode(pdf['data']))
        
        debug_message(f"Saved {url} to {file_name}")
        
        return file_name  # Return the PDF file path
    
    except Exception as e:
        debug_message(f"Error saving {url} to PDF: {e}")
        return None

def crawl_and_save(url, base_domain, driver, output_dir, pdf_only=False, download_pdfs=False, depth=2):
    """Recursively crawl internal links, downloading PDFs if in pdf_only mode or if PDF links are encountered."""
    if depth == 0:
        return []
    
    # Normalize URL and add it to visited URLs
    url = url.rstrip('/')
    visited_urls.add(url)
    
    pdf_files = []
    
    if url.endswith(".pdf"):
        # If the URL is a PDF and we're in download mode or pdf_only mode, download it
        if pdf_only or download_pdfs:
            download_pdf(url, output_dir)
            pdf_files.append(os.path.join(output_dir, url.split("/")[-1]))  # Add downloaded PDF filename to the list
    elif not pdf_only:
        # Save the HTML page to a PDF file
        page_name = os.path.join(output_dir, url.replace("https://", "").replace("http://", "").replace("/", "_") + ".pdf")
        pdf_file = save_page_to_pdf(url, page_name, driver)
        if pdf_file:
            pdf_files.append(pdf_file)
    
    # Recursively find and process internal links
    internal_links = get_internal_links(url, base_domain)
    for link in internal_links:
        if link not in visited_urls:
            # In pdf_only mode, continue to crawl for more links but only download PDFs
            pdf_files.extend(crawl_and_save(link, base_domain, driver, output_dir, pdf_only=pdf_only, download_pdfs=download_pdfs, depth=depth - 1) or [])
            time.sleep(1)  # Pause briefly to respect server load

    return pdf_files

def combine_pdfs(pdf_files, output_filename):
    """Combine a list of PDF files into a single PDF."""
    merger = PdfMerger()
    for pdf in pdf_files:
        merger.append(pdf)
    merger.write(output_filename)
    merger.close()
    debug_message(f"Combined PDF saved as {output_filename}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Crawl a website and save pages as PDFs or download linked PDFs.")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Depth of crawling")
    parser.add_argument("--single-pdf", action="store_true", help="Combine all pages into a single PDF")
    parser.add_argument("--download-pdfs", action="store_true", help="Download any PDF files linked on pages")
    parser.add_argument("--pdf-only", action="store_true", help="Only download PDF files and ignore HTML pages")
    args = parser.parse_args()
    
    target_url = args.url
    base_domain = urlparse(target_url).netloc

    # Create output directory based on the domain name
    output_dir = base_domain
    os.makedirs(output_dir, exist_ok=True)
    
    chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # Replace with your actual ChromeDriver path

    # Set up Selenium WebDriver with a Service object
    service = Service(chrome_driver_path)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Run in headless mode
    driver = webdriver.Chrome(service=service, options=options)
    
    # Crawl and save pages
    pdf_files = crawl_and_save(target_url, base_domain, driver, output_dir, pdf_only=args.pdf_only, download_pdfs=args.download_pdfs, depth=args.depth)
    
    # Combine PDFs if requested
    if args.single_pdf and not args.pdf_only:
        combined_output = os.path.join(output_dir, "combined_document.pdf")
        combine_pdfs(pdf_files, combined_output)
    else:
        debug_message("Saved each page or downloaded PDF as a separate file.")

    # Close the driver when done
    driver.quit()

if __name__ == "__main__":
    main()
import os
import requests
import base64
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime
from PyPDF2 import PdfMerger
import time

visited_urls = set()

# User-Agent string for a typical Chrome browser
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"

def debug_message(message):
    """Prints a debug message with a timestamp."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def get_internal_links(url, base_domain):
    """Fetch internal links and PDF links from a page within the same domain."""
    internal_links = set()
    headers = {"User-Agent": USER_AGENT}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        debug_message(f"Started extracting links from: {url} | HTTP Status: {response.status_code}")
        
        if response.status_code != 200:
            debug_message(f"Failed to retrieve page: {url} | HTTP Status: {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            full_url = urljoin(url, href)
            link_domain = urlparse(full_url).netloc
            
            # Check if the link is within the same domain
            if link_domain == base_domain and full_url not in visited_urls:
                internal_links.add(full_url)
                
    except requests.exceptions.RequestException as e:
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
        with open(file_name, "wb") as f:
            f.write(base64.b64decode(pdf['data']))
        
        debug_message(f"Saved {url} to {file_name}")
        
        return file_name  # Return the PDF file path
    
    except TimeoutException:
        debug_message(f"Timeout while processing URL: {url}")
    except WebDriverException as e:
        debug_message(f"WebDriver exception while processing URL: {url} | {e}")
    except Exception as e:
        debug_message(f"Error saving {url} to PDF: {e}")
    
    return None

def crawl_and_save(url, base_domain, driver, output_dir, pdf_only=False, download_pdfs=False, depth=2):
    """Recursively crawl internal links, downloading PDFs if in pdf_only mode or if PDF links are encountered."""
    if depth == 0:
        return []
    
    # Normalize URL and add it to visited URLs
    url = url.rstrip('/')
    visited_urls.add(url)
    
    pdf_files = []
    
    if url.endswith(".pdf"):
        # If the URL is a PDF and we're in download mode or pdf_only mode, download it
        if pdf_only or download_pdfs:
            download_pdf(url, output_dir)
            pdf_files.append(os.path.join(output_dir, url.split("/")[-1]))  # Add downloaded PDF filename to the list
    elif not pdf_only:
        # Save the HTML page to a PDF file
        page_name = os.path.join(output_dir, url.replace("https://", "").replace("http://", "").replace("/", "_") + ".pdf")
        pdf_file = save_page_to_pdf(url, page_name, driver)
        if pdf_file:
            pdf_files.append(pdf_file)
    
    # Recursively find and process internal links
    internal_links = get_internal_links(url, base_domain)
    for link in internal_links:
        if link not in visited_urls:
            try:
                pdf_files.extend(crawl_and_save(link, base_domain, driver, output_dir, pdf_only=pdf_only, download_pdfs=download_pdfs, depth=depth - 1) or [])
                time.sleep(1)  # Pause briefly to respect server load
            except Exception as e:
                debug_message(f"Error processing link {link}: {e}")

    return pdf_files

def combine_pdfs(pdf_files, output_filename):
    """Combine a list of PDF files into a single PDF."""
    merger = PdfMerger()
    for pdf in pdf_files:
        merger.append(pdf)
    merger.write(output_filename)
    merger.close()
    debug_message(f"Combined PDF saved as {output_filename}")

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description="Crawl a website and save pages as PDFs or download linked PDFs.")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Depth of crawling")
    parser.add_argument("--single-pdf", action="store_true", help="Combine all pages into a single PDF")
    parser.add_argument("--download-pdfs", action="store_true", help="Download any PDF files linked on pages")
    parser.add_argument("--pdf-only", action="store_true", help="Only download PDF files and ignore HTML pages")
    args = parser.parse_args()
    
    target_url = args.url
    base_domain = urlparse(target_url).netloc

    # Create output directory based on the domain name
    output_dir = base_domain
    os.makedirs(output_dir, exist_ok=True)
    
    # Set up Chrome WebDriver with a custom User-Agent
    chrome_options = ChromeOptions()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument(f"user-agent={USER_AGENT}")
    
    chrome_driver_path = '/opt/homebrew/bin/chromedriver'  # Update this to your ChromeDriver path
    driver = webdriver.Chrome(service=ChromeService(chrome_driver_path), options=chrome_options)
    driver.set_page_load_timeout(30)  # Set page load timeout
    
    # Crawl and save pages
    pdf_files = crawl_and_save(target_url, base_domain, driver, output_dir, pdf_only=args.pdf_only, download_pdfs=args.download_pdfs, depth=args.depth)
    
    # Combine PDFs if requested
    if args.single_pdf and not args.pdf_only:
        combined_output = os.path.join(output_dir, "combined_document.pdf")
        combine_pdfs(pdf_files, combined_output)
    else:
        debug_message("Saved each page or downloaded PDF as a separate file.")

    # Close the driver when done
    driver.quit()

if __name__ == "__main__":
    main()
