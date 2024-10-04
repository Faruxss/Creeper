

---

# Creeper Web Crawler & Vulnerability Scanner

**Creeper** is a web crawling and vulnerability scanning tool that helps security professionals identify potential injection points, scan subdomains, check paths from `robots.txt`, and fetch historical versions of websites using the Wayback Machine. Additionally, it integrates with tools like **Nikto**, **Nuclei**, **Subfinder**, and **Dirsearch** for comprehensive web security analysis.

## Features

- Find potential URL injection points for testing SQLi and XSS vulnerabilities.
- Automatically download and check paths from `robots.txt` for accessible files and directories.
- Fetch and scan older versions of websites using the **Wayback Machine**.
- Perform scans using **Nikto** and **Nuclei** for known vulnerabilities.
- Discover subdomains using **Subfinder** and scan them using **Dirsearch**.
- Automated scanning using the `--all` option to run all available scans.

## Prerequisites

Before installing **Creeper**, ensure that you have the following tools installed:

- **Nikto**: Web server scanner
- **Nuclei**: Vulnerability scanner
- **Subfinder**: Subdomain discovery tool
- **Dirsearch**: Directory brute-force tool

You can install these tools using the following commands:

```bash
# Install Nikto
sudo apt-get install nikto

# Install Nuclei
go install -v github.com/projectdiscovery/nuclei/v2/cmd/nuclei@latest

# Install Subfinder
go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest

# Install Dirsearch
git clone https://github.com/maurosoria/dirsearch.git
cd dirsearch
pip3 install -r requirements.txt
```

## Installation

To install **Creeper**, clone this repository and install the required Python libraries:

```bash
# Clone the repository
git clone https://github.com/Faruxss/creeper.git

# Navigate to the Creeper directory
cd creeper

# Install required Python packages
pip install -r requirements.txt
```

## Usage

```bash
python creeper.py <url> [options]
```

### Options

| Flag    | Description                                                                                                                                               |
|---------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| `-h`    | Show help message and usage information.                                                                                                                  |
| `-r`    | Check paths from robots.txt. Downloads `/robots.txt`, extracts disallowed paths, and checks for valid paths (200 status code).                             |
| `-i`    | Find potential injection points in the URL. Scans URL parameters for possible payload injection points.                                                    |
| `-w`    | Fetch old versions from the Wayback Machine. Retrieves historical versions of the site using the Wayback Machine.                                          |
| `-n`    | Run Nikto scan on the given URL. Performs a Nikto scan to check for known vulnerabilities and misconfigurations.                                           |
| `-c`    | Run Nuclei scan on the given URL. Runs a Nuclei scan to identify vulnerabilities using predefined templates.                                               |
| `-s`    | Enumerate subdomains. Uses **Subfinder** to discover and list subdomains of the given URL.                                                                 |
| `-u`    | Run **Dirsearch** on found subdomains. Scans the subdomains found with `-s` for directories and files using **Dirsearch**.                                 |
| `--all` | Run all scans (robots.txt, Nikto, Nuclei, subdomains). Automatically executes all scans and confirms "yes" for Nikto and Nuclei.                         |

### Example Commands

```bash
# Scan a URL for injection points and check robots.txt
python creeper.py https://example.com -i -r

# Fetch Wayback Machine snapshots and run Nikto scan
python creeper.py https://example.com -w -n

# Find subdomains and scan them using Dirsearch
python creeper.py https://example.com -s -u

# Run all scans (robots.txt, Nikto, Nuclei, subdomains)
python creeper.py https://example.com --all
```

### Advanced Usage

- Use the `--all` option to run all scans in a single command, automating the full analysis of the target website.
- Use `-r` to check for restricted paths from `robots.txt` and automatically detect which ones are accessible (return a 200 status code).
- Combine different options to tailor the scanning process according to your requirements, such as running subdomain discovery with **Subfinder** and scanning those subdomains with **Dirsearch**.

---

## Contributing

Feel free to submit issues and pull requests if you have ideas to improve the tool. Contributions are welcome!

## License

This project is licensed under the MIT License.

---

### Author
[Farhan](https://github.com/Faruxss)

---

