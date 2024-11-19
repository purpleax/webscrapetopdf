import os
import requests
import base64
import argparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright
from datetime import datetime
from PyPDF2 import PdfMerger
import time

visited_urls = set()

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

def save_page_to_pdf(url, file_name, page):
    """Fetch page content and save it as a PDF using Playwright."""
    try:
        page.goto(url, timeout=30000, wait_until="load")
        debug_message(f"Started processing URL: {url}")
        page.pdf(path=file_name, format="A4", print_background=True)
        debug_message(f"Saved {url} to {file_name}")
        return file_name
    except Exception as e:
        debug_message(f"Error saving {url} to PDF: {e}")
    return None

def crawl_and_save(url, base_domain, page, output_dir, pdf_only=False, download_pdfs=False, depth=2):
    """Recursively crawl internal links, downloading PDFs if in pdf_only mode or if PDF links are encountered."""
    if depth == 0:
        return []
    
    url = url.rstrip('/')
    visited_urls.add(url)
    pdf_files = []
    
    if url.endswith(".pdf"):
        if pdf_only or download_pdfs:
            response = requests.get(url, stream=True)
            pdf_path = os.path.join(output_dir, url.split("/")[-1])
            with open(pdf_path, 'wb') as f:
                f.write(response.content)
            debug_message(f"Downloaded PDF from {url} to {pdf_path}")
            pdf_files.append(pdf_path)
    elif not pdf_only:
        page_name = os.path.join(output_dir, url.replace("https://", "").replace("http://", "").replace("/", "_") + ".pdf")
        pdf_file = save_page_to_pdf(url, page_name, page)
        if pdf_file:
            pdf_files.append(pdf_file)
    
    internal_links = get_internal_links(url, base_domain)
    for link in internal_links:
        if link not in visited_urls:
            try:
                pdf_files.extend(crawl_and_save(link, base_domain, page, output_dir, pdf_only=pdf_only, download_pdfs=download_pdfs, depth=depth - 1) or [])
                time.sleep(1)
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
    parser = argparse.ArgumentParser(description="Crawl a website and save pages as PDFs or download linked PDFs.")
    parser.add_argument("url", help="The starting URL to crawl")
    parser.add_argument("--depth", type=int, default=2, help="Depth of crawling")
    parser.add_argument("--single-pdf", action="store_true", help="Combine all pages into a single PDF")
    parser.add_argument("--download-pdfs", action="store_true", help="Download any PDF files linked on pages")
    parser.add_argument("--pdf-only", action="store_true", help="Only download PDF files and ignore HTML pages")
    args = parser.parse_args()
    
    target_url = args.url
    base_domain = urlparse(target_url).netloc
    output_dir = base_domain
    os.makedirs(output_dir, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()
        
        pdf_files = crawl_and_save(target_url, base_domain, page, output_dir, pdf_only=args.pdf_only, download_pdfs=args.download_pdfs, depth=args.depth)
        
        if args.single_pdf and not args.pdf_only:
            combined_output = os.path.join(output_dir, "combined_document.pdf")
            combine_pdfs(pdf_files, combined_output)
        else:
            debug_message("Saved each page or downloaded PDF as a separate file.")
        
        browser.close()

if __name__ == "__main__":
    main()
