"""
CML Usage Reporting Utilities
Shared functions for CML usage data collection and processing
"""

import cmlapi
from datetime import datetime, timedelta
import json
import pandas as pd
from calendar import monthrange
import os
import sys

def get_cml_client():
    """Initialize CML API client"""
    try:
        return cmlapi.default_client()
    except Exception as e:
        print(f"ERROR: Failed to initialize CML client: {e}")
        sys.exit(1)

def get_resource_usage_data(series_type, start_date, end_date):
    """
    Get resource usage data for a specific time period
    
    Args:
        series_type (str): 'cpu', 'memory', or 'gpu'
        start_date (datetime): Start date
        end_date (datetime): End date
    
    Returns:
        dict: Processed usage data with timestamps and values
    """
    
    client = get_cml_client()
    
    # Format time range
    time_range = {
        "created_time": {
            "min": start_date.strftime("%Y-%m-%d %H:%M:%S"),
            "max": end_date.strftime("%Y-%m-%d %H:%M:%S")
        }
    }
    
    try:
        print(f"Fetching {series_type} data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        
        # Get time series data
        result = client.get_time_series(
            series_type=series_type,
            time_range_search_filter=json.dumps(time_range)
        )
        
        # Convert to dict to access the data
        result_dict = result.to_dict()
        
        # Extract the time series values
        raw_values = result_dict['result']['values']
        
        # Process the data
        processed_data = []
        for item in raw_values:
            # Convert timestamp from milliseconds to datetime
            timestamp_ms = int(item['time_stamp'])
            timestamp_dt = datetime.fromtimestamp(timestamp_ms / 1000)
            
            processed_data.append({
                'timestamp': timestamp_dt,
                'timestamp_str': timestamp_dt.isoformat(),
                'count': int(item['count']),
                'raw_timestamp': item['time_stamp']
            })
        
        # Sort by timestamp
        processed_data.sort(key=lambda x: x['timestamp'])
        
        # Calculate statistics
        if processed_data:
            counts = [item['count'] for item in processed_data]
            stats = {
                'total_data_points': len(processed_data),
                'min_count': min(counts),
                'max_count': max(counts),
                'avg_count': sum(counts) / len(counts),
                'total_count': sum(counts),
                'first_timestamp': processed_data[0]['timestamp_str'],
                'last_timestamp': processed_data[-1]['timestamp_str']
            }
        else:
            stats = {
                'total_data_points': 0,
                'min_count': 0,
                'max_count': 0,
                'avg_count': 0,
                'total_count': 0,
                'first_timestamp': None,
                'last_timestamp': None
            }
        
        print(f"✅ {series_type}: {stats['total_data_points']} data points, avg={stats['avg_count']:.1f}")
        
        return {
            'success': True,
            'series_type': series_type,
            'data_points': processed_data,
            'statistics': stats,
            'raw_result': result_dict
        }
        
    except Exception as e:
        print(f"❌ {series_type} failed: {e}")
        return {
            'success': False,
            'series_type': series_type,
            'error': str(e)
        }

def export_to_csv(usage_data, filename):
    """Export usage data to CSV file"""
    try:
        if not usage_data['data_points']:
            print(f"No data to export for {filename}")
            return False
            
        # Create DataFrame
        df = pd.DataFrame(usage_data['data_points'])
        df = df[['timestamp_str', 'count']]  # Keep only essential columns
        df.columns = ['timestamp', f"{usage_data['series_type']}_count"]
        
        # Ensure reports directory exists and prepend to filename
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        # Export to CSV
        df.to_csv(filepath, index=False)
        print(f"📁 Exported: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Export failed for {filename}: {e}")
        return False

def create_combined_csv(resource_data_list, filename):
    """Create combined CSV with all resource types"""
    try:
        combined_data = []
        
        for usage_data in resource_data_list:
            if usage_data['success']:
                for point in usage_data['data_points']:
                    combined_data.append({
                        'timestamp': point['timestamp_str'],
                        'resource_type': usage_data['series_type'],
                        'count': point['count']
                    })
        
        if not combined_data:
            print("No data to create combined CSV")
            return False
            
        # Create DataFrame and pivot
        df = pd.DataFrame(combined_data)
        pivot_df = df.pivot(index='timestamp', columns='resource_type', values='count').fillna(0)
        
        # Ensure reports directory exists and prepend to filename
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        # Export
        pivot_df.to_csv(filepath)
        print(f"📁 Combined CSV: {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Combined CSV creation failed: {e}")
        return False

def save_report_json(report_data, filename):
    """Save full report as JSON"""
    try:
        # Ensure reports directory exists and prepend to filename
        os.makedirs('reports', exist_ok=True)
        filepath = os.path.join('reports', filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        print(f"📁 Report JSON: {filepath}")
        return True
    except Exception as e:
        print(f"❌ JSON save failed: {e}")
        return False

def send_notification(message, subject="CML Usage Report"):
    """Send notification (placeholder for email/slack integration)"""
    print(f"\n🔔 NOTIFICATION: {subject}")
    print(f"📧 {message}")
    # TODO: Add actual email/Slack notification logic here

def get_last_month_dates():
    """Get start and end dates for last month"""
    now = datetime.now()
    if now.month == 1:
        last_month = 12
        last_year = now.year - 1
    else:
        last_month = now.month - 1
        last_year = now.year
        
    start_date = datetime(last_year, last_month, 1)
    last_day = monthrange(last_year, last_month)[1]
    end_date = datetime(last_year, last_month, last_day, 23, 59, 59)
    
    return start_date, end_date, last_year, last_month

def get_month_dates(year, month):
    """Get start and end dates for specific month"""
    start_date = datetime(year, month, 1)
    last_day = monthrange(year, month)[1]
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    return start_date, end_date