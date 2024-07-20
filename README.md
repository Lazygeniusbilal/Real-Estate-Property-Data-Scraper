 # Real Estate Property Data Scraper

This project is a web scraper that collects real estate property data from the Graana website. It extracts details such as address, price, number of bathrooms, bedrooms, and area for both residential and commercial properties across different cities.

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

## Features
- Scrapes property data from multiple pages of the Graana website.
- Collects details including address, price, number of bathrooms, bedrooms, and area.
- Supports both residential and commercial properties.
- Covers multiple cities including Islamabad, Lahore, and Rawalpindi.

## Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/your-username/real-estate-property-data-scraper.git
    ```
2. Navigate to the project directory:
    ```bash
    cd real-estate-property-data-scraper
    ```
3. Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Run the scraper script:
    ```bash
    python scraper.py
    ```
2. The script will fetch property data and store it in a pandas DataFrame. You can modify the script to save the data to a CSV file or any other format as needed.

### Note
The current dataset in this repository is for first 2 pages. You can adjust the range of pages to scrape according to your needs.

## Dependencies
- `pandas`
- `numpy`
- `requests`
- `beautifulsoup4`

Install the dependencies using the command:
```bash
pip install pandas numpy requests beautifulsoup4
 
