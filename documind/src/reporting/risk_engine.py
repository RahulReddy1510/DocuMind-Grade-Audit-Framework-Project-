from typing import List, Dict, Any

class RiskEngine:
    """
    Calculates a qualitative Risk Score for the contract based on verified violations.
    """
    def __init__(self):
        # Weighting for different types of violations (could be dynamic or fine-tuned)
        self.severity_map = {
            "CRITICAL": 25,  # Termination, Liability, Indemnity
            "HIGH": 15,      # Payment terms, Confidentiality
            "MEDIUM": 10,    # Notice periods
            "LOW": 2         # Formatting, Typos
        }

    def calculate_risk(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes findings to produce a risk profile.
        
        Args:
            findings: List of verified critic outputs.
            
        Returns:
            Dict containing 'score' (0-100) and 'risk_level'.
        """
        total_risk_points = 0
        breakdown = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

        for finding in findings:
            if finding.get("status") != "VIOLATION":
                continue
                
            # Heuristic to determine severity if not provided by Critic
            # In a real system, the Critic should output severity. 
            # Here we infer from keywords in 'law_reference' or 'reasoning'
            severity = self._infer_severity(finding)
            
            points = self.severity_map.get(severity, 5)
            total_risk_points += points
            breakdown[severity] += 1
            
        # Normalize score (0 to 100, where 100 is max risk)
        # Cap at 100
        final_score = min(total_risk_points, 100)
        
        return {
            "risk_score": final_score,
            "risk_level": self._get_level_label(final_score),
            "violation_breakdown": breakdown
        }

    def _infer_severity(self, finding: Dict) -> str:
        text = (finding.get("reasoning", "") + " " + finding.get("clause_id", "")).lower()
        
        if any(x in text for x in ["termination", "liability", "indemnity", "penalty"]):
            return "CRITICAL"
        if any(x in text for x in ["payment", "confidentiality", "intellectual property"]):
            return "HIGH"
        if any(x in text for x in ["notice", "jurisdiction"]):
            return "MEDIUM"
        return "LOW"

    def _get_level_label(self, score: int) -> str:
        if score >= 80: return "CRITICAL"
        if score >= 50: return "HIGH"
        if score >= 20: return "MEDIUM"
        return "LOW"
