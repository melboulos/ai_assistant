# ai_assistant
The service receives sales lead updates from Couchbase Eventing, generates executive summaries and actionable recommendations using Bedrock LLMs, and writes them back to Couchbase while preserving historical data.

# AI Summary Service

[![Python](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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

### Python Packages

```bash
flask>=3.0
boto3>=2.0
couchbase>=4.1

