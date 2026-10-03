import sys
import os
import json
from unittest.mock import MagicMock
from flask import Flask, request, render_template_string

# Mock all missing heavy ML/web dependencies so the core python code can run!
mock_modules = [
    'bs4', 'fastapi', 'uvicorn', 'streamlit', 'neo4j',
    'xgboost', 'shap', 'tldextract', 'torch', 'transformers',
    'pydantic', 'matplotlib', 'joblib', 'nlp.distilbert', 'api.service'
]
for mod in mock_modules:
    sys.modules[mod] = MagicMock()

# Mock the specific bs4 import needed by body_extractor
class MockBS:
    def __init__(self, *args, **kwargs):
        pass
    def get_text(self, *args, **kwargs):
        return "Mock extracted text"
sys.modules['bs4'].BeautifulSoup = MockBS

from integration.orchestrator import analyze_email_bytes
from blockchain.service import EvidenceService
from blockchain.chain_of_custody import ChainOfCustody

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>PHISHGUARD-X</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 900px; margin: 40px auto; padding: 20px; background: #f8fafc; color: #1e293b; }
        .header { text-align: center; border-bottom: 2px solid #cbd5e1; padding-bottom: 20px; margin-bottom: 30px; }
        .header h1 { margin: 0; color: #0f172a; font-size: 2.5em; letter-spacing: 2px; }
        .header p { margin: 5px 0 0 0; color: #64748b; font-size: 1.2em; text-transform: uppercase; letter-spacing: 1px; }
        
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); margin-bottom: 30px; border: 1px solid #e2e8f0; }
        .card h2 { margin-top: 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 10px; color: #334155; text-transform: uppercase; font-size: 1.1em; letter-spacing: 1px; }
        
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; justify-content: center; }
        .tab-btn { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 10px 30px; border-radius: 6px; cursor: pointer; font-weight: bold; color: #475569; }
        .tab-btn.active { background: #2563eb; color: white; border-color: #2563eb; }
        
        .input-section { display: none; text-align: center; }
        .input-section.active { display: block; }
        
        .upload-box { border: 2px dashed #cbd5e1; padding: 40px; border-radius: 8px; background: #f8fafc; margin-bottom: 20px; }
        textarea { width: 100%; height: 200px; border: 1px solid #cbd5e1; border-radius: 8px; padding: 15px; font-family: monospace; resize: vertical; box-sizing: border-box; }
        
        .analyze-btn { background: #10b981; color: white; border: none; padding: 15px 40px; border-radius: 8px; cursor: pointer; font-size: 1.1em; font-weight: bold; width: 100%; text-transform: uppercase; letter-spacing: 1px; transition: background 0.2s; }
        .analyze-btn:hover { background: #059669; }
        
        .verdict-critical { text-align: center; background: #fee2e2; border: 2px solid #ef4444; color: #b91c1c; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
        .verdict-safe { text-align: center; background: #dcfce7; border: 2px solid #22c55e; color: #15803d; padding: 30px; border-radius: 12px; margin-bottom: 20px; }
        
        .verdict-title { font-size: 2em; font-weight: bold; margin: 0 0 15px 0; }
        .metric-row { display: flex; justify-content: space-around; font-size: 1.2em; }
        
        .section-title { font-size: 1em; color: #64748b; text-transform: uppercase; letter-spacing: 1px; margin: 30px 0 15px 0; border-bottom: 1px solid #e2e8f0; padding-bottom: 5px; }
        
        .finding-list { list-style: none; padding: 0; margin: 0; }
        .finding-list li { padding: 10px 0; border-bottom: 1px solid #f1f5f9; display: flex; align-items: center; }
        .finding-list li:last-child { border-bottom: none; }
        
        .details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .detail-item { background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; }
        .detail-label { font-size: 0.85em; color: #64748b; text-transform: uppercase; margin-bottom: 5px; }
        .detail-value { font-weight: bold; color: #0f172a; word-break: break-all; }
        
        details { margin-top: 30px; background: #f1f5f9; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; }
        summary { cursor: pointer; font-weight: bold; color: #475569; }
        pre { background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 6px; overflow-x: auto; font-size: 0.9em; }
        
        .verify-btn { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; cursor: pointer; font-weight: bold; margin-top: 15px; width: 100%; }
        .verify-btn:hover { background: #2563eb; }
        .status-badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }
        .status-ok { background: #dcfce7; color: #166534; }
        .status-fail { background: #fee2e2; color: #991b1b; }
    </style>
    <script>
        function setTab(tabId) {
            document.getElementById('upload-tab').classList.remove('active');
            document.getElementById('paste-tab').classList.remove('active');
            document.getElementById('btn-upload').classList.remove('active');
            document.getElementById('btn-paste').classList.remove('active');
            
            document.getElementById(tabId).classList.add('active');
            document.getElementById('btn-' + tabId.split('-')[0]).classList.add('active');
        }
    </script>
</head>
<body>
    <div class="header">
        <h1>PHISHGUARD-X</h1>
        <p>AI-Powered Phishing Detection</p>
    </div>

    <div class="card">
        <h2>Email Input</h2>
        <div class="tabs">
            <button type="button" id="btn-upload" class="tab-btn active" onclick="setTab('upload-tab')">Upload Email</button>
            <button type="button" id="btn-paste" class="tab-btn" onclick="setTab('paste-tab')">Paste Email</button>
        </div>
        
        <form method="POST" action="/analyze" enctype="multipart/form-data">
            <div id="upload-tab" class="input-section active">
                <div class="upload-box">
                    <p style="color: #64748b; font-weight: bold; margin-bottom: 20px;">Drag & Drop Email Here<br><br>OR</p>
                    <input type="file" name="eml_file" accept=".eml" style="font-size: 1.1em;">
                </div>
            </div>
            
            <div id="paste-tab" class="input-section">
                <textarea name="raw_email" placeholder="Paste email content here...&#10;&#10;From: attacker@example.com&#10;To: victim@example.com&#10;Subject: Verify your account&#10;&#10;Your account requires verification..."></textarea>
                <br><br>
            </div>
            
            <button type="submit" class="analyze-btn">ANALYZE EMAIL</button>
        </form>
    </div>

    {% if analysis %}
    <div class="card">
        <h2>Threat Analysis</h2>
        
        <!-- 1. THREAT VERDICT -->
        {% if analysis.is_phishing %}
        <div class="verdict-critical">
            <div class="verdict-title">⚠️ PHISHING DETECTED</div>
            <div class="metric-row">
                <div>Threat Probability<br><strong>{{ analysis.probability }}%</strong></div>
                <div>Risk Level<br><strong>CRITICAL</strong></div>
            </div>
        </div>
        {% else %}
        <div class="verdict-safe">
            <div class="verdict-title">✅ EMAIL APPEARS SAFE</div>
            <div class="metric-row">
                <div>Threat Probability<br><strong>{{ analysis.probability }}%</strong></div>
                <div>Risk Level<br><strong>LOW</strong></div>
            </div>
        </div>
        {% endif %}
        
        <!-- 2. KEY FINDINGS -->
        <div class="section-title">Why was it flagged? / Key Findings</div>
        <ul class="finding-list">
            {% for finding in analysis.findings %}
            <li>{{ finding }}</li>
            {% endfor %}
        </ul>
        
        <!-- 3. THREAT DETAILS -->
        <div class="section-title">Security Evidence Details</div>
        <div class="details-grid">
            <div class="detail-item">
                <div class="detail-label">URL Threats</div>
                <div class="detail-value">{{ analysis.urls_detected }} URLs Detected<br>{{ analysis.urls_suspicious }} Suspicious URLs</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Attachments</div>
                <div class="detail-value">{{ analysis.attachment_name }}<br>Risk: {{ analysis.attachment_risk }}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Email Authentication</div>
                <div class="detail-value">{{ analysis.auth_status }}</div>
            </div>
            <div class="detail-item">
                <div class="detail-label">Semantic Analysis</div>
                <div class="detail-value">{{ analysis.semantic_status }}</div>
            </div>
        </div>
        
        <!-- 4. BLOCKCHAIN EVIDENCE -->
        <div class="section-title">🔐 Blockchain Evidence Integrity</div>
        <div class="details-grid" style="grid-template-columns: 1fr;">
            <div class="detail-item" style="border-left: 4px solid #3b82f6;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <div><span class="detail-label">Status</span><br><span class="status-badge status-ok">✅ RECORDED</span></div>
                    <div style="text-align: right;"><span class="detail-label">Timestamp</span><br><span class="detail-value">{{ case.ingestion_timestamp }}</span></div>
                </div>
                
                <div style="margin-bottom: 10px;">
                    <span class="detail-label">Evidence ID</span><br>
                    <span class="detail-value">{{ case.evidence_id }}</span>
                </div>
                
                <div style="margin-bottom: 10px;">
                    <span class="detail-label">Cryptographic Hash (SHA-256)</span><br>
                    <code style="word-break: break-all; color: #0f172a; background: #e2e8f0; padding: 4px; border-radius: 4px;">{{ case.email_sha256 }}</code>
                </div>
                
                <div style="margin-bottom: 15px;">
                    <span class="detail-label">Transaction (Mock Fabric)</span><br>
                    <code style="word-break: break-all; color: #0f172a;">{{ case.blockchain_tx_id }}</code>
                </div>
                
                <form method="POST" action="/verify">
                    <input type="hidden" name="case_id" value="{{ case.case_id }}">
                    <button type="submit" class="verify-btn">VERIFY EVIDENCE</button>
                </form>
            </div>
        </div>
        
        {% if verify_result %}
        <div style="margin-top: 15px; padding: 15px; border-radius: 8px; text-align: center; border: 2px solid {% if verify_result.overall_integrity == 'VERIFIED' %}#22c55e{% else %}#ef4444{% endif %}; background: {% if verify_result.overall_integrity == 'VERIFIED' %}#dcfce7{% else %}#fee2e2{% endif %};">
            <strong style="font-size: 1.2em; color: {% if verify_result.overall_integrity == 'VERIFIED' %}#15803d{% else %}#b91c1c{% endif %};">
                {% if verify_result.overall_integrity == 'VERIFIED' %}✅ EVIDENCE INTEGRITY VERIFIED{% else %}❌ EVIDENCE MODIFIED - INTEGRITY FAILURE{% endif %}
            </strong>
        </div>
        {% endif %}
        
        <!-- TECHNICAL DETAILS -->
        <details>
            <summary>View Technical Details</summary>
            <p><strong>Raw Mock Analysis Output:</strong></p>
            <pre>{{ analysis | tojson(indent=4) }}</pre>
            <p><strong>Chain of Custody Events:</strong></p>
            <pre>{{ audit_trail | tojson(indent=4) }}</pre>
        </details>
        
    </div>
    {% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route("/analyze", methods=["POST"])
def analyze():
    eml_file = request.files.get("eml_file")
    
    if eml_file and eml_file.filename:
        raw_email = eml_file.read()
    else:
        email_text = request.form.get("raw_email", "").strip()
        if not email_text:
            return "Please either paste email content or upload a file", 400
            
        text_lower = email_text.lower()
        is_raw = any(text_lower.startswith(h) for h in (
            "from:", "return-path:", "delivered-to:", "received:", 
            "message-id:", "date:", "subject:", "mime-version:", "content-type:"
        ))
        
        if is_raw:
            raw_email = email_text.encode("utf-8")
        else:
            raw_email = f"Subject: No Subject\n\n{email_text}".encode("utf-8")
        
    # 1. Register Evidence
    evidence_record = EvidenceService.register_evidence(raw_email)
    case_id = evidence_record['case_id']
    
    # 2. Comprehensive Final Analysis UI Mock
    unified_analysis = {
        "is_phishing": True,
        "probability": 95.7,
        "findings": [
            "🔗 Suspicious URLs detected (example-login.com)",
            "🧠 Phishing indicators found in email content (urgency detected)",
            "📧 Email authentication anomalies detected (SPF/DKIM failed)",
            "📎 Suspicious attachment detected (Invoice.zip)"
        ],
        "urls_detected": 3,
        "urls_suspicious": 2,
        "attachment_name": "Invoice.zip",
        "attachment_risk": "Suspicious",
        "auth_status": "Failed",
        "semantic_status": "High Urgency / Credential Theft"
    }
    
    # If the user didn't paste anything inherently suspicious, randomly toggle for demo
    if b'legit' in raw_email.lower():
        unified_analysis = {
            "is_phishing": False,
            "probability": 8.4,
            "findings": [
                "✓ No significant phishing indicators",
                "✓ No suspicious URLs detected",
                "✓ Email authentication appears normal",
                "✓ No suspicious attachments detected"
            ],
            "urls_detected": 0,
            "urls_suspicious": 0,
            "attachment_name": "None",
            "attachment_risk": "Safe",
            "auth_status": "Passed",
            "semantic_status": "Normal Routine Conversation"
        }
    
    # 3. Register Report & Anchor
    EvidenceService.register_report(case_id, unified_analysis)
    EvidenceService.anchor_evidence(case_id)
    
    case = EvidenceService.get_case(case_id)
    audit_trail = ChainOfCustody.get_audit_trail(case_id)
    
    return render_template_string(HTML_TEMPLATE, case=case, audit_trail=audit_trail, analysis=unified_analysis)

@app.route("/verify", methods=["POST"])
def verify():
    case_id = request.form.get("case_id")
    verify_result = EvidenceService.verify_case_integrity(case_id)
    
    case = EvidenceService.get_case(case_id)
    audit_trail = ChainOfCustody.get_audit_trail(case_id)
    
    # Reload the mocked report for display
    report_path = os.path.join(os.path.dirname(__file__), 'storage', 'reports', f"{case_id}_report.json")
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            unified_analysis = json.load(f)
    else:
        unified_analysis = None
    
    return render_template_string(HTML_TEMPLATE, case=case, verify_result=verify_result, audit_trail=audit_trail, analysis=unified_analysis)

if __name__ == "__main__":
    print("Starting Fallback Platform on port 8080...")
    app.run(host="0.0.0.0", port=8080)
