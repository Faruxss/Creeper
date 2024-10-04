# Creeper Web Crawler & Vulnerability Scanner

Creeper is a versatile web crawler designed for penetration testing and vulnerability scanning. It offers multiple features, such as checking for robots.txt paths, identifying injection points in URLs, fetching older versions of websites, subdomain enumeration, directory scanning, and performing Nikto and Nuclei scans for security assessment.

## Features

1. **Crawl and Find Injection Points**
   - Scans URLs for query parameters and identifies potential payload injection points.

2. **Robots.txt Handling**
   - Downloads and parses the `robots.txt` file, checks the status of disallowed paths, and saves URLs with 200, 301, or 302 status codes.

3. **Wayback Machine Integration**
   - Fetches historical versions of websites from the Wayback Machine and optionally runs Nikto and Nuclei scans on older versions.

4. **Nikto and Nuclei Scans**
   - Performs Nikto and Nuclei scans to check for known vulnerabilities and misconfigurations in web servers.

5. **Subdomain Enumeration**
   - Uses `Subfinder` to enumerate subdomains of the target domain and scans them with `Dirsearch` to find directories and files.

## Installation

Ensure you have Python 3.x and the necessary libraries installed before running the tool:

```bash
pip install requests beautifulsoup4
```

You also need to have the following tools installed and available in your system's PATH:
- Nikto
- Nuclei
- Subfinder
- Dirsearch

## Usage

To run the tool, use the following format:

```bash
python creeper.py <url> [options]
```

### Options

- `-h`: Show this help message.
- `-r`: Download and check paths from `robots.txt`.
- `-i`: Find potential injection points in URL query parameters.
- `-w`: Fetch historical versions of the website from the Wayback Machine.
- `-n`: Run a Nikto scan on the given URL.
- `-c`: Run a Nuclei scan on the given URL.
- `-s`: Enumerate subdomains using Subfinder.
- `-u`: Run Dirsearch on subdomains found by Subfinder.
- `--all`: Run all scans automatically.

### Examples

- To find injection points and scan directories:
  ```bash
  python creeper.py https://example.com -i -u
  ```

- To check paths from robots.txt and fetch historical snapshots:
  ```bash
  python creeper.py https://example.com -r -w
  ```

- To run all scans on a website:
  ```bash
  python creeper.py https://example.com --all
  ```

## Outputs

- **Injection Points**: Saved in a file named `<domain>_injection_points.txt`.
- **Status Links**: Paths with status codes (200, 301, 302) are saved in `<domain>_status_links.txt`.
- **Subdomains**: Subdomains discovered by Subfinder are saved in `<domain>_subdomains.txt`.
- **Dirsearch Results**: Each subdomain's directory scan results are saved in `<subdomain>_dirsearch_results.txt`.
- **Wayback Snapshots**: Historical snapshots are saved in `<domain>_wayback_snapshots.txt`.

## Dependencies

- Python 3.x
- `requests`
- `beautifulsoup4`
- Tools: Nikto, Nuclei, Subfinder, Dirsearch

## License

This tool is open-source and available under the MIT License.

---

Feel free to contribute or open issues for bug reports and feature requests!
