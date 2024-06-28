#!/usr/bin/env python
# coding: utf-8

import argparse
import logging
import os
import shutil
import sys

import ffmpeg
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import seaborn as sns
from bs4 import BeautifulSoup
from tqdm import tqdm
from wordcloud import WordCloud

tqdm.pandas()
logging.basicConfig(level=logging.WARNING, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arguments():
    """
    Parse command-line arguments.
    """
    parser = argparse.ArgumentParser(description="Process DGS Korpus data.")
    parser.add_argument('--webpage_url', type=str, default='https://www.sign-lang.uni-hamburg.de/meinedgs/ling/start-name_en.html', help='URL of the webpage containing the table')
    parser.add_argument('--downloadable_url_path', type=str, default='https://www.sign-lang.uni-hamburg.de/meinedgs/', help='Base path for downloadable URLs')
    parser.add_argument('--ca_cert', type=lambda x: x if x.lower() not in ['true', 'false'] else x.lower() == 'true', default=True, help='Path to the CA certificate')  # '/usr/local/share/ca-certificates/Fortinet_CA_SSL-1.crt'
    parser.add_argument('--dgs_path', type=str, default='/home/marcel/Documents/data/DGS_Korpus', help='Path where you want to store the DGS Korpus')
    parser.add_argument('--csv_filename', type=str, default='dgs_korpus_paths.csv', help='Name of the CSV file to save paths data')
    parser.add_argument('--csv_filepath', type=str, default=None, help='Absolute path to the CSV file to save paths data')
    parser.add_argument('--action', type=str, choices=['download', 'analyse', 'both'], default='both', help='Action to perform: download, analyse, or both')
    return parser.parse_args()

def scrape_table(url, ca_cert, downloadable_url_path):
    """
    Scrape the table from the given URL.

    Parameters:
    - url: str, the URL of the webpage containing the table.
    - ca_cert: str or bool, the path to the CA certificate or True/False for verification.
    - downloadable_url_path: str, base path for downloadable URLs.

    Returns:
    - df: pd.DataFrame, the scraped data as a DataFrame.
    """
    response = requests.get(url, verify=ca_cert)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table')
    data = []

    for i, row in enumerate(table.find_all('tr')):
        if i == 0:
            header_cells = row.find_all("th")
            header = [c.text.strip() for c in header_cells]

        cells = row.find_all('td')
        if cells:
            transcript = cells[0].text.strip()
            age_group = cells[1].text.strip()
            format_type = cells[2].text.strip()
            topics = [topic.text.strip() for topic in cells[3].find_all('a')]
            text_dict = {
                'Transcript': transcript,
                'Age Group': age_group,
                'Format': format_type,
                'Topics': ', '.join(topics),
            }

            urls_dict = {}
            for col_header, cell in zip(header[4:], cells[4:]):
                links = [downloadable_url_path + link.get('href')[3:] for link in cell.find_all('a') if link.get('href')]
                if len(links) == 1:
                    urls_dict[col_header] = links[0]
                elif len(links) > 1:
                    urls_dict[col_header] = links
                else:
                    urls_dict[col_header] = None

            merged_dict = {**text_dict, **urls_dict}
            data.append(merged_dict)

    df = pd.DataFrame(data, columns=header)
    return df

def download_file(url, save_path, ca_cert, max_retries=3):
    """
    Download a file from the given URL with retry logic.

    Parameters:
    - url: str, the URL of the file to download.
    - save_path: str, the path to save the downloaded file.
    - ca_cert: str or bool, the path to the CA certificate or True/False for verification.
    - max_retries: int, maximum number of download attempts.

    Returns:
    - str, the path to the saved file or None if the download failed.
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, stream=True, verify=ca_cert)
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            return save_path
        except requests.exceptions.RequestException as e:
            logging.warning(f"Failed to download {url} (Attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                logging.warning(f"Url {url} could not be downloaded after {max_retries} attempts.")
                return None
    return None

def create_directory(path):
    """
    Create a directory if it doesn't exist.

    Parameters:
    - path: str, the path of the directory to create.
    """
    if not os.path.exists(path):
        os.makedirs(path)

def download_file_row(row, base_dir, ca_cert, max_retries=3):
    """
    Download files for a given row of the DataFrame.

    Parameters:
    - row: pd.Series, a row of the DataFrame.
    - base_dir: str, the base directory to save the files.
    - ca_cert: str or bool, the path to the CA certificate or True/False for verification.
    - max_retries: int, maximum number of download attempts.

    Returns:
    - pd.Series, a series with paths of downloaded files.
    """
    row_dir = os.path.join(base_dir, row.name)
    filenames = {("Paths", "base_dir"): row_dir}
    create_directory(row_dir)

    for col in row.index:
        url = row[col]
        if isinstance(url, str):
            filename = os.path.basename(url)
            filepath = os.path.join(row_dir, filename)
            downloaded_file = download_file(url, filepath, ca_cert, max_retries)
            filenames[("Paths", col)] = filename if downloaded_file else None
            if not downloaded_file:
                logging.warning(f"Url {url} could not be downloaded after {max_retries} attempts.")
        elif isinstance(url, list):
            urls = url
            paths = []
            for url in urls:
                filename = os.path.basename(url)
                filepath = os.path.join(row_dir, filename)
                downloaded_file = download_file(url, filepath, ca_cert, max_retries)
                paths.append(filename if downloaded_file else None)
            filenames[("Paths", col)] = paths
            if any(file is None for file in paths):
                logging.warning(f"Some URLs in the list {urls} could not be downloaded after {max_retries} attempts.")
        elif url is None:
            filenames[("Paths", col)] = None
        else:
            raise TypeError(f"URL {url} of type {type(url)}.")
            
    return pd.Series(filenames)

def get_video_metadata(file_path):
    """
    Get metadata of a video file.

    Parameters:
    - file_path: str, the path to the video file.

    Returns:
    - tuple, containing duration and dimensions (width, height) of the video or None if failed.
    """
    try:
        probe = ffmpeg.probe(file_path)
        video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
        if video_stream is None:
            return None

        duration = float(video_stream['duration'])
        width = int(video_stream['width'])
        height = int(video_stream['height'])

        return duration, (width, height)
    except Exception as e:
        print(f"Error getting metadata for {file_path}: {e}")
        return None

def extract_metadata(row):
    """
    Extract metadata from video files in a DataFrame row.

    Parameters:
    - row: pd.Series, a row of the DataFrame.

    Returns:
    - pd.Series, a series with metadata of the videos.
    """
    base_dir = row['base_dir']
    video_types = ['Video A', 'Video B', 'Video Total', 'Video AB']
    metadata_dict = {}
    
    for video_type in video_types:
        filename_col = f'{video_type}'
        filename = row[filename_col]
        if filename is np.nan:
            metadata = [None, (None, None)]
        else:
            path = os.path.join(base_dir, filename)
            metadata = get_video_metadata(path)
        
        if metadata:
            metadata_dict[("Metadata", f'{video_type} Duration')] = metadata[0]
            metadata_dict[("Metadata", f'{video_type} Dimensions')] = metadata[1]
    
    return pd.Series(metadata_dict)

def seconds_to_hms(seconds):
    """
    Convert seconds to hours, minutes, and seconds.

    Parameters:
    - seconds: float, the number of seconds.

    Returns:
    - str, formatted string in the form of "H hours, M minutes, S seconds".
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    result = []
    if hours > 0:
        result.append(f"{hours} hours")
    if minutes > 0:
        result.append(f"{minutes} minutes")
    result.append(f"{seconds:.2f} seconds")
    return ", ".join(result)

def print_video_duration_stats(df):
    """
    Print statistics for video duration.

    Parameters:
    - df: pandas.DataFrame, the DataFrame containing video metadata.
    """
    video_durations = df[('Metadata', 'Video Total Duration')]

    # Calculate statistics
    num_videos = video_durations.count()
    mean_duration = video_durations.mean()
    std_duration = video_durations.std()
    median_duration = video_durations.median()
    max_duration = video_durations.max()
    min_duration = video_durations.min()
    total_duration = video_durations.sum()
    
    # Print statistics
    print(f"Number of videos: {num_videos}")
    print(f"Mean duration: {seconds_to_hms(mean_duration)}")
    print(f"Standard deviation: {seconds_to_hms(std_duration)}")
    print(f"Median duration: {seconds_to_hms(median_duration)}")
    print(f"Maximum duration: {seconds_to_hms(max_duration)}")
    print(f"Minimum duration: {seconds_to_hms(min_duration)}")
    print(f"Total duration: {seconds_to_hms(total_duration)}")
    
def plot_and_save_figures(df, figures_dir):
    plt.figure(figsize=(20, 12))
    sns.countplot(x=df[('Data', 'Age Group')], order=df[('Data', 'Age Group')].value_counts().index)
    plt.title('Distribution of Age Groups')
    plt.xlabel('Age Group')
    plt.ylabel('Count')
    plt.savefig(os.path.join(figures_dir, "1_Distribution_of_Age_Groups.png"))
    plt.close()

    plt.figure(figsize=(20, 12))
    sns.countplot(x=df[('Data', 'Format')], order=df[('Data', 'Format')].value_counts().index)
    plt.title('Distribution of Formats')
    plt.xlabel('Format')
    plt.ylabel('Count')
    plt.savefig(os.path.join(figures_dir, "2_Distribution_of_Formats.png"))
    plt.close()

    topics = df[('Data', 'Topics')].str.split(', ').explode()
    plt.figure(figsize=(20, 12))
    sns.countplot(y=topics, order=topics.value_counts().index)
    plt.title('Distribution of Topics')
    plt.xlabel('Count')
    plt.ylabel('Topic')
    plt.savefig(os.path.join(figures_dir, "3_Distribution_of_Topics.png"))
    plt.close()

    wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(topics.dropna()))
    plt.figure(figsize=(20, 12))
    plt.imshow(wordcloud, interpolation='bilinear')
    plt.axis('off')
    plt.title('Word Cloud of Topics')
    plt.savefig(os.path.join(figures_dir, "4_Word_Cloud_of_Topics.png"))
    plt.close()

    age_groups = df[('Data', 'Age Group')].unique()
    for age_group in age_groups:
        age_group_topics = df[df[('Data', 'Age Group')] == age_group][('Data', 'Topics')].str.split(', ').explode()
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(age_group_topics.dropna()))

        plt.figure(figsize=(20, 12))
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis('off')
        plt.title(f'Word Cloud for Age Group: {age_group}')
        plt.savefig(os.path.join(figures_dir, f"5_Word_Cloud_for_Age_Group_{age_group}.png"))
        plt.close()

    plt.figure(figsize=(20, 12))
    sns.histplot(df[('Metadata', 'Video Total Duration')], bins=30, kde=True)
    plt.title('Distribution of Video Durations')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('Count')
    plt.savefig(os.path.join(figures_dir, "6_Distribution_of_Video_Durations.png"))
    plt.close()
    
    print(f"Saved figures at {figures_dir}")

def download_data(args):
    """
    Download the DGS Korpus data.

    Parameters:
    - args: argparse.Namespace, command-line arguments.
    """
    # Check if the path exists and prompt the user
    if os.path.exists(args.dgs_path):
        user_input = input(f"The path {args.dgs_path} already exists. Do you want to replace the existing data? (yes/no): ").strip().lower()
        if user_input == 'yes':
            # Remove the directory and its contents
            shutil.rmtree(args.dgs_path)
            print(f"Removed existing directory {args.dgs_path}.")
        else:
            print("Download aborted.")
            sys.exit()

    # Create the directory
    create_directory(args.dgs_path)
    
    df = scrape_table(args.webpage_url, args.ca_cert, args.downloadable_url_path)
    df['Transcript'] = df['Transcript'] + '__' + df.groupby('Transcript').cumcount().astype(str)
    df.set_index('Transcript', inplace=True)
    df.columns = pd.MultiIndex.from_tuples([
        ('Data', 'Age Group'),
        ('Data', 'Format'),
        ('Data', 'Topics'),
        ('URLs', 'iLex'),
        ('URLs', 'ELAN'),
        ('URLs', 'Video A'),
        ('URLs', 'Video B'),
        ('URLs', 'Video Total'),
        ('URLs', 'SRT'),
        ('URLs', 'Video AB'),
        ('URLs', 'CMDI'),
        ('URLs', 'OpenPose'),
    ])

    tqdm.pandas(desc="Downloading DGS Korpus")
    df_paths = df["URLs"].progress_apply(download_file_row, args=(args.dgs_path, args.ca_cert), axis=1)
    df = pd.merge(df, df_paths, left_index=True, right_index=True)
    
    if args.csv_filepath:
        csv_filename = args.csv_filepath
    else:
        csv_filename = os.path.join(args.dgs_path, args.csv_filename)
    df.to_csv(csv_filename)
    print(f"DataFrame saved at {csv_filename}")

def analyze_data(args):
    """
    Analyze the DGS Korpus data.

    Parameters:
    - args: argparse.Namespace, command-line arguments.
    """
    # Create _figures directory if it doesn't exist
    figures_dir = os.path.join(args.dgs_path, "_figures")
    if os.path.exists(figures_dir):
        user_input = input(f"The directory {figures_dir} already exists. Do you want to replace its content? (yes/no): ").strip().lower()
        if user_input == 'yes':
            shutil.rmtree(figures_dir)
            print(f"Removed existing directory {figures_dir}.")
            os.makedirs(figures_dir, exist_ok=True)
        else:
            print("Operation aborted.")
            return
    os.makedirs(figures_dir, exist_ok=True)
    print(f"Created directory {figures_dir}.")

    # Extract videos metadata
    csv_metadata_filename = os.path.join(args.dgs_path, "dgs_korpus_metadata.csv")
    df = pd.read_csv(args.csv_filepath if args.csv_filepath else os.path.join(args.dgs_path, args.csv_filename), header=[0, 1], index_col=0)
    tqdm.pandas(desc="Extracting metadata")
    df_metadata = df["Paths"].progress_apply(extract_metadata, axis=1)
    df = pd.merge(df, df_metadata, left_index=True, right_index=True)
    df.to_csv(csv_metadata_filename)
    print(f"DataFrame saved as {csv_metadata_filename}")

    print_video_duration_stats(df)
    plot_and_save_figures(df, figures_dir)

def main():
    """
    Main function to parse arguments and execute download or analyze actions.
    """
    args = parse_arguments()
    
    if args.action in ['download', 'both']:
        download_data(args)
    
    if args.action in ['analyse', 'both']:
        analyze_data(args)

if __name__ == "__main__":
    main()
