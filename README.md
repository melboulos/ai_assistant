# ai_assistant
The service receives sales lead updates from Couchbase Eventing, generates executive summaries and actionable recommendations using Bedrock LLMs, and writes them back to Couchbase while preserving historical data.

# AI Summary Service
AI Sales Summary Service is a Flask-based service that generates executive summaries and actionable recommendations for sales leads. It integrates with Couchbase and AWS Bedrock to enrich sales lead documents and preserve historical changes.

An enterprise sales lead **summary and recommendation generator** using **Flask**, **AWS Bedrock**, and **Couchbase Eventing**.  

The service receives sales lead updates from Couchbase Eventing, generates executive summaries and actionable recommendations using Bedrock LLMs, and writes them back to Couchbase while preserving historical data.

---

## 🌟 Features

- Generates 2–3 sentence **executive summaries** for sales leads
- Creates actionable **recommendations** with 4–5 next steps
- Preserves `old_data` to avoid overwriting historical information
- Formats all USD amounts (e.g., `$1,234,567`)
- Prevents infinite Couchbase Eventing loops with `_enriched` flag
- Logs both Flask and Eventing activity for traceability

---

## 🧰 Dependencies
- Python 3.13+
- Flask
- Couchbase Python SDK
- Boto3 (AWS SDK for Python)
- re (regular expressions)
- json
- traceback

### Python Packages

python3 -m venv venv
source venv/bin/activate
pip install flask couchbase boto3

**Setup**

Couchbase Configuration:
**Bucket:** sales_lead
**Scope:** _default
**Collection**: _default
Ensure proper authentication (Administrator / password).
AWS Bedrock Configuration:
**Region:** us-east-1
**Model:** meta.llama3-70b-instruct-v1:0
**Run the Flask App:**
python3 app.py



