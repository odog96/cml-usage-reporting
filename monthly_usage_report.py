#!/usr/bin/env python3
"""
CML Monthly Usage Report Job
Run this as a scheduled CML Job on the 1st of each month

This script generates usage reports for the previous month and exports:
- Individual CSV files for each resource type
- Combined CSV with all resources  
- JSON report with metadata and statistics
"""

import sys
import os
from datetime import datetime

# Import our utility functions
from cml_usage_utils import (
    get_resource_usage_data, 
    export_to_csv, 
    create_combined_csv,
    save_report_json,
    send_notification,
    get_last_month_dates
)

def main():
    """Main function to generate monthly usage report"""
    
    print("=" * 60)
    print("CML MONTHLY USAGE REPORT")
    print("=" * 60)
    
    # Get last month's date range
    start_date, end_date, year, month = get_last_month_dates()
    
    print(f"📅 Generating report for: {year}-{month:02d}")
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize report data
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'report_period': f"{year}-{month:02d}",
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'script_name': 'monthly_usage_report.py'
        },
        'resource_usage': {},
        'summary': {},
        'export_files': []
    }
    
    # Resource types to collect
    resource_types = ['cpu', 'memory', 'gpu']
    successful_resources = []
    
    print(f"\n📊 Collecting usage data...")
    
    # Collect data for each resource type
    for resource_type in resource_types:
        print(f"\n  Processing {resource_type.upper()}...")
        
        usage_data = get_resource_usage_data(resource_type, start_date, end_date)
        report['resource_usage'][resource_type] = usage_data
        
        if usage_data['success']:
            successful_resources.append(usage_data)
            
            # Export individual CSV
            csv_filename = f"cml_{resource_type}_usage_{year}_{month:02d}.csv"
            if export_to_csv(usage_data, csv_filename):
                report['export_files'].append(csv_filename)
        else:
            print(f"  ❌ Failed to get {resource_type} data: {usage_data['error']}")
    
    # Create combined CSV if we have any successful data
    if successful_resources:
        print(f"\n📊 Creating combined report...")
        combined_filename = f"cml_combined_usage_{year}_{month:02d}.csv"
        if create_combined_csv(successful_resources, combined_filename):
            report['export_files'].append(combined_filename)
    
    # Calculate summary statistics
    total_points = sum([r['statistics']['total_data_points'] for r in successful_resources])
    
    report['summary'] = {
        'successful_resources': len(successful_resources),
        'failed_resources': len(resource_types) - len(successful_resources),
        'total_data_points': total_points,
        'resources_processed': [r['series_type'] for r in successful_resources]
    }
    
    # Save JSON report
    json_filename = f"cml_monthly_report_{year}_{month:02d}.json"
    if save_report_json(report, json_filename):
        report['export_files'].append(json_filename)
    
    # Print summary
    print(f"\n" + "=" * 60)
    print(f"📋 REPORT SUMMARY")
    print(f"=" * 60)
    print(f"📅 Period: {report['report_metadata']['report_period']}")
    print(f"✅ Successful resources: {report['summary']['successful_resources']}")
    print(f"❌ Failed resources: {report['summary']['failed_resources']}")
    print(f"📊 Total data points: {report['summary']['total_data_points']}")
    print(f"📁 Files created: {len(report['export_files'])}")
    
    for filename in report['export_files']:
        print(f"   - {filename}")
    
    # Send notification
    if successful_resources:
        message = f"""Monthly CML usage report completed successfully!
        
Period: {year}-{month:02d}
Resources: {', '.join([r['series_type'] for r in successful_resources])}
Data points: {total_points}
Files: {len(report['export_files'])} files generated

Files created:
{chr(10).join(['- ' + f for f in report['export_files']])}
        """
        send_notification(message, f"CML Usage Report - {year}-{month:02d}")
        
        print(f"\n✅ Monthly report completed successfully!")
        return 0
    else:
        error_message = f"Monthly CML usage report FAILED - no data collected for {year}-{month:02d}"
        send_notification(error_message, f"CML Usage Report ERROR - {year}-{month:02d}")
        
        print(f"\n❌ Monthly report failed - no data collected!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        send_notification(f"CML Usage Report FATAL ERROR: {e}", "CML Usage Report CRITICAL ERROR")
        sys.exit(1)