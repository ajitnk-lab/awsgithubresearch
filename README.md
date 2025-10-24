# AWS GitHub Repository Classification System

Production-ready intelligent categorization system for GitHub repositories with crash recovery, resumability, and smart rate limit handling.

## 🎯 Overview

Automatically classifies repositories from any GitHub organization using a comprehensive 20-dimension framework including business classification, technical analysis, and solution marketing categories.

**Successfully tested with:**
- ✅ **awslabs**: 945 repositories (97.9% success rate)
- ✅ **aws-samples**: 7,552 repositories (ready for processing)
- ✅ **Any GitHub organization**: microsoft, google, hashicorp, etc.

## 🚀 Features

- **20-Dimension Classification**: Complete business-ready analysis framework
- **S3-Based Checkpointing**: Crash recovery and resumable processing
- **Smart Rate Limit Handling**: Automatic 1-hour waits with perfect resumption
- **README Fallback**: Extracts descriptions from README when GitHub description is missing
- **Robust Error Handling**: Handles None values and API failures gracefully
- **Public Results**: Accessible via S3 for analysis and sharing
- **Production Ready**: Processes 7,500+ repositories with batch processing
- **Generic Support**: Works with any GitHub organization

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
- **GitHub Token** (recommended for large organizations)

### Quick Start - Small Organizations (<1000 repos)

```bash
# Fetch repositories
python3 generic_fetch_repos.py hashicorp

# Run classification
python3 generic_classifier.py hashicorp --batch-size 10
```

### Large Organizations (1000+ repos) - Recommended

```bash
# For aws-samples (7,552 repos) - Smart rate limit handling
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5

# For microsoft, google, etc.
python3 smart_rate_limit_classifier.py microsoft --github-token YOUR_TOKEN --batch-size 5
```

### AWSlabs (Original - Complete Results Available)

```bash
# Already processed - view results
# CSV: https://aws-github-repo-classification.s3.amazonaws.com/results/classification_results.csv
# Progress: https://aws-github-repo-classification.s3.amazonaws.com/checkpoints/progress.json
```

## 🔑 GitHub Token Setup (Essential for Large Orgs)

**Why needed for 7,500+ repositories:**
- **Without token**: 60 requests/hour → 125+ hours (5+ days)
- **With token**: 5,000 requests/hour → 1.5 hours

**Setup:**
1. Go to https://github.com/settings/tokens
2. Generate new token (classic) with `public_repo` scope
3. Use in commands: `--github-token YOUR_TOKEN`

## 🔄 Resumability & Rate Limit Handling

### Perfect Resumption
```bash
# If process stops at repo 3,247 out of 7,552:
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN

# Output:
📊 Total repositories: 7552
🔄 Resuming from index: 3247
✅ Already completed: 3247
📦 Processing batch 650 (repos 3248-3252)
```

### Smart Rate Limit Handling
- **Automatic detection** of rate limit (403 errors)
- **Calculates exact wait time** until reset (usually ~1 hour)
- **Saves checkpoint** before waiting
- **Perfect resumption** after wait period
- **No duplicate processing**

### Processing New Repositories (Weekly Updates)

**❌ Current Limitation**: Rerunning the same command will NOT detect new repositories added by AWS.

**✅ Solution - Manual Refresh (Recommended)**:
```bash
# Step 1: Fetch updated repository list (includes new repos)
python3 generic_fetch_repos.py aws-samples

# Step 2: Run classification (processes only new repos)
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN
```

**Example Workflow**:
- **Week 1**: 7,552 repos → Process all (1.5 hours)
- **Week 2**: 7,600 repos (48 new) → Process only 48 new repos (2-3 minutes)
- **Week 3**: 7,650 repos (50 new) → Process only 50 new repos (2-3 minutes)

**✅ Alternative - Fresh Start**:
```bash
# Delete existing data and start fresh
aws s3 rm s3://aws-github-repo-classification-aws-samples/ --recursive
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN
```

**🔄 Smart Detection Logic**:
- ✅ Skips already processed repos (no duplicates)
- ✅ Processes only new repos added since last run
- ✅ Maintains all existing classifications
- ✅ Updates checkpoint with new total count

**💡 Best Practice**: Run `generic_fetch_repos.py {org}` weekly to capture new repositories, then run the classifier to process only new additions.

## 📈 Results & Performance

### AWSlabs (Completed)
- **Total Repositories**: 945
- **Successfully Classified**: 925 (97.9% success rate)
- **Processing Time**: ~6 minutes
- **Public Results**: https://aws-github-repo-classification.s3.amazonaws.com/

### AWS-Samples (Ready)
- **Total Repositories**: 7,552
- **Estimated Time**: 1.5 hours with GitHub token
- **Batch Processing**: 5 repositories per checkpoint
- **Smart Rate Limits**: Automatic 1-hour waits with resumption

### Generic Organizations
- **Automatic S3 bucket creation** with organization prefix
- **Same 20-dimension classification** framework
- **Configurable batch processing**
- **Public access** to all results

## 🔗 Public Access Examples

### AWSlabs (Original)
- **Bucket**: https://aws-github-repo-classification.s3.amazonaws.com/
- **CSV Results**: https://aws-github-repo-classification.s3.amazonaws.com/results/classification_results.csv

### AWS-Samples
- **Bucket**: https://aws-github-repo-classification-aws-samples.s3.amazonaws.com/
- **Progress**: https://aws-github-repo-classification-aws-samples.s3.amazonaws.com/checkpoints/progress.json

### Any Organization
- **Pattern**: https://aws-github-repo-classification-{org}.s3.amazonaws.com/

## 📁 File Structure & Usage Guide

### Core Files

| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **README.md** | Complete documentation | Reference guide | Read for instructions |
| **classification_results.csv** | AWSlabs results (925 repos) | Analysis & reference | Download/view in Excel |

### AWSlabs (Original) - Complete Results Available
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **s3_classifier.py** | Original awslabs classifier | AWSlabs only (already complete) | `python3 s3_classifier.py` |
| **fetch_repos.py** | Original awslabs fetcher | AWSlabs only (already complete) | `python3 fetch_repos.py` |

### Generic Classifiers - Any Organization

#### 1. Basic Generic (Small Organizations <1000 repos)
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **generic_fetch_repos.py** | Fetch repos from any org | First time setup | `python3 generic_fetch_repos.py {org}` |
| **generic_classifier.py** | Basic classification | Small orgs, no token needed | `python3 generic_classifier.py {org} --batch-size 10` |

#### 2. Enhanced Generic (Medium Organizations 1000-5000 repos)
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **enhanced_generic_classifier.py** | Enhanced error handling | Medium orgs, token recommended | `python3 enhanced_generic_classifier.py {org} --github-token TOKEN --batch-size 8` |

#### 3. Smart Rate Limit (Large Organizations 5000+ repos) - **Recommended**
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **smart_rate_limit_classifier.py** | Production-ready for large orgs | aws-samples, microsoft, google | `python3 smart_rate_limit_classifier.py {org} --github-token TOKEN --batch-size 5` |

### Usage Workflows

#### **New Organization Setup**
```bash
# Step 1: Fetch repositories
python3 generic_fetch_repos.py microsoft

# Step 2: Classify (choose based on org size)
# Small org (<1000 repos)
python3 generic_classifier.py microsoft --batch-size 10

# Large org (5000+ repos) - Recommended
python3 smart_rate_limit_classifier.py microsoft --github-token YOUR_TOKEN --batch-size 5
```

#### **Weekly Updates (Add New Repos)**
```bash
# Step 1: Fetch updated repository list
python3 generic_fetch_repos.py aws-samples

# Step 2: Process only new repos
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5
```

#### **Resume After Interruption**
```bash
# Same command automatically resumes from checkpoint
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5
```

## 📁 File Structure & Usage Guide

### Core Files

| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **README.md** | Complete documentation | Reference guide | Read for instructions |
| **classification_results.csv** | AWSlabs results (925 repos) | Analysis & reference | Download/view in Excel |

### AWSlabs (Original) - Complete Results Available
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **s3_classifier.py** | Original awslabs classifier | AWSlabs only (already complete) | `python3 s3_classifier.py` |
| **fetch_repos.py** | Original awslabs fetcher | AWSlabs only (already complete) | `python3 fetch_repos.py` |

### Generic Classifiers - Any Organization

#### 1. Basic Generic (Small Organizations <1000 repos)
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **generic_fetch_repos.py** | Fetch repos from any org | First time setup | `python3 generic_fetch_repos.py {org}` |
| **generic_classifier.py** | Basic classification | Small orgs, no token needed | `python3 generic_classifier.py {org} --batch-size 10` |

#### 2. Enhanced Generic (Medium Organizations 1000-5000 repos)
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **enhanced_generic_classifier.py** | Enhanced error handling | Medium orgs, token recommended | `python3 enhanced_generic_classifier.py {org} --github-token TOKEN --batch-size 8` |

#### 3. Smart Rate Limit (Large Organizations 5000+ repos) - **Recommended**
| File | Purpose | When to Use | How to Run |
|------|---------|-------------|------------|
| **smart_rate_limit_classifier.py** | Production-ready for large orgs | aws-samples, microsoft, google | `python3 smart_rate_limit_classifier.py {org} --github-token TOKEN --batch-size 5` |

### Usage Workflows

#### **New Organization Setup**
```bash
# Step 1: Fetch repositories
python3 generic_fetch_repos.py microsoft

# Step 2: Classify (choose based on org size)
# Small org (<1000 repos)
python3 generic_classifier.py microsoft --batch-size 10

# Large org (5000+ repos) - Recommended
python3 smart_rate_limit_classifier.py microsoft --github-token YOUR_TOKEN --batch-size 5
```

#### **Weekly Updates (Add New Repos)**
```bash
# Step 1: Fetch updated repository list
python3 generic_fetch_repos.py aws-samples

# Step 2: Process only new repos
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5
```

#### **Resume After Interruption**
```bash
# Same command automatically resumes from checkpoint
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5
```

### File Selection Guide

**Choose classifier based on organization size:**

| Organization Size | Recommended File | GitHub Token | Batch Size | Processing Time |
|------------------|------------------|--------------|------------|-----------------|
| <1,000 repos | `generic_classifier.py` | Optional | 10 | Minutes |
| 1,000-5,000 repos | `enhanced_generic_classifier.py` | Recommended | 8 | 30-60 minutes |
| 5,000+ repos | `smart_rate_limit_classifier.py` | **Required** | 5 | 1-2 hours |

**Examples:**
- **HashiCorp** (~500 repos): Use `generic_classifier.py`
- **Microsoft** (~3,000 repos): Use `enhanced_generic_classifier.py`
- **AWS-Samples** (~7,500 repos): Use `smart_rate_limit_classifier.py`

## 📋 Sample Commands

```bash
# Small organization (no token needed)
python3 generic_classifier.py hashicorp --batch-size 10

# Medium organization (token recommended)
python3 enhanced_generic_classifier.py microsoft --github-token YOUR_TOKEN --batch-size 8

# Large organization (token required, smart rate limits)
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5

# Resume after interruption (same command)
python3 smart_rate_limit_classifier.py aws-samples --github-token YOUR_TOKEN --batch-size 5
```

## 📊 Sample Output

Each repository gets classified with:
```csv
repository,solution_type,competency,customer_problems,solution_marketing,primary_language,aws_services,cost_range,setup_time,usp,freshness_status,...
aws-samples/serverless-patterns,Foundation Builders,DevOps,Development Efficiency,starter,TypeScript,"Lambda,API Gateway,DynamoDB",Medium ($1K-10K),Half-day Setup,Popular community solution (2000+ stars),Recently Updated
```

## 🛡️ Error Recovery Features

- **Rate Limit**: Automatic 1-hour waits with exact reset time calculation
- **Network Issues**: Retry logic with exponential backoff
- **S3 Failures**: Checkpoint save retries
- **Process Crash**: Resumes from exact last position
- **Failed Repos**: Tracked separately, skipped on resume
- **Progress Monitoring**: Real-time progress with milestone celebrations

## 🔧 Troubleshooting

### CSV Generation Issue Fix

If your CSV contains identical values for all repositories (hardcoded defaults), run the fix script:

```bash
# After classification is complete, generate real results
python3 fix_smart_classifier.py
```

**Issue**: The smart classifier processes repositories but doesn't save actual classification results - only tracks completion status.

**Solution**: The fix script re-runs classification logic on completed repositories (no API calls) and generates proper CSV with real analysis results.

**When to use**: After `smart_rate_limit_classifier.py` completes but CSV shows identical values for all rows.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Test with sample repositories
4. Submit pull request

## 📄 License

MIT License - See LICENSE file for details

---

**Built for AWS Solutions Architects and DevOps teams to quickly identify and categorize open-source solutions from any GitHub organization with production-ready reliability.**
