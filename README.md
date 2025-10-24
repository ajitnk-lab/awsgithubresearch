# AWS GitHub Repository Classification System

Production-ready intelligent categorization system for AWS official repositories with crash recovery and resumability.

## 🎯 Overview

Automatically classifies 945+ awslabs repositories using a comprehensive 20-dimension framework including business classification, technical analysis, and solution marketing categories.

## 🚀 Features

- **20-Dimension Classification**: Complete business-ready analysis framework
- **S3-Based Checkpointing**: Crash recovery and resumable processing
- **README Fallback**: Extracts descriptions from README when GitHub description is missing
- **Robust Error Handling**: Handles None values and API failures gracefully
- **Public Results**: Accessible via S3 for analysis and sharing
- **Production Ready**: Processes 945+ repositories with batch processing
- **Generic Support**: Works with any GitHub organization (awslabs, microsoft, google, etc.)

## 📊 Classification Dimensions

### Business Classification
- **Solution Type**: Foundation Builders, Innovation Catalysts, Quick Wins, Compliance Accelerators
- **Competency**: Analytics, Security, DevOps, AI/ML, etc.
- **Customer Problems**: Pre-deployment pain points and challenges
- **Solution Marketing**: 15 categories (setup, landingzone, starter, optimise, compliance, etc.)

### Technical Analysis
- **Languages & Frameworks**: Primary and secondary technologies
- **AWS Services**: Detected AWS service integrations
- **Deployment Tools**: Infrastructure and deployment technologies

### Business Value
- **Cost Range**: Estimated implementation costs
- **Setup Time**: Quick setup vs full-day implementation
- **USP**: Unique selling propositions
- **Freshness**: Last update status

### AI/GenAI Detection
- **Agentic Capabilities**: Identifies AI agent frameworks and patterns

## 🏗️ Architecture

```
s3://aws-github-repo-classification-{org}/
├── master-index/{org}_repos.json       # All repositories to process
├── checkpoints/progress.json           # Current position & completed repos  
└── results/classification_results.csv  # Final classification output
```

## 🔧 Usage

### Prerequisites
- Python 3.7+
- AWS CLI configured with S3 permissions
- Required packages: `boto3`, `requests`

### AWSlabs (Original)

1. **Fetch Repositories**
```bash
python3 fetch_repos.py
```

2. **Run Classification**
```bash
python3 s3_classifier.py
```

3. **Access Results**
- CSV: https://aws-github-repo-classification.s3.amazonaws.com/results/classification_results.csv
- Progress: https://aws-github-repo-classification.s3.amazonaws.com/checkpoints/progress.json

### Generic (Any Organization)

1. **Fetch Repositories**
```bash
python3 generic_fetch_repos.py microsoft
python3 generic_fetch_repos.py google
python3 generic_fetch_repos.py hashicorp
```

2. **Run Classification**
```bash
python3 generic_classifier.py microsoft
python3 generic_classifier.py google --batch-size 20
python3 generic_classifier.py hashicorp
```

3. **Access Results**
- Bucket: https://aws-github-repo-classification-{org}.s3.amazonaws.com/
- CSV: https://aws-github-repo-classification-{org}.s3.amazonaws.com/results/classification_results.csv

### Resumability

The system automatically resumes from last checkpoint if interrupted:
- Tracks completed repositories
- Skips already processed items
- Saves progress after each batch (every 10 repositories)
- No duplicate processing

## 📈 Results

### AWSlabs Results
- **Total Repositories**: 945 awslabs repositories
- **Successfully Classified**: 925 repositories (97.9% success rate)
- **Processing Time**: ~6 minutes for full dataset
- **Batch Size**: 10 repositories per checkpoint

### Generic Results
- **Supports any GitHub organization**
- **Automatic S3 bucket creation** with organization prefix
- **Same 20-dimension classification** framework
- **Configurable batch processing**

## 🔗 Public Access

### AWSlabs (Original)
- **S3 Bucket**: https://aws-github-repo-classification.s3.amazonaws.com/
- **Results CSV**: Direct download of 925 classified repositories
- **Real-time Progress**: Monitor processing status via checkpoints
- **Master Index**: Complete repository metadata

### Generic Organizations
- **S3 Bucket**: https://aws-github-repo-classification-{org}.s3.amazonaws.com/
- **Results CSV**: Organization-specific classification results
- **Progress Monitoring**: Real-time processing status
- **Automatic Public Access**: All buckets created with public read access

## 🛠️ Technical Details

### Error Handling
- Handles None values in GitHub API responses
- README fallback for missing descriptions
- Robust field mapping (stargazers_count, forks_count, html_url)
- Graceful API rate limit handling

### Performance
- Batch processing with configurable sizes
- S3-based persistence for large datasets
- Memory-efficient streaming processing
- Automatic retry logic for failed classifications

### Data Quality
- 20-dimension validation framework
- Consistent classification methodology
- Automated filtering of samples/examples repositories
- Production-ready solution focus

## 📋 Sample Output

Each repository gets classified with:
```csv
repository,solution_type,competency,customer_problems,solution_marketing,primary_language,aws_services,cost_range,setup_time,usp,freshness_status,...
awslabs/aws-sdk-rust,Foundation Builders,DevOps,Development Efficiency,foundation,Rust,"S3,Lambda,DynamoDB",Medium ($1K-10K),Half-day Setup,Popular community solution (2000+ stars),Recently Updated
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test with sample repositories
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

---

**Built for AWS Solutions Architects and DevOps teams to quickly identify and categorize open-source solutions from any GitHub organization.**
