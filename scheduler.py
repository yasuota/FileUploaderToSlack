import sys
import os
import argparse
import logging
import slackupload
import tempfile
import subprocess

# Configuration
current_dir = os.path.dirname(os.path.abspath(__file__))
LOGGER = logging.getLogger('app')
LOGGER.setLevel('INFO')


def ping_and_save(host="google.com"):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")

    with open(temp_file.name, "w") as f:
        subprocess.run(["ping", "-c", "1", host],
                       stdout=f, stderr=subprocess.STDOUT)
    return temp_file.name


def upload_to_slack(file_path, threadflag, thread_ts):
    """Upload the generated file to Slack."""
    try:
        sys.argv = ['slackupload.py', '--file', file_path,
                    '--threadflag', str(threadflag), '--thread_ts', str(thread_ts)]
        return slackupload.main()
    except Exception as e:
        LOGGER.error(f"Failed to upload file to Slack: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description="Scheduler script for the script and Slack upload.")
    parser.add_argument('--threadflag', type=str, required=True,
                        help="Specify 'true' or 'false' for thread usage.")
    args = parser.parse_args()

    # Convert flags to boolean
    threadflag = args.threadflag.lower() in ('true', '1', 'yes')
    thread_ts = None

    while True:

        file_name = ping_and_save("google.com")

        if threadflag:
            thread_ts = upload_to_slack(file_name, threadflag, thread_ts)
        else:
            thread_ts = upload_to_slack(file_name, threadflag, "0")


if __name__ == "__main__":
    main()
