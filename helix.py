import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import ftplib
import csv
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
import threading
import queue
import sys
import requests
import time

class ClinicalDataProcessor:
    """Handles FTP connection and file operations for PAGH Clinical Data"""
    def __init__(self, ftp_host, ftp_user, ftp_pass, remote_dir=""):
        self.ftp_host = ftp_host
        self.ftp_user = ftp_user
        self.ftp_pass = ftp_pass
        self.remote_dir = remote_dir
        self.ftp = None
        self.connected = False
    
    def connect(self, status_queue=None):
        """Connect to FTP server with passive mode"""
        try:
            if self.ftp:
                try:
                    self.ftp.quit()
                except:
                    pass
            
            self.ftp = ftplib.FTP(self.ftp_host, timeout=30)
            self.ftp.set_pasv(True)
            self.ftp.login(self.ftp_user, self.ftp_pass)
            
            if self.remote_dir:
                try:
                    self.ftp.cwd(self.remote_dir)
                except:
                    if status_queue:
                        status_queue.put((f"Warning: Could not change to remote dir '{self.remote_dir}'", "warning"))
            
            self.connected = True
            if status_queue:
                status_queue.put(("✅ FTP connection successful", "success"))
                status_queue.put((f"Current directory: {self.ftp.pwd()}", "info"))
            
            return True
        except Exception as e:
            self.connected = False
            if status_queue:
                status_queue.put((f"❌ Connection failed: {e}", "error"))
            return False
    
    def disconnect(self):
        """Safely disconnect from FTP"""
        if self.ftp:
            try:
                self.ftp.quit()
                self.connected = False
            except:
                pass
    
    def get_file_list(self, status_queue=None):
        """Get list of CSV files from server"""
        if not self.ftp or not self.connected:
            if status_queue:
                status_queue.put(("Not connected to FTP server", "error"))
            return []
        
        try:
            files = self.ftp.nlst()
            csv_files = [f for f in files if f.upper().endswith('.CSV')]
            
            if status_queue and csv_files:
                status_queue.put((f"Found {len(csv_files)} CSV files", "success"))
            elif status_queue:
                status_queue.put(("No CSV files found", "warning"))
            
            return sorted(csv_files)
        except Exception as e:
            if status_queue:
                status_queue.put((f"Failed to retrieve file list: {e}", "error"))
            return []

class ClinicalDataValidator:
    """Handles file validation logic for clinical data"""
    def __init__(self, download_dir, archive_dir, error_dir):
        self.download_dir = Path(download_dir)
        self.archive_dir = Path(archive_dir)
        self.error_dir = Path(error_dir)
        
        # Create directories if they don't exist
        for directory in [self.download_dir, self.archive_dir, self.error_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        self.processed_files_log = self.download_dir / "processed_files.txt"
        self.processed_files = self._load_processed_files()
    
    def _load_processed_files(self):
        """Load list of already processed files"""
        if self.processed_files_log.exists():
            return set(self.processed_files_log.read_text().splitlines())
        return set()
    
    def _save_processed_file(self, filename):
        """Mark file as processed"""
        self.processed_files.add(filename)
        self.processed_files_log.write_text("\n".join(sorted(self.processed_files)))
    
    def _generate_guid(self):
            """Generate GUID using external API with fallback"""
            api_url = "https://www.uuidtools.com/api/generate/v4"
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(api_url, timeout=5)
                    if response.status_code == 200:
                        guids = response.json()
                        if guids and isinstance(guids, list) and len(guids) > 0:
                            return guids[0]  # Return the first GUID
                    
                    # If we got here but no valid response, raise an exception
                    raise Exception(f"Invalid API response: {response.status_code}")
                    
                except requests.exceptions.Timeout:
                    if attempt < max_retries - 1:
                        time.sleep(1)  # Wait before retry
                        continue
                    else:
                        self._log_api_failure("Timeout")
                        break
                except requests.exceptions.ConnectionError:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        self._log_api_failure("Connection Error")
                        break
                except Exception as e:
                    if attempt < max_retries - 1:
                        time.sleep(1)
                        continue
                    else:
                        self._log_api_failure(str(e))
                        break
            
            # Fallback to local UUID generation
            fallback_guid = str(uuid.uuid4())
            self._log_api_failure(f"Using fallback GUID: {fallback_guid}")
            return fallback_guid
    
    def _log_api_failure(self, error_message):
        """Log API failures for monitoring"""
        api_log_path = self.error_dir / "api_failures.log"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        log_entry = f"[{timestamp}] API Failure: {error_message}\n"
        with open(api_log_path, "a") as f:
            f.write(log_entry)
        
    
        def _log_error(self, filename, error_details, status_queue=None):
            """Log error with API-generated GUID and timestamp"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate GUID via API
            if status_queue:
                status_queue.put(("  → Generating GUID via API...", "info"))
            
            guid = self._generate_guid()
            
            # Check if it's a fallback GUID
            is_fallback = not guid.startswith("API:")
            if is_fallback:
                guid_source = "Local Fallback"
            else:
                guid_source = "API"
                # Remove the "API:" prefix for cleaner display
                guid = guid[4:]
            
            # Create structured log entry
            log_entry = f"[{timestamp}] GUID: {guid} | Source: {guid_source} | File: {filename} | Error: {error_details}\n"
            
            error_log_path = self.error_dir / "error_report.log"
            with open(error_log_path, "a") as f:
                f.write(log_entry)
            
            if status_queue:
                status_queue.put((f"  📝 Error logged with {guid_source} GUID: {guid}", "warning"))
            
            return guid, log_entry
        
    def _validate_filename_pattern(self, filename, status_queue=None):
        """Validate filename against CLINICALDATA_YYYYMMDDHHMMSS.csv pattern"""
        pattern = r'^CLINICALDATA_\d{14}\.CSV$'
        is_valid = re.match(pattern, filename, re.IGNORECASE) is not None
        
        if status_queue:
            if is_valid:
                status_queue.put((f"  ✓ Filename pattern valid", "success"))
            else:
                status_queue.put((f"  ✗ Invalid filename pattern (expected CLINICALDATA_YYYYMMDDHHMMSS.csv)", "error"))
        return is_valid
    
    def _validate_csv_content(self, file_path, status_queue=None):
        """Validate CSV content structure and data integrity"""
        errors = []
        valid_records = []
        seen_records = set()
        
        if status_queue:
            status_queue.put((f"  → Validating content...", "info"))
        
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                
                try:
                    header = next(reader)
                    expected_fields = ["PatientID", "TrialCode", "DrugCode", "Dosage_mg", 
                                     "StartDate", "EndDate", "Outcome", "SideEffects", "Analyst"]
                    if header != expected_fields:
                        errors.append(f"Invalid header. Expected {len(expected_fields)} fields: {expected_fields}")
                        if status_queue:
                            status_queue.put((f"  ✗ Header mismatch", "error"))
                        return False, errors, 0
                    elif status_queue:
                        status_queue.put((f"  ✓ Header valid ({len(header)} fields)", "success"))
                except StopIteration:
                    errors.append("File is empty")
                    if status_queue:
                        status_queue.put((f"  ✗ File is empty", "error"))
                    return False, errors, 0
                
                row_num = 1
                error_counts = {
                    'field_count': 0, 'missing_fields': 0, 'dosage': 0,
                    'date_range': 0, 'date_format': 0, 'outcome': 0,
                    'duplicate': 0
                }
                
                for row in reader:
                    row_num += 1
                    record_errors = []
                    
                    # Check field count
                    if len(row) != 9:
                        error_counts['field_count'] += 1
                        errors.append(f"Row {row_num}: Expected 9 fields, got {len(row)}")
                        continue
                    
                    # Unpack fields
                    (patient_id, trial_code, drug_code, dosage, 
                     start_date, end_date, outcome, side_effects, analyst) = row
                    
                    # Check for missing required fields
                    if not all([patient_id, trial_code, drug_code, dosage, 
                               start_date, end_date, outcome, side_effects, analyst]):
                        error_counts['missing_fields'] += 1
                        record_errors.append("Missing required fields")
                    
                    # Validate dosage (positive integer)
                    try:
                        dosage_val = int(dosage)
                        if dosage_val <= 0:
                            error_counts['dosage'] += 1
                            record_errors.append(f"Dosage must be positive integer, got '{dosage}'")
                    except ValueError:
                        error_counts['dosage'] += 1
                        record_errors.append(f"Non-numeric dosage: '{dosage}'")
                    
                    # Validate date range and format
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        if end_dt < start_dt:
                            error_counts['date_range'] += 1
                            record_errors.append(f"EndDate ({end_date}) before StartDate ({start_date})")
                    except ValueError:
                        error_counts['date_format'] += 1
                        record_errors.append(f"Invalid date format (expected YYYY-MM-DD)")
                    
                    # Validate outcome values
                    valid_outcomes = ["Improved", "No Change", "Worsened"]
                    if outcome not in valid_outcomes:
                        error_counts['outcome'] += 1
                        record_errors.append(f"Invalid outcome '{outcome}'. Must be one of: {', '.join(valid_outcomes)}")
                    
                    # Check for duplicate records
                    record_key = f"{patient_id}_{trial_code}_{drug_code}_{start_date}"
                    if record_key in seen_records:
                        error_counts['duplicate'] += 1
                        record_errors.append(f"Duplicate record")
                    else:
                        seen_records.add(record_key)
                    
                    if record_errors:
                        errors.append(f"Row {row_num}: {'; '.join(record_errors)}")
                    else:
                        valid_records.append(row)
                
                # Summary reporting
                if status_queue:
                    status_queue.put((f"  → Scanned {row_num - 1} rows", "info"))
                    status_queue.put((f"  → Valid records: {len(valid_records)}", "success"))
                    
                    if error_counts['field_count'] > 0:
                        status_queue.put((f"    • Field count errors: {error_counts['field_count']}", "error"))
                    if error_counts['missing_fields'] > 0:
                        status_queue.put((f"    • Missing fields: {error_counts['missing_fields']}", "error"))
                    if error_counts['dosage'] > 0:
                        status_queue.put((f"    • Dosage errors: {error_counts['dosage']}", "error"))
                    if error_counts['date_range'] > 0:
                        status_queue.put((f"    • Date range errors: {error_counts['date_range']}", "error"))
                    if error_counts['date_format'] > 0:
                        status_queue.put((f"    • Date format errors: {error_counts['date_format']}", "error"))
                    if error_counts['outcome'] > 0:
                        status_queue.put((f"    • Outcome errors: {error_counts['outcome']}", "error"))
                    if error_counts['duplicate'] > 0:
                        status_queue.put((f"    • Duplicates: {error_counts['duplicate']}", "error"))
            
            if errors:
                return False, errors, len(valid_records)
            return True, [], len(valid_records)
            
        except UnicodeDecodeError:
            return False, ["File is not valid UTF-8 encoded CSV"], 0
        except Exception as e:
            return False, [f"File read error: {str(e)}"], 0
    
    def validate_selected_files(self, ftp, files, status_queue):
        """Validate specific files without archiving (dry-run)"""
        valid_count = 0
        invalid_count = 0
        
        for filename in files:
            if filename in self.processed_files:
                status_queue.put((f"\n⏭️ Skipping: {filename} (already processed)", "warning"))
                continue
            
            status_queue.put((f"\n{'='*60}", "info"))
            status_queue.put((f"🔍 Validating: {filename}", "info"))
            
            temp_path = self.download_dir / f"temp_validate_{filename}"
            try:
                # Download file temporarily for validation
                with open(temp_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                
                # Validate filename pattern
                if self._validate_filename_pattern(filename, status_queue):
                    is_valid, errors, record_count = self._validate_csv_content(temp_path, status_queue)
                    
                    if is_valid:
                        status_queue.put((f"✅ VALID: {filename} ({record_count} records)", "success"))
                        valid_count += 1
                    else:
                        status_queue.put((f"❌ INVALID: {filename} ({len(errors)} errors)", "error"))
                        invalid_count += 1
                else:
                    status_queue.put((f"❌ INVALID: {filename} (filename pattern)", "error"))
                    invalid_count += 1
                
                # Clean up temporary file
                temp_path.unlink()
            except Exception as e:
                status_queue.put((f"❌ Error validating {filename}: {e}", "error"))
                invalid_count += 1
                if temp_path.exists():
                    temp_path.unlink()
        
        status_queue.put(("\n" + "="*60, "info"))
        status_queue.put(("✅ Validation complete!", "complete"))
        status_queue.put((f"📊 Results: {valid_count} valid, {invalid_count} invalid", "summary"))
    
    def process_selected_files(self, ftp, files, status_queue):
        """Process files: download, validate, archive or reject"""
        processed_count = 0
        error_count = 0
        
        for filename in files:
            if filename in self.processed_files:
                status_queue.put((f"\n⏭️ Skipping: {filename} (already processed)", "warning"))
                continue
            
            status_queue.put((f"\n{'='*60}", "info"))
            status_queue.put((f"🔄 Processing: {filename}", "info"))
            
            local_path = self.download_dir / filename
            try:
                # Download file
                with open(local_path, 'wb') as f:
                    ftp.retrbinary(f'RETR {filename}', f.write)
                status_queue.put((f"  📥 Downloaded successfully", "success"))
                
                # Validate filename pattern
                if not self._validate_filename_pattern(filename, status_queue):
                    error_file = self.error_dir / filename
                    local_path.rename(error_file)
                    guid, _ = self._log_error(filename, "Invalid filename pattern")
                    status_queue.put((f"  ❌ Rejected - Invalid filename pattern (GUID: {guid})", "error"))
                    error_count += 1
                    continue
                
                # Validate content
                is_valid, errors, record_count = self._validate_csv_content(local_path, status_queue)
                
                if is_valid:
                    # Archive valid file with current date suffix
                    try:
                        current_date = datetime.now().strftime("%Y%m%d")
                        base_name = filename.replace('.CSV', '').replace('.csv', '')
                        archive_filename = f"{base_name}_{current_date}.CSV"
                        archive_path = self.archive_dir / archive_filename
                        
                        local_path.rename(archive_path)
                        self._save_processed_file(filename)
                        
                        status_queue.put((f"  ✅ Archived as: {archive_filename} ({record_count} records)", "success"))
                        processed_count += 1
                    except Exception as e:
                        guid, _ = self._log_error(filename, f"Archival failed: {e}")
                        status_queue.put((f"  ❌ Archival error (GUID: {guid})", "error"))
                        error_count += 1
                        if local_path.exists():
                            local_path.unlink()
                else:
                    # Move invalid file to error directory
                    error_file = self.error_dir / filename
                    local_path.rename(error_file)
                    
                    # Create error summary
                    error_summary = " | ".join(errors[:3])
                    if len(errors) > 3:
                        error_summary += f" ... and {len(errors) - 3} more"
                    
                    guid, _ = self._log_error(filename, error_summary)
                    status_queue.put((f"  ❌ Rejected ({len(errors)} errors)", "error"))
                    for error in errors[:3]:
                        status_queue.put((f"    • {error}", "error"))
                    if len(errors) > 3:
                        status_queue.put((f"    • ... and {len(errors) - 3} more errors", "error"))
                    
                    error_count += 1
            except Exception as e:
                status_queue.put((f"  ❌ Fatal error: {e}", "error"))
                error_count += 1
                if local_path.exists():
                    local_path.unlink()
        
        status_queue.put(("\n" + "="*60, "info"))
        status_queue.put(("✅ Processing complete!", "complete"))
        status_queue.put((f"📊 Summary: {processed_count} archived, {error_count} rejected", "summary"))

class PAGHClinicalDataManager:
    """Main GUI application for PAGH Clinical Data Management"""
    def __init__(self, root):
        self.root = root
        self.root.title("PAGH Clinical Data Manager")
        self.root.geometry("1200x800")  # Increased width for 3-column layout
        
        self.processor = None
        self.validator = None
        self.is_processing = False
        
        self.all_files = []
        self.displayed_files = []
        
        # Default configuration
        self.ftp_host = tk.StringVar(value="127.0.0.1")
        self.ftp_user = tk.StringVar(value="thiri")
        self.ftp_pass = tk.StringVar(value="123")
        self.remote_dir = tk.StringVar(value="")
        
        # Default directories
        default_base = Path.home() / "PAGH_ClinicalData"
        self.download_dir = tk.StringVar(value=str(default_base / "Downloads"))
        self.archive_dir = tk.StringVar(value=str(default_base / "Archive"))
        self.error_dir = tk.StringVar(value=str(default_base / "Errors"))
        
        self.search_var = tk.StringVar()
        
        self.create_widgets()
        self.setup_directories()
    
    def setup_directories(self):
        """Create necessary directories"""
        for var in [self.download_dir, self.archive_dir, self.error_dir]:
            Path(var.get()).mkdir(parents=True, exist_ok=True)
    
    def create_widgets(self):
        """Create the main GUI layout with 3-column design"""
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="PAGH Clinical Data Management System", 
                               font=('Arial', 16, 'bold'))
        title_label.pack(pady=(0, 15))
        
        # FTP Connection Frame (spans all columns)
        ftp_frame = ttk.LabelFrame(main_frame, text="FTP Connection Settings", padding="10")
        ftp_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(ftp_frame, text="Host:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(ftp_frame, textvariable=self.ftp_host, width=25).grid(row=0, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(ftp_frame, text="Username:").grid(row=0, column=2, sticky=tk.W, padx=(20, 5))
        ttk.Entry(ftp_frame, textvariable=self.ftp_user, width=20).grid(row=0, column=3, sticky=tk.W, pady=5)
        
        ttk.Label(ftp_frame, text="Password:").grid(row=0, column=4, sticky=tk.W, padx=(20, 5))
        ttk.Entry(ftp_frame, textvariable=self.ftp_pass, show="*", width=20).grid(row=0, column=5, sticky=tk.W, pady=5)
        
        # Connection buttons
        btn_frame = ttk.Frame(ftp_frame)
        btn_frame.grid(row=0, column=6, padx=(20, 0))
        
        self.connect_btn = ttk.Button(btn_frame, text="🔌 Connect", command=self.connect_to_server, width=12)
        self.connect_btn.pack(side=tk.LEFT, padx=2)
        
        self.disconnect_btn = ttk.Button(btn_frame, text="❌ Disconnect", command=self.disconnect_from_server, 
                                       width=12, state=tk.DISABLED)
        self.disconnect_btn.pack(side=tk.LEFT, padx=2)
        
        # Status label
        self.status_label = ttk.Label(ftp_frame, text="Status: Disconnected", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=7, sticky=tk.W, pady=(5, 0))
        
        # Create a container for the 3-column layout
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Configure grid weights for equal columns
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.columnconfigure(2, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # COLUMN 1: Server Files
        server_frame = ttk.LabelFrame(content_frame, text="Server Files", padding="10")
        server_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Search and controls in server frame
        control_frame = ttk.Frame(server_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(control_frame, text="Search:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(control_frame, textvariable=self.search_var, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.search_entry.bind('<KeyRelease>', self.filter_file_list)
        
        ttk.Button(control_frame, text="🔍", command=self.filter_file_list, width=3).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(control_frame, text="🔄", command=self.refresh_file_list, width=3).pack(side=tk.LEFT)
        
        # File list with scrollbar
        list_container = ttk.Frame(server_frame)
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.file_listbox = tk.Listbox(list_container, height=15, selectmode=tk.SINGLE)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(list_container, command=self.file_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=scrollbar.set)
        
        # Bind selection event
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_selection_change)
        
        # Action buttons in server frame
        action_frame = ttk.Frame(server_frame)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.validate_btn = ttk.Button(action_frame, text="🔍 Validate Selected", 
                                     command=self.validate_selected, state=tk.DISABLED, width=15)
        self.validate_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.process_btn = ttk.Button(action_frame, text="🚀 Process Selected", 
                                    command=self.process_selected, state=tk.DISABLED, width=15)
        self.process_btn.pack(side=tk.LEFT)
        
        # COLUMN 2: Local Directories
        dir_frame = ttk.LabelFrame(content_frame, text="Local Directories", padding="10")
        dir_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        
        directories = [
            ("Download Directory:", self.download_dir),
            ("Archive Directory:", self.archive_dir),
            ("Error Directory:", self.error_dir)
        ]
        
        for i, (label, var) in enumerate(directories):
            ttk.Label(dir_frame, text=label).pack(anchor=tk.W, pady=(10 if i==0 else 5, 2))
            entry_frame = ttk.Frame(dir_frame)
            entry_frame.pack(fill=tk.X, pady=(0, 10))
            ttk.Entry(entry_frame, textvariable=var, width=35).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(entry_frame, text="...", width=3,
                      command=lambda v=var: self.browse_directory(v)).pack(side=tk.RIGHT, padx=(5, 0))
        
        # Directory action buttons
        dir_action_frame = ttk.Frame(dir_frame)
        dir_action_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Button(dir_action_frame, text="📂 Open Error Log", 
                  command=self.open_error_log, width=20).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(dir_action_frame, text="🗑️ Clear Log", 
                  command=self.clear_log, width=10).pack(side=tk.LEFT)
        
        # COLUMN 3: Activity Log
        log_frame = ttk.LabelFrame(content_frame, text="Activity Log", padding="10")
        log_frame.grid(row=0, column=2, sticky="nsew")
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure log text tags for colored output
        self.log_text.tag_configure("info", foreground="#0066cc")
        self.log_text.tag_configure("success", foreground="#009900")
        self.log_text.tag_configure("warning", foreground="#ff9900")
        self.log_text.tag_configure("error", foreground="#cc0000")
        self.log_text.tag_configure("complete", foreground="#0099cc", font=("TkDefaultFont", 9, "bold"))
        self.log_text.tag_configure("summary", foreground="#9900cc", font=("TkDefaultFont", 9, "bold"))
        
        # Progress bar at the bottom
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.pack(fill=tk.X, pady=(10, 0))
        
        # Queue for thread-safe GUI updates
        self.status_queue = queue.Queue()
        self.root.after(100, self.check_queue)
    
    def browse_directory(self, var):
        """Browse for directory"""
        path = filedialog.askdirectory()
        if path:
            var.set(path)
            self.setup_directories()
    
    def log_message(self, message, tag="info"):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)
        self.root.update()
    
    def check_queue(self):
        """Check for messages from worker threads"""
        try:
            while True:
                message, tag = self.status_queue.get_nowait()
                self.log_message(message, tag)
                
                if tag in ["complete", "error"]:
                    self.is_processing = False
                    self.progress.stop()
                    if hasattr(self, 'validate_btn'):
                        self.validate_btn.config(state=tk.NORMAL, text="🔍 Validate Selected")
                    if hasattr(self, 'process_btn'):
                        self.process_btn.config(state=tk.NORMAL, text="🚀 Process Selected")
        except queue.Empty:
            pass
        
        self.root.after(100, self.check_queue)
    
    def update_status_label(self):
        """Update connection status label"""
        if self.processor and self.processor.connected:
            self.status_label.config(text=f"Status: Connected to {self.ftp_host.get()}", foreground="green")
            self.connect_btn.config(state=tk.DISABLED)
            self.disconnect_btn.config(state=tk.NORMAL)
        else:
            self.status_label.config(text="Status: Disconnected", foreground="red")
            self.connect_btn.config(state=tk.NORMAL)
            self.disconnect_btn.config(state=tk.DISABLED)
            self.validate_btn.config(state=tk.DISABLED)
            self.process_btn.config(state=tk.DISABLED)
    
    def on_file_selection_change(self, event):
        """Handle file selection changes"""
        selection = self.file_listbox.curselection()
        if selection and self.processor and self.processor.connected:
            self.validate_btn.config(state=tk.NORMAL)
            self.process_btn.config(state=tk.NORMAL)
        else:
            self.validate_btn.config(state=tk.DISABLED)
            self.process_btn.config(state=tk.DISABLED)
    
    def connect_to_server(self):
        """Connect to FTP server"""
        if self.is_processing:
            return
        
        if not all([self.ftp_host.get(), self.ftp_user.get(), self.ftp_pass.get()]):
            messagebox.showerror("Missing Information", "Please fill in all FTP connection fields.")
            return
        
        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.progress.start()
        
        thread = threading.Thread(target=self._connect_and_load_files)
        thread.daemon = True
        thread.start()
    
    def _connect_and_load_files(self):
        """Worker thread for FTP connection"""
        try:
            self.processor = ClinicalDataProcessor(
                self.ftp_host.get(),
                self.ftp_user.get(),
                self.ftp_pass.get(),
                self.remote_dir.get()
            )
            
            if self.processor.connect(self.status_queue):
                self.all_files = self.processor.get_file_list(self.status_queue)
                self.root.after(0, self.update_file_listbox)
                self.root.after(0, self.update_status_label)
            else:
                self.status_queue.put(("❌ Failed to establish connection", "error"))
            
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"🚨 Connection error: {e}", "error"))
            self.status_queue.put(("complete", "complete"))
    
    def disconnect_from_server(self):
        """Disconnect from FTP server"""
        if self.is_processing:
            return
        
        if not self.processor:
            messagebox.showwarning("Not Connected", "You are not connected to any server.")
            return
        
        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.progress.start()
        
        thread = threading.Thread(target=self._disconnect_worker)
        thread.daemon = True
        thread.start()
    
    def _disconnect_worker(self):
        """Worker thread for disconnection"""
        try:
            if self.processor:
                self.processor.disconnect()
                self.all_files = []
                self.root.after(0, self.update_file_listbox)
                self.root.after(0, self.update_status_label)
                self.status_queue.put(("✅ Disconnected from FTP server", "success"))
            
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"🚨 Disconnect failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))
    
    def update_file_listbox(self):
        """Update the file listbox with current files"""
        self.file_listbox.delete(0, tk.END)
        self.displayed_files = self.all_files.copy()
        for file in self.displayed_files:
            self.file_listbox.insert(tk.END, file)
        self.log_message(f"📁 Loaded {len(self.displayed_files)} files from server", "info")
    
    def filter_file_list(self, event=None):
        """Filter files based on search term"""
        search_term = self.search_var.get().lower()
        self.file_listbox.delete(0, tk.END)
        self.displayed_files = [f for f in self.all_files if search_term in f.lower()]
        
        for file in self.displayed_files:
            self.file_listbox.insert(tk.END, file)
        
        # Show message if no results
        if search_term and not self.displayed_files:
            self.log_message(f"❌ No files found matching '{search_term}'", "error")
        elif search_term and self.displayed_files:
            self.log_message(f"🔍 Filtered: showing {len(self.displayed_files)} files matching '{search_term}'", "info")
    
    def refresh_file_list(self):
        """Refresh file list from server"""
        if not self.processor:
            messagebox.showwarning("Not Connected", "Please connect to the FTP server first.")
            return
        
        if self.is_processing:
            return
        
        # Clear search
        self.search_var.set("")
        
        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.progress.start()
        
        thread = threading.Thread(target=self._refresh_files)
        thread.daemon = True
        thread.start()
    
    def _refresh_files(self):
        """Worker thread for refreshing files"""
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)
            
            self.all_files = self.processor.get_file_list(self.status_queue)
            self.root.after(0, self.update_file_listbox)
            self.status_queue.put(("✅ File list refreshed", "success"))
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"🚨 Refresh failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))
    
    def validate_selected(self):
        """Validate selected file (dry-run)"""
        if self.is_processing:
            return
        
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to validate.")
            return
        
        selected_file = self.displayed_files[selection[0]]
        
        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.validate_btn.config(state=tk.DISABLED, text="⏳ Validating...")
        self.process_btn.config(state=tk.DISABLED)
        self.progress.start()
        
        self.validator = ClinicalDataValidator(
            self.download_dir.get(),
            self.archive_dir.get(),
            self.error_dir.get()
        )
        
        thread = threading.Thread(target=self._validate_selected_worker, args=([selected_file],))
        thread.daemon = True
        thread.start()
    
    def _validate_selected_worker(self, files):
        """Worker thread for validation"""
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)
            
            self.validator.validate_selected_files(self.processor.ftp, files, self.status_queue)
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"🚨 Validation failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))
    
    def process_selected(self):
        """Process selected file (download, validate, archive/reject)"""
        if self.is_processing:
            return
        
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("No Selection", "Please select a file to process.")
            return
        
        selected_file = self.displayed_files[selection[0]]
        
        confirm = messagebox.askyesno("Confirm Processing", 
                                    f"Process file '{selected_file}'?\n\n"
                                    "✓ If valid, will be archived with date suffix\n"
                                    "✗ If invalid, will be moved to error folder\n"
                                    "⏭ Already processed files will be skipped")
        if not confirm:
            return
        
        self.log_text.delete(1.0, tk.END)
        self.is_processing = True
        self.validate_btn.config(state=tk.DISABLED)
        self.process_btn.config(state=tk.DISABLED, text="⏳ Processing...")
        self.progress.start()
        
        self.validator = ClinicalDataValidator(
            self.download_dir.get(),
            self.archive_dir.get(),
            self.error_dir.get()
        )
        
        thread = threading.Thread(target=self._process_selected_worker, args=([selected_file],))
        thread.daemon = True
        thread.start()
    
    def _process_selected_worker(self, files):
        """Worker thread for processing"""
        try:
            if not self.processor.connected:
                self.processor.connect(self.status_queue)
            
            self.validator.process_selected_files(self.processor.ftp, files, self.status_queue)
            self.status_queue.put(("complete", "complete"))
        except Exception as e:
            self.status_queue.put((f"🚨 Processing failed: {e}", "error"))
            self.status_queue.put(("complete", "complete"))
    
    def open_error_log(self):
        """Open error log file"""
        error_log_path = Path(self.error_dir.get()) / "error_report.log"
        if error_log_path.exists():
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(error_log_path)
                else:  # macOS/Linux
                    os.system(f'open "{error_log_path}"' if sys.platform == "darwin" else f'xdg-open "{error_log_path}"')
            except Exception as e:
                messagebox.showerror("Error", f"Could not open error log: {e}")
        else:
            messagebox.showinfo("Error Log", "No errors have been logged yet.")
    
    def clear_log(self):
        """Clear the activity log"""
        self.log_text.delete(1.0, tk.END)

def main():
    """Main application entry point"""
    root = tk.Tk()
    app = PAGHClinicalDataManager(root)
    root.mainloop()

if __name__ == "__main__":
    main()