#!/usr/bin/env python3
"""
Power BI Integration Module for Facial Recognition Attendance System
====================================================================

This module provides data preparation and export functionality for Power BI integration.
It creates optimized views and exports for comprehensive attendance analytics.

Features:
- SQLite to Power BI data connection
- Automated data refresh preparation
- Comprehensive attendance analytics views
- Real-time data export for dashboards

Author: Facial Attendance System
Date: 2025-06-23
"""

import sqlite3
import pandas as pd
import json
from datetime import datetime, timedelta
import os
from typing import Dict, List, Optional, Tuple

class PowerBIIntegration:
    """Power BI Integration class for attendance data analytics"""
    
    def __init__(self, db_path: str = "attendance.db"):
        """Initialize Power BI integration with database connection"""
        self.db_path = db_path
        self.connection = None
        self.connect_database()
    
    def connect_database(self) -> bool:
        """Establish connection to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row  # Enable column access by name
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return False
    
    def get_attendance_summary(self, days: int = 30) -> pd.DataFrame:
        """Get attendance summary for the last N days"""
        query = """
        SELECT
            DATE(timestamp) as date,
            COUNT(*) as total_detections,
            COUNT(DISTINCT nom) as unique_students
        FROM presences
        WHERE timestamp >= datetime('now', '-{} days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """.format(days)

        return pd.read_sql_query(query, self.connection)
    
    def get_student_attendance_patterns(self) -> pd.DataFrame:
        """Get individual student attendance patterns"""
        query = """
        SELECT
            nom as student_name,
            DATE(timestamp) as date,
            TIME(timestamp) as time,
            COUNT(*) as detection_count,
            MIN(timestamp) as first_detection,
            MAX(timestamp) as last_detection
        FROM presences
        WHERE timestamp >= datetime('now', '-90 days')
        GROUP BY nom, DATE(timestamp)
        ORDER BY nom, date DESC
        """

        return pd.read_sql_query(query, self.connection)
    
    def get_daily_attendance_rates(self) -> pd.DataFrame:
        """Calculate daily attendance rates by student"""
        query = """
        WITH student_days AS (
            SELECT DISTINCT
                s.prenom || ' ' || s.nom as full_name,
                DATE(p.timestamp) as date
            FROM etudiants s
            CROSS JOIN (
                SELECT DISTINCT DATE(timestamp) as timestamp
                FROM presences
                WHERE timestamp >= datetime('now', '-30 days')
            ) p
        ),
        attendance_data AS (
            SELECT
                nom as student_name,
                DATE(timestamp) as date,
                1 as was_present
            FROM presences
            WHERE timestamp >= datetime('now', '-30 days')
        )
        SELECT
            sd.full_name as student_name,
            sd.date,
            COALESCE(MAX(ad.was_present), 0) as was_present,
            COUNT(ad.student_name) as total_detections
        FROM student_days sd
        LEFT JOIN attendance_data ad ON sd.full_name = ad.student_name AND sd.date = ad.date
        GROUP BY sd.full_name, sd.date
        ORDER BY sd.full_name, sd.date DESC
        """

        return pd.read_sql_query(query, self.connection)
    
    def get_weekly_summary(self) -> pd.DataFrame:
        """Get weekly attendance summary"""
        query = """
        SELECT
            strftime('%Y-W%W', timestamp) as week,
            strftime('%Y-%m-%d', timestamp, 'weekday 0', '-6 days') as week_start,
            COUNT(*) as total_detections,
            COUNT(DISTINCT nom) as unique_students
        FROM presences
        WHERE timestamp >= datetime('now', '-12 weeks')
        GROUP BY strftime('%Y-W%W', timestamp)
        ORDER BY week DESC
        """

        return pd.read_sql_query(query, self.connection)
    
    def get_monthly_summary(self) -> pd.DataFrame:
        """Get monthly attendance summary"""
        query = """
        SELECT
            strftime('%Y-%m', timestamp) as month,
            COUNT(*) as total_detections,
            COUNT(DISTINCT nom) as unique_students
        FROM presences
        WHERE timestamp >= datetime('now', '-12 months')
        GROUP BY strftime('%Y-%m', timestamp)
        ORDER BY month DESC
        """

        return pd.read_sql_query(query, self.connection)
    
    def get_real_time_status(self) -> pd.DataFrame:
        """Get current real-time attendance status"""
        query = """
        WITH latest_detections AS (
            SELECT
                nom,
                MAX(timestamp) as last_seen
            FROM presences
            WHERE timestamp >= datetime('now', '-1 day')
            GROUP BY nom
        )
        SELECT
            s.prenom || ' ' || s.nom as student_name,
            s.id_etudiant as student_id,
            COALESCE(ld.last_seen, 'Never') as last_detection,
            CASE
                WHEN ld.last_seen >= datetime('now', '-2 hours') THEN 'Recently Active'
                WHEN ld.last_seen >= datetime('now', '-1 day') THEN 'Active Today'
                ELSE 'Inactive'
            END as activity_status
        FROM etudiants s
        LEFT JOIN latest_detections ld ON s.prenom || ' ' || s.nom = ld.nom
        ORDER BY ld.last_seen DESC NULLS LAST
        """

        return pd.read_sql_query(query, self.connection)
    
    def export_for_powerbi(self, output_dir: str = "powerbi_exports") -> Dict[str, str]:
        """Export all data views for Power BI consumption"""
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        exports = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # Export attendance summary
            df_summary = self.get_attendance_summary(90)  # Last 90 days
            summary_file = f"{output_dir}/attendance_summary_{timestamp}.csv"
            df_summary.to_csv(summary_file, index=False)
            exports['attendance_summary'] = summary_file
            
            # Export student patterns
            df_patterns = self.get_student_attendance_patterns()
            patterns_file = f"{output_dir}/student_patterns_{timestamp}.csv"
            df_patterns.to_csv(patterns_file, index=False)
            exports['student_patterns'] = patterns_file
            
            # Export daily rates
            df_rates = self.get_daily_attendance_rates()
            rates_file = f"{output_dir}/daily_rates_{timestamp}.csv"
            df_rates.to_csv(rates_file, index=False)
            exports['daily_rates'] = rates_file
            
            # Export weekly summary
            df_weekly = self.get_weekly_summary()
            weekly_file = f"{output_dir}/weekly_summary_{timestamp}.csv"
            df_weekly.to_csv(weekly_file, index=False)
            exports['weekly_summary'] = weekly_file
            
            # Export monthly summary
            df_monthly = self.get_monthly_summary()
            monthly_file = f"{output_dir}/monthly_summary_{timestamp}.csv"
            df_monthly.to_csv(monthly_file, index=False)
            exports['monthly_summary'] = monthly_file
            
            # Export real-time status
            df_realtime = self.get_real_time_status()
            realtime_file = f"{output_dir}/realtime_status_{timestamp}.csv"
            df_realtime.to_csv(realtime_file, index=False)
            exports['realtime_status'] = realtime_file
            
            print(f"✅ Power BI exports completed: {len(exports)} files created")
            return exports
            
        except Exception as e:
            print(f"❌ Export error: {e}")
            return {}
    
    def create_powerbi_connection_info(self) -> Dict:
        """Create connection information for Power BI"""
        return {
            "database_type": "SQLite",
            "database_path": os.path.abspath(self.db_path),
            "connection_string": f"Data Source={os.path.abspath(self.db_path)}",
            "tables": {
                "presences": "Main attendance records with facial recognition data",
                "etudiants": "Student information and registration data"
            },
            "recommended_refresh_interval": "15 minutes",
            "last_updated": datetime.now().isoformat()
        }
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("✅ Database connection closed")

if __name__ == "__main__":
    # Example usage
    pbi = PowerBIIntegration()
    
    # Export data for Power BI
    exports = pbi.export_for_powerbi()
    
    # Create connection info
    conn_info = pbi.create_powerbi_connection_info()
    
    # Save connection info
    with open("powerbi_exports/connection_info.json", "w") as f:
        json.dump(conn_info, f, indent=2)
    
    print("\n📊 Power BI Integration Summary:")
    print(f"   Database: {pbi.db_path}")
    print(f"   Exports: {len(exports)} files")
    print(f"   Connection info: powerbi_exports/connection_info.json")
    
    pbi.close_connection()
