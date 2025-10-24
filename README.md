# AWS GitHub Repository Classification System

S3-based intelligent categorization system for AWS official repositories with crash recovery and resumability.

## Features

- **19-Dimension Classification**: Complete business-ready classification framework
- **S3-Based Checkpointing**: Crash recovery and resumable processing
- **Pre-deployment Focus**: Customer problems represent pain points before solution deployment
- **Production Ready**: Handles 939+ awslabs repositories with batch processing

## Architecture

```
s3://aws-github-repo-classification/
├── master-index/awslabs_repos_939.json    # All repositories to process
├── checkpoints/progress.json              # Current position & completed repos  
└── results/classification_results.csv     # Final classification output
```

## Usage

```bash
python3 s3_classifier.py
```

## Classification Dimensions

1. **Business Classification**: Solution types, competencies, customer problems
2. **Technical Stack**: Languages, frameworks, AWS services
3. **Deployment**: Tools, readiness level, setup time
4. **Business Value**: Cost range, USP, freshness status
5. **AI/GenAI**: Agentic capabilities detection

## Resumability

System automatically resumes from last checkpoint if interrupted:
- Tracks completed repositories
- Skips already processed items
- Saves progress after each batch
- No duplicate processing

## Public Access

- **Bucket**: https://aws-github-repo-classification.s3.amazonaws.com/
- **Checkpoints**: Publicly accessible for monitoring progress
- **Results**: Internet accessible classification data
