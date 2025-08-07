import os
import sys
import cmlapi
import pandas as pd
from datetime import datetime, date

def get_last_month_dates():
    """Calculates the start and end dates for the previous month."""
    today = date.today()
    first_day_of_current_month = today.replace(day=1)
    end_date_of_last_month = first_day_of_current_month - pd.Timedelta(days=1)
    start_date_of_last_month = end_date_of_last_month.replace(day=1)
    return start_date_of_last_month, end_date_of_last_month

def get_usage_data(start_time, end_time):
    """
    Fetches all CML usage data and filters manually by date range.
    
    Args:
        start_time (datetime.date): The start date of the report.
        end_time (datetime.date): The end date of the report.
    
    Returns:
        pandas.DataFrame: A DataFrame containing all usage records for the period.
    """
    client = cmlapi.default_client()
    
    print(f"Fetching usage data and filtering for {start_time} to {end_time}...")
    
    all_usage_records = []
    page_token = None
    page_count = 0
    
    # Convert dates to datetime objects for comparison
    start_datetime = datetime.combine(start_time, datetime.min.time())
    end_datetime = datetime.combine(end_time, datetime.max.time())
    
    while True:
        try:
            # Use the working API call format (no search_filter!)
            if page_token:
                usage_list = client.list_usage(page_size=1000, page_token=page_token)
            else:
                usage_list = client.list_usage(page_size=1000)
            
            page_count += 1
            print(f"  Processing page {page_count}...")
            
            # Filter the records manually by date
            if usage_list.usage_response:
                filtered_records = []
                for record in usage_list.usage_response:
                    # The debug showed created_at is already a datetime object
                    if hasattr(record, 'created_at') and record.created_at:
                        # Remove timezone info for comparison if present
                        record_datetime = record.created_at
                        if record_datetime.tzinfo is not None:
                            record_datetime = record_datetime.replace(tzinfo=None)
                        
                        if start_datetime <= record_datetime <= end_datetime:
                            filtered_records.append(record)
                
                all_usage_records.extend(filtered_records)
                print(f"    Added {len(filtered_records)} records from this page")
            
            # Check for more pages
            page_token = usage_list.next_page_token
            if not page_token:
                break
                
        except Exception as e:
            print(f"Error calling CML API: {e}", file=sys.stderr)
            break
            
    print(f"Successfully fetched {len(all_usage_records)} records for the specified period.")
    
    # Convert to DataFrame using the structure we discovered
    if not all_usage_records:
        return pd.DataFrame()
    
    records_data = []
    for record in all_usage_records:
        record_dict = record.to_dict()
        records_data.append(record_dict)
    
    return pd.DataFrame(records_data)

def process_usage_df(df):
    """Cleans and enhances the raw usage DataFrame with calculated metrics."""
    if df.empty:
        return df
    
    # Convert numeric fields - we know the exact field names now
    numeric_columns = ['cpu', 'memory', 'nvidia_gpu']
    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    # Convert duration - it came as string "0" in the debug
    df['duration'] = pd.to_numeric(df['duration'], errors='coerce').fillna(0)
    
    # created_at is already a datetime, just ensure it
    df['created_at'] = pd.to_datetime(df['created_at'], errors='coerce')
    
    # Extract usernames from the structures we saw in debug
    df['creator_username'] = df['creator']  # This was already a plain string
    df['project_name'] = df['project_name']  # This was already a plain string
    
    # Calculate resource-hour metrics
    df['duration_hours'] = df['duration'] / 3600.0
    df['cpu_hours'] = df['cpu'] * df['duration_hours'] 
    df['gpu_hours'] = df['nvidia_gpu'] * df['duration_hours']
    df['memory_gb_hours'] = (df['memory'] / (1024**3)) * df['duration_hours']  # Convert bytes to GB
    
    return df

def generate_summary_reports(df):
    """Generates several aggregated summary reports from the detailed usage data."""
    if df.empty:
        empty_df = pd.DataFrame()
        return empty_df, empty_df, empty_df
    
    user_report = df.groupby('creator_username').agg(
        total_cpu_hours=('cpu_hours', 'sum'),
        total_memory_gb_hours=('memory_gb_hours', 'sum'),
        total_gpu_hours=('gpu_hours', 'sum'),
        total_workloads=('id', 'count')
    ).round(2).sort_values(by='total_cpu_hours', ascending=False)
    
    project_report = df.groupby('project_name').agg(
        total_cpu_hours=('cpu_hours', 'sum'),
        total_memory_gb_hours=('memory_gb_hours', 'sum'),
        total_gpu_hours=('gpu_hours', 'sum'),
        total_workloads=('id', 'count')
    ).round(2).sort_values(by='total_cpu_hours', ascending=False)
    
    workload_report = df.groupby('workload_type').agg(
        total_cpu_hours=('cpu_hours', 'sum'),
        total_gpu_hours=('gpu_hours', 'sum'),
        total_runs=('id', 'count')
    ).round(2).sort_values(by='total_runs', ascending=False)
    
    return user_report, project_report, workload_report

def main():
    """Main function to orchestrate the report generation."""
    print("=" * 60)
    print("CML ENHANCED MONTHLY USAGE REPORT (listUsage API - Fixed)")
    print("=" * 60)
    
    start_date, end_date = get_last_month_dates()
    report_period = start_date.strftime("%Y-%m")
    
    # Set the output directory to 'reports'
    OUTPUT_DIR = "reports"
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    print(f"📅 Generating report for: {report_period}")
    print(f"📅 Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    
    # 1. Fetch and process data
    usage_df = get_usage_data(start_date, end_date)
    if usage_df.empty:
        print("No usage data found for the specified period. Exiting.")
        return
        
    processed_df = process_usage_df(usage_df)
    
    # 2. Generate summary reports
    user_report, project_report, workload_report = generate_summary_reports(processed_df)
    
    # 3. Print summaries to console
    print("\n--- Top 5 User Consumption ---")
    print(user_report.head())
    print("\n--- Top 5 Project Consumption ---") 
    print(project_report.head())
    print("\n--- Consumption by Workload Type ---")
    print(workload_report)

    # 4. Export reports to CSV
    timestamp = datetime.now().strftime("%Y%m%d")
    
    # Export detailed, granular data
    detailed_cols = [
        'created_at', 'creator_username', 'project_name', 'workload_type', 
        'status', 'duration_hours', 'cpu_hours', 'memory_gb_hours', 'gpu_hours'
    ]
    detailed_filename = f"{OUTPUT_DIR}/{report_period}_detailed_usage_{timestamp}.csv"
    processed_df[detailed_cols].to_csv(detailed_filename, index=False)
    
    # Export aggregated reports
    user_filename = f"{OUTPUT_DIR}/{report_period}_user_summary_{timestamp}.csv"
    project_filename = f"{OUTPUT_DIR}/{report_period}_project_summary_{timestamp}.csv"
    workload_filename = f"{OUTPUT_DIR}/{report_period}_workload_summary_{timestamp}.csv"
    
    user_report.to_csv(user_filename)
    project_report.to_csv(project_filename)
    workload_report.to_csv(workload_filename)
    
    print("\n" + "=" * 60)
    print(f"✅ Reports successfully generated in the '{OUTPUT_DIR}' directory.")
    print(f"   - {detailed_filename}")
    print(f"   - {user_filename}")
    print(f"   - {project_filename}")
    print(f"   - {workload_filename}")
    print("=" * 60)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 A fatal error occurred: {e}", file=sys.stderr)
        sys.exit(1)