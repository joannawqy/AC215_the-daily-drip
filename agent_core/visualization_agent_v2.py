"""
DailyDrip Visualization Agent V2
Enhanced version with improved single-line timeline visualization.
"""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class BrewingStep:
    """Represents a single brewing step."""
    step_number: int
    start_time: int
    end_time: int
    water_added: int
    cumulative_water: int
    action: str


class CoffeeBrewVisualizationAgent:
    """
    Agent for generating visual flowcharts of coffee brewing recipes.
    V2: Enhanced with single-line timeline visualization.
    """

    def __init__(self):
        self.recipe_data = None
        self.brewing_steps = []

    def load_recipe(self, recipe: Dict[str, Any]) -> None:
        """Load a recipe from JSON data."""
        self.recipe_data = recipe
        self.brewing_steps = self._parse_brewing_steps()

    def load_recipe_from_file(self, filepath: str, recipe_index: int = 0) -> None:
        """Load a recipe from a JSONL file."""
        import re

        with open(filepath, 'r') as f:
            content = f.read()

        # Parse JSON objects by counting braces
        recipes = []
        depth = 0
        current_obj = ""

        for char in content:
            if char == '{':
                if depth == 0:
                    current_obj = char
                else:
                    current_obj += char
                depth += 1
            elif char == '}':
                depth -= 1
                current_obj += char
                if depth == 0 and current_obj.strip():
                    try:
                        recipes.append(json.loads(current_obj))
                    except json.JSONDecodeError as e:
                        print(f"Warning: Skipping invalid JSON object: {e}")
                    current_obj = ""
            elif depth > 0:
                current_obj += char

        if recipe_index >= len(recipes):
            raise ValueError(f"Recipe index {recipe_index} out of range (found {len(recipes)} recipes)")
        self.load_recipe(recipes[recipe_index])

    def _parse_brewing_steps(self) -> List[BrewingStep]:
        """Parse the pours data into structured brewing steps."""
        if not self.recipe_data:
            return []

        pours = self.recipe_data['brewing']['pours']
        steps = []
        cumulative_water = 0

        for i, pour in enumerate(pours, 1):
            cumulative_water += pour['water_added']

            # Determine the action type
            if i == 1:
                action = "BLOOM"
            elif i == len(pours):
                action = "FINAL POUR"
            else:
                action = f"POUR #{i}"

            step = BrewingStep(
                step_number=i,
                start_time=pour['start'],
                end_time=pour['end'],
                water_added=pour['water_added'],
                cumulative_water=cumulative_water,
                action=action
            )
            steps.append(step)

        return steps

    def _generate_single_line_timeline_html(self) -> str:
        """Generate a single horizontal timeline with markers at different times."""
        total_time = self.brewing_steps[-1].end_time
        brewing = self.recipe_data['brewing']

        # Calculate positions for each event
        events = []

        # Start event
        events.append({
            'time': 0,
            'position': 0,
            'label': 'START',
            'description': f'Begin brewing',
            'icon': '▶️'
        })

        # Pour events
        for step in self.brewing_steps:
            events.append({
                'time': step.start_time,
                'position': (step.start_time / total_time) * 100,
                'label': f'{step.action}',
                'description': f'Add {step.water_added}ml',
                'icon': '💧'
            })

        # End event
        events.append({
            'time': total_time,
            'position': 100,
            'label': 'FINISH',
            'description': f'Total: {brewing["target_water"]}ml',
            'icon': '✓'
        })

        # Generate event markers HTML
        event_markers = []
        for i, event in enumerate(events):
            # Alternate positions above/below line
            is_above = i % 2 == 0
            marker_class = 'above' if is_above else 'below'

            event_markers.append(f"""
            <div class="timeline-event {marker_class}" style="left: {event['position']:.1f}%;">
                <div class="event-marker"></div>
                <div class="event-label">
                    <div class="event-icon">{event['icon']}</div>
                    <div class="event-time">{event['time']}s</div>
                    <div class="event-name">{event['label']}</div>
                    <div class="event-desc">{event['description']}</div>
                </div>
            </div>
            """)

        return f"""
        <div class="single-line-timeline">
            <h2>⏱️ Timeline Chart</h2>
            <div class="timeline-container">
                <div class="timeline-line"></div>
                {''.join(event_markers)}
            </div>
        </div>
        """

    def _generate_brewing_timeline_html(self) -> str:
        """Generate detailed brewing timeline with steps."""
        total_time = self.brewing_steps[-1].end_time
        target_water = self.recipe_data['brewing']['target_water']

        timeline_items = []
        for step in self.brewing_steps:
            percentage = (step.cumulative_water / target_water) * 100
            duration = step.end_time - step.start_time

            timeline_items.append(f"""
            <div class="timeline-item">
                <div class="timeline-marker">{step.step_number}</div>
                <div class="timeline-content">
                    <div class="timeline-header">
                        <h3>{step.action}</h3>
                        <span class="timeline-time">{step.start_time}s - {step.end_time}s</span>
                    </div>
                    <div class="timeline-details">
                        <p>💧 Add <strong>{step.water_added}ml</strong> water over <strong>{duration}s</strong></p>
                        <p>📊 Progress: <strong>{step.cumulative_water}ml</strong> / {target_water}ml ({percentage:.0f}%)</p>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {percentage}%"></div>
                    </div>
                </div>
            </div>
            """)

        return f"""
        <div class="brewing-timeline">
            <h2>📋 Brewing Timeline</h2>
            {''.join(timeline_items)}
        </div>
        """

    def generate_html_visualization(self, include_mermaid: bool = False) -> str:
        """
        Generate an HTML page with the improved visualization layout.

        Layout (top to bottom):
        1. Parameters (info cards)
        2. Timeline Chart (single line with markers)
        3. Brewing Timeline (detailed steps)
        4. Expected Flavor Notes
        """
        if not self.recipe_data:
            raise ValueError("No recipe loaded")

        brewing = self.recipe_data['brewing']
        bean = self.recipe_data['bean']

        # Generate sections
        single_line_timeline = self._generate_single_line_timeline_html()
        brewing_timeline = self._generate_brewing_timeline_html()

        html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DailyDrip - {bean['name']} Recipe</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #6B4423 0%, #3D2817 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        /* === PARAMETERS SECTION === */
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 50px;
        }}

        .info-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }}

        .info-card h3 {{
            color: #333;
            margin-bottom: 10px;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .info-card .value {{
            font-size: 1.5em;
            color: #667eea;
            font-weight: bold;
        }}

        /* === SINGLE LINE TIMELINE === */
        .single-line-timeline {{
            margin: 40px 0 60px 0;
        }}

        .single-line-timeline h2 {{
            margin-bottom: 40px;
            color: #333;
            font-size: 1.8em;
        }}

        .timeline-container {{
            position: relative;
            height: 250px;
            margin: 40px 20px;
        }}

        .timeline-line {{
            position: absolute;
            top: 50%;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }}

        .timeline-event {{
            position: absolute;
            top: 50%;
            transform: translateX(-50%);
        }}

        .event-marker {{
            position: absolute;
            left: 50%;
            top: 50%;
            width: 16px;
            height: 16px;
            background: white;
            border: 4px solid #667eea;
            border-radius: 50%;
            transform: translate(-50%, -50%);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
            z-index: 2;
            transition: all 0.3s ease;
        }}

        .timeline-event:hover .event-marker {{
            width: 20px;
            height: 20px;
            border-width: 5px;
        }}

        .event-label {{
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            text-align: center;
            white-space: nowrap;
            background: white;
            padding: 12px 18px;
            border-radius: 10px;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
            border: 2px solid #e0e0e0;
            transition: all 0.3s ease;
        }}

        .timeline-event:hover .event-label {{
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
            border-color: #667eea;
        }}

        .timeline-event.above .event-label {{
            bottom: 40px;
        }}

        .timeline-event.below .event-label {{
            top: 40px;
        }}

        .event-icon {{
            font-size: 24px;
            margin-bottom: 5px;
        }}

        .event-time {{
            font-size: 14px;
            color: #667eea;
            font-weight: bold;
            margin-bottom: 3px;
        }}

        .event-name {{
            font-size: 12px;
            color: #333;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 3px;
        }}

        .event-desc {{
            font-size: 11px;
            color: #666;
        }}

        /* === BREWING TIMELINE === */
        .brewing-timeline {{
            margin: 50px 0;
        }}

        .brewing-timeline h2 {{
            margin-bottom: 30px;
            color: #333;
            font-size: 1.8em;
        }}

        .timeline-item {{
            display: flex;
            gap: 20px;
            margin-bottom: 30px;
            position: relative;
        }}

        .timeline-item:not(:last-child)::after {{
            content: '';
            position: absolute;
            left: 19px;
            top: 45px;
            bottom: -30px;
            width: 2px;
            background: #e0e0e0;
        }}

        .timeline-marker {{
            width: 40px;
            height: 40px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            flex-shrink: 0;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.4);
        }}

        .timeline-content {{
            flex: 1;
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 3px solid #667eea;
            transition: all 0.3s ease;
        }}

        .timeline-content:hover {{
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateX(5px);
        }}

        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .timeline-header h3 {{
            color: #333;
            margin: 0;
        }}

        .timeline-time {{
            color: #667eea;
            font-weight: bold;
            font-size: 0.9em;
        }}

        .timeline-details {{
            margin-bottom: 15px;
        }}

        .timeline-details p {{
            margin: 5px 0;
            color: #666;
        }}

        .progress-bar {{
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }}

        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s ease;
        }}

        /* === FLAVOR NOTES === */
        .flavor-notes {{
            margin-top: 50px;
            padding: 30px;
            background: #fff3e0;
            border-radius: 15px;
            border: 2px solid #ffa726;
        }}

        .flavor-notes h3 {{
            color: #e65100;
            margin-bottom: 15px;
            font-size: 1.5em;
        }}

        .flavor-tags {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }}

        .flavor-tag {{
            background: #ff9800;
            color: white;
            padding: 10px 18px;
            border-radius: 20px;
            font-size: 0.95em;
            font-weight: 500;
            transition: all 0.3s ease;
        }}

        .flavor-tag:hover {{
            background: #f57c00;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(255, 152, 0, 0.4);
        }}

        /* === FOOTER === */
        .footer {{
            text-align: center;
            padding: 25px;
            background: #f8f9fa;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }}

        /* === RESPONSIVE === */
        @media (max-width: 768px) {{
            .timeline-container {{
                height: 300px;
                margin: 40px 10px;
            }}

            .event-label {{
                font-size: 0.85em;
                padding: 8px 12px;
            }}

            .header h1 {{
                font-size: 2em;
            }}

            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>☕ {bean['name']}</h1>
            <p class="subtitle">DailyDrip Brewing Recipe</p>
        </div>

        <div class="content">
            <!-- 1. PARAMETERS -->
            <div class="info-grid">
                <div class="info-card">
                    <h3>🌡️ Temperature</h3>
                    <div class="value">{brewing['temperature']}°C</div>
                </div>
                <div class="info-card">
                    <h3>⚙️ Grind Size</h3>
                    <div class="value">{brewing['grinding_size']}</div>
                </div>
                <div class="info-card">
                    <h3>☕ Dose</h3>
                    <div class="value">{brewing['dose']}g</div>
                </div>
                <div class="info-card">
                    <h3>💧 Water</h3>
                    <div class="value">{brewing['target_water']}ml</div>
                </div>
                <div class="info-card">
                    <h3>📊 Ratio</h3>
                    <div class="value">1:{brewing['target_water']/brewing['dose']:.1f}</div>
                </div>
                <div class="info-card">
                    <h3>🔧 Brewer</h3>
                    <div class="value">{brewing['brewer']}</div>
                </div>
            </div>

            <!-- 2. TIMELINE CHART (Single Line) -->
            {single_line_timeline}

            <!-- 3. BREWING TIMELINE (Detailed Steps) -->
            {brewing_timeline}

            <!-- 4. EXPECTED FLAVOR NOTES -->
            <div class="flavor-notes">
                <h3>🌸 Expected Flavor Notes</h3>
                <div class="flavor-tags">
                    {''.join([f'<span class="flavor-tag">{note}</span>' for note in bean['flavor_notes']])}
                </div>
            </div>
        </div>

        <div class="footer">
            Generated by DailyDrip Visualization Agent | {datetime.now().strftime("%Y-%m-%d %H:%M")}
        </div>
    </div>
</body>
</html>
        """

        return html

    def generate_mermaid_flowchart(self) -> str:
        """Generate a Mermaid flowchart diagram."""
        if not self.recipe_data:
            raise ValueError("No recipe loaded")

        brewing = self.recipe_data['brewing']
        bean = self.recipe_data['bean']

        lines = [
            "flowchart TD",
            f"    START([\"☕ START BREWING<br/>{bean['name']}\"])",
            "    ",
            "    %% Setup Phase",
            f"    SETUP[\"⚙️ SETUP<br/>━━━━━━━━━━<br/>Grind: {brewing['grinding_size']} clicks<br/>Dose: {brewing['dose']}g coffee<br/>Water temp: {brewing['temperature']}°C<br/>Brewer: {brewing['brewer']}\"]",
            "    ",
            "    START --> SETUP"
        ]

        prev_node = "SETUP"
        for step in self.brewing_steps:
            node_id = f"STEP{step.step_number}"
            duration = step.end_time - step.start_time

            lines.append("    ")
            lines.append(f"    {node_id}[\"🌊 {step.action}<br/>━━━━━━━━━━<br/>Time: {step.start_time}s - {step.end_time}s ({duration}s)<br/>Add: {step.water_added}ml water<br/>Total: {step.cumulative_water}ml\"]")

            if step.step_number == 1:
                lines.append(f"    {prev_node} --> |Begin brewing| {node_id}")
            else:
                lines.append(f"    {prev_node} --> |Wait & pour| {node_id}")

            prev_node = node_id

        lines.append("    ")
        lines.append(f"    FINISH([\"✓ COMPLETE<br/>Total water: {brewing['target_water']}ml<br/>Ratio: 1:{brewing['target_water']/brewing['dose']:.1f}\"])")
        lines.append(f"    {prev_node} --> |Brewing complete| FINISH")

        lines.extend([
            "    ",
            "    %% Styling",
            "    classDef startEnd fill:#e1f5e1,stroke:#4caf50,stroke-width:3px",
            "    classDef setup fill:#e3f2fd,stroke:#2196f3,stroke-width:2px",
            "    classDef pour fill:#fff3e0,stroke:#ff9800,stroke-width:2px",
            "    ",
            "    class START,FINISH startEnd",
            "    class SETUP setup",
        ])

        pour_classes = [f"STEP{i}" for i in range(1, len(self.brewing_steps) + 1)]
        lines.append(f"    class {','.join(pour_classes)} pour")

        return "\n".join(lines)

    def generate_ascii_flowchart(self) -> str:
        """Generate a simple ASCII text flowchart."""
        if not self.recipe_data:
            raise ValueError("No recipe loaded")

        brewing = self.recipe_data['brewing']
        bean = self.recipe_data['bean']

        lines = []

        def box(text: str, char: str = "═") -> List[str]:
            """Create a box with text."""
            text_lines = text.split('\n')
            max_len = max(len(line) for line in text_lines)
            result = []
            result.append("╔" + char * (max_len + 2) + "╗")
            for line in text_lines:
                result.append("║ " + line.ljust(max_len) + " ║")
            result.append("╚" + char * (max_len + 2) + "╝")
            return result

        def arrow() -> str:
            return "          ↓"

        # Title
        lines.extend(box(f"☕ COFFEE BREWING RECIPE\n{bean['name']}", "═"))
        lines.append(arrow())

        # Setup
        setup_text = f"""⚙️  SETUP
Grind Size: {brewing['grinding_size']} clicks
Coffee Dose: {brewing['dose']}g
Water Temp: {brewing['temperature']}°C
Brewer: {brewing['brewer']}
Target Water: {brewing['target_water']}ml
Ratio: 1:{brewing['target_water']/brewing['dose']:.1f}"""
        lines.extend(box(setup_text, "─"))
        lines.append(arrow())

        # Each pour step
        for step in self.brewing_steps:
            duration = step.end_time - step.start_time
            step_text = f"""🌊 {step.action}
Time: {step.start_time}s → {step.end_time}s (duration: {duration}s)
Water: {step.water_added}ml
Cumulative: {step.cumulative_water}ml / {brewing['target_water']}ml"""
            lines.extend(box(step_text, "─"))
            lines.append(arrow())

        # Finish
        finish_text = f"""✓ BREWING COMPLETE
Total Water: {brewing['target_water']}ml
Total Time: {self.brewing_steps[-1].end_time}s (~{self.brewing_steps[-1].end_time//60}m {self.brewing_steps[-1].end_time%60}s)
Expected Yield: ~{brewing['target_water'] - brewing['dose']*2}ml"""
        lines.extend(box(finish_text, "═"))

        return "\n".join(lines)

    def save_visualization(self, output_path: str, format: str = 'html') -> None:
        """Save the visualization to a file."""
        if format == 'html':
            content = self.generate_html_visualization()
        elif format == 'mermaid':
            content = self.generate_mermaid_flowchart()
        elif format == 'ascii':
            content = self.generate_ascii_flowchart()
        else:
            raise ValueError(f"Unsupported format: {format}")

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✓ Visualization saved to: {output_path}")

    def get_recipe_summary(self) -> Dict[str, Any]:
        """Get a summary of the loaded recipe."""
        if not self.recipe_data:
            raise ValueError("No recipe loaded")

        brewing = self.recipe_data['brewing']
        bean = self.recipe_data['bean']

        return {
            'bean_name': bean['name'],
            'brewer': brewing['brewer'],
            'total_time': self.brewing_steps[-1].end_time if self.brewing_steps else 0,
            'total_water': brewing['target_water'],
            'coffee_dose': brewing['dose'],
            'ratio': f"1:{brewing['target_water']/brewing['dose']:.1f}",
            'num_pours': len(self.brewing_steps),
            'temperature': brewing['temperature'],
            'grind_size': brewing['grinding_size']
        }


def main():
    """Example usage."""
    agent = CoffeeBrewVisualizationAgent()
    agent.load_recipe_from_file('coffee_brew_logs.jsonl', recipe_index=0)

    summary = agent.get_recipe_summary()
    print(f"\n{'='*60}")
    print(f"Recipe Summary: {summary['bean_name']}")
    print(f"{'='*60}")
    for key, value in summary.items():
        if key != 'bean_name':
            print(f"{key.replace('_', ' ').title()}: {value}")
    print(f"{'='*60}\n")

    print(agent.generate_ascii_flowchart())
    print("\n")

    agent.save_visualization('brew_recipe_v2.html', format='html')
    print("\n✓ Visualization generated!")


if __name__ == "__main__":
    main()
