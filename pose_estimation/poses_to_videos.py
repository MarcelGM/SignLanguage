import argparse
import os

from joblib import Parallel, delayed
from pose_format import Pose
from pose_format.pose_visualizer import PoseVisualizer
from tqdm import tqdm


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
    """
    parser = argparse.ArgumentParser(description='Visualize poses from .pose files in a directory and save as videos.')
    parser.add_argument('--input_dir', type=str, required=True, help='Path to the input directory containing .pose files.')
    parser.add_argument('--output_dir', type=str, required=True, help='Directory to save the output video files.')
    parser.add_argument('--replace', type=str, choices=['True', 'False', 'ask'], default='ask', help='Replace existing files: True, False, or ask.')
    parser.add_argument('--n_jobs', type=int, default=1, help='Number of CPU cores to use for parallel processing.')
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
        print(f"Error reading pose file {pose_file}: {e}")
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
        print(f"Error saving video {output_video_path}: {e}")

def process_file(pose_file, input_dir, output_dir, replace_option):
    """
    Process a single pose file to create a video.

    Args:
        pose_file (str): Path to the input .pose file.
        input_dir (str): Path to the input directory.
        output_dir (str): Path to the output directory.
        replace_option (str): Replace option ('True', 'False', or 'ask').
    """
    relative_path = os.path.relpath(pose_file, input_dir)
    output_video_path = os.path.join(output_dir, os.path.splitext(relative_path)[0] + ".mp4")
    os.makedirs(os.path.dirname(output_video_path), exist_ok=True)

    if not check_output_file(output_video_path, replace_option):
        return

    pose = read_pose_file(pose_file)
    if pose is None:
        return

    save_pose_video(pose, output_video_path)

def main():
    """
    Main function to visualize poses from .pose files in a directory and save as videos.
    """
    args = parse_arguments()

    input_dir = args.input_dir
    output_dir = args.output_dir
    replace_option = args.replace.lower()
    n_jobs = args.n_jobs

    pose_files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(input_dir) for f in filenames if os.path.splitext(f)[1] == '.pose']

    with tqdm(total=len(pose_files), desc="Processing Videos") as pbar:
        Parallel(n_jobs=n_jobs)(
            delayed(lambda pf: (process_file(pf, input_dir, output_dir, replace_option), pbar.update()))(pose_file)
            for pose_file in pose_files
        )

if __name__ == '__main__':
    main()
