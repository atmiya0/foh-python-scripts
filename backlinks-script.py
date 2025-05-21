import urllib.request
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse
import csv
import re
import time

# Constants
BASE_URL = "https://www.yorku.ca/health/"
TARGET_URL = "https://www.yorku.ca/health/academic-advising/"
DOMAIN = "www.yorku.ca"

visited = set()
backlinks = []
page_number = 0

class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.in_title = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            for attr_name, attr_value in attrs:
                if attr_name == 'href':
                    self.links.append(attr_value)
        elif tag == 'title':
            self.in_title = True

    def handle_data(self, data):
        if self.in_title:
            self.title += data.strip()

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

def is_valid_link(href):
    return href and not href.startswith('#') and not href.startswith('mailto:')

def normalize_url(href, base):
    full_url = urljoin(base, href)
    parsed = urlparse(full_url)
    return f"https://{parsed.netloc}{parsed.path.rstrip('/')}"

def sanitize_filename(name):
    return re.sub(r'[^\w\- ]', '', name).strip().replace(' ', '_').lower()

def crawl(url):
    global page_number

    if url in visited:
        return
    visited.add(url)
    page_number += 1
    print(f"📄 Crawling page {page_number}: {url}")

    try:
        response = urllib.request.urlopen(url)
        html = response.read().decode(errors="ignore")

        parser = LinkParser()
        parser.feed(html)

        normalized_target = TARGET_URL.rstrip('/')
        found = False

        for href in parser.links:
            if is_valid_link(href):
                full_link = normalize_url(href, url)
                if full_link == normalized_target:
                    found = True

        if found:
            backlinks.append((parser.title or "No Title", url))

        # Crawl further internal links
        for href in parser.links:
            if is_valid_link(href):
                full_link = normalize_url(href, url)
                parsed = urlparse(full_link)
                if parsed.netloc == DOMAIN and parsed.path.startswith("/health"):
                    crawl(full_link)

        time.sleep(0.5)

    except Exception as e:
        print(f"❌ Error crawling {url}: {e}")

# Get title of target page
try:
    response = urllib.request.urlopen(TARGET_URL)
    html = response.read().decode(errors="ignore")
    parser = LinkParser()
    parser.feed(html)
    target_title = parser.title or "target_page"
except:
    target_title = "target_page"

# Begin crawling
crawl(BASE_URL)

# Save results
filename = f"backlinks_for_{sanitize_filename(target_title)}.csv"
with open(filename, mode='w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["Linking Page Title", "Linking Page URL"])
    for title, url in backlinks:
        writer.writerow([title, url])

# Final summary
print(f"\n✅ Finished crawling {page_number} pages.")
print(f"🔗 Found {len(backlinks)} backlinks to: {TARGET_URL}")
print(f"📁 Saved to: {filename}")
