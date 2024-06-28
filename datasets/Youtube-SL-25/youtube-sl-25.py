#!/usr/bin/env python
# coding: utf-8

import argparse
import csv
import os
import re
from urllib.parse import urlparse

import requests
from pytube import YouTube
from tqdm import tqdm


def read_csv(file_path):
    """
    Read the CSV file and return a list of tuples containing video IDs and subdirectory names.

    :param file_path: Path to the CSV file.
    :return: List of tuples (video_id, subdirectory_name).
    """
    with open(file_path, mode='r') as file:
        reader = csv.reader(file)
        video_data = list(reader)
    return video_data

def create_directory(directory_name):
    """
    Create a directory if it does not exist.

    :param directory_name: Name of the directory to create.
    """
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

def download_video(video_id, directory_name):
    """
    Download a YouTube video by its ID and save it to the specified directory.

    :param video_id: YouTube video ID.
    :param directory_name: Directory where the video will be saved.
    """
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        yt = YouTube(url)
        stream = yt.streams.get_highest_resolution()
        # Sanitize the title to be used in filenames
        title = re.sub(r'[\\/*?:"<>|]', "", yt.title)
        filename = f"{video_id}_{title}.mp4"
        stream.download(output_path=directory_name, filename=filename)
        print(f"Downloaded {filename} to {directory_name}")
    except Exception as e:
        print(f"Failed to download {video_id}: {e}")

def download_csv_from_url(url, output_dir, verify):
    """
    Download a CSV file from a URL and save it in the specified output directory.

    :param url: URL of the CSV file.
    :param output_dir: Directory where the CSV file will be saved.
    :param verify: Path to CA_BUNDLE file or directory with certificates of trusted CAs
    :return: Path to the downloaded CSV file.
    """
    response = requests.get(url, verify=verify)
    response.raise_for_status()  # Raise an error for bad status codes
    parsed_url = urlparse(url)
    file_name = os.path.basename(parsed_url.path)
    file_path = os.path.join(output_dir, file_name)
    with open(file_path, 'wb') as file:
        file.write(response.content)
    return file_path

def parse_arguments():
    """
    Parse command-line arguments.

    :return: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Download YouTube videos based on a CSV file.")
    parser.add_argument('csv_file', type=str, nargs='?', default="https://storage.googleapis.com/gresearch/youtube-sl-25/youtube-sl-25-metadata.csv",
                        help='Path to the CSV file containing video IDs and subdirectory names or URL to the CSV file.')
    parser.add_argument('output_dir', type=str, help='Path to the output directory where videos will be saved.')
    parser.add_argument('--languages', type=str, nargs='+', help='List of languages to download videos for.')
    parser.add_argument('--replace', type=str, choices=['all', 'skip', 'custom'], default='custom', help='Option to replace, skip, or ask for each existing subdirectory.')
    parser.add_argument('--ca_cert', type=lambda x: x if x.lower() not in ['true', 'false'] else x.lower() == 'true', default=True, help='Path to the CA certificate or a boolean to bypass SSL verification.')
    return parser.parse_args()

def handle_existing_directory(directory_name, replace_option):
    """
    Handle existing directories based on the replace option.

    :param directory_name: Directory to handle.
    :param replace_option: Option to handle existing directories ('all', 'skip', 'custom').
    :return: Boolean indicating whether to proceed with downloading.
    """
    if replace_option == 'all':
        os.system(f"rm -rf {directory_name}")
        create_directory(directory_name)
        return True
    elif replace_option == 'skip':
        return False
    elif replace_option == 'custom':
        choice = input(f"Directory {directory_name} already exists. Do you want to replace it? (y/n): ").strip().lower()
        if choice == 'y':
            os.system(f"rm -rf {directory_name}")
            create_directory(directory_name)
            return True
        else:
            return False

def main():
    """
    Main function to read CSV, create directories, and download videos.
    """
    args = parse_arguments()
    verify = args.ca_cert

    if args.csv_file.startswith('http://') or args.csv_file.startswith('https://'):
        csv_file_path = download_csv_from_url(args.csv_file, args.output_dir, verify)
    else:
        csv_file_path = args.csv_file

    video_data = read_csv(csv_file_path)
    if args.languages:
        video_data = [video for video in video_data if video[1] in args.languages]

    languages = set([video[1] for video in video_data])
    
    with tqdm(total=len(video_data), desc="Total Progress") as total_pbar:
        for language in languages:
            lang_videos = [video for video in video_data if video[1] == language]
            lang_dir = os.path.join(args.output_dir, language)

            if os.path.exists(lang_dir):
                if not handle_existing_directory(lang_dir, args.replace):
                    print(f"Skipping {lang_dir}")
                    total_pbar.update(len(lang_videos))
                    continue
            else:
                create_directory(lang_dir)
            
            with tqdm(total=len(lang_videos), desc=f"Downloading videos for {language}") as lang_pbar:
                for video_id, _ in lang_videos:
                    download_video(video_id, lang_dir)
                    lang_pbar.update(1)
                    total_pbar.update(1)

if __name__ == "__main__":
    main()
