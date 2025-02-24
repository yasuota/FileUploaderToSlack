import json
import logging
import os
import uuid
import requests  # type: ignore
import argparse

# Log configuration
LOGGER = logging.getLogger('app')
LOGGER.setLevel('INFO')
logging.basicConfig(
    level='INFO', format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Manage Slack token and channel ID via environment variables or hardcoding
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
CHANNEL_ID = 'CHANNELID'


def main() -> None:
    """
    Sample script to send a notification to Slack
    """
    # 🔥 Get command-line arguments
    parser = argparse.ArgumentParser(
        description="Script to upload a file to Slack")
    parser.add_argument('--file', type=str, required=True,
                        help='Path to the file to be uploaded')

    parser.add_argument('--threadflag', type=str, required=True,
                        help='Path to the file to be uploaded')

    parser.add_argument('--thread_ts', type=str, required=True,
                        help='Path to the file to be uploaded')

    args = parser.parse_args()
    file_path = args.file

    # Convert it to Bool
    if args.threadflag.lower() in ('true', '1', 'yes'):
        threadflag = True
    elif args.threadflag.lower() in ('false', '0', 'no'):
        threadflag = False
    else:
        raise ValueError(
            "Invalid value for --threadflag. Use 'true' or 'false'.")

    thread_ts = args.thread_ts

    if not os.path.isfile(file_path):
        print(f"❌ The specified file was not found: {file_path}")
        exit()

    # Read the contents of the file
    with open(file_path, 'r', encoding='utf-8') as f:
        file_content = f.read()

    # Use only the filename as the title
    file_title = os.path.basename(file_path)

    # Post a message to Slack
    if not threadflag:
        slack_msg = f"Uploading the file {file_title} to Slack."
        response_json = send_message(slack_msg, CHANNEL_ID, SLACK_BOT_TOKEN)
        # Post the file contents as a thread to the message
        thread_ts = response_json['ts']
        send_file_content_on_message_thread(
            file_title, file_content, CHANNEL_ID, "0", SLACK_BOT_TOKEN)
    elif thread_ts == 'None' and threadflag:
        slack_msg = f"Uploading the file {file_title} to Slack."
        response_json = send_message(slack_msg, CHANNEL_ID, SLACK_BOT_TOKEN)
        # Post the file contents as a thread to the message
        thread_ts = response_json['ts']
        send_file_content_on_message_thread(
            file_title, file_content, CHANNEL_ID, thread_ts, SLACK_BOT_TOKEN)
    elif thread_ts != 'None' and threadflag:
        send_file_content_on_message_thread(
            file_title, file_content, CHANNEL_ID, thread_ts, SLACK_BOT_TOKEN)
    return thread_ts


def send_message(msg: str, channel_id: str, token: str) -> dict:
    """
    Post a message to Slack
    """
    LOGGER.info('Sending message to Slack.')
    url = 'https://slack.com/api/chat.postMessage'
    header = {'Authorization': f'Bearer {token}'}
    data = {'channel': channel_id, 'text': msg}

    response = requests.post(url, headers=header, data=data)
    response.raise_for_status()
    if not response.ok:
        raise Exception('Failed to post message to Slack.')

    response_json = response.json()
    LOGGER.info(response_json)
    return response_json


def send_file_content_on_message_thread(
    file_title: str, file_content: str, channel_id: str, thread_ts: str, token: str
) -> None:
    """
    Post the file to a specific Slack thread
    """
    file_name = f'{str(uuid.uuid4())}.txt'
    length = len(file_content.encode(encoding='utf-8'))
    upload_url, file_id = _get_upload_url_and_file_id(file_name, length, token)
    _upload_file_content(upload_url, file_content)
    _complete_upload(
        file_id, file_title, channel_id, thread_ts, token)


def _get_upload_url_and_file_id(filename: str, length: int, token: str) -> tuple[str, str]:
    """
    Get the file upload URL and file ID from Slack
    """
    LOGGER.info('Getting the upload URL from Slack.')
    url = 'https://slack.com/api/files.getUploadURLExternal'
    header = {'Authorization': f'Bearer {token}'}
    params = {'filename': filename, 'length': length}

    response = requests.get(url, headers=header, params=params)
    response.raise_for_status()
    if not response.ok:
        raise Exception('Failed to get upload URL from Slack.')

    response_json = response.json()
    LOGGER.info(response_json)
    return response_json['upload_url'], response_json['file_id']


def _upload_file_content(upload_url: str, file_content: str) -> None:
    """
    Upload the file content to Slack
    """
    LOGGER.info('Uploading file to Slack.')
    data = file_content.encode(encoding='utf-8')

    response = requests.post(upload_url, data=data)
    response.raise_for_status()
    if not response.ok:
        raise Exception('Failed to upload file to Slack.')


def _complete_upload(file_id: str, title: str, channel_id: str, thread_ts: str, token: str) -> None:
    """
    Complete the file upload to Slack
    """
    LOGGER.info("Completing the upload.")
    url = 'https://slack.com/api/files.completeUploadExternal'
    header = {'Authorization': f'Bearer {token}',
              'Content-Type': 'application/json; charset=utf-8'}
    data = {'files': [{'id': file_id, 'title': title}],
            'channel_id': channel_id, 'thread_ts': thread_ts}

    response = requests.post(url, headers=header, data=json.dumps(data))
    response.raise_for_status()

    if not response.ok:
        raise Exception('Failed to complete the upload.')


if __name__ == '__main__':
    main()
