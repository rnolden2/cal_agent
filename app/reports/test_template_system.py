"""
Test script for the collaborative report generation and template processing system.
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from .template_processor import TemplateProcessor
from .collaborative_generator import CollaborativeReportGenerator, ReportRequest
from .section_manager import SectionManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateSystemTester:
    """
    Comprehensive testing system for template processing and collaborative generation
    """
    
    def __init__(self):
        self.template_processor = TemplateProcessor()
        self.collaborative_generator = CollaborativeReportGenerator()
        self.section_manager = SectionManager()
        
        self.test_results = {
            "template_parsing": {},
            "section_validation": {},
            "collaborative_generation": {},
            "integration_tests": {},
            "performance_metrics": {}
        }
    
    async def run_comprehensive_tests(self) -> Dict[str, Any]:
        """
        Run all tests and return comprehensive results
        """
        logger.info("Starting comprehensive template system tests...")
        
        # Test 1: Template Processing
        await self._test_template_processing()
        
        # Test 2: Section Management
        await self._test_section_management()
        
        # Test 3: Template Validation
        await self._test_template_validation()
        
        # Test 4: Context Processing
        await self._test_context_processing()
        
        # Test 5: Integration Tests
        await self._test_system_integration()
        
        # Test 6: Performance Tests
        await self._test_performance()
        
        # Generate test report
        test_report = self._generate_test_report()
        
        logger.info("Comprehensive tests completed!")
        return test_report
    
    async def _test_template_processing(self):
        """Test template processing functionality"""
        logger.info("Testing template processing...")
        
        try:
            # Test market research template parsing
            template_config = self.template_processor.parse_market_research_template()
            
            self.test_results["template_parsing"]["market_research"] = {
                "success": len(template_config) > 0,
                "sections_found": len(template_config),
                "sections": list(template_config.keys()),
                "verification_sections": sum(1 for s in template_config.values() if s.get("verification_required")),
                "table_sections": sum(1 for s in template_config.values() if s.get("format") == "table")
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
            
            self.test_results["template_parsing"]["metadata_extraction"] = {
                "success": metadata.get("total_sections", 0) > 0,
                "sections_found": metadata.get("sections_found", []),
                "complexity": metadata.get("estimated_complexity"),
                "agent_requirements": metadata.get("agent_requirements", {}),
                "quality_requirements": metadata.get("quality_requirements", {})
            }
            
            # Test template generation
            for section_name, section_config in list(template_config.items())[:3]:  # Test first 3 sections
                generated_template = self.template_processor.generate_section_template(section_name, section_config)
                
                self.test_results["template_parsing"][f"generation_{section_name}"] = {
                    "success": len(generated_template) > 50,
                    "has_title": "##" in generated_template,
                    "has_description": "Purpose:" in generated_template,
                    "has_format": "|" in generated_template or "•" in generated_template,
                    "template_length": len(generated_template)
                }
            
            logger.info("Template processing tests completed successfully")
            
        except Exception as e:
            logger.error(f"Template processing test failed: {e}")
            self.test_results["template_parsing"]["error"] = str(e)
    
    async def _test_section_management(self):
        """Test section management functionality"""
        logger.info("Testing section management...")
        
        try:
            # Test section metadata retrieval
            all_sections = self.section_manager.get_all_sections("market_research")
            
            self.test_results["section_validation"]["metadata_retrieval"] = {
                "success": len(all_sections) > 0,
                "total_sections": len(all_sections),
                "sections_with_dependencies": sum(1 for s in all_sections.values() if s.dependencies),
                "high_priority_sections": sum(1 for s in all_sections.values() if s.priority <= 3)
            }
            
            # Test generation order
            generation_order = self.section_manager.get_generation_order("market_research")
            
            self.test_results["section_validation"]["generation_order"] = {
                "success": len(generation_order) == len(all_sections),
                "order": generation_order,
                "dependencies_respected": self._validate_dependency_order(generation_order, all_sections)
            }
            
            # Test section validation
            sample_content = """
| Headline | Impact |
|----------|--------|
| New Army modernization program | High relevance to Calnetix inverter systems |
| Defense budget increases | Potential for increased procurement |
"""
            
            validation_result = self.section_manager.validate_section_requirements(
                "defense_military_news", sample_content, "market_research"
            )
            
            self.test_results["section_validation"]["content_validation"] = {
                "success": validation_result.get("valid", False),
                "errors": validation_result.get("errors", []),
                "warnings": validation_result.get("warnings", []),
                "metrics": validation_result.get("metrics", {})
            }
            
            logger.info("Section management tests completed successfully")
            
        except Exception as e:
            logger.error(f"Section management test failed: {e}")
            self.test_results["section_validation"]["error"] = str(e)
    
    async def _test_template_validation(self):
        """Test template validation functionality"""
        logger.info("Testing template validation...")
        
        try:
            # Test section content validation
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
                    "name": "missing_urls",
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
                }
            ]
            
            template_config = self.template_processor.parse_market_research_template()
            
            for test_case in test_cases:
                section_config = template_config.get(test_case["section"], {})
                validation_result = self.template_processor.validate_template_section(
                    test_case["section"], test_case["content"], section_config
                )
                
                self.test_results["section_validation"][test_case["name"]] = {
                    "success": validation_result.get("valid") == test_case["expected_valid"],
                    "valid": validation_result.get("valid"),
                    "expected_valid": test_case["expected_valid"],
                    "errors": validation_result.get("errors", []),
                    "warnings": validation_result.get("warnings", []),
                    "metrics": validation_result.get("metrics", {})
                }
            
            # Test template completeness validation
            completeness_result = self.template_processor.validate_template_completeness(template_config)
            
            self.test_results["section_validation"]["template_completeness"] = {
                "success": completeness_result.get("complete", False),
                "missing_elements": completeness_result.get("missing_elements", []),
                "inconsistencies": completeness_result.get("inconsistencies", []),
                "recommendations": completeness_result.get("recommendations", [])
            }
            
            logger.info("Template validation tests completed successfully")
            
        except Exception as e:
            logger.error(f"Template validation test failed: {e}")
            self.test_results["section_validation"]["validation_error"] = str(e)
    
    async def _test_context_processing(self):
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
            
            self.test_results["integration_tests"]["context_processing"] = {
                "success": len(enhanced_config) > 0,
                "sections_enhanced": len([s for s in enhanced_config.values() if "feedback_context" in s]),
                "priority_adjustments_applied": len([s for s in enhanced_config.values() if "adjusted_priority" in s]),
                "dynamic_focus_added": len([s for s in enhanced_config.values() if "dynamic_focus" in s])
            }
            
            logger.info("Context processing tests completed successfully")
            
        except Exception as e:
            logger.error(f"Context processing test failed: {e}")
            self.test_results["integration_tests"]["context_error"] = str(e)
    
    async def _test_system_integration(self):
        """Test integration between all components"""
        logger.info("Testing system integration...")
        
        try:
            # Test collaborative generator initialization
            supported_types = self.collaborative_generator.get_supported_report_types()
            section_agents = self.collaborative_generator.get_section_agents("market_research")
            
            self.test_results["integration_tests"]["component_integration"] = {
                "success": len(supported_types) > 0 and len(section_agents) > 0,
                "supported_report_types": supported_types,
                "section_agent_mappings": len(section_agents),
                "agents_available": list(set([agent for agents in section_agents.values() for agent in agents.values()]))
            }
            
            # Test report request creation (without actual generation to avoid API calls)
            test_request = ReportRequest(
                report_type="market_research",
                user_id="test_user",
                template_name="market_research",
                parameters={
                    "focus_areas": ["defense", "power_electronics"],
                    "time_period": "last_30_days"
                },
                verification_required=True,
                quality_threshold=0.8
            )
            
            self.test_results["integration_tests"]["request_creation"] = {
                "success": test_request.report_type == "market_research",
                "verification_enabled": test_request.verification_required,
                "quality_threshold": test_request.quality_threshold,
                "parameters_set": len(test_request.parameters) > 0
            }
            
            # Test section complexity estimation
            complexity_estimates = {}
            for section_name in ["defense_military_news", "technology_advances", "key_takeaways"]:
                complexity = self.section_manager.estimate_section_complexity(section_name, "market_research")
                complexity_estimates[section_name] = complexity
            
            self.test_results["integration_tests"]["complexity_estimation"] = {
                "success": len(complexity_estimates) > 0,
                "estimates": complexity_estimates,
                "avg_complexity_score": sum(c.get("score", 0) for c in complexity_estimates.values()) / len(complexity_estimates)
            }
            
            logger.info("System integration tests completed successfully")
            
        except Exception as e:
            logger.error(f"System integration test failed: {e}")
            self.test_results["integration_tests"]["integration_error"] = str(e)
    
    async def _test_performance(self):
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
            self.test_results["performance_metrics"]["performance_error"] = str(e)
    
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
        
        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                if isinstance(result, dict) and "success" in result:
                    total_tests += 1
                    if result["success"]:
                        successful_tests += 1
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Identify critical issues
        critical_issues = []
        for category, tests in self.test_results.items():
            for test_name, result in tests.items():
                if isinstance(result, dict):
                    if not result.get("success", True):
                        critical_issues.append(f"{category}.{test_name}: {result.get('error', 'Test failed')}")
                    if "error" in result:
                        critical_issues.append(f"{category}.{test_name}: {result['error']}")
        
        # Generate recommendations
        recommendations = []
        
        if success_rate < 90:
            recommendations.append("Address failing tests before production deployment")
        
        if self.test_results.get("performance_metrics", {}).get("total_test_time", 0) > 5:
            recommendations.append("Consider performance optimization for better response times")
        
        if len(critical_issues) > 0:
            recommendations.append("Resolve critical issues identified in test results")
        
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
async def run_template_system_tests() -> Dict[str, Any]:
    """
    Convenience function to run all template system tests
    """
    tester = TemplateSystemTester()
    return await tester.run_comprehensive_tests()

# Main execution for standalone testing
if __name__ == "__main__":
    async def main():
        print("Starting CAL Template System Tests...")
        print("=" * 50)
        
        results = await run_template_system_tests()
        
        print(f"\nTest Results Summary:")
        print(f"Total Tests: {results['test_summary']['total_tests']}")
        print(f"Successful: {results['test_summary']['successful_tests']}")
        print(f"Success Rate: {results['test_summary']['success_rate']}%")
        print(f"System Status: {results['system_status']}")
        
        if results['critical_issues']:
            print(f"\nCritical Issues ({len(results['critical_issues'])}):")
            for issue in results['critical_issues']:
                print(f"  - {issue}")
        
        if results['recommendations']:
            print(f"\nRecommendations:")
            for rec in results['recommendations']:
                print(f"  - {rec}")
        
        print("\n" + "=" * 50)
        print("Template System Tests Completed!")
    
    asyncio.run(main())
