#!/usr/bin/env python3
"""
Power BI Auto-Refresh Script for Facial Recognition Attendance System
====================================================================

This script automatically refreshes Power BI data exports at scheduled intervals
to ensure dashboards always show the latest attendance information.

Features:
- Scheduled data exports for Power BI
- Automatic file cleanup
- Error handling and logging
- Configurable refresh intervals

Usage:
    python powerbi_auto_refresh.py [--interval MINUTES] [--cleanup-days DAYS]

Author: Facial Attendance System
Date: 2025-06-23
"""

import os
import sys
import time
import argparse
import logging
import schedule
from datetime import datetime, timedelta
from powerbi_integration import PowerBIIntegration
import json

class PowerBIAutoRefresh:
    """Automated Power BI data refresh manager"""
    
    def __init__(self, db_path="attendance.db", export_dir="powerbi_exports", cleanup_days=7):
        """Initialize auto-refresh manager"""
        self.db_path = db_path
        self.export_dir = export_dir
        self.cleanup_days = cleanup_days
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/powerbi_refresh.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def refresh_data(self):
        """Perform data refresh for Power BI"""
        try:
            self.logger.info("🔄 Starting Power BI data refresh...")
            
            # Initialize Power BI integration
            pbi = PowerBIIntegration(self.db_path)
            
            # Export data for Power BI
            exports = pbi.export_for_powerbi(self.export_dir)
            
            if exports:
                self.logger.info(f"✅ Data refresh completed: {len(exports)} files exported")
                
                # Update connection info
                conn_info = pbi.create_powerbi_connection_info()
                conn_file = os.path.join(self.export_dir, "connection_info.json")
                
                with open(conn_file, "w") as f:
                    json.dump(conn_info, f, indent=2)
                
                # Create refresh status file
                status = {
                    "last_refresh": datetime.now().isoformat(),
                    "status": "success",
                    "files_exported": len(exports),
                    "export_files": list(exports.values()),
                    "next_refresh": self.get_next_refresh_time()
                }
                
                status_file = os.path.join(self.export_dir, "refresh_status.json")
                with open(status_file, "w") as f:
                    json.dump(status, f, indent=2)
                
                self.logger.info(f"📊 Refresh status saved to: {status_file}")
                
            else:
                self.logger.error("❌ Data refresh failed: No files exported")
                self.create_error_status("Export failed")
            
            # Close database connection
            pbi.close_connection()
            
            # Cleanup old files
            self.cleanup_old_files()
            
        except Exception as e:
            self.logger.error(f"❌ Data refresh error: {e}")
            self.create_error_status(str(e))
    
    def create_error_status(self, error_message):
        """Create error status file"""
        try:
            os.makedirs(self.export_dir, exist_ok=True)
            status = {
                "last_refresh": datetime.now().isoformat(),
                "status": "error",
                "error_message": error_message,
                "next_retry": (datetime.now() + timedelta(minutes=5)).isoformat()
            }
            
            status_file = os.path.join(self.export_dir, "refresh_status.json")
            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to create error status: {e}")
    
    def cleanup_old_files(self):
        """Clean up old export files"""
        try:
            if not os.path.exists(self.export_dir):
                return
            
            cutoff_date = datetime.now() - timedelta(days=self.cleanup_days)
            cleaned_count = 0
            
            for filename in os.listdir(self.export_dir):
                if filename.endswith('.csv') and '_' in filename:
                    filepath = os.path.join(self.export_dir, filename)
                    
                    # Extract timestamp from filename
                    try:
                        timestamp_str = filename.split('_')[-1].replace('.csv', '')
                        file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                        
                        if file_date < cutoff_date:
                            os.remove(filepath)
                            cleaned_count += 1
                            
                    except (ValueError, IndexError):
                        # Skip files that don't match expected format
                        continue
            
            if cleaned_count > 0:
                self.logger.info(f"🧹 Cleaned up {cleaned_count} old export files")
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def get_next_refresh_time(self):
        """Get next scheduled refresh time"""
        try:
            jobs = schedule.get_jobs()
            if jobs:
                next_run = min(job.next_run for job in jobs)
                return next_run.isoformat()
            return None
        except:
            return None
    
    def start_scheduler(self, interval_minutes=15):
        """Start the scheduled refresh process"""
        self.logger.info(f"🚀 Starting Power BI auto-refresh scheduler...")
        self.logger.info(f"📅 Refresh interval: {interval_minutes} minutes")
        self.logger.info(f"🗂️  Export directory: {self.export_dir}")
        self.logger.info(f"🧹 Cleanup after: {self.cleanup_days} days")
        
        # Schedule regular refresh
        schedule.every(interval_minutes).minutes.do(self.refresh_data)
        
        # Schedule daily cleanup at 2 AM
        schedule.every().day.at("02:00").do(self.cleanup_old_files)
        
        # Perform initial refresh
        self.logger.info("🔄 Performing initial data refresh...")
        self.refresh_data()
        
        # Start scheduler loop
        self.logger.info("⏰ Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Scheduler error: {e}")
    
    def run_once(self):
        """Run data refresh once and exit"""
        self.logger.info("🔄 Running one-time Power BI data refresh...")
        self.refresh_data()
        self.logger.info("✅ One-time refresh completed")

def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="Power BI Auto-Refresh for Facial Recognition Attendance System"
    )
    
    parser.add_argument(
        "--interval", 
        type=int, 
        default=15,
        help="Refresh interval in minutes (default: 15)"
    )
    
    parser.add_argument(
        "--cleanup-days", 
        type=int, 
        default=7,
        help="Days to keep old export files (default: 7)"
    )
    
    parser.add_argument(
        "--once", 
        action="store_true",
        help="Run refresh once and exit (no scheduling)"
    )
    
    parser.add_argument(
        "--db-path", 
        default="attendance.db",
        help="Path to SQLite database (default: attendance.db)"
    )
    
    parser.add_argument(
        "--export-dir", 
        default="powerbi_exports",
        help="Export directory (default: powerbi_exports)"
    )
    
    args = parser.parse_args()
    
    # Create auto-refresh manager
    refresh_manager = PowerBIAutoRefresh(
        db_path=args.db_path,
        export_dir=args.export_dir,
        cleanup_days=args.cleanup_days
    )
    
    if args.once:
        # Run once and exit
        refresh_manager.run_once()
    else:
        # Start scheduler
        refresh_manager.start_scheduler(args.interval)

if __name__ == "__main__":
    main()
