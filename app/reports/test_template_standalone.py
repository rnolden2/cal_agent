"""
Standalone test script for template processor and section manager components.
"""

import logging
from typing import Dict, Any
from datetime import datetime

from .template_processor import TemplateProcessor
from .section_manager import SectionManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class StandaloneTemplateTest:
    """
    Standalone testing for template processor and section manager
    """
    
    def __init__(self):
        self.template_processor = TemplateProcessor()
        self.section_manager = SectionManager()
        self.test_results = {}
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all standalone tests
        """
        logger.info("Starting standalone template system tests...")
        
        # Test 1: Template Processing
        self._test_template_processing()
        
        # Test 2: Section Management
        self._test_section_management()
        
        # Test 3: Template Validation
        self._test_template_validation()
        
        # Test 4: Context Processing
        self._test_context_processing()
        
        # Test 5: Performance Tests
        self._test_performance()
        
        # Generate test report
        test_report = self._generate_test_report()
        
        logger.info("Standalone tests completed!")
        return test_report
    
    def _test_template_processing(self):
        """Test template processing functionality"""
        logger.info("Testing template processing...")
        
        try:
            # Test market research template parsing
            template_config = self.template_processor.parse_market_research_template()
            
            self.test_results["template_parsing"] = {
                "success": len(template_config) > 0,
                "sections_found": len(template_config),
                "sections": list(template_config.keys()),
                "verification_sections": sum(1 for s in template_config.values() if s.get("verification_required")),
                "table_sections": sum(1 for s in template_config.values() if s.get("format") == "table"),
                "bullet_sections": sum(1 for s in template_config.values() if s.get("format") == "bullet_list")
            }
            
            # Test template metadata extraction
            sample_template = """
1. Defense & Military News Summary
Provide 2-3 recent news items with verifiable URLs.

2. Technology Advances
Highlight technical developments in SiC and GaN.

3. Key Takeaways
Provide strategic recommendations.
"""
            
            metadata = self.template_processor.extract_template_metadata(sample_template)
            
            self.test_results["metadata_extraction"] = {
                "success": metadata.get("total_sections", 0) > 0,
                "sections_found": metadata.get("sections_found", []),
                "complexity": metadata.get("estimated_complexity"),
                "agent_requirements": len(metadata.get("agent_requirements", {})),
                "quality_requirements": len(metadata.get("quality_requirements", {}))
            }
            
            # Test template generation for each section
            generation_results = {}
            for section_name, section_config in template_config.items():
                try:
                    generated_template = self.template_processor.generate_section_template(section_name, section_config)
                    generation_results[section_name] = {
                        "success": len(generated_template) > 50,
                        "has_title": "##" in generated_template,
                        "has_description": "Purpose:" in generated_template,
                        "has_format": "|" in generated_template or "•" in generated_template,
                        "template_length": len(generated_template)
                    }
                except Exception as e:
                    generation_results[section_name] = {"success": False, "error": str(e)}
            
            self.test_results["template_generation"] = generation_results
            
            logger.info("Template processing tests completed successfully")
            
        except Exception as e:
            logger.error(f"Template processing test failed: {e}")
            self.test_results["template_parsing"] = {"success": False, "error": str(e)}
    
    def _test_section_management(self):
        """Test section management functionality"""
        logger.info("Testing section management...")
        
        try:
            # Test section metadata retrieval
            all_sections = self.section_manager.get_all_sections("market_research")
            
            self.test_results["section_metadata"] = {
                "success": len(all_sections) > 0,
                "total_sections": len(all_sections),
                "sections_with_dependencies": sum(1 for s in all_sections.values() if s.dependencies),
                "high_priority_sections": sum(1 for s in all_sections.values() if s.priority <= 3),
                "section_names": list(all_sections.keys())
            }
            
            # Test generation order
            generation_order = self.section_manager.get_generation_order("market_research")
            
            self.test_results["generation_order"] = {
                "success": len(generation_order) == len(all_sections),
                "order": generation_order,
                "dependencies_respected": self._validate_dependency_order(generation_order, all_sections)
            }
            
            # Test section templates
            template_results = {}
            for section_name in list(all_sections.keys())[:5]:  # Test first 5 sections
                try:
                    template = self.section_manager.get_section_template(section_name, "market_research")
                    template_results[section_name] = {
                        "success": len(template) > 0,
                        "has_table": "|" in template,
                        "has_bullets": "•" in template,
                        "template_length": len(template)
                    }
                except Exception as e:
                    template_results[section_name] = {"success": False, "error": str(e)}
            
            self.test_results["section_templates"] = template_results
            
            # Test complexity estimation
            complexity_results = {}
            for section_name in list(all_sections.keys())[:5]:  # Test first 5 sections
                try:
                    complexity = self.section_manager.estimate_section_complexity(section_name, "market_research")
                    complexity_results[section_name] = {
                        "success": "complexity" in complexity,
                        "complexity_level": complexity.get("complexity"),
                        "score": complexity.get("score", 0),
                        "estimated_time": complexity.get("estimated_time_minutes", 0)
                    }
                except Exception as e:
                    complexity_results[section_name] = {"success": False, "error": str(e)}
            
            self.test_results["complexity_estimation"] = complexity_results
            
            logger.info("Section management tests completed successfully")
            
        except Exception as e:
            logger.error(f"Section management test failed: {e}")
            self.test_results["section_metadata"] = {"success": False, "error": str(e)}
    
    def _test_template_validation(self):
        """Test template validation functionality"""
        logger.info("Testing template validation...")
        
        try:
            template_config = self.template_processor.parse_market_research_template()
            
            # Test cases for different validation scenarios
            test_cases = [
                {
                    "name": "valid_table_content",
                    "section": "defense_military_news",
                    "content": """
| Headline | Source & Date | Impact |
|----------|---------------|--------|
| Army announces new power system requirements | Defense News, 01/15/2024 | High relevance to Enercycle inverter family |
| Navy tests bidirectional power systems | Navy.mil, 01/20/2024 | Validates our technology approach |
""",
                    "expected_valid": True
                },
                {
                    "name": "missing_urls_verification_required",
                    "section": "technology_advances",
                    "content": """
| Development | Impact |
|-------------|--------|
| New SiC technology | Better efficiency |
""",
                    "expected_valid": False  # Missing URLs for verification-required section
                },
                {
                    "name": "valid_bullet_list",
                    "section": "key_takeaways",
                    "content": """
• Strategic Action: Focus on Army modernization opportunities
• Risk: Increased competition in power electronics market
• Opportunity: Expand into commercial microgrid applications
• Recommendation: Strengthen partnerships with defense contractors
""",
                    "expected_valid": True
                },
                {
                    "name": "insufficient_entries",
                    "section": "defense_military_news",
                    "content": """
| Headline | Impact |
|----------|--------|
| Single entry only | Not enough entries |
""",
                    "expected_valid": False  # Needs minimum 2 entries
                },
                {
                    "name": "valid_with_urls",
                    "section": "competitor_updates",
                    "content": """
| Company | Update | Strategic Takeaway |
|---------|--------|-------------------|
| Aegis Power | New inverter announcement https://example.com | Competitive threat in defense market |
| BAE Systems | Partnership with startup https://example.com | Potential collaboration opportunity |
""",
                    "expected_valid": True
                }
            ]
            
            validation_results = {}
            for test_case in test_cases:
                try:
                    section_config = template_config.get(test_case["section"], {})
                    validation_result = self.template_processor.validate_template_section(
                        test_case["section"], test_case["content"], section_config
                    )
                    
                    validation_results[test_case["name"]] = {
                        "success": validation_result.get("valid") == test_case["expected_valid"],
                        "valid": validation_result.get("valid"),
                        "expected_valid": test_case["expected_valid"],
                        "errors": validation_result.get("errors", []),
                        "warnings": validation_result.get("warnings", []),
                        "metrics": validation_result.get("metrics", {})
                    }
                except Exception as e:
                    validation_results[test_case["name"]] = {"success": False, "error": str(e)}
            
            self.test_results["content_validation"] = validation_results
            
            # Test template completeness validation
            try:
                completeness_result = self.template_processor.validate_template_completeness(template_config)
                
                self.test_results["template_completeness"] = {
                    "success": completeness_result.get("complete", False),
                    "missing_elements": completeness_result.get("missing_elements", []),
                    "inconsistencies": completeness_result.get("inconsistencies", []),
                    "recommendations": completeness_result.get("recommendations", [])
                }
            except Exception as e:
                self.test_results["template_completeness"] = {"success": False, "error": str(e)}
            
            logger.info("Template validation tests completed successfully")
            
        except Exception as e:
            logger.error(f"Template validation test failed: {e}")
            self.test_results["content_validation"] = {"success": False, "error": str(e)}
    
    def _test_context_processing(self):
        """Test context processing functionality"""
        logger.info("Testing context processing...")
        
        try:
            # Test context-enhanced template processing
            context_data = {
                "user_preferences": {
                    "focus_on_defense": True,
                    "include_commercial": False,
                    "detail_level": "high"
                },
                "historical_feedback": [
                    "Need more technical depth in power electronics sections",
                    "Include more competitor analysis",
                    "Focus on actionable business opportunities"
                ],
                "priority_adjustments": {
                    "technology_advances": 1,  # Increase priority
                    "startup_watch": -1  # Decrease priority
                },
                "focus_areas": ["SiC", "GaN", "bidirectional_inverters", "defense_applications"]
            }
            
            enhanced_config = self.template_processor.process_template_with_context(
                "market_research", context_data
            )
            
            self.test_results["context_processing"] = {
                "success": len(enhanced_config) > 0,
                "sections_enhanced": len([s for s in enhanced_config.values() if "feedback_context" in s]),
                "priority_adjustments_applied": len([s for s in enhanced_config.values() if "adjusted_priority" in s]),
                "dynamic_focus_added": len([s for s in enhanced_config.values() if "dynamic_focus" in s]),
                "user_preferences_added": len([s for s in enhanced_config.values() if "user_preferences" in s])
            }
            
            logger.info("Context processing tests completed successfully")
            
        except Exception as e:
            logger.error(f"Context processing test failed: {e}")
            self.test_results["context_processing"] = {"success": False, "error": str(e)}
    
    def _test_performance(self):
        """Test system performance"""
        logger.info("Testing system performance...")
        
        try:
            start_time = datetime.now()
            
            # Performance test: Template parsing
            parse_start = datetime.now()
            for _ in range(10):  # Parse template 10 times
                self.template_processor.parse_market_research_template()
            parse_time = (datetime.now() - parse_start).total_seconds()
            
            # Performance test: Section validation
            validation_start = datetime.now()
            template_config = self.template_processor.parse_market_research_template()
            sample_content = "| Test | Content | With | Multiple | Columns |\n|------|---------|------|----------|----------|\n| Row1 | Data1 | Data2 | Data3 | Data4 |"
            
            for section_name, section_config in list(template_config.items())[:5]:  # Test 5 sections
                self.template_processor.validate_template_section(section_name, sample_content, section_config)
            
            validation_time = (datetime.now() - validation_start).total_seconds()
            
            # Performance test: Template generation
            generation_start = datetime.now()
            for section_name, section_config in list(template_config.items())[:5]:  # Generate 5 templates
                self.template_processor.generate_section_template(section_name, section_config)
            generation_time = (datetime.now() - generation_start).total_seconds()
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            self.test_results["performance_metrics"] = {
                "template_parsing_time": parse_time,
                "section_validation_time": validation_time,
                "template_generation_time": generation_time,
                "total_test_time": total_time,
                "performance_acceptable": total_time < 5.0,  # Should complete within 5 seconds
                "parsing_per_second": 10 / parse_time if parse_time > 0 else 0,
                "validations_per_second": 5 / validation_time if validation_time > 0 else 0
            }
            
            logger.info("Performance tests completed successfully")
            
        except Exception as e:
            logger.error(f"Performance test failed: {e}")
            self.test_results["performance_metrics"] = {"success": False, "error": str(e)}
    
    def _validate_dependency_order(self, generation_order: list, all_sections: dict) -> bool:
        """Validate that generation order respects dependencies"""
        try:
            processed_sections = set()
            
            for section_name in generation_order:
                section_metadata = all_sections.get(section_name)
                if section_metadata:
                    # Check if all dependencies have been processed
                    for dependency in section_metadata.dependencies:
                        if dependency not in processed_sections and dependency != "all_previous_sections":
                            return False
                    processed_sections.add(section_name)
            
            return True
            
        except Exception:
            return False
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        
        # Calculate overall success rates
        total_tests = 0
        successful_tests = 0
        
        def count_tests(obj):
            nonlocal total_tests, successful_tests
            if isinstance(obj, dict):
                if "success" in obj:
                    total_tests += 1
                    if obj["success"]:
                        successful_tests += 1
                else:
                    for value in obj.values():
                        count_tests(value)
        
        count_tests(self.test_results)
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Identify critical issues
        critical_issues = []
        
        def find_issues(obj, path=""):
            if isinstance(obj, dict):
                if "success" in obj and not obj["success"]:
                    error_msg = obj.get("error", "Test failed")
                    critical_issues.append(f"{path}: {error_msg}")
                elif "error" in obj:
                    critical_issues.append(f"{path}: {obj['error']}")
                else:
                    for key, value in obj.items():
                        find_issues(value, f"{path}.{key}" if path else key)
        
        find_issues(self.test_results)
        
        # Generate recommendations
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("Address failing tests before production deployment")
        
        if self.test_results.get("performance_metrics", {}).get("total_test_time", 0) > 5:
            recommendations.append("Consider performance optimization for better response times")
        
        if len(critical_issues) > 0:
            recommendations.append("Resolve critical issues identified in test results")
        
        # Check specific recommendations based on test results
        if not self.test_results.get("template_completeness", {}).get("success", True):
            recommendations.append("Review template configuration for completeness")
        
        if self.test_results.get("performance_metrics", {}).get("parsing_per_second", 0) < 5:
            recommendations.append("Template parsing performance may need optimization")
        
        # Compile final report
        test_report = {
            "test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "success_rate": round(success_rate, 2),
                "critical_issues_count": len(critical_issues)
            },
            "detailed_results": self.test_results,
            "critical_issues": critical_issues,
            "recommendations": recommendations,
            "test_timestamp": datetime.now().isoformat(),
            "system_status": "READY" if success_rate >= 90 and len(critical_issues) == 0 else "NEEDS_ATTENTION"
        }
        
        return test_report

# Convenience function for running tests
def run_standalone_tests() -> Dict[str, Any]:
    """
    Convenience function to run all standalone tests
    """
    tester = StandaloneTemplateTest()
    return tester.run_all_tests()

# Main execution for standalone testing
if __name__ == "__main__":
    print("Starting CAL Template System Standalone Tests...")
    print("=" * 60)
    
    results = run_standalone_tests()
    
    print(f"\nTest Results Summary:")
    print(f"Total Tests: {results['test_summary']['total_tests']}")
    print(f"Successful: {results['test_summary']['successful_tests']}")
    print(f"Success Rate: {results['test_summary']['success_rate']}%")
    print(f"System Status: {results['system_status']}")
    
    if results['critical_issues']:
        print(f"\nCritical Issues ({len(results['critical_issues'])}):")
        for issue in results['critical_issues'][:10]:  # Show first 10 issues
            print(f"  - {issue}")
        if len(results['critical_issues']) > 10:
            print(f"  ... and {len(results['critical_issues']) - 10} more issues")
    
    if results['recommendations']:
        print(f"\nRecommendations:")
        for rec in results['recommendations']:
            print(f"  - {rec}")
    
    # Show some detailed results
    print(f"\nDetailed Results:")
    if "template_parsing" in results['detailed_results']:
        tp = results['detailed_results']['template_parsing']
        print(f"  Template Parsing: {tp.get('sections_found', 0)} sections found")
        print(f"  Verification Sections: {tp.get('verification_sections', 0)}")
        print(f"  Table Sections: {tp.get('table_sections', 0)}")
    
    if "performance_metrics" in results['detailed_results']:
        pm = results['detailed_results']['performance_metrics']
        print(f"  Performance: {pm.get('total_test_time', 0):.3f}s total")
        print(f"  Parsing Speed: {pm.get('parsing_per_second', 0):.1f} parses/sec")
    
    print("\n" + "=" * 60)
    print("Template System Standalone Tests Completed!")
