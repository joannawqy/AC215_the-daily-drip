"""
DailyDrip Integrated Agent
Connects the Core Recipe Agent with the Visualization Agent to provide
end-to-end recipe generation and visualization.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Import core agent functions
from .agent import (
    load_bean_info,
    generate_recipe,
    normalize_recipe,
    validate_recipe,
    query_reference_recipes,
    DEFAULT_RAG_PERSIST_DIR,
)

# Import visualization agent
from .visualization_agent_v2 import CoffeeBrewVisualizationAgent


class IntegratedCoffeeAgent:
    """
    Integrated agent that combines recipe generation and visualization.

    Workflow:
    1. Load bean information
    2. Query RAG for similar recipes (optional)
    3. Generate recipe using Core Agent
    4. Visualize recipe using Visualization Agent
    5. Output both recipe JSON and visualizations
    """

    def __init__(
        self,
        rag_enabled: bool = True,
        rag_persist_dir: Path = DEFAULT_RAG_PERSIST_DIR,
        rag_k: int = 3,
    ):
        """
        Initialize the integrated agent.

        Args:
            rag_enabled: Whether to use RAG for reference recipes
            rag_persist_dir: Path to RAG database
            rag_k: Number of reference recipes to retrieve
        """
        self.rag_enabled = rag_enabled
        self.rag_persist_dir = rag_persist_dir
        self.rag_k = rag_k
        self.viz_agent = CoffeeBrewVisualizationAgent()

    def generate_complete_recipe(
        self,
        bean_info: Dict[str, Any],
        brewer: str,
        custom_note: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.6,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        """
        Generate a complete recipe with reference recipes.

        Args:
            bean_info: Bean information dictionary
            brewer: Brewer name (V60, April, Orea, Origami)
            custom_note: Optional custom instruction
            model: OpenAI model to use
            temperature: Sampling temperature
            top_p: Nucleus sampling probability

        Returns:
            Complete recipe dictionary with bean, brewing, and references
        """
        # Step 1: Query RAG for reference recipes
        references = []
        if self.rag_enabled:
            try:
                references = query_reference_recipes(
                    bean_info,
                    persist_dir=self.rag_persist_dir,
                    k=self.rag_k,
                )
                print(f"✓ Retrieved {len(references)} reference recipes from RAG")
            except Exception as exc:
                print(f"⚠ Warning: Could not retrieve RAG references: {exc}")
                references = []

        # Step 2: Generate recipe using core agent
        print(f"🔄 Generating recipe for {bean_info.get('name', 'Unknown')} with {brewer}...")
        recipe = generate_recipe(
            bean_info,
            brewer,
            reference_recipes=references,
            custom_note=custom_note,
            model=model,
            temperature=temperature,
            top_p=top_p,
        )

        # Step 3: Normalize and validate
        recipe = normalize_recipe(recipe)
        validate_recipe(recipe)

        # Step 4: Add bean info to recipe for visualization
        complete_recipe = {
            "bean": bean_info,
            "brewing": recipe["brewing"],
            "evaluation": None,  # No evaluation yet (to be filled after brewing)
        }

        print(f"✓ Recipe generated successfully!")
        return complete_recipe

    def visualize_recipe(
        self,
        recipe: Dict[str, Any],
        output_formats: list = ["html", "mermaid", "ascii"],
    ) -> Dict[str, str]:
        """
        Generate visualizations for a recipe.

        Args:
            recipe: Complete recipe dictionary
            output_formats: List of desired formats

        Returns:
            Dictionary with format -> content mappings
        """
        print(f"🎨 Generating visualizations...")
        self.viz_agent.load_recipe(recipe)

        visualizations = {}
        if "html" in output_formats:
            visualizations["html"] = self.viz_agent.generate_html_visualization()
        if "mermaid" in output_formats:
            visualizations["mermaid"] = self.viz_agent.generate_mermaid_flowchart()
        if "ascii" in output_formats:
            visualizations["ascii"] = self.viz_agent.generate_ascii_flowchart()

        print(f"✓ Generated {len(visualizations)} visualization formats")
        return visualizations

    def generate_and_visualize(
        self,
        bean_source: str,
        brewer: str,
        custom_note: Optional[str] = None,
        output_dir: Optional[Path] = None,
        output_formats: list = ["html", "mermaid", "ascii"],
        model: str = "gpt-4o-mini",
    ) -> Dict[str, Any]:
        """
        Complete workflow: generate recipe and create visualizations.

        Args:
            bean_source: Path to bean JSON file or JSON string
            brewer: Brewer name
            custom_note: Optional custom instruction
            output_dir: Directory to save outputs (optional)
            output_formats: List of visualization formats to generate
            model: OpenAI model to use

        Returns:
            Dictionary containing recipe and visualizations
        """
        # Load bean info
        bean_info = load_bean_info(bean_source)
        print(f"\n{'='*70}")
        print(f"☕ DailyDrip Integrated Agent")
        print(f"{'='*70}")
        print(f"Bean: {bean_info.get('name', 'Unknown')}")
        print(f"Brewer: {brewer}")
        if custom_note:
            print(f"Custom Note: {custom_note}")
        print(f"{'='*70}\n")

        # Generate recipe
        recipe = self.generate_complete_recipe(
            bean_info,
            brewer,
            custom_note=custom_note,
            model=model,
        )

        # Generate visualizations
        visualizations = self.visualize_recipe(recipe, output_formats)

        # Save outputs if directory specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

            # Save recipe JSON
            bean_name = bean_info.get('name', 'recipe').replace(' ', '_')
            recipe_path = output_dir / f"{bean_name}_recipe.json"
            recipe_path.write_text(
                json.dumps(recipe, ensure_ascii=False, indent=2),
                encoding='utf-8'
            )
            print(f"✓ Saved recipe to: {recipe_path}")

            # Save visualizations
            for fmt, content in visualizations.items():
                ext = fmt if fmt != 'mermaid' else 'md'
                viz_path = output_dir / f"{bean_name}_visualization.{ext}"
                viz_path.write_text(content, encoding='utf-8')
                print(f"✓ Saved {fmt} visualization to: {viz_path}")

        # Return complete package
        return {
            "recipe": recipe,
            "visualizations": visualizations,
            "summary": self.viz_agent.get_recipe_summary(),
        }


def main():
    """Command-line interface for integrated agent."""
    import argparse

    parser = argparse.ArgumentParser(
        description="DailyDrip Integrated Agent - Generate and visualize coffee recipes"
    )
    parser.add_argument(
        "--bean",
        required=True,
        help="JSON string or path to JSON file describing the bean",
    )
    parser.add_argument(
        "--brewer",
        required=True,
        choices=["V60", "April", "Orea", "Origami"],
        help="Name of the brewer",
    )
    parser.add_argument(
        "--note",
        help="Optional custom instruction for the recipe",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to save outputs (recipe + visualizations)",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        default=["html", "mermaid", "ascii"],
        choices=["html", "mermaid", "ascii"],
        help="Visualization formats to generate",
    )
    parser.add_argument(
        "--no-rag",
        action="store_false",
        dest="rag_enabled",
        help="Disable RAG retrieval",
    )
    parser.add_argument(
        "--rag-k",
        type=int,
        default=3,
        help="Number of reference recipes to retrieve",
    )
    parser.add_argument(
        "--show-ascii",
        action="store_true",
        help="Print ASCII visualization to console",
    )

    args = parser.parse_args()

    # Create integrated agent
    agent = IntegratedCoffeeAgent(
        rag_enabled=args.rag_enabled,
        rag_k=args.rag_k,
    )

    try:
        # Generate and visualize
        result = agent.generate_and_visualize(
            bean_source=args.bean,
            brewer=args.brewer,
            custom_note=args.note,
            output_dir=Path(args.output_dir) if args.output_dir else None,
            output_formats=args.formats,
            model=args.model,
        )

        # Print summary
        summary = result["summary"]
        print(f"\n{'='*70}")
        print(f"📋 Recipe Summary")
        print(f"{'='*70}")
        print(f"Bean:        {summary['bean_name']}")
        print(f"Brewer:      {summary['brewer']}")
        print(f"Dose:        {summary['coffee_dose']}g")
        print(f"Water:       {summary['total_water']}ml")
        print(f"Ratio:       {summary['ratio']}")
        print(f"Temperature: {summary['temperature']}°C")
        print(f"Grind Size:  {summary['grind_size']}")
        print(f"Total Time:  {summary['total_time']}s")
        print(f"Pours:       {summary['num_pours']}")
        print(f"{'='*70}\n")

        # Show ASCII if requested
        if args.show_ascii and "ascii" in result["visualizations"]:
            print(result["visualizations"]["ascii"])

        print(f"✓ Complete! Recipe and visualizations ready.\n")

    except Exception as exc:
        print(f"❌ Error: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
