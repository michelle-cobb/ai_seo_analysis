#!/usr/bin/env python3
"""
SFTP Log Download Script
Downloads rotated web server access logs from remote hosting provider via SFTP.
Handles multiple log files with date patterns and tracks downloaded files to avoid duplicates.
"""

import sys
import paramiko
import logging
import json
import re
from pathlib import Path
from datetime import datetime, date
from scripts.common import setup_logging


try:
    from config.credentials import SFTP_CONFIG, LOG_PATHS
except ImportError:
    print("ERROR: config/credentials.py not found!")
    print("Please create config/credentials.py based on credentials.py.example")
    sys.exit(1)

def ensure_data_directory():
    """Ensure the data/raw directory exists."""
    raw_data_dir = Path('data/raw')
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    return raw_data_dir

def parse_log_filename_date(filename):
    """
    Extract date from log filename pattern: access.log-2025-08-13-1755043209
    
    Args:
        filename (str): The log filename
        
    Returns:
        date or None: Parsed date object, or None if pattern doesn't match
    """
    # Pattern: access.log-YYYY-MM-DD-timestamp
    pattern = r'access\.log-(\d{4})-(\d{2})-(\d{2})-\d+'
    match = re.match(pattern, filename)
    
    if match:
        year, month, day = map(int, match.groups())
        try:
            return date(year, month, day)
        except ValueError:
            return None
    
    return None


def list_remote_log_files(sftp_client, remote_directory, logger):
    """
    List all access log files in the remote directory that match our pattern.
    
    Args:
        sftp_client: Active SFTP client connection
        remote_directory (str): Remote directory path
        logger: Logger instance
        
    Returns:
        list: List of tuples (filename, parsed_date) for matching files
    """
    try:
        logger.info(f"Listing files in remote directory: {remote_directory}")
        
        # List all files in the directory
        all_files = sftp_client.listdir(remote_directory)
        
        # Filter for access log files with date pattern
        log_files = []
        pattern = r'access\.log-\d{4}-\d{2}-\d{2}-\d+'
        
        for filename in all_files:
            if re.match(pattern, filename):
                file_date = parse_log_filename_date(filename)
                if file_date:
                    log_files.append((filename, file_date))
                    logger.debug(f"Found log file: {filename} (date: {file_date})")
                else:
                    logger.warning(f"Could not parse date from filename: {filename}")
        
        logger.info(f"Found {len(log_files)} access log files")
        return log_files
        
    except Exception as e:
        logger.error(f"Error listing remote directory: {str(e)}")
        return []

def get_existing_raw_files():
    raw_data_dir = Path('data/raw')
    return set(f.name for f in raw_data_dir.glob("access.log*") if f.is_file())

def filter_files_to_download(log_files, logger):
    """
    Filter log files to only include those that:
    1. Have dates before today
    2. Aren't already present in data/raw
    3. Are actual log files (not directories, compressed files, etc.)
    
    Args:
        log_files (list): List of tuples (filename, date)
        logger: Logger instance
        
    Returns:
        list: Filtered list of (filename, date) tuples to download
    """
    today = date.today()
    existing_files = get_existing_raw_files()
    to_download = []
    
    for filename, file_date in log_files:
        logger.debug(f"Processing file: {filename} with date: {file_date}")

        # Skip if it's not a proper log file
        if not is_valid_log_file(filename):
            logger.debug(f"Skipping {filename}: not a valid log file")
            continue
            
        # Skip if date is today or in the future
        if file_date >= today:
            logger.debug(f"Skipping {filename}: date {file_date} is not before today")
            continue
        
        # Skip if already downloaded
        if filename in existing_files:
            logger.debug(f"Skipping {filename}: already exists in raw folder")
            continue
        
        logger.debug(f"FILTER: Adding {filename} to download list")
        to_download.append((filename, file_date))
    
    logger.info(f"Files to download: {len(to_download)}")
    return to_download


def is_valid_log_file(filename):
    """
    Check if a filename represents a valid log file to download.
    
    Args:
        filename (str): The filename to check
        
    Returns:
        bool: True if it's a valid log file, False otherwise
    """
    # Convert to lowercase for case-insensitive checks
    filename_lower = filename.lower()
    
    # Skip compressed files
    compressed_extensions = ['.gz', '.zip', '.bz2', '.xz', '.7z', '.tar']
    if any(filename_lower.endswith(ext) for ext in compressed_extensions):
        return False

    return True

def download_log_file(sftp_client, remote_directory, filename, local_dir, logger):
    """
    Download a single log file from the remote server.
    
    Args:
        sftp_client: Active SFTP client connection
        remote_directory (str): Remote directory path
        filename (str): Name of the file to download
        local_dir (Path): Local directory to save the file
        logger: Logger instance
    
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        remote_path = f"{remote_directory.rstrip('/')}/{filename}"
        local_path = local_dir / filename  # Keep original filename
        
        logger.info(f"Downloading {filename}...")
        
        # Check if remote file exists and get size
        try:
            file_stats = sftp_client.stat(remote_path)
            file_size_mb = file_stats.st_size / (1024 * 1024)
            logger.info(f"File size: {file_size_mb:.2f} MB")
        except FileNotFoundError:
            logger.error(f"Remote file not found: {remote_path}")
            return False
        
        # Download the file
        sftp_client.get(remote_path, str(local_path))
        
        # Verify download
        if local_path.exists():
            local_size_mb = local_path.stat().st_size / (1024 * 1024)
            logger.info(f"✓ Downloaded {filename} ({local_size_mb:.2f} MB)")
            return True
        else:
            logger.error(f"✗ Download failed - local file not found: {filename}")
            return False
            
    except Exception as e:
        logger.error(f"✗ Error downloading {filename}: {str(e)}")
        return False


def connect_sftp(config, logger):
    """
    Establish SFTP connection to the remote server.
    
    Args:
        config: Dictionary with SFTP connection details
        logger: Logger instance
    
    Returns:
        tuple: (sftp_client, ssh_client) or (None, None) if failed
    """
    try:
        logger.info(f"Connecting to {config['hostname']}...")
        
        # Create SSH client
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.MissingHostKeyPolicy())
        
        # Connect to the server
        ssh_client.connect(
            hostname=config['hostname'],
            username=config['username'],
            password=config.get('password'),
            key_filename=config.get('key_filename'),
            port=config.get('port', 22),
            timeout=30
        )
        
        # Open SFTP session
        sftp_client = ssh_client.open_sftp()
        logger.info("SFTP connection established successfully")
        
        return sftp_client, ssh_client
        
    except paramiko.AuthenticationException:
        logger.error("Authentication failed - check username/password")
        return None, None
    except paramiko.SSHException as e:
        logger.error(f"SSH connection error: {str(e)}")
        return None, None
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        return None, None


def main():
    """Main execution function."""
    logger = setup_logging()
    logger.info("Starting rotated log download process")
    
    # Ensure data directory exists
    local_dir = ensure_data_directory()
    
    # Connect to SFTP server
    sftp_client, ssh_client = connect_sftp(SFTP_CONFIG, logger)
    
    if not sftp_client:
        logger.error("Failed to establish SFTP connection")
        return False
    
    downloaded_files = []
    new_downloads = set()
    
    try:
        # Get the remote log directory from config
        remote_log_directory = LOG_PATHS.get('log_directory', '/home/logs')
        
        # List all matching log files on remote server
        log_files = list_remote_log_files(sftp_client, remote_log_directory, logger)
        
        if not log_files:
            logger.warning("No access log files found matching the expected pattern")
            return False
        
        # Filter files to download (exclude today's date and already downloaded)
        files_to_download = filter_files_to_download(log_files, logger)
        
        if not files_to_download:
            logger.info("No new files to download")
            return True
        
        # Download each file
        for filename, file_date in files_to_download:
            success = download_log_file(
                sftp_client, remote_log_directory, filename, local_dir, logger
            )
            
            if success:
                downloaded_files.append(filename)
                new_downloads.add(filename)
            else:
                logger.warning(f"Failed to download {filename}")
        
        # Summary
        logger.info(f"\nDownload Summary:")
        logger.info(f"Total log files found: {len(log_files)}")
        logger.info(f"Files eligible for download: {len(files_to_download)}")
        logger.info(f"Files successfully downloaded: {len(downloaded_files)}")
        
        if downloaded_files:
            logger.info("Downloaded files:")
            for filename in sorted(downloaded_files):
                logger.info(f"  - {filename}")
        
        return len(downloaded_files) > 0 or len(files_to_download) == 0
        
    except Exception as e:
        logger.error(f"Unexpected error during download: {str(e)}")
        return False
        
    finally:
        # Clean up connections
        if sftp_client:
            sftp_client.close()
        if ssh_client:
            ssh_client.close()
        logger.info("SFTP connection closed")


if __name__ == "__main__":
    success = main()
    if success:
        print("\n✓ Log download process completed successfully!")
    else:
        print("\n✗ Log download process failed. Check the logs for details.")
        sys.exit(1)