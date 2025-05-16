import requests
from urllib.parse import urljoin, urlparse
import os
import sys
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Validate input
if len(sys.argv) != 2:
    print("Usage: python3 crawl.py <base_url>")
    print("Example: python3 crawl.py https://xx.xx.xx.xx/")
    sys.exit(1)

# Configuration from CLI
FULL_URL = sys.argv[1].rstrip("/") + "/"  # Ensure trailing slash
parsed = urlparse(FULL_URL)
BASE_URL = f"{parsed.scheme}://{parsed.netloc}/"
start_path = parsed.path.strip("/")

OUTPUT_DIR = "cvs_dump"
VERIFY_SSL = False
TIMEOUT = 10

visited = set()
files_downloaded = []

def download_file(url, output_path):
    try:
        print(f"[→] Trying: {url}")
        response = requests.get(url, verify=VERIFY_SSL, timeout=TIMEOUT)
        if response.status_code == 200:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(response.content)
            print(f"[✔] Saved: {output_path}")
            return True
        else:
            print(f"[✖] Failed: HTTP {response.status_code}")
    except:
        print(f"[!] Error: {url}")
    return False

def crawl_cvs(path):
    if path in visited:
        return
    visited.add(path)

    entries_url = urljoin(BASE_URL, f"{path}/CVS/Entries" if path else "CVS/Entries")
    print(f"\n[📁] Scanning Entries: {entries_url}")
    try:
        response = requests.get(entries_url, verify=VERIFY_SSL, timeout=TIMEOUT)
        if response.status_code != 200 or not response.text.strip():
            print("[×] No valid Entries found.")
            return
    except:
        print("[!] Error fetching Entries.")
        return

    local_entries_path = os.path.join(OUTPUT_DIR, path, "CVS", "Entries")
    try:
        os.makedirs(os.path.dirname(local_entries_path), exist_ok=True)
        with open(local_entries_path, "w") as f:
            f.write(response.text)
    except:
        pass

    for line in response.text.strip().splitlines():
        if line.startswith("D/"):
            try:
                subdir = line.split("/")[1]
                crawl_cvs(os.path.join(path, subdir))
            except:
                pass
        elif line.startswith("/"):
            try:
                filename = line.split("/")[1]

                base_url = urljoin(BASE_URL, f"{path}/CVS/Base/{filename}" if path else f"CVS/Base/{filename}")
                base_path = os.path.join(OUTPUT_DIR, path, "CVS", "Base", filename)
                if download_file(base_url, base_path):
                    files_downloaded.append(f"{path}/CVS/Base/{filename}")

                raw_url = urljoin(BASE_URL, f"{path}/{filename}" if path else filename)
                raw_path = os.path.join(OUTPUT_DIR, path, filename)
                if download_file(raw_url, raw_path):
                    files_downloaded.append(f"{path}/{filename}")
            except:
                pass

if __name__ == "__main__":
    crawl_cvs(start_path)
    print("\n=== ✅ Completed ===")
    print(f"Total files downloaded: {len(files_downloaded)}")
    for f in files_downloaded:
        print(f" - {f}")
