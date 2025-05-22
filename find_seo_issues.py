import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import tldextract

def fetch_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return None

def check_seo_bugs(html, url):
    soup = BeautifulSoup(html, 'html.parser')
    details = {}

    # Title tag
    titles = soup.find_all("title")
    if not titles:
        details["Missing <title> tag"] = []
    elif len(titles) > 1:
        details["Multiple <title> tags found"] = [str(t) for t in titles]

    # Meta description
    meta_desc = soup.find_all("meta", attrs={"name": "description"})
    if not meta_desc:
        details["Missing <meta name='description'>"] = []
    elif len(meta_desc) > 1:
        details["Multiple meta descriptions found"] = [str(m) for m in meta_desc]

    # H1 tag
    h1s = soup.find_all("h1")
    if not h1s:
        details["Missing <h1> tag"] = []
    elif len(h1s) > 1:
        details["Multiple <h1> tags found"] = [str(h) for h in h1s]

    # Images without alt
    images = soup.find_all("img")
    missing_alt_imgs = [str(img) for img in images if not img.get("alt")]
    if missing_alt_imgs:
        details[f"{len(missing_alt_imgs)} <img> tag(s) missing alt attribute"] = missing_alt_imgs

    # Overuse of <strong> and <b>
    bold_tags = soup.find_all(["b", "strong"])
    if len(bold_tags) > 15:
        details["Overuse of <strong>/<b> tags"] = [str(b) for b in bold_tags]

    # Broken internal links
    broken_links = []
    domain_info = tldextract.extract(url)
    domain = f"{domain_info.domain}.{domain_info.suffix}"
    for link in soup.find_all("a", href=True):
        href = link['href']
        full_url = urljoin(url, href)
        parsed = urlparse(full_url)
        if domain in parsed.netloc:  # Internal links only
            try:
                r = requests.head(full_url, timeout=5)
                if r.status_code >= 400:
                    broken_links.append(f"{full_url} (status: {r.status_code})")
            except:
                broken_links.append(f"{full_url} (unreachable)")
    if broken_links:
        details[f"{len(broken_links)} broken internal link(s) found"] = broken_links

    return details

def print_report(details):
    if not details:
        print("✅ No major SEO issues found.")
    else:
        print("\n🔍 SEO Issues Report:")
        for issue, items in details.items():
            print(f"\n❌ {issue}:")
            if items:
                for item in items:
                    print(f"   - {item.strip()[:150]}{'...' if len(item.strip()) > 150 else ''}")
            else:
                print("   - [No additional details]")

if __name__ == "__main__":
    url = input("Enter the URL to scan: ").strip()
    html = fetch_html(url)
    if html:
        issues = check_seo_bugs(html, url)
        print_report(issues)
