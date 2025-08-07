#!/usr/bin/env python3
"""
CML Enhanced Monthly Usage Report Job
Run this as a scheduled CML Job on the 1st of each month

This script generates enhanced usage reports using the listUsage API for the previous month:
- Detailed CSV with all workload records
- User summary report (top consumers by CPU/GPU/Memory)
- Project summary report (resource usage by project)
- Workload type analysis (jobs vs sessions vs applications)
- JSON report with metadata and statistics
"""

import sys
import os
import json
from datetime import datetime, timedelta
import cmlapi
import pandas as pd

# Import our utility functions
from cml_usage_utils import (
    send_notification,
    get_last_month_dates
)

def get_cml_client():
    """Initialize CML API client"""
    try:
        return cmlapi.default_client()
    except Exception as e:
        print(f"ERROR: Failed to initialize CML client: {e}")
        sys.exit(1)

def get_enhanced_usage_data(start_date, end_date):
    """
    Fetch comprehensive usage data using listUsage API
    
    Args:
        start_date (datetime): Start date for the report
        end_date (datetime): End date for the report
    
    Returns:
        dict: Success status and DataFrame with usage data
    """
    client = get_cml_client()
    
    # Convert to ISO format with timezone
    # Ensure we have datetime objects with proper time components
    if hasattr(start_date, 'date'):
        # It's already a datetime
        start_str = start_date.isoformat() + "Z"
    else:
        # It's a date, convert to datetime at start of day
        start_str = datetime.combine(start_date, datetime.min.time()).isoformat() + "Z"
    
    if hasattr(end_date, 'date'):
        # It's already a datetime  
        end_str = end_date.isoformat() + "Z"
    else:
        # It's a date, convert to datetime at end of day
        end_str = datetime.combine(end_date, datetime.max.time()).isoformat() + "Z"
    
    print(f"📊 Fetching enhanced usage data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    try:
        all_usage_records = []
        page_token = None
        
        while True:
            # Create search filter for time range (similar to get_time_series)
            time_range = {
                "created_time": {
                    "min": start_date.strftime("%Y-%m-%d %H:%M:%S"),
                    "max": end_date.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            # Call list_usage API with correct parameters
            api_params = {
                'search_filter': json.dumps(time_range),
                'page_size': 1000
            }
            
            if page_token:
                api_params['page_token'] = page_token
            
            usage_list = client.list_usage(**api_params)
            
            # Extract records from correct field name (usage_response, not usage)
            all_usage_records.extend(usage_list.usage_response)
            page_token = usage_list.next_page_token
            if not page_token:
                break
        
        print(f"✅ Successfully fetched {len(all_usage_records)} usage records")
        
        if not all_usage_records:
            return {
                'success': False,
                'data': pd.DataFrame(),
                'error': 'No usage data found for the specified period'
            }
        
        # Convert to DataFrame
        df = pd.DataFrame([record.to_dict() for record in all_usage_records])
        
        return {
            'success': True,
            'data': df,
            'record_count': len(all_usage_records)
        }
        
    except Exception as e:
        print(f"❌ Failed to fetch usage data: {e}")
        return {
            'success': False,
            'data': pd.DataFrame(),
            'error': str(e)
        }

def process_usage_data(df):
    """
    Clean and enhance the raw usage DataFrame with calculated metrics
    
    Args:
        df (DataFrame): Raw usage data from listUsage API
    
    Returns:
        DataFrame: Processed data with calculated metrics
    """
    if df.empty:
        return df
    
    try:
        # Convert numeric columns
        for col in ['duration', 'cpu', 'memory', 'nvidia_gpu']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        # Convert timestamps
        df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Extract nested information
        df['creator_username'] = df['creator_info'].apply(
            lambda x: x.get('username', 'Unknown') if isinstance(x, dict) else 'Unknown'
        )
        df['project_name'] = df['project_info'].apply(
            lambda x: x.get('name', 'Unknown') if isinstance(x, dict) else 'Unknown'
        )
        
        # Calculate resource-hour metrics
        df['duration_hours'] = df['duration'] / 3600.0
        df['cpu_hours'] = df['cpu'] * df['duration_hours']
        df['gpu_hours'] = df['nvidia_gpu'] * df['duration_hours']
        df['memory_gb_hours'] = (df['memory'] / 1024) * df['duration_hours']
        
        # Additional calculated fields
        df['has_gpu'] = df['nvidia_gpu'] > 0
        df['is_long_running'] = df['duration_hours'] > 1.0
        
        print(f"✅ Processed {len(df)} records with calculated metrics")
        return df
        
    except Exception as e:
        print(f"❌ Error processing usage data: {e}")
        return df

def generate_summary_reports(df):
    """Generate aggregated summary reports"""
    try:
        # User summary report
        user_report = df.groupby('creator_username').agg(
            total_cpu_hours=('cpu_hours', 'sum'),
            total_memory_gb_hours=('memory_gb_hours', 'sum'),
            total_gpu_hours=('gpu_hours', 'sum'),
            total_workloads=('id', 'count'),
            gpu_workloads=('has_gpu', 'sum'),
            avg_duration_hours=('duration_hours', 'mean')
        ).round(2).sort_values(by='total_cpu_hours', ascending=False)
        
        # Project summary report
        project_report = df.groupby('project_name').agg(
            total_cpu_hours=('cpu_hours', 'sum'),
            total_memory_gb_hours=('memory_gb_hours', 'sum'),
            total_gpu_hours=('gpu_hours', 'sum'),
            total_workloads=('id', 'count'),
            unique_users=('creator_username', 'nunique')
        ).round(2).sort_values(by='total_cpu_hours', ascending=False)
        
        # Workload type analysis
        workload_report = df.groupby('workload_type').agg(
            total_cpu_hours=('cpu_hours', 'sum'),
            total_memory_gb_hours=('memory_gb_hours', 'sum'),
            total_gpu_hours=('gpu_hours', 'sum'),
            total_runs=('id', 'count'),
            avg_duration_hours=('duration_hours', 'mean')
        ).round(2).sort_values(by='total_runs', ascending=False)
        
        # Status analysis
        status_report = df.groupby('status').agg(
            count=('id', 'count'),
            total_cpu_hours=('cpu_hours', 'sum')
        ).sort_values(by='count', ascending=False)
        
        return {
            'user_report': user_report,
            'project_report': project_report,
            'workload_report': workload_report,
            'status_report': status_report
        }
        
    except Exception as e:
        print(f"❌ Error generating summary reports: {e}")
        return None

def export_reports(processed_df, reports_dict, report_period):
    """Export all reports to CSV files"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        export_files = []
        
        # Ensure reports directory exists
        os.makedirs('reports', exist_ok=True)
        
        # Export detailed data
        detailed_cols = [
            'created_at', 'creator_username', 'project_name', 'workload_type', 
            'status', 'duration_hours', 'cpu', 'memory', 'nvidia_gpu',
            'cpu_hours', 'memory_gb_hours', 'gpu_hours', 'has_gpu'
        ]
        
        detailed_filename = f"enhanced_detailed_usage_{report_period}_{timestamp}.csv"
        detailed_path = os.path.join('reports', detailed_filename)
        processed_df[detailed_cols].to_csv(detailed_path, index=False)
        export_files.append(detailed_path)
        print(f"📁 Exported: {detailed_path}")
        
        # Export summary reports
        summary_files = [
            ('user_report', f"enhanced_user_summary_{report_period}_{timestamp}.csv"),
            ('project_report', f"enhanced_project_summary_{report_period}_{timestamp}.csv"),
            ('workload_report', f"enhanced_workload_summary_{report_period}_{timestamp}.csv"),
            ('status_report', f"enhanced_status_summary_{report_period}_{timestamp}.csv")
        ]
        
        for report_key, filename in summary_files:
            if report_key in reports_dict:
                filepath = os.path.join('reports', filename)
                reports_dict[report_key].to_csv(filepath)
                export_files.append(filepath)
                print(f"📁 Exported: {filepath}")
        
        return export_files
        
    except Exception as e:
        print(f"❌ Export failed: {e}")
        return []

def save_json_report(report_data, report_period):
    """Save comprehensive JSON report"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"enhanced_monthly_report_{report_period}_{timestamp}.json"
        filepath = os.path.join('reports', filename)
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📁 JSON Report: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ JSON save failed: {e}")
        return None

def main():
    """Main function to generate enhanced monthly usage report"""
    
    print("=" * 70)
    print("CML ENHANCED MONTHLY USAGE REPORT (listUsage API)")
    print("=" * 70)
    
    # Get last month's date range
    start_date, end_date, year, month = get_last_month_dates()
    report_period = f"{year}-{month:02d}"
    
    print(f"📅 Generating enhanced report for: {report_period}")
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # Initialize comprehensive report data
    report = {
        'report_metadata': {
            'generated_at': datetime.now().isoformat(),
            'report_period': report_period,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'script_name': 'enhanced_monthly_report.py',
            'api_method': 'listUsage'
        },
        'data_summary': {},
        'export_files': [],
        'processing_summary': {}
    }
    
    # 1. Fetch enhanced usage data
    usage_result = get_enhanced_usage_data(start_date, end_date)
    
    if not usage_result['success']:
        error_message = f"Enhanced monthly report FAILED - {usage_result['error']}"
        send_notification(error_message, f"CML Enhanced Report ERROR - {report_period}")
        print(f"\n❌ {error_message}")
        return 1
    
    # 2. Process the data
    processed_df = process_usage_data(usage_result['data'])
    
    if processed_df.empty:
        error_message = f"Enhanced monthly report FAILED - no processable data for {report_period}"
        send_notification(error_message, f"CML Enhanced Report ERROR - {report_period}")
        print(f"\n❌ {error_message}")
        return 1
    
    # 3. Generate summary reports
    summary_reports = generate_summary_reports(processed_df)
    
    if not summary_reports:
        error_message = f"Enhanced monthly report FAILED - could not generate summaries for {report_period}"
        send_notification(error_message, f"CML Enhanced Report ERROR - {report_period}")
        print(f"\n❌ {error_message}")
        return 1
    
    # 4. Display key insights
    print(f"\n📊 DATA INSIGHTS")
    print(f"=" * 70)
    print(f"Total Records: {len(processed_df)}")
    print(f"Total CPU Hours: {processed_df['cpu_hours'].sum():.1f}")
    print(f"Total GPU Hours: {processed_df['gpu_hours'].sum():.1f}")
    print(f"Total Memory GB-Hours: {processed_df['memory_gb_hours'].sum():.1f}")
    print(f"Unique Users: {processed_df['creator_username'].nunique()}")
    print(f"Unique Projects: {processed_df['project_name'].nunique()}")
    
    print(f"\n--- Top 5 Users by CPU Hours ---")
    print(summary_reports['user_report'][['total_cpu_hours', 'total_workloads', 'gpu_workloads']].head())
    
    print(f"\n--- Top 5 Projects by CPU Hours ---")
    print(summary_reports['project_report'][['total_cpu_hours', 'total_workloads', 'unique_users']].head())
    
    print(f"\n--- Usage by Workload Type ---")
    print(summary_reports['workload_report'])
    
    # 5. Export reports
    exported_files = export_reports(processed_df, summary_reports, report_period)
    
    # 6. Update report metadata
    report['data_summary'] = {
        'total_records': len(processed_df),
        'total_cpu_hours': float(processed_df['cpu_hours'].sum()),
        'total_gpu_hours': float(processed_df['gpu_hours'].sum()),
        'total_memory_gb_hours': float(processed_df['memory_gb_hours'].sum()),
        'unique_users': int(processed_df['creator_username'].nunique()),
        'unique_projects': int(processed_df['project_name'].nunique()),
        'date_range_days': (end_date - start_date).days
    }
    
    report['export_files'] = exported_files
    report['processing_summary'] = {
        'records_fetched': usage_result['record_count'],
        'records_processed': len(processed_df),
        'files_exported': len(exported_files)
    }
    
    # 7. Save JSON report
    json_file = save_json_report(report, report_period)
    if json_file:
        report['export_files'].append(json_file)
    
    # 8. Print final summary
    print(f"\n" + "=" * 70)
    print(f"📋 ENHANCED REPORT SUMMARY")
    print(f"=" * 70)
    print(f"📅 Period: {report_period}")
    print(f"📊 Records: {report['data_summary']['total_records']}")
    print(f"👥 Users: {report['data_summary']['unique_users']}")
    print(f"📂 Projects: {report['data_summary']['unique_projects']}")
    print(f"📁 Files created: {len(report['export_files'])}")
    
    for filename in report['export_files']:
        print(f"   - {filename}")
    
    # 9. Send notification
    message = f"""Enhanced CML usage report completed successfully!

Period: {report_period}
Records Processed: {report['data_summary']['total_records']:,}
Total CPU Hours: {report['data_summary']['total_cpu_hours']:.1f}
Total GPU Hours: {report['data_summary']['total_gpu_hours']:.1f}
Unique Users: {report['data_summary']['unique_users']}
Unique Projects: {report['data_summary']['unique_projects']}

Files Generated: {len(report['export_files'])}
{chr(10).join(['- ' + f for f in report['export_files']])}
"""
    
    send_notification(message, f"CML Enhanced Usage Report - {report_period}")
    
    print(f"\n✅ Enhanced monthly report completed successfully!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n💥 FATAL ERROR: {e}")
        send_notification(f"CML Enhanced Usage Report FATAL ERROR: {e}", "CML Enhanced Report CRITICAL ERROR")
        sys.exit(1)