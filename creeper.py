import sys
import requests
import random
import os
import time
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

MAX_URLS = 950  # Limit the number of URLs to check
visited_pages = set()  # Keep track of visited URLs

def save_injection_points(url, query_params):
    """Save detected injection points to a file for further testing."""
    domain = url.split("//")[-1].split("/")[0]
    filename = f"{domain}_injection_points.txt"
    
    with open(filename, "a") as file:
        file.write(f"URL: {url}\n")
        for param in query_params:
            file.write(f"Potential injection point: {param}=\n")
        file.write("\n")
    
    print(f"Injection points saved to {filename}.")

def find_injection_points(url):
    """Find potential injection points in the URL."""
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    
    if query_params:
        print(f"\nFound query parameters in {url}:")
        for param in query_params:
            print(f"- {param}")
            print(f"Potential injection point: {param}=")
        save_injection_points(url, query_params)
    else:
        print(f"No query parameters found in {url}, no injection points detected.")

def find_injection_points_in_page(url, visited_pages):
    """Crawl the page and find potential injection points in URLs."""
    if url in visited_pages:
        return  # Avoid revisiting the same page
    
    visited_pages.add(url)
    
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.find_all('a', href=True)

        for link in links:
            href = link['href']
            full_url = urljoin(url, href)
            if full_url not in visited_pages:  # Avoid revisiting
                visited_pages.add(full_url)
                print(f"Visiting: {full_url}")
                find_injection_points(full_url)
                find_injection_points_in_page(full_url, visited_pages)  # Recursively crawl
        
    except requests.exceptions.RequestException as e:
        print(f"Failed to crawl {url}: {e}")

def crawl_and_find_injection_points(start_url):
    """Start crawling from the given URL to find injection points."""
    print(f"Starting crawl at {start_url} to find injection points...\n")
    find_injection_points_in_page(start_url, visited_pages)

def save_status_links(full_url, status_code):
    """Save the path to a file for later analysis based on the URL and status code."""
    domain = full_url.split("/")[2].replace("www.", "")
    filename = f"{domain}_status_links.txt"
    
    with open(filename, "a") as file:
        if status_code == 200:
            file.write(f"[200 OK] {full_url}\n")
        elif status_code == 301:
            file.write(f"[301 Moved Permanently] {full_url}\n")
        elif status_code == 302:
            file.write(f"[302 Found] {full_url}\n")

def check_path_status(url, path):
    """Check the status of a path and save it if the status code is 200, 301, or 302."""
    full_url = url.rstrip("/") + "/" + path.lstrip("/")
    try:
        response = requests.get(full_url)
        if response.status_code in [200, 301, 302]:
            print(f"{full_url} -> {response.status_code}")
            save_status_links(full_url, response.status_code)  # Save the URL with its status code
    except Exception as e:
        print(f"Error checking path {path}: {e}")

def get_robot_paths(url):
    """Download and parse robots.txt, then return paths."""
    robot_url = url.rstrip("/") + "/robots.txt"
    try:
        response = requests.get(robot_url)
        if response.status_code == 200:
            print(f"Downloading {robot_url} ...")
            paths = []
            for line in response.text.splitlines():
                if line.startswith("Disallow:"):
                    parts = line.split(": ")
                    if len(parts) == 2:
                        paths.append(parts[1].strip())
            return paths
        else:
            print(f"No robots.txt found or inaccessible at {robot_url}")
            return []
    except Exception as e:
        print(f"Error requesting robots.txt: {e}")
        return []

def nikto_scan(url):
    """Run Nikto scan on the given URL."""
    print(f"\nRunning Nikto scan on {url} ...")
    os.system(f"nikto -h {url}")

def nuclei_scan(url):
    """Run Nuclei scan on the given URL."""
    print(f"\nRunning Nuclei scan on {url} ...")
    os.system(f"nuclei -u {url}")
    
def automated_snapshot_scanning(snapshot_urls, run_nikto='n', run_nuclei='n'):
    """Run scans on all historical snapshot URLs based on user's response."""
    if run_nikto != 'y' and run_nuclei != 'y':
        print("Skipping both Nikto and Nuclei scans on all snapshots.")
        return
    
    for snapshot_url in snapshot_urls:
        print(f"\nProcessing snapshot: {snapshot_url}")

        if run_nikto == 'y':
            nikto_scan(snapshot_url)
        else:
            print(f"Skipping Nikto scan on snapshot: {snapshot_url}")

        if run_nuclei == 'y':
            nuclei_scan(snapshot_url)
        else:
            print(f"Skipping Nuclei scan on snapshot: {snapshot_url}")



def fetch_wayback_versions(url, max_results=13, auto_run=False):
    """Fetch up to 23 older versions of a site using the Wayback Machine and save them to a file."""
    wayback_cdx_url = f"http://web.archive.org/cdx/search/coll?url={url}&output=json&limit={max_results}"
    
    try:
        response = requests.get(wayback_cdx_url)
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1:
                print(f"\nFound {len(data) - 1} snapshots for {url}:")
                
                domain = url.split("//")[-1].split("/")[0]
                filename = f"{domain}_wayback_snapshots.txt"
                
                with open(filename, "w") as file:
                    snapshots = []
                    for snapshot in data[1:]:  # Skip the first entry (header row)
                        timestamp = snapshot[1]
                        snapshot_url = f"http://web.archive.org/web/{timestamp}/{url}"
                        print(snapshot_url)
                        file.write(f"{snapshot_url}\n")
                        snapshots.append(snapshot_url)
                
                print(f"\nSnapshots saved to {filename}.")
                
                if auto_run:
                    automated_snapshot_scanning(snapshots, run_nikto='y', run_nuclei='y')
                else:
                    automated_snapshot_scanning(snapshots)
            else:
                print(f"No snapshots found for {url}.")
        else:
            print(f"Failed to contact the Wayback Machine for {url}.")
    except Exception as e:
        print(f"Error fetching Wayback Machine data: {e}")

def subfinder_scan(domain):
    """Run Subfinder to find subdomains for the given domain."""
    print(f"\nRunning Subfinder on {domain} ...")
    os.system(f"subfinder -d {domain} -o {domain}_subdomains.txt -silent")
    print(f"Subdomains saved to {domain}_subdomains.txt.")
    
    # Start Dirsearch on the found subdomains if -u option is used
    if "-u" in sys.argv:
        run_dirsearch_on_subdomains(domain)

def run_dirsearch_on_subdomains(domain):
    """Run Dirsearch on the subdomains found by Subfinder."""
    print(f"\nRunning Dirsearch on subdomains of {domain} ...")
    with open(f"{domain}_subdomains.txt", "r") as file:
        for line in file:
            subdomain = line.strip()
            print(f"Scanning {subdomain} with Dirsearch ...")
            os.system(f"dirsearch -u {subdomain} -o {subdomain}_dirsearch_results.txt")
            
def countdown(duration=5):
    """Word-based countdown before executing commands."""
    steps = ["Preparing...", "Setting up...", "Finalizing...", "Action initiated!"]
    
    for step in steps:
        print(step, end="\r")  # Print each step
        time.sleep(duration / len(steps))  # Sleep for a fraction of the total duration
    print(" " * 50, end="\r")  # Clear the line after countdown
    print("Action initiated!")  # Final message



def show_intro(url):
    """Show ASCII art and initialize the web crawler."""
    ascii_art = [

                                        
       
        r"""
       

 ▄████▄   ██▀███  ▓█████ ▓█████  ██▓███  ▓█████  ██▀███  
▒██▀ ▀█  ▓██ ▒ ██▒▓█   ▀ ▓█   ▀ ▓██░  ██▒▓█   ▀ ▓██ ▒ ██▒
▒▓█    ▄ ▓██ ░▄█ ▒▒███   ▒███   ▓██░ ██▓▒▒███   ▓██ ░▄█ ▒
▒▓▓▄ ▄██▒▒██▀▀█▄  ▒▓█  ▄ ▒▓█  ▄ ▒██▄█▓▒ ▒▒▓█  ▄ ▒██▀▀█▄  
▒ ▓███▀ ░░██▓ ▒██▒░▒████▒░▒████▒▒██▒ ░  ░░▒████▒░██▓ ▒██▒
░ ░▒ ▒  ░░ ▒▓ ░▒▓░░░ ▒░ ░░░ ▒░ ░▒▓▒░ ░  ░░░ ▒░ ░░ ▒▓ ░▒▓░
  ░  ▒     ░▒ ░ ▒░ ░ ░  ░ ░ ░  ░░▒ ░      ░ ░  ░  ░▒ ░ ▒░
░          ░░   ░    ░      ░   ░░          ░     ░░   ░ 
░ ░         ░        ░  ░   ░  ░            ░  ░   ░     
░                                                        

                                                   

        """
    

    ]
    
    print(random.choice(ascii_art))
    print(f"Initializing web crawler for {url}...\n")


def print_help():
    """Display help information with brief descriptions of the options."""
    help_message = """
Usage: python creeper.py <url> [options]

Options:
  -h      Show this help message
          Displays available commands and usage information.

  -r      Check paths from robots.txt
          Downloads /robots.txt, extracts disallowed paths, and checks for valid paths (200 status code).
          
  -i      Find potential injection points in URL
          Scans URL parameters for possible payload injection points.        

  -w      Fetch old versions from the Wayback Machine
          Retrieves historical versions of the site using the Wayback Machine.

  -n      Run Nikto scan on the given URL
          Performs a Nikto scan to check for known vulnerabilities and misconfigurations.

  -c      Run Nuclei scan on the given URL
          Runs a Nuclei scan to identify vulnerabilities using predefined templates.
          
  -s      Enumerate subdomains
          Uses Subfinder to discover and list subdomains of the given URL.

  -u      Run Dirsearch on found subdomains
          Scans the subdomains found with -s for directories and files using Dirsearch.

  --all   Run all scans
          Automatically executes all scans (robots.txt, Nikto, Nuclei, subdomains) and confirms yes for Nikto and Nuclei.

Examples:
  python creeper.py https://example.com -r -s -u -n
  python creeper.py https://example.com -w -n -c
  python creeper.py https://example.com --all

"""
    print(help_message)


def main():
    if len(sys.argv) < 2:
        print_help()
        sys.exit(1)

    url = sys.argv[1]
    
      # New feature: the --all flag to execute all operations
    if '--all' in sys.argv:
        print("\n--all flag detected. Running all scans automatically...\n")
        # Perform all operations with automatic 'yes' for Nikto and Nuclei scans
        show_intro(url)
        crawl_and_find_injection_points(url)
        subfinder_scan(url)
        paths = get_robot_paths(url)
        for path in paths:
            check_path_status(url, path)
        fetch_wayback_versions(url, auto_run=True)
        sys.exit(0)  # Exit after running all scans

    # Show countdown before intro unless -h is used
    if "-h" not in sys.argv:
        countdown(5)
        show_intro(url)

    # Handle flags
    if "-h" in sys.argv:
        print_help()
        return

    if "-r" in sys.argv:
        paths = get_robot_paths(url)
        for path in paths:
            check_path_status(url, path)

    if "-w" in sys.argv:
        fetch_wayback_versions(url)

    if "-s" in sys.argv:
        domain = url.split("//")[-1].split("/")[0]
        subfinder_scan(domain)

    # Check if the -u option is present to run Dirsearch on subdomains
    if "-u" in sys.argv:
        domain = url.split("//")[-1].split("/")[0]
        run_dirsearch_on_subdomains(domain)

    if "-n" in sys.argv:
        nikto_scan(url)

    if "-c" in sys.argv:
        nuclei_scan(url)
     
    if "-i" in sys.argv:
       visited_pages = set()
       find_injection_points_in_page(url, visited_pages)   

if __name__ == "__main__":
    main()

