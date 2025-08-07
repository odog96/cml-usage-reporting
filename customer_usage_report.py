#!/usr/bin/env python3
"""
CML Custom Usage Report Job
Generate usage reports for specific date ranges

Usage examples:
- python custom_usage_report.py 2024 7        # July 2024
- python custom_usage_report.py 2024 7 15     # July 1-15, 2024  
- python custom_usage_report.py               # Current month to date
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
    get_month_dates
)

def parse_arguments():
    """Parse command line arguments"""
    args = sys.argv[1:]
    
    if len(args) == 0:
        # Current month to date
        now = datetime.now()
        start_date = datetime(now.year, now.month, 1)
        end_date = now
        period_label = f"{now.year}-{now.month:02d} (to date)"
        
    elif len(args) == 2:
        # Specific month (full month)
        year = int(args[0])
        month = int(args[1])
        start_date, end_date = get_month_dates(year, month)
        period_label = f"{year}-{month:02d}"
        
    elif len(args) == 3:
        # Specific month with end day
        year = int(args[0])
        month = int(args[1])
        end_day = int(args[2])
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, end_day, 23, 59, 59)
        period_label = f"{year}-{month:02d} (days 1-{end_day})"
        
    else:
        print("Usage: python custom_usage_report.py [year month [end_day]]")
        print("Examples:")
        print("  python custom_usage_report.py                # Current month to date")
        print("  python custom_usage_report.py 2024 7         # Full July 2024")
        print("  python custom_usage_report.py 2024 7 15      # July 1-15, 2024")
        sys.exit(1)
    
    return start_date, end_date, period_label

def main():
    """Main function to generate custom usage report"""
    
    print("=" * 60)
    print("CML CUSTOM USAGE REPORT")
    print("=" * 60)
    
    # Parse arguments
    try:
        start_date, end_date, period_label = parse_arguments()
    except Exception as e:
        print(f"❌ Error parsing arguments: {e}")
        sys.exit(1)
    
    print(f"📅 Generating report for: {period_label}")
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}")
    
    # Create filename-safe period label
    filename_period = f"{start_date.strftime('%Y_%m_%d')}_{end_date.strftime('%Y_%m_%d')}"
    
    # Initialize report data
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'report_period': period_label,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'script_name': 'custom_usage_report.py'
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
            csv_filename = f"cml_{resource_type}_usage_{filename_period}.csv"
            if export_to_csv(usage_data, csv_filename):
                report['export_files'].append(csv_filename)
        else:
            print(f"  ❌ Failed to get {resource_type} data: {usage_data['error']}")
    
    # Create combined CSV if we have any successful data
    if successful_resources:
        print(f"\n📊 Creating combined report...")
        combined_filename = f"cml_combined_usage_{filename_period}.csv"
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
    json_filename = f"cml_custom_report_{filename_period}.json"
    if save_report_json(report, json_filename):
        report['export_files'].append(json_filename)
    
    # Print summary
    print(f"\n" + "=" * 60)
    print(f"📋 REPORT SUMMARY")
    print(f"=" * 60)
    print(f"📅 Period: {period_label}")
    print(f"✅ Successful resources: {report['summary']['successful_resources']}")
    print(f"❌ Failed resources: {report['summary']['failed_resources']}")
    print(f"📊 Total data points: {report['summary']['total_data_points']}")
    print(f"📁 Files created: {len(report['export_files'])}")
    
    for filename in report['export_files']:
        print(f"   - {filename}")
    
    # Send notification
    if successful_resources:
        message = f"""Custom CML usage report completed successfully!
        
Period: {period_label}
Resources: {', '.join([r['series_type'] for r in successful_resources])}
Data points: {total_points}
Files: {len(report['export_files'])} files generated

Files created:
{chr(10).join(['- ' + f for f in report['export_files']])}
        """
        send_notification(message, f"CML Custom Usage Report - {period_label}")
        
        print(f"\n✅ Custom report completed successfully!")
        return 0
    else:
        error_message = f"Custom CML usage report FAILED - no data collected for {period_label}"
        send_notification(error_message, f"CML Custom Usage Report ERROR - {period_label}")
        
        print(f"\n❌ Custom report failed - no data collected!")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        send_notification(f"CML Custom Usage Report FATAL ERROR: {e}", "CML Usage Report CRITICAL ERROR")
        sys.exit(1)