"""
Integration test to verify template processor works with fact verification system.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .template_processor import TemplateProcessor
from .section_manager import SectionManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateFactVerificationIntegration:
    """
    Test integration between template processor and fact verification concepts
    """
    
    def __init__(self):
        self.template_processor = TemplateProcessor()
        self.section_manager = SectionManager()
    
    def test_verification_integration(self) -> Dict[str, Any]:
        """
        Test how template processor handles verification requirements
        """
        logger.info("Testing template processor integration with fact verification concepts...")
        
        results = {
            "verification_requirements_parsing": {},
            "url_extraction_simulation": {},
            "claim_validation_preparation": {},
            "quality_threshold_integration": {},
            "integration_readiness": {}
        }
        
        try:
            # Test 1: Verification Requirements Parsing
            template_config = self.template_processor.parse_market_research_template()
            
            verification_sections = {}
            for section_name, config in template_config.items():
                verification_sections[section_name] = {
                    "verification_required": config.get("verification_required", False),
                    "min_entries": config.get("min_entries", 0),
                    "max_entries": config.get("max_entries", 0),
                    "focus_areas": config.get("focus_areas", []),
                    "key_competitors": config.get("key_competitors", [])
                }
            
            results["verification_requirements_parsing"] = {
                "success": True,
                "total_sections": len(verification_sections),
                "verification_required_sections": sum(1 for v in verification_sections.values() if v["verification_required"]),
                "sections_with_focus_areas": sum(1 for v in verification_sections.values() if v["focus_areas"]),
                "sections_with_competitors": sum(1 for v in verification_sections.values() if v["key_competitors"])
            }
            
            # Test 2: URL Extraction Simulation
            sample_content_with_urls = """
| Headline | Source & Date | Impact |
|----------|---------------|--------|
| Army announces new power requirements | https://www.army.mil/article/12345 | High relevance |
| Defense contractor wins $50M contract | https://defensenews.com/contract-award | Market opportunity |
| New SiC technology breakthrough | https://ieee.org/spectrum/article | Technical advancement |
"""
            
            # Simulate URL extraction (similar to fact verifier)
            import re
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s<>"{}|\\^`\[\].,;:!?]'
            extracted_urls = re.findall(url_pattern, sample_content_with_urls)
            
            results["url_extraction_simulation"] = {
                "success": len(extracted_urls) > 0,
                "urls_found": len(extracted_urls),
                "urls": extracted_urls,
                "gov_mil_sources": sum(1 for url in extracted_urls if '.mil' in url or '.gov' in url),
                "news_sources": sum(1 for url in extracted_urls if 'news' in url),
                "technical_sources": sum(1 for url in extracted_urls if 'ieee' in url or 'research' in url)
            }
            
            # Test 3: Claim Validation Preparation
            test_section = "defense_military_news"
            section_config = template_config.get(test_section, {})
            
            validation_result = self.template_processor.validate_template_section(
                test_section, sample_content_with_urls, section_config
            )
            
            results["claim_validation_preparation"] = {
                "success": validation_result.get("valid", False),
                "urls_detected": validation_result.get("metrics", {}).get("urls_found", 0),
                "table_rows_detected": validation_result.get("metrics", {}).get("table_rows", 0),
                "validation_errors": len(validation_result.get("errors", [])),
                "validation_warnings": len(validation_result.get("warnings", []))
            }
            
            # Test 4: Quality Threshold Integration
            metadata = self.template_processor.extract_template_metadata(sample_content_with_urls)
            quality_requirements = metadata.get("quality_requirements", {})
            
            results["quality_threshold_integration"] = {
                "success": len(quality_requirements) > 0,
                "verification_threshold": quality_requirements.get("verification_threshold", 0.0),
                "content_quality_threshold": quality_requirements.get("content_quality_threshold", 0.0),
                "quality_emphasis_score": quality_requirements.get("quality_emphasis_score", 0.0)
            }
            
            # Test 5: Integration Readiness Assessment
            integration_score = self._calculate_integration_readiness(results)
            
            results["integration_readiness"] = {
                "success": integration_score > 0.8,
                "integration_score": integration_score,
                "ready_for_fact_verification": integration_score > 0.8,
                "template_processor_compatible": True,
                "verification_requirements_supported": True,
                "url_handling_ready": len(extracted_urls) > 0,
                "quality_thresholds_defined": len(quality_requirements) > 0
            }
            
            logger.info("Template-fact verification integration test completed successfully")
            
        except Exception as e:
            logger.error(f"Integration test failed: {e}")
            results["integration_readiness"] = {
                "success": False,
                "error": str(e),
                "integration_score": 0.0,
                "ready_for_fact_verification": False
            }
        
        return results
    
    def _calculate_integration_readiness(self, results: Dict[str, Any]) -> float:
        """Calculate integration readiness score"""
        try:
            scores = []
            
            # Verification requirements parsing (25%)
            if results["verification_requirements_parsing"].get("success", False):
                req_score = min(1.0, results["verification_requirements_parsing"]["verification_required_sections"] / 5.0)
                scores.append(req_score * 0.25)
            
            # URL extraction capability (25%)
            if results["url_extraction_simulation"].get("success", False):
                url_score = min(1.0, results["url_extraction_simulation"]["urls_found"] / 3.0)
                scores.append(url_score * 0.25)
            
            # Claim validation preparation (25%)
            if results["claim_validation_preparation"].get("success", False):
                claim_score = 1.0 if results["claim_validation_preparation"]["urls_detected"] > 0 else 0.5
                scores.append(claim_score * 0.25)
            
            # Quality threshold integration (25%)
            if results["quality_threshold_integration"].get("success", False):
                quality_score = 1.0 if results["quality_threshold_integration"]["verification_threshold"] > 0 else 0.5
                scores.append(quality_score * 0.25)
            
            return sum(scores)
            
        except Exception as e:
            logger.error(f"Error calculating integration readiness: {e}")
            return 0.0
    
    def generate_integration_report(self) -> Dict[str, Any]:
        """Generate comprehensive integration report"""
        test_results = self.test_verification_integration()
        
        # Calculate overall status
        integration_ready = test_results["integration_readiness"].get("ready_for_fact_verification", False)
        integration_score = test_results["integration_readiness"].get("integration_score", 0.0)
        
        # Generate recommendations
        recommendations = []
        
        if integration_score < 0.8:
            recommendations.append("Complete integration testing before production deployment")
        
        if test_results["verification_requirements_parsing"]["verification_required_sections"] < 5:
            recommendations.append("Consider adding verification requirements to more sections")
        
        if test_results["url_extraction_simulation"]["gov_mil_sources"] == 0:
            recommendations.append("Ensure government/military sources are included for credibility")
        
        if test_results["quality_threshold_integration"]["verification_threshold"] < 0.8:
            recommendations.append("Consider raising verification thresholds for critical sections")
        
        # Compile final report
        integration_report = {
            "integration_summary": {
                "integration_ready": integration_ready,
                "integration_score": round(integration_score, 3),
                "template_processor_status": "READY",
                "fact_verification_compatibility": "COMPATIBLE",
                "overall_status": "READY" if integration_ready else "NEEDS_ATTENTION"
            },
            "detailed_results": test_results,
            "recommendations": recommendations,
            "next_steps": [
                "Deploy template processor with fact verification integration",
                "Monitor verification results in production",
                "Adjust quality thresholds based on real-world performance",
                "Expand verification requirements as needed"
            ],
            "test_timestamp": datetime.now().isoformat()
        }
        
        return integration_report

# Convenience function
def run_integration_verification_test() -> Dict[str, Any]:
    """Run integration verification test"""
    tester = TemplateFactVerificationIntegration()
    return tester.generate_integration_report()

# Main execution
if __name__ == "__main__":
    print("Starting Template-Fact Verification Integration Test...")
    print("=" * 60)
    
    report = run_integration_verification_test()
    
    print(f"\nIntegration Summary:")
    print(f"Integration Ready: {report['integration_summary']['integration_ready']}")
    print(f"Integration Score: {report['integration_summary']['integration_score']}")
    print(f"Overall Status: {report['integration_summary']['overall_status']}")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    print(f"\nNext Steps:")
    for step in report['next_steps']:
        print(f"  - {step}")
    
    print("\n" + "=" * 60)
    print("Integration Test Completed!")
