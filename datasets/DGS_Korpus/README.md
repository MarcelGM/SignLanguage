# DGS Korpus Data Processor

This script processes the DGS Korpus data by scraping, downloading, and analyzing it. It provides functionalities to download data from a specified URL and to analyze the downloaded data. The script can be executed with various command-line options to customize its behavior.

## Prerequisites

Before running the script, ensure you have the following Python packages installed:

- argparse
- os
- ffmpeg
- matplotlib
- numpy
- pandas
- requests
- seaborn
- BeautifulSoup
- tqdm
- wordcloud

You can install them using pip:

```sh
pip install argparse os ffmpeg matplotlib numpy pandas requests seaborn beautifulsoup4 tqdm wordcloud
```

## Usage

The script can be run from the command line with various options:
```sh
python DGS_Korpus.py [OPTIONS]
```

## Options

- `--webpage_url` (default: 'https://www.sign-lang.uni-hamburg.de/meinedgs/ling/start-name_en.html')
  - **Description**: URL of the webpage containing the table to scrape.
  - **Type**: String
  - **Example**: `--webpage_url 'https://example.com/table.html'`

- `--downloadable_url_path` (default: 'https://www.sign-lang.uni-hamburg.de/meinedgs/')
  - **Description**: Base path for downloadable URLs.
  - **Type**: String
  - **Example**: `--downloadable_url_path 'https://example.com/downloads/'`

- `--ca_cert` (default: True)
  - **Description**: Path to the CA certificate or a boolean (True/False) for verification.
  - **Type**: String or Boolean
  - **Example**: `--ca_cert '/path/to/ca_cert.crt'` or `--ca_cert False`

- `--dgs_path` (default: '/home/marcel/Documents/data/DGS_Korpus')
  - **Description**: Path where you want to store the DGS Korpus data.
  - **Type**: String
  - **Example**: `--dgs_path '/path/to/store/data'`

- `--csv_filename` (default: 'dgs_korpus_paths.csv')
  - **Description**: Name of the CSV file to save paths data.
  - **Type**: String
  - **Example**: `--csv_filename 'my_paths_data.csv'`

- `--csv_filepath` (default: None)
  - **Description**: Absolute path to the CSV file to save paths data. Overrides `csv_filename` if provided.
  - **Type**: String
  - **Example**: `--csv_filepath '/absolute/path/to/my_paths_data.csv'`

- `--action` (default: 'both')
  - **Description**: Action to perform: `download`, `analyse`, or `both`.
  - **Type**: String (choices: `download`, `analyse`, `both`)
  - **Example**: `--action download`


## Examples

### Download Data Only
To download data only:
```sh
python DGS_Korpus.py --action download
```


### Analyze Data Only

To analyze data only:
``` sh
python DGS_Korpus.py --action analyse --csv_filepath /path/to/your/csvfile.csv
```

### Download and Analyze Data
To download and then analyze data:
```sh
python DGS_Korpus.py --action both
```


<!-- ## Script Overview

The script is divided into several functions:

- **`parse_arguments()`**
  - **Description**: Parses command-line arguments.
  
- **`scrape_table(url, ca_cert, downloadable_url_path)`**
  - **Description**: Scrapes the table from the given URL.
  - **Parameters**:
    - `url`: URL of the webpage containing the table.
    - `ca_cert`: Path to the CA certificate or a boolean for verification.
    - `downloadable_url_path`: Base path for downloadable URLs.
  
- **`download_file(url, save_path, ca_cert)`**
  - **Description**: Downloads a file from the given URL.
  - **Parameters**:
    - `url`: URL of the file to download.
    - `save_path`: Path to save the downloaded file.
    - `ca_cert`: Path to the CA certificate or a boolean for verification.
  
- **`create_directory(path)`**
  - **Description**: Creates a directory if it doesn't exist.
  - **Parameters**:
    - `path`: Path of the directory to create.
  
- **`download_file_row(row, base_dir, ca_cert)`**
  - **Description**: Downloads files for a given row of the DataFrame.
  - **Parameters**:
    - `row`: A row of the DataFrame.
    - `base_dir`: Base directory to save the files.
    - `ca_cert`: Path to the CA certificate or a boolean for verification.
  
- **`get_video_metadata(file_path)`**
  - **Description**: Gets metadata of a video file.
  - **Parameters**:
    - `file_path`: Path to the video file.
  
- **`extract_metadata(row)`**
  - **Description**: Extracts metadata from video files in a DataFrame row.
  - **Parameters**:
    - `row`: A row of the DataFrame.
  
- **`download_data(args)`**
  - **Description**: Downloads the DGS Korpus data.
  - **Parameters**:
    - `args`: Command-line arguments.
  
- **`analyze_data(args)`**
  - **Description**: Analyzes the DGS Korpus data.
  - **Parameters**:
    - `args`: Command-line arguments.
  
- **`main()`**
  - **Description**: Main function to parse arguments and execute download or analyze actions. -->


## License

This project is licensed under the MIT License - see the LICENSE file for details.
