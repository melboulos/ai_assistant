#!/usr/bin/env python3
from flask import Flask, request, jsonify
import json
import re
import traceback
from couchbase.cluster import Cluster
from couchbase.auth import PasswordAuthenticator
from couchbase.options import ClusterOptions
import boto3

app = Flask(__name__)

# ------------------------------
# Couchbase setup
# ------------------------------
cluster = Cluster(
    "couchbase://localhost",
    ClusterOptions(PasswordAuthenticator("Administrator", "password"))
)
bucket = cluster.bucket("sales_lead")
collection = bucket.scope("_default").collection("_default")

# ------------------------------
# Bedrock setup
# ------------------------------
bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

# ------------------------------
# Utility functions
# ------------------------------
def format_usd(amount):
    try:
        return f"${amount:,.0f}"
    except Exception:
        return str(amount)

def clean_text(text):
    if not text:
        return ""
    text = text.strip()
    text = re.sub(r'^\*+', '', text)
    text = re.sub(r'\*+$', '', text)
    text = re.sub(r'\n\s*\n', '\n\n', text)
    return text

def bullet_recommendation(text):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return "\n".join([f"• {s.strip()}" for s in sentences if s.strip()])

def format_old_data(old_data):
    """Create human-readable string describing changes."""
    changes = []
    for field, change in old_data.items():
        old_value = change.get("old_value", "N/A")
        audit_date = change.get("audit_date", "")
        changes.append(f"- {field}: was '{old_value}' (as of {audit_date})")
    return "\n".join(changes)

# ------------------------------
# Health check
# ------------------------------
@app.route('/health', methods=['GET'])
def health():
    return "OK", 200

# ------------------------------
# Generate summary for a single lead
# ------------------------------
@app.route('/generate_summary', methods=['POST'])
def generate_summary():
    try:
        data = request.get_json(force=True)
        print("📥 Raw incoming request data:", data)

        lead_id = data.get('lead_id')
        sales_lead = data.get('sales_lead')
        old_data = data.get('old_data', {})

        if not lead_id or not sales_lead:
            return jsonify({"error": "Missing lead_id or sales_lead"}), 400

        # Normalize key to avoid double 'lead::'
        doc_key = lead_id
        if doc_key.startswith("lead::lead::"):
            doc_key = doc_key.replace("lead::lead::", "lead::", 1)

        # Format USD fields
        market_cap = format_usd(sales_lead.get('market_cap_usd', 0))
        annual_sales = format_usd(sales_lead.get('annual_sales_usd', 0))
        last_deal = format_usd(sales_lead.get('last_deal_size_usd', 0))

        # Include old_data changes in prompt
        old_changes_text = format_old_data(old_data)

        # Build prompt for Bedrock
        prompt = f"""
You are an expert enterprise sales strategist.
Format all currency values as USD amounts with dollar signs and commas, e.g., $1,234,567.

Given the following sales lead data, generate:

1. A 2–3 sentence executive summary highlighting changes since the previous record.
2. A single-paragraph recommendation with 4–5 specific, actionable next steps.

Previous changes:
{old_changes_text if old_changes_text else "No prior changes recorded."}

Current Lead Data:
Company Name: {sales_lead.get('company_name', 'N/A')}
Market Region: {sales_lead.get('primary_market_region', 'N/A')}
Market Cap: {market_cap}
Annual Sales: {annual_sales}
Lead Status: {sales_lead.get('lead_status', 'N/A')}
Pipeline Stage: {sales_lead.get('pipeline_stage', 'N/A')}
Last Deal Size: {last_deal}
Sales Contact: {sales_lead.get('sales_contact_name', 'N/A')}
Notes: {sales_lead.get('notes', '')}
High Priority Lead: {"Yes" if sales_lead.get('high_priority_flag', False) else "No"}

Begin your response:
"""

        # Call Bedrock model
        response = bedrock.invoke_model(
            modelId="meta.llama3-70b-instruct-v1:0",
            contentType="application/json",
            accept="application/json",
            body=json.dumps({"prompt": prompt, "temperature": 0.7})
        )

        response_body = json.loads(response['body'].read())
        generated_text = response_body.get("generation", "").strip()

        # ------------------------------
        # Parse summary and recommendation
        # ------------------------------
        summary = generated_text
        recommendation = ""

        # Extract recommendation from summary if embedded
        rec_match = re.search(r'Recommendations?:\s*(.*)', summary, re.DOTALL | re.IGNORECASE)
        if rec_match:
            recommendation = clean_text(rec_match.group(1))
            # Remove recommendation part from summary
            summary = re.sub(r'Recommendations?:.*', '', summary, flags=re.DOTALL | re.IGNORECASE).strip()

        # Cleanup summary
        summary = clean_text(summary)

        # Format recommendation into bullets
        recommendation = bullet_recommendation(recommendation)

        # High-priority flag
        if sales_lead.get('high_priority_flag', False):
            recommendation = "⚠️ High-priority lead!\n" + recommendation

        # ------------------------------
        # Merge with existing document in Couchbase
        # ------------------------------
        try:
            existing_doc = {}
            try:
                existing_doc = collection.get(doc_key).content_as[dict]
            except Exception:
                pass  # doc might not exist yet

            merged_doc = {
                **existing_doc,  # keeps old_data and other fields
                "sales_lead": sales_lead,
                "summary": summary,
                "recommendation": recommendation,
                "_enriched": True
            }

            collection.upsert(doc_key, merged_doc)
            print(f"✅ Upserted document {doc_key} with summary and recommendation")

        except Exception as e:
            print(f"❌ Couchbase upsert error for {doc_key}: {e}")

        return jsonify({
            "lead_id": doc_key,
            "summary": summary,
            "recommendation": recommendation
        })

    except Exception as e:
        print("❌ Error in /generate_summary:", str(e))
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ------------------------------
# Main
# ------------------------------
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)

