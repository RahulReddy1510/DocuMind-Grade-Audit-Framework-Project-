from typing import List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.reporting.risk_engine import RiskEngine
from src.reporting.redliner import AutoRedliner

class SummarizerAgent:
    """
    Aggregates findings, calculates risk, generates redlines, 
    and produces a final Markdown report.
    """
    def __init__(self):
        self.risk_engine = RiskEngine()
        self.redliner = AutoRedliner()
        # Using GPT-4o as a proxy for JAIS if JAIS API acts as OpenAI-compatible
        # or separate logic would be needed.
        self.llm = ChatOpenAI(model="gpt-4o", temperature=0)

    def generate_report(self, contract_name: str, findings: List[Dict[str, Any]]) -> str:
        """
        Main entry point to generate the full audit report.
        """
        # 1. Analytics
        risk_data = self.risk_engine.calculate_risk(findings)
        
        # 2. Enrich Findings with Redlines
        enriched_findings = []
        for f in findings:
            if f['status'] == 'VIOLATION':
                f['suggested_fix'] = self.redliner.generate_fix(f)
            enriched_findings.append(f)
            
        # 3. Generate Narrative Sections
        english_summary = self._generate_summary(contract_name, risk_data, enriched_findings, "English")
        arabic_summary = self._generate_summary(contract_name, risk_data, enriched_findings, "Arabic")
        
        # 4. Assemble Markdown
        report = f"""# DocuMind Compliance Report: {contract_name}

## 📊 Executive Summary
**Overall Risk Score**: {risk_data['risk_score']}/100 ({risk_data['risk_level']})

| Severity | Count |
| :--- | :--- |
| 🔴 Critical | {risk_data['violation_breakdown']['CRITICAL']} |
| 🟠 High | {risk_data['violation_breakdown']['HIGH']} |
| 🟡 Medium | {risk_data['violation_breakdown']['MEDIUM']} |
| 🟢 Low | {risk_data['violation_breakdown']['LOW']} |

---

## 📝 English Audit Summary
{english_summary}

---

## 🇦🇪 Arabic Audit Summary (ملخص التدقيق)
{arabic_summary}

---

## 🔍 Detailed Findings & Redlines

"""
        for f in enriched_findings:
            if f['status'] == 'COMPLIANT':
                continue
                
            icon = "🔴" if f['status'] == 'VIOLATION' else "⚠️"
            report += f"### {icon} Clause {f['clause_id']}\n"
            report += f"**Status**: {f['status']}\n\n"
            report += f"**Finding**: {f['reasoning']}\n\n"
            report += f"**Law**: {f['law_reference']}\n\n"
            if f.get('suggested_fix'):
                 report += f"> **Suggested Fix**: *{f['suggested_fix']}*\n\n"
            report += "---\n"
            
        return report

    def _generate_summary(self, name: str, risk: Dict, findings: List[Dict], language: str) -> str:
        """Helper to generate a narrative summary in a specific language."""
        
        prompt = f"""
        You are an Executive Legal Assistant. Write a concise executive summary for the contract "{name}" in {language}.
        
        Context:
        - Risk Level: {risk['risk_level']} (Score: {risk['risk_score']}).
        - Critical Violations: {risk['violation_breakdown']['CRITICAL']}
        
        Highlight the most critical issues found in the 'findings' list below.
        Keep it professional and suitable for C-Level executives.
        
        Findings Sample:
        {str([f for f in findings if f['status'] == 'VIOLATION'][:3])}
        """
        
        return self.llm.invoke(prompt).content
