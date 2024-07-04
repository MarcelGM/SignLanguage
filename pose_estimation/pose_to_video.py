import argparse
import os
import sys

from pose_format import Pose
from pose_format.pose_visualizer import PoseVisualizer


def parse_arguments():
    """
    Parse command-line arguments.
    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Visualize poses from a .pose file and save as a video.')
    parser.add_argument('--pose', type=str, required=True, help='Path to the input .pose file.')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save the output video file.')
    parser.add_argument('--replace', type=str, choices=['True', 'False', 'ask'], required=True, help='Replace existing files: True, False, or ask.')
    return parser.parse_args()

def check_output_file(output_video_path, replace_option):
    """
    Check the output file based on the replace option.
    Args:
        output_video_path (str): Path to the output video file.
        replace_option (str): Replace option ('True', 'False', or 'ask').
    Returns:
        bool: True if the file can be written, False otherwise.
    """
    if os.path.exists(output_video_path):
        if replace_option == 'true':
            print(f"Output file {output_video_path} exists. Overwriting because --replace is set to True.")
            return True
        elif replace_option == 'ask':
            response = input(f"Output file {output_video_path} exists. Do you want to overwrite it? (y/n): ").strip().lower()
            if response != 'y':
                print("File will not be overwritten. Exiting.")
                return False
            print("File will be overwritten.")
            return True
        else:
            print(f"Output file {output_video_path} exists. Not changing it because --replace is set to False.")
            return False
    return True

def read_pose_file(pose_file):
    """
    Read the pose data from the .pose file.
    Args:
        pose_file (str): Path to the input .pose file.
    Returns:
        Pose: The Pose object read from the file.
    """
    try:
        with open(pose_file, "rb") as f:
            pose = Pose.read(f.read())
        return pose
    except Exception as e:
        print(f"Error reading pose file: {e}")
        return None

def save_pose_video(pose, output_video_path):
    """
    Save the pose data as a video file.
    Args:
        pose (Pose): The Pose object to visualize and save.
        output_video_path (str): Path to save the output video file.
    """
    try:
        v = PoseVisualizer(pose)
        v.save_video(output_video_path, v.draw())
        print(f"Video saved successfully to {output_video_path}")
    except ImportError as e:
        print(f"Error: {e}. Please ensure that vidgear is installed.")
        print("You can install it using: pip install vidgear")
    except Exception as e:
        print(f"Error saving video: {e}")

def main():
    """
    Main function to visualize poses from a .pose file and save as a video.
    """
    args = parse_arguments()

    pose_file = args.pose
    output_dir = args.output_dir
    replace_option = args.replace.lower()

    output_filename = os.path.splitext(os.path.basename(pose_file))[0] + ".mp4"
    output_video_path = os.path.join(output_dir, output_filename)

    if not check_output_file(output_video_path, replace_option):
        return

    pose = read_pose_file(pose_file)
    if pose is None:
        return

    save_pose_video(pose, output_video_path)

if __name__ == '__main__':
    main()
