FTP CSV Validator
Overview
FTP CSV Validator is a Python application designed to automate the process of downloading, validating, and processing CSV files from a remote FTP server. It is ideal for data ingestion pipelines, ETL processes, or any workflow that requires reliable, scheduled validation of data from an FTP source.

Key Features
Secure FTP Connectivity: Connects to FTP/S servers using credentials and secure modes (TLS/SSL).

Automated File Discovery: Lists and filters files in a target remote directory based on naming patterns (e.g., *.csv).

Robust CSV Validation: Performs structural validation on downloaded CSV files, including checks for:

Correct column count and header names.

Data type integrity (e.g., integers, dates, strings).

Mandatory field presence and absence of empty values.

Configurable Processing: Highly customizable validation rules and file handling through a central configuration file.

Singleton FTP Client: Implements the Singleton design pattern for the FTPClient to ensure a single, managed connection is used throughout the application lifecycle, preventing connection conflicts and resource leaks.

Comprehensive Logging: Detailed logs for monitoring connection status, file transfers, validation results, and errors.

Post-Validation Actions: Configurable actions for processed files (e.g., move to processed/ or failed/ folders on the server, local archiving).

Prerequisites
Python 3.8+

PostgreSQL 12+ database instance

FTP Server(s) hosting the sensor data files

Required Python packages (see requirements.txt or pyproject.toml0
