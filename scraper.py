#!/usr/bin/env python3
"""
Times of India ePaper Scraper
Downloads today's TOI Delhi edition PDF from dailyepaper.in
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import re
import sys

# Configuration
BASE_URL = "https://dailyepaper.in/times-of-india-epaper-pdf-aug-2025/"
DOWNLOAD_DIR = os.path.expanduser("~/Documents/newspapers/toi")
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_date_string(days_ago=0):
    """Returns date string in format like '31 Jan 2026' for N days ago"""
    from datetime import timedelta
    target_date = datetime.now() - timedelta(days=days_ago)
    return target_date.strftime("%-d %b %Y"), target_date


def get_pdf_link_for_date(date_str):
    """
    Scrapes the dailyepaper.in page and finds the Delhi edition link for given date
    Returns tuple (file_id, date_used) or (None, None)
    """
    headers = {"User-Agent": USER_AGENT}
    
    try:
        response = requests.get(BASE_URL, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching page: {e}", file=sys.stderr)
        return None, None
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Search for paragraphs containing the date
    for para in soup.find_all('p'):
        text = para.get_text()
        if date_str in text:
            # Find the "Delhi" link
            delhi_link = para.find('a', string='Delhi')
            if delhi_link and 'href' in delhi_link.attrs:
                href = delhi_link['href']
                # Extract file ID from Google Drive URL
                # Format: https://drive.google.com/file/d/{FILE_ID}/view
                match = re.search(r'/file/d/([^/]+)/', href)
                if match:
                    return match.group(1), date_str
    
    return None, None


def get_latest_available_pdf():
    """
    Tries to find the latest available PDF, checking today and up to 3 days back
    Returns tuple (file_id, date_str, date_obj) or (None, None, None)
    """
    for days_back in range(4):  # Try today, yesterday, 2 days ago, 3 days ago
        date_str, date_obj = get_date_string(days_back)
        print(f"Checking: {date_str}")
        
        file_id, found_date = get_pdf_link_for_date(date_str)
        if file_id:
            return file_id, found_date, date_obj
    
    print("Could not find any PDF in the last 4 days", file=sys.stderr)
    return None, None, None


def download_pdf_from_gdrive(file_id, output_dir, date_obj):
    """
    Downloads a PDF from Google Drive using direct download URL
    Handles Google Drive's confirmation page for large files
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate filename using the actual date of the newspaper
    date_str = date_obj.strftime("%Y-%m-%d")
    filename = f"TOI_Delhi_{date_str}.pdf"
    filepath = os.path.join(output_dir, filename)
    
    # Check if file already exists (skip if already downloaded)
    if os.path.exists(filepath):
        file_size = os.path.getsize(filepath)
        if file_size > 1024 * 1024:  # Only skip if file is larger than 1MB
            print(f"✓ File already exists: {filepath} ({file_size / (1024*1024):.1f} MB)")
            return filepath
        else:
            print(f"Found incomplete file ({file_size} bytes), re-downloading...")
            os.remove(filepath)
    
    print(f"Downloading to: {filepath}")
    
    headers = {"User-Agent": USER_AGENT}
    
    # Try direct download first
    download_url = f"https://drive.google.com/uc?export=download&id={file_id}"
    
    try:
        session = requests.Session()
        
        # First request - might get confirmation page for large files
        response = session.get(download_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        # Check if we got a confirmation page
        if 'text/html' in response.headers.get('Content-Type', ''):
            # Parse confirmation page to get the download link
            soup = BeautifulSoup(response.text, 'html.parser')
            confirm_link = soup.find('a', id='uc-download-link')
            
            if confirm_link and 'href' in confirm_link.attrs:
                # Get the confirmation URL
                confirm_url = "https://drive.google.com" + confirm_link['href']
                print("Handling Google Drive confirmation page...")
                response = session.get(confirm_url, headers=headers, stream=True, timeout=60)
                response.raise_for_status()
        
        # Write to file in chunks
        downloaded_size = 0
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                if chunk:
                    f.write(chunk)
                    downloaded_size += len(chunk)
                    # Show progress for large downloads
                    if downloaded_size > 10 * 1024 * 1024:  # Show after 10MB
                        print(f"  Downloaded: {downloaded_size / (1024*1024):.1f} MB", end='\r')
        
        final_size = os.path.getsize(filepath)
        
        # Verify download succeeded (should be at least 10MB for a newspaper PDF)
        if final_size < 1024 * 1024:
            print(f"\n✗ Download failed - file too small ({final_size} bytes)")
            os.remove(filepath)
            return None
        
        print(f"\n✓ Downloaded successfully: {filepath} ({final_size / (1024*1024):.1f} MB)")
        return filepath
        
    except requests.RequestException as e:
        print(f"Error downloading PDF: {e}", file=sys.stderr)
        # Clean up partial download
        if os.path.exists(filepath):
            os.remove(filepath)
        return None


def main():
    print("=" * 50)
    print("Times of India ePaper Scraper")
    print("=" * 50)
    
    # Step 1: Get latest available PDF (tries today and falls back to recent days)
    file_id, date_str, date_obj = get_latest_available_pdf()
    
    if not file_id:
        print("✗ Failed to find any available PDF")
        sys.exit(1)
    
    print(f"✓ Found PDF for: {date_str}")
    print(f"  File ID: {file_id}")
    
    # Step 2: Download the PDF
    filepath = download_pdf_from_gdrive(file_id, DOWNLOAD_DIR, date_obj)
    
    if filepath:
        print(f"\n✓ Success! PDF saved to: {filepath}")
        sys.exit(0)
    else:
        print("\n✗ Failed to download PDF")
        sys.exit(1)


if __name__ == "__main__":
    main()
