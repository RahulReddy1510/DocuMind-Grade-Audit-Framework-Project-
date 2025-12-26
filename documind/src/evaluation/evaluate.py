import os
import json
from glob import glob
from typing import List
# Import pipeline components
# In a real run, we would import the main workflow. 
# For now, we stub the actual execution to demonstrate the evaluation logic.

class Evaluator:
    """
    Runs the DocuMind pipeline against the Golden Dataset and calculates accuracy.
    """
    def __init__(self, dataset_dir: str = "data/golden_dataset"):
        self.dataset_dir = dataset_dir

    def run_evaluation(self):
        """
        Iterates through truth files, runs the audit on corresponding docs, 
        and compares results.
        """
        truth_files = glob(f"{self.dataset_dir}/*_truth.json")
        if not truth_files:
            print("No golden dataset found. Run dataset_generator.py first.")
            return

        total_violations = 0
        detected_violations = 0
        
        print(f"Starting Evaluation on {len(truth_files)} documents...")
        
        for truth_file in truth_files:
            base_name = os.path.basename(truth_file).replace("_truth.json", "")
            doc_path = os.path.join(self.dataset_dir, f"{base_name}.md")
            
            # Load Ground Truth
            with open(truth_file, "r") as f:
                known_violations = json.load(f)
            
            # Run System (Stubbed for now)
            # system_findings = run_audit_on_text(doc_path) 
            # For demonstration, let's pretend we detected 2 out of 3.
            system_findings = self._mock_system_run(known_violations)
            
            # Compare
            matched = 0
            for v in known_violations:
                # specific matching logic (by clause_id or semantic similarity)
                if v['clause_id'] in [f['clause_id'] for f in system_findings]:
                     matched += 1
            
            total_violations += len(known_violations)
            detected_violations += matched
            
            print(f"Doc: {base_name} | Accuracy: {matched}/{len(known_violations)}")

        if total_violations > 0:
            accuracy = (detected_violations / total_violations) * 100
            print(f"\n--- Final Results ---")
            print(f"Total violations in dataset: {total_violations}")
            print(f"Detected violations: {detected_violations}")
            print(f"System Accuracy: {accuracy:.2f}%")
            if accuracy >= 94:
                print("✅ TARGET REACHED (>=94%)")
            else:
                print("❌ TARGET FAILED (<94%)")
        else:
            print("No violations to test.")

    def _mock_system_run(self, truth):
        """Simulates the system detecting stuff for the sake of the script working."""
        # Return a subset to simulate <100% accuracy
        return list(truth)[0:-1] if len(truth) > 1 else list(truth)

if __name__ == "__main__":
    evaluator = Evaluator()
    evaluator.run_evaluation()
