import sys
import requests
import random
import logging
import os
import time
import re 
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urljoin

visited_pages = set()  # Keep track of visited URLs

# Set up logging
logging.basicConfig(filename='errors.log', level=logging.ERROR)

# Custom exceptions (add these if not already present)
class FetchError(Exception):
    pass

class ParseError(Exception):
    pass

# Utility functions (replace existing fetch logic with the enhanced version)
def validate_url(url):
    """Validate if the URL is well-formed."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def fetch_with_retry(url, retries=3):
    """Fetch a URL with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an error for bad responses
            return response
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            raise FetchError(f"HTTP error: {http_err}")
        except requests.exceptions.ConnectionError:
            logging.error("Connection error occurred.")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.Timeout:
            logging.error("The request timed out.")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except requests.exceptions.RequestException as err:
            logging.error(f"An error occurred: {err}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise FetchError(f"Failed to fetch {url} after {retries} attempts.")

# Your existing fetch functions can be updated as follows
def fetch_js_content(js_url):
    """Fetch the content of a JavaScript file with error handling."""
    if not validate_url(js_url):
        logging.error(f"Invalid URL: {js_url}")
        return None

    response = fetch_with_retry(js_url)  # Using the fetch with retry
    if response:
        print(f"Fetching JS file: {js_url}")
        return response.text
    return None

def fetch_html_content(url):
    """Fetch the HTML content of a webpage."""
    if not validate_url(url):
        logging.error(f"Invalid URL: {url}")
        return None

    response = fetch_with_retry(url)  # Using the fetch with retry
    if response:
        return response.text
    return None


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
        
def find_js_files(soup, base_url):
    """Find and return all JavaScript file URLs from the page."""
    js_files = []
    for script in soup.find_all("script", src=True):
        src = script['src']
        full_url = urljoin(base_url, src)
        js_files.append(full_url)
        print(f"Found JavaScript file: {full_url}")
    return js_files

def fetch_js_content(js_url):
    """Fetch the content of a JavaScript file."""
    try:
        response = requests.get(js_url)
        if response.status_code == 200:
            print(f"Fetching JS file: {js_url}")
            return response.text
        else:
            print(f"Failed to fetch JS file: {js_url}, Status Code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error fetching JS file {js_url}: {e}")
        return None

def detect_api_keys(js_content, js_url):
    """Scan the JS content for potential API key exposure."""
    api_key_patterns = [
        r'["\'](?:api[-_]key|secret|token)["\']\s*[:=]\s*["\'][a-zA-Z0-9_\-]{20,}["\']',  # General API key pattern
        r'[A-Za-z0-9_\-]{20,}',  # Any long string resembling an API key
    ]
    
    found_keys = []
    for pattern in api_key_patterns:
        matches = re.findall(pattern, js_content)
        if matches:
            found_keys.extend(matches)

    if found_keys:
        domain = js_url.split("//")[-1].split("/")[0]
        filename = f"{domain}_exposed_api_keys.txt"
        with open(filename, "a") as file:
            for key in found_keys:
                file.write(f"Exposed API Key in {js_url}: {key}\n")
        print(f"Potential API keys detected in {js_url}. Saved to {filename}.")
    else:
        print(f"No API keys detected in {js_url}.")

def check_for_api_key_exposure(url):
    """Crawl the page and linked JavaScript files to check for exposed API keys."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        js_files = find_js_files(soup, url)

        for js_url in js_files:
            js_content = fetch_js_content(js_url)
            if js_content:
                detect_api_keys(js_content, js_url)
    except requests.exceptions.RequestException as e:
        print(f"Failed to crawl {url} for API key exposure: {e}")
        
def nikto_scan(url):
    """Run Nikto scan on the given URL."""
    print(f"\nRunning Nikto scan on {url} ...")
    os.system(f"nikto -h {url}")

def nuclei_scan(url):
    """Run Nuclei scan on the given URL."""
    print(f"\nRunning Nuclei scan on {url} ...")
    os.system(f"nuclei -u {url}")
    
def nmap_scan(url):
    """Run Nmap scan on the given URL."""
    domain = url.split("//")[-1].split("/")[0]
    print(f"\nRunning Nmap scan on {domain} ...")
    os.system(f"nmap -A {domain}")
    
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
                    # Ask user if they want to run scans on snapshots
                    run_nikto = input("Do you want to run Nikto scan on Wayback URLs? (y/n): ").lower()
                    run_nuclei = input("Do you want to run Nuclei scan on Wayback URLs? (y/n): ").lower()
                    automated_snapshot_scanning(snapshots, run_nikto=run_nikto, run_nuclei=run_nuclei)
            else:
                print(f"No snapshots found for {url}.")
        else:
            print(f"Failed to contact the Wayback Machine for {url}.")
    except Exception as e:
        print(f"Error fetching Wayback Machine data: {e}")


def subfinder_scan(domain):
    """Run Subfinder to find subdomains for the given domain."""
    print(f"\nRunning Subfinder on {domain} ...")
    
    # Command to run Subfinder
    subfinder_cmd = f"subfinder -d {domain} -o {domain}_all_subdomains.txt -silent"
    
    result = os.system(subfinder_cmd)
    
    if result != 0:
        print(f"Subfinder failed to find subdomains for {domain}. Check if Subfinder is installed properly.")
    else:
        print(f"All subdomains saved to {domain}_all_subdomains.txt.")
        
        # If --all flag is used, do not limit subdomains
        if '--all' not in sys.argv:
            limit_subdomains_to_10(domain)
        
        # Start Dirsearch on the found subdomains if -u option is used
        if "-u" in sys.argv:
            run_dirsearch_on_subdomains(domain)

def limit_subdomains_to_10(domain):
    """Limit the number of subdomains to 10 and save them in a separate file."""
    print(f"Limiting the number of subdomains for {domain} to 10 ...")
    
    # Read all subdomains and limit to 10
    with open(f"{domain}_all_subdomains.txt", "r") as infile:
        subdomains = infile.readlines()[:10]  # Get only the first 10 subdomains

    # Write the 10 subdomains to a new file
    with open(f"{domain}_subdomains.txt", "w") as outfile:
        outfile.writelines(subdomains)
    
    print(f"First 10 subdomains saved to {domain}_subdomains.txt.")

def run_dirsearch_on_subdomains(domain):
    """Run Dirsearch on the subdomains found by Subfinder."""
    print(f"\nRunning Dirsearch on subdomains of {domain} ...")
    
    # Use limited subdomains file if it exists, otherwise use all subdomains
    subdomains_file = f"{domain}_subdomains.txt" if '--all' not in sys.argv else f"{domain}_all_subdomains.txt"
    
    with open(subdomains_file, "r") as file:
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
          
  -m      Run Nmap scan on the given URL
          Performs an Nmap scan with OS detection and version detection (-A) to identify open ports and services.
          
  -k      Check for API key exposure
          Scans JavaScript files for potential API keys or secrets.


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

    url = sys.argv[1]  # Define the url within the main function

    if '--all' in sys.argv:
        print("\n--all flag detected. Running all scans automatically...\n")

        # 1. Show the intro
        try:
            show_intro(url)
        except Exception as e:
            logging.error(f"Error in show_intro: {e}")
            print(f"An error occurred while showing the intro: {e}")

        # 2. Fetch Wayback Machine snapshots and auto-run Nikto/Nuclei
        print("Fetching Wayback Machine snapshots and running Nikto/Nuclei...")
        try:
            fetch_wayback_versions(url, auto_run=True)
        except Exception as e:
            logging.error(f"Error in fetch_wayback_versions: {e}")
            print(f"An error occurred while fetching Wayback snapshots: {e}")

        # 3. Crawl and find injection points
        print("Running injection point scan...")
        try:
            crawl_and_find_injection_points(url)
        except Exception as e:
            logging.error(f"Error in crawl_and_find_injection_points: {e}")
            print(f"An error occurred while crawling for injection points: {e}")

        # 4. Subfinder scan
        print("Running subfinder scan...")
        try:
            subfinder_scan(url)
        except Exception as e:
            logging.error(f"Error in subfinder_scan: {e}")
            print(f"An error occurred during the subfinder scan: {e}")

        # 5. Check robots.txt paths
        print("Checking robots.txt paths...")
        try:
            paths = get_robot_paths(url)
            for path in paths:
                check_path_status(url, path)
        except Exception as e:
            logging.error(f"Error checking robots.txt paths: {e}")
            print(f"An error occurred while checking robots.txt paths: {e}")

        # 6. Run Nmap scan
        print("Running Nmap scan...")
        try:
            nmap_scan(url)
        except Exception as e:
            logging.error(f"Error in nmap_scan: {e}")
            print(f"An error occurred during the Nmap scan: {e}")

        # 7. Check for API key exposure
        print("Checking for API key exposure...")
        try:
            check_for_api_key_exposure(url)
        except Exception as e:
            logging.error(f"Error in check_for_api_key_exposure: {e}")
            print(f"An error occurred while checking for API key exposure: {e}")

        # Exit after running all scans
        print("All scans completed.")
        sys.exit(0)  # Exit after running --all scans
     # Show countdown before intro unless -h is used
    if "-h" not in sys.argv:
        countdown(5)
        try:
            show_intro(url)
        except Exception as e:
            logging.error(f"Error in show_intro during countdown: {e}")
            print(f"An error occurred while showing the intro: {e}")

    # Handle individual flags
    if "-h" in sys.argv:
        print_help()
        return

    if "-r" in sys.argv:
        try:
            paths = get_robot_paths(url)
            for path in paths:
                check_path_status(url, path)
        except Exception as e:
            logging.error(f"Error in -r flag: {e}")
            print(f"An error occurred while checking robots.txt paths: {e}")

    if "-m" in sys.argv:
        try:
            nmap_scan(url)
        except Exception as e:
            logging.error(f"Error in -m flag: {e}")
            print(f"An error occurred during the Nmap scan: {e}")

    if "-w" in sys.argv:
        try:
            fetch_wayback_versions(url)
        except Exception as e:
            logging.error(f"Error in -w flag: {e}")
            print(f"An error occurred while fetching Wayback versions: {e}")

    if "-s" in sys.argv:
        try:
            domain = url.split("//")[-1].split("/")[0]
            subfinder_scan(domain)
        except Exception as e:
            logging.error(f"Error in -s flag: {e}")
            print(f"An error occurred during the subfinder scan: {e}")

    # Check if the -u option is present to run Dirsearch on subdomains
    if "-u" in sys.argv:
        try:
            domain = url.split("//")[-1].split("/")[0]
            run_dirsearch_on_subdomains(domain)
        except Exception as e:
            logging.error(f"Error in -u flag: {e}")
            print(f"An error occurred while running Dirsearch on subdomains: {e}")

    if "-n" in sys.argv:
        try:
            nikto_scan(url)
        except Exception as e:
            logging.error(f"Error in -n flag: {e}")
            print(f"An error occurred during the Nikto scan: {e}")

    if "-c" in sys.argv:
        try:
            nuclei_scan(url)
        except Exception as e:
            logging.error(f"Error in -c flag: {e}")
            print(f"An error occurred during the Nuclei scan: {e}")
     
    if "-i" in sys.argv:
        try:
            visited_pages = set()
            find_injection_points_in_page(url, visited_pages)
        except Exception as e:
            logging.error(f"Error in -i flag: {e}")
            print(f"An error occurred while finding injection points in the page: {e}")

    if "-k" in sys.argv:
        try:
            check_for_api_key_exposure(url)
        except Exception as e:
            logging.error(f"Error in -k flag: {e}")
            print(f"An error occurred while checking for API key exposure: {e}")

if __name__ == '__main__':
    main()
