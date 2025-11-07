"""
Injects context into agent prompts.
"""
from typing import List

class ContextInjector:
    """
    Injects various types of context into agent prompts.
    """

    def inject_context(self, prompt: str, context: List[str]) -> str:
        """
        Injects a list of context strings into the prompt.
        """
        if not context:
            return prompt

        context_str = "\n".join(f"- {c}" for c in context)
        return f"ADDITIONAL CONTEXT:\n{context_str}\n\nORIGINAL PROMPT:\n{prompt}"

    def market_report_context(self, title: str, description: str, market_research_template: str) -> str:
        """
        Generate context for market report section generation.
        
        Args:
            title: Section title
            description: Report description
            market_research_template: The template content
            
        Returns:
            Formatted prompt string
        """
        context_str = f"""
Using the Calnetix Defense & Power Systems Market Intelligence Report template, generate content for the "{title}" section.

Report Topic: {title}
Report Description: {description or 'Market research and analysis report for Calnetix Defense & Power Systems'}

Template Context: {market_research_template}

Please generate comprehensive, professional content for the "{title}" section that follows the template requirements:

- Include verifiable sources with URLs where required
- Focus on Calnetix products (Enercycle inverter family, DC-1000 variant)
- Provide actionable intelligence and strategic insights
- Use proper formatting (tables, bullet points as specified in template)
- Include specific dates, companies, and technical details
- Ensure all information is relevant to defense power systems and military applications

Generate detailed, fact-based content that would be valuable for strategic decision-making.
"""
        return context_str
    
    def section_revision_prompt(self, section_title: str, current_content: str, feedback: str) -> str:
        """
        Generate a prompt for revising a section based on feedback.
        
        Args:
            section_title: The title of the section to revise
            current_content: The current content of the section
            feedback: User feedback for improvement
            
        Returns:
            Formatted revision prompt string
        """
        prompt = f"""
Please revise the following section based on the provided feedback:

**Section Title:** {section_title}

**Current Content:**
{current_content}

**Feedback for Improvement:**
{feedback}

**Instructions:**
- Incorporate the feedback to improve the content
- Maintain professional tone and formatting
- Ensure the content is comprehensive and accurate
- Keep the same general structure but enhance based on feedback

Please provide the revised content:
"""
        return prompt
