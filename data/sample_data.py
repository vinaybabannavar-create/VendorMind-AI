"""
data/sample_data.py

Rich Preset RFPs and B2B Vendor Submissions for VendorMind AI.
Provides ready-to-use procurement scenarios for live hackathon demos.
"""

PRESET_RFPS = {
    "enterprise_cloud": {
        "title": "☁️ Enterprise Cloud Infrastructure & Monitoring RFP",
        "description": "High-availability multi-cloud infrastructure monitoring, K8s cluster tracking, and 24/7 incident response.",
        "rfp_text": """
We are seeking an enterprise-grade vendor to provide cloud infrastructure monitoring, Kubernetes cluster observability, and automated incident response for our production environment (500+ microservices).

Mandatory Requirements:
1. ISO 27001 and SOC 2 Type II certifications are mandatory.
2. 24/7 alerting with sub-minute latency and Slack/PagerDuty integration.
3. Native Kubernetes cluster integration with support for 2,000+ monitored endpoints.
4. Onboarding and full deployment must complete within 30 days.
5. Budget cap: $60,000 / year.

Preferred Qualifications:
- At least 4 years of proven track record serving Fortune 500 / FinTech enterprise clients.
- Automated anomaly detection powered by ML.
- Zero vendor lock-in with open-telemetry export support.
"""
    },
    "cybersecurity_audit": {
        "title": "🛡️ Enterprise SOC 2 & Pen-Testing Security RFP",
        "description": "Third-party penetration testing, vulnerability assessment, and continuous compliance audit for SaaS.",
        "rfp_text": """
We require a premier cybersecurity vendor to perform comprehensive annual penetration testing, continuous vulnerability management, and SOC 2 readiness auditing.

Mandatory Requirements:
1. Certified Ethical Hackers (CEH) and CISSP certified lead auditors.
2. Full compliance with CREST, ISO 27001, and HIPAA data protection guidelines.
3. Remediation re-testing included within contract scope at no extra charge.
4. Final audit report and executive presentation delivered within 21 days.
5. Pricing ceiling: $40,000 total engagement.

Preferred Qualifications:
- Automated daily web application vulnerability scanning dashboard.
- Past experience auditing healthcare and financial SaaS platforms.
"""
    },
    "supply_chain_saas": {
        "title": "📦 Logistics & Supply Chain Predictive Analytics RFP",
        "description": "Real-time fleet tracking, inventory optimization, and AI predictive delay forecasting.",
        "rfp_text": """
We are procuring a B2B SaaS platform for supply chain intelligence, real-time shipment tracking, and predictive inventory forecasting.

Mandatory Requirements:
1. REST API and Webhook integration with SAP ERP and Salesforce.
2. Real-time GPS tracking latency under 5 seconds for global freight carriers.
3. SOC 2 Type II certified data security with AES-256 encryption.
4. SLA guarantee of 99.9% platform uptime with financial penalty clauses.
5. Onboarding timeline under 45 days.

Preferred Qualifications:
- Custom machine learning models for route optimization.
- Support for multi-currency and international customs documentation.
"""
    }
}

SAMPLE_VENDORS = [
    {
        "vendor_id": "vendor_1",
        "vendor_name": "SentinelOps Enterprise",
        "raw_text": """
SentinelOps Enterprise provides full-stack cloud infrastructure monitoring at $52,000/year.
We are fully ISO 27001 and SOC 2 Type II compliant with annual independent audits.
Our platform offers sub-second 24/7 alerting, native Kubernetes cluster auto-discovery, and supports 5,000+ endpoints.
Onboarding is completed within 14 business days by a dedicated solutions architect.
We have 6+ years of track record serving tier-1 FinTech and Healthcare clients.
Included: OpenTelemetry support, automated ML anomaly detection, and PagerDuty/Slack integrations.
"""
    },
    {
        "vendor_id": "vendor_2",
        "vendor_name": "CloudWatch Pro",
        "raw_text": """
CloudWatch Pro delivers scalable enterprise monitoring at $45,000/year.
We hold ISO 27001 and SOC 2 Type II certifications.
Features: 24/7 alerting, Kubernetes metrics integration, Slack/PagerDuty routing, and support for up to 2,500 endpoints.
Onboarding timeline is 21 days. We have 5 years of industry experience across enterprise SaaS accounts.
Full OpenTelemetry export capability is supported out of the box.
"""
    },
    {
        "vendor_id": "vendor_3",
        "vendor_name": "MonitorNow (Budget Tier)",
        "raw_text": """
MonitorNow provides basic infrastructure monitoring at an ultra-low rate of $18,000/year.
We currently hold SOC 2 Type I certification (ISO 27001 and SOC 2 Type II are in progress).
Onboarding takes 45 days. Kubernetes integration is currently in beta. Supports up to 400 endpoints.
Founded 9 months ago as an early-stage startup. Note: 24/7 phone support requires an add-on tier.
"""
    },
    {
        "vendor_id": "vendor_4",
        "vendor_name": "Apex CyberGuard",
        "raw_text": """
Apex CyberGuard specializes in enterprise security assessments at $38,000/engagement.
Our lead auditors hold CISSP, CEH, and CISA certifications. Fully CREST and ISO 27001 accredited.
Deliverables: Complete pen-test report, daily automated vulnerability dashboard, and free re-testing within 60 days.
Report delivery within 18 calendar days. Over 7 years experience auditing global SaaS and FinTech companies.
"""
    },
    {
        "vendor_id": "vendor_5",
        "vendor_name": "LogiChain Intelligence",
        "raw_text": """
LogiChain Intelligence offers predictive supply chain analytics for $55,000/year.
Includes SAP ERP and Salesforce pre-built connectors. Real-time GPS tracking with 3-second update frequency.
SOC 2 Type II certified with 99.95% uptime SLA backed by credit guarantees.
Onboarding completed in 30 days. Custom ML route optimization engine included. 4 years in market.
"""
    }
]

# Legacy fallbacks for backward compatibility
SAMPLE_RFP = PRESET_RFPS["enterprise_cloud"]["rfp_text"]

if __name__ == "__main__":
    import json
    print("Preset RFPs:", list(PRESET_RFPS.keys()))
    print("Sample Vendors Count:", len(SAMPLE_VENDORS))
