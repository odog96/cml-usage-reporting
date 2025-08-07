# CML Usage Reporting Setup Guide

## 📁 File Structure

Your CML project should have these files:

```
your-cml-project/
├── cml_usage_utils.py          # Shared utility functions
├── monthly_usage_report.py     # Monthly automated report (Job)
├── custom_usage_report.py      # Custom date range reports (Job)
└── README.md                   # This setup guide
```

## 🚀 Quick Setup

### 1. Create the Files
- Copy each script into separate `.py` files in your CML project
- Make sure all files are in the same directory

### 2. Install Dependencies
In a CML session, run:
```bash
pip install pandas
```

### 3. Test the Setup
```bash
# Test the monthly report (will generate for last month)
python monthly_usage_report.py

# Test custom report (current month to date)
python custom_usage_report.py
```

## 📅 Automated Monthly Reports

### Setup CML Job for Monthly Reports

1. **Create a new CML Job:**
   - Name: `Monthly Usage Report`
   - Script: `monthly_usage_report.py`
   - Schedule: `0 2 1 * *` (2 AM on 1st of each month)
   - Resource Profile: Small (1 CPU, 2GB RAM)

2. **Job Configuration:**
   ```
   Name: Monthly Usage Report
   Script: monthly_usage_report.py
   Schedule: 0 2 1 * *
   Kernel: Python 3
   ```

### What the Monthly Job Does:
- ✅ Automatically runs on the 1st of each month
- ✅ Generates reports for the previous month
- ✅ Creates CSV files for CPU, memory, GPU usage
- ✅ Creates combined CSV with all resources
- ✅ Creates JSON report with metadata
- ✅ Sends notifications (console output)

### Output Files (Monthly):
```
cml_cpu_usage_2024_07.csv           # CPU usage data
cml_memory_usage_2024_07.csv        # Memory usage data  
cml_gpu_usage_2024_07.csv           # GPU usage data
cml_combined_usage_2024_07.csv      # All resources combined
cml_monthly_report_2024_07.json     # Full report with metadata
```

## 🎯 Custom Reports

### Run Custom Reports On-Demand

```bash
# Current month to date
python custom_usage_report.py

# Specific full month
python custom_usage_report.py 2024 7

# Specific date range (July 1-15, 2024)
python custom_usage_report.py 2024 7 15
```

### Setup CML Job for Custom Reports
Create additional jobs as needed:
- **Weekly Reports**: Schedule to run weekly
- **Quarterly Reports**: Custom date ranges for quarters
- **On-Demand**: Manual job runs

## 📊 Report Contents

### CSV Files Include:
- **timestamp**: ISO format timestamps
- **[resource]_count**: Usage count for each resource type
- **Combined CSV**: All resources in one file with timestamp index

### JSON Report Includes:
- **Metadata**: Generation time, period, script info
- **Statistics**: Min, max, average, total for each resource
- **Raw Data**: Complete time series data
- **Summary**: Success/failure counts, file lists

## 🔧 Customization Options

### 1. Modify Resource Types
Edit `cml_usage_utils.py`:
```python
# Change this line to add/remove resource types
resource_types = ['cpu', 'memory', 'gpu']  # Add others if available
```

### 2. Add Email Notifications
Edit the `send_notification()` function in `cml_usage_utils.py`:
```python
def send_notification(message, subject="CML Usage Report"):
    # Add your email/Slack integration here
    # Example: send_email(subject, message)
    pass
```

### 3. Custom File Locations
Modify file paths in the scripts to save to shared storage:
```python
# Example: Save to shared project directory
csv_filename = f"/home/cdsw/shared/{resource_type}_usage_{year}_{month:02d}.csv"
```

### 4. Additional Filters
Add search filters to the API calls in `get_resource_usage_data()`:
```python
# Example: Filter by project
search_filter = {"project_name": "my-project"}
# Add to API call parameters
```

## 🚨 Troubleshooting

### Common Issues:

1. **Import Error**: Make sure all files are in the same directory
2. **Permission Error**: Ensure CML Job has write permissions
3. **No Data**: Check if time range has actual workload activity
4. **API Errors**: Verify CML API access and permissions

### Debug Mode:
Add debug prints to scripts:
```python
print(f"DEBUG: API call parameters: {params}")
```

## 📈 Usage Patterns

### For Your Customer's Requirements:

1. **"Download usage report every month"** ✅
   - Use `monthly_usage_report.py` as scheduled CML Job
   - Automatically generates CSV files
   - No manual intervention needed

2. **"Adjusting parameters every month"** ✅
   - Parameters auto-adjust for each month
   - No manual date changes required
   - Consistent file naming and format

3. **"API way to download"** ✅
   - Uses CML API (`get_time_series`)
   - Programmatic data collection
   - Structured output formats

## 🎉 Production Deployment

1. **Schedule Monthly Job**: Set up automated monthly reports
2. **Test Custom Reports**: Verify ad-hoc reporting works
3. **Configure Notifications**: Add email/Slack alerts
4. **Set File Storage**: Configure shared storage location
5. **Monitor Jobs**: Check job success/failure logs

Your customer now has a complete automated solution for monthly CML usage reporting! 🚀
