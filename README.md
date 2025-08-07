# CML Usage Reporting Suite

A comprehensive collection of Python scripts for generating detailed usage reports in Cloudera Machine Learning (CML) environments. This suite provides both enhanced detailed reporting via the `listUsage` API and resource trend analysis via the `getTimeSeries` API.

## 🎯 Overview

The CML Usage Reporting Suite includes four main components:

1. **🔥 Enhanced Monthly Report** (`enhanced_monthly_report.py`) - **PRIMARY SCRIPT**
   - Uses `listUsage` API for detailed workload attribution
   - Provides user, project, and workload-level insights
   - Generates comprehensive billing and usage analytics

2. **Monthly Usage Report** (`monthly_usage_report.py`)
   - Uses `getTimeSeries` API for resource trend analysis
   - Automated monthly reports via CML Jobs
   - Focuses on CPU, Memory, and GPU utilization trends

3. **Custom Usage Report** (`customer_usage_report.py`) 
   - Custom date range reporting with `getTimeSeries`
   - Flexible on-demand report generation
   - Support for partial months and specific periods

4. **Shared Utilities** (`cml_usage_utils.py`)
   - Common functions for data processing and export
   - Unified error handling and notifications
   - Consistent CSV/JSON export functionality

## ✨ Key Features

### 📊 Enhanced Reporting Capabilities (Primary Focus)
- **Detailed Workload Attribution**: Individual workload records with user, project, and resource details
- **User & Project Analytics**: CPU/GPU/memory consumption per user and project
- **Workload Type Analysis**: Usage patterns by models, jobs, applications, sessions
- **Cost Attribution**: Ready for chargeback and billing reports
- **Comprehensive Metrics**: Duration, resource utilization, efficiency calculations

### 📈 Resource Trend Analysis
- **Time Series Data**: Resource utilization trends over time
- **Multi-Resource Tracking**: CPU, Memory, GPU usage patterns
- **Historical Analysis**: Month-over-month comparisons
- **Capacity Planning**: Data for resource scaling decisions

### 🔧 Production Features
- **Automated Scheduling**: CML Job integration for monthly reports
- **Error Resilience**: Multiple fallback strategies and robust error handling
- **Flexible Output**: CSV, JSON export formats in organized directory structure
- **Scalable Processing**: Handles large datasets with pagination

## 🚀 Quick Start

### Prerequisites
```bash
# Required in your CML environment
pip install pandas cmlapi
```

### 🔥 Primary Usage - Enhanced Monthly Report
```bash
# Generate comprehensive monthly report (RECOMMENDED)
python enhanced_monthly_report.py
```

This creates detailed user, project, and workload analysis with the richest data available.

### Alternative Usage - Resource Trend Reports
```bash
# Generate resource trend reports
python monthly_usage_report.py        # Last month trends
python customer_usage_report.py       # Custom date range trends
python customer_usage_report.py 2024 7 15  # July 1-15, 2024
```

## 📁 File Structure

```
your-cml-project/
├── enhanced_monthly_report.py      # 🔥 PRIMARY - Detailed usage analytics
├── monthly_usage_report.py         # Monthly resource trends (getTimeSeries)
├── customer_usage_report.py        # Custom date resource trends  
├── cml_usage_utils.py              # Shared utility functions
├── reports/                        # Generated reports directory
│   ├── enhanced_*_detailed_usage_*.csv    # Individual workload records
│   ├── enhanced_*_user_summary_*.csv      # User consumption totals
│   ├── enhanced_*_project_summary_*.csv   # Project consumption totals
│   ├── enhanced_*_workload_summary_*.csv  # Workload type analysis
│   ├── monthly_*_usage_*.csv              # Resource trend data
│   ├── custom_*_usage_*.csv               # Custom period trends
│   └── *_monthly_report_*.json            # Comprehensive metadata
└── README.md                       # This documentation
```

## 📊 Report Types & Outputs

### 🔥 Enhanced Reports (Primary - listUsage API)

#### Detailed Usage Report
Individual workload records including:
- **Timestamps**: When workloads were created/executed
- **Attribution**: Creator usernames and project names
- **Resource Consumption**: CPU hours, GPU hours, memory GB-hours
- **Workload Context**: Type (model/job/application/session), status, duration
- **Efficiency Metrics**: Resource utilization calculations

#### User Summary Report  
Per-user aggregations:
- **Total CPU Hours**: Sum of all CPU time consumed
- **Total GPU Hours**: Sum of all GPU time consumed
- **Total Memory GB-Hours**: Memory consumption over time
- **Total Workloads**: Count of workloads created
- **GPU Workloads**: Count of GPU-enabled workloads
- **Average Duration**: Mean workload execution time

#### Project Summary Report
Same metrics as user summary, grouped by project with additional:
- **Unique Users**: Number of different users per project
- **Activity Level**: Project utilization patterns

#### Workload Type Analysis
Usage breakdown by workload type (models vs jobs vs applications vs sessions).

### 📈 Resource Trend Reports (getTimeSeries API)

#### Individual Resource Files
- `monthly_cpu_usage_2024_07.csv` - CPU utilization over time
- `monthly_memory_usage_2024_07.csv` - Memory utilization trends  
- `monthly_gpu_usage_2024_07.csv` - GPU utilization patterns

#### Combined Resource Analysis
- `monthly_combined_usage_2024_07.csv` - All resources in one dataset
- Time series data with timestamps and resource counts
- Suitable for trend analysis and capacity planning

#### Comprehensive JSON Reports
- Complete metadata and processing statistics
- Raw time series data for advanced analysis
- Success/failure tracking and file inventories

## 🔧 Setup & Configuration

### 1. Basic Setup
```bash
# Copy all scripts to your CML project directory
# Install dependencies
pip install pandas cmlapi

# Test the enhanced report (recommended)
python enhanced_monthly_report.py
```

### 2. Automated Monthly Reports (CML Jobs)

#### Primary Job - Enhanced Monthly Report
```
Name: Enhanced Monthly Usage Report  
Script: enhanced_monthly_report.py
Schedule: 0 2 1 * * (2 AM on 1st of each month)
Resource Profile: Small (1 CPU, 2GB RAM)
Kernel: Python 3
```

#### Supplementary Job - Resource Trends
```
Name: Monthly Resource Trends Report
Script: monthly_usage_report.py  
Schedule: 0 3 1 * * (3 AM on 1st of each month, after enhanced report)
Resource Profile: Small (1 CPU, 2GB RAM)
Kernel: Python 3
```

### 3. Environment Configuration
The scripts use `cmlapi.default_client()` which automatically authenticates using CML's built-in environment variables. No additional configuration needed when running inside CML.

## 🎯 Use Cases

### 💰 Cost Management & Chargeback
**Primary Script: `enhanced_monthly_report.py`**
- **User-level billing**: Detailed CPU/GPU/memory consumption per user
- **Project cost allocation**: Resource usage broken down by project
- **Resource optimization**: Identify high-usage patterns and inefficiencies
- **Budget tracking**: Monitor resource consumption against quotas

### 📊 Analytics & Capacity Planning  
**Use both Enhanced + Trend Reports**
- **User behavior analysis**: Understand how teams utilize CML resources
- **Project health monitoring**: Track project activity and resource patterns
- **Capacity forecasting**: Predict future resource needs based on trends
- **Performance optimization**: Identify underutilized resources

### 🔒 Governance & Compliance
**Primary Script: `enhanced_monthly_report.py`**
- **Usage auditing**: Comprehensive tracking of workspace utilization
- **Policy enforcement**: Monitor adherence to resource quotas
- **Executive reporting**: Generate high-level usage dashboards
- **Compliance documentation**: Detailed records for audit requirements

## 🔍 API Methods Comparison

### listUsage API (Enhanced Report - PRIMARY)
✅ **Best for detailed attribution and billing**
- **Rich Context**: User names, project details, workload types
- **Resource Attribution**: Detailed CPU/GPU/memory allocation per workload  
- **Billing Data**: Duration, status, resource consumption
- **Comprehensive**: Individual workload records with full metadata

### getTimeSeries API (Trend Reports - SUPPLEMENTARY)  
✅ **Best for resource trends and capacity planning**
- **Time Series**: Resource utilization patterns over time
- **Trend Analysis**: Historical usage for capacity planning
- **Lightweight**: Efficient for monitoring and alerting
- **Aggregated**: Summary-level resource consumption data

## 🐛 Troubleshooting

### Common Issues

#### Enhanced Monthly Report Issues
- **"No usage data found"**: Check date range and ensure workload activity exists
- **API authentication errors**: Ensure running inside CML environment
- **Large dataset processing**: May take 1-2 minutes for high-activity workspaces

#### Resource Trend Report Issues  
- **API parameter errors**: Verify `getTimeSeries` API access
- **No trend data**: Check if resource monitoring is enabled
- **Time range issues**: Ensure valid date ranges for historical data

### Debug Strategies
- Monitor console output for processing progress
- Check the `reports/` directory for partial file generation
- Review JSON report files for detailed error information

## 🛠️ Customization

### Custom Metrics in Enhanced Reports
Extend `process_usage_df()` in `enhanced_monthly_report.py`:

```python
# Add cost calculations
df['estimated_cost'] = df['cpu_hours'] * CPU_COST_PER_HOUR
df['gpu_cost'] = df['gpu_hours'] * GPU_COST_PER_HOUR

# Add efficiency metrics
df['cpu_efficiency'] = df['cpu_hours'] / df['duration_hours']
df['resource_intensity'] = (df['cpu'] + df['nvidia_gpu']) / df['memory']
```

### Custom Date Ranges
Modify the date calculation functions:

```python
def get_custom_date_range():
    # Example: Last quarter
    end_date = date.today().replace(day=1) - pd.Timedelta(days=1)
    start_date = end_date.replace(day=1) - pd.DateOffset(months=2)
    return start_date, end_date
```

### Additional Export Formats
Add Excel, JSON, or other formats:

```python
# In the export section
processed_df.to_excel(f"{OUTPUT_DIR}/enhanced_{report_period}_usage.xlsx")
processed_df.to_json(f"{OUTPUT_DIR}/enhanced_{report_period}_usage.json")
```

### Email/Slack Notifications
Enhance `send_notification()` in `cml_usage_utils.py`:

```python
def send_notification(message, subject="CML Usage Report"):
    # Add email integration
    send_email(to="admin@company.com", subject=subject, body=message)
    
    # Add Slack integration  
    slack_webhook(message=f"{subject}: {message}")
```

## 📈 Production Deployment

### Recommended Setup
1. **Deploy Enhanced Report**: Primary monthly job using `enhanced_monthly_report.py`
2. **Add Trend Analysis**: Secondary job using `monthly_usage_report.py`  
3. **Configure Storage**: Set up shared storage for report outputs
4. **Set Up Notifications**: Configure email/Slack alerts for job completion
5. **Monitor Performance**: Track job execution times and success rates

### File Management
```bash
# Organize outputs in shared storage
/shared/cml-reports/
├── enhanced/           # Detailed usage reports
├── trends/             # Resource trend reports  
├── custom/             # Ad-hoc custom reports
└── archive/            # Historical reports
```

## 📚 API Reference

- **CML API v2**: [Cloudera Machine Learning REST API Reference](https://docs.cloudera.com/machine-learning/cloud/rest-api-reference/index.html)
- **Python CML API Client**: `cmlapi` library
- **listUsage endpoint**: Detailed workload usage data
- **getTimeSeries endpoint**: Resource utilization time series

## 🎉 Success Metrics

After deployment, you'll have:
- ✅ **Automated monthly billing reports** with user/project attribution
- ✅ **Resource trend analysis** for capacity planning
- ✅ **Custom reporting capability** for ad-hoc analysis  
- ✅ **Executive dashboards** ready for cost allocation
- ✅ **Comprehensive audit trail** for governance requirements

Your CML workspace now has enterprise-grade usage reporting and analytics! 🚀

---

## 🤝 Contributing

To enhance these scripts:
1. Test changes thoroughly in a CML environment
2. Ensure backward compatibility with existing report formats
3. Add appropriate error handling for new features
4. Update documentation for any new functionality

**Note**: These scripts are designed to run within Cloudera Machine Learning environments and require appropriate API access permissions.