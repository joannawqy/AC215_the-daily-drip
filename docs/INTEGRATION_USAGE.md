# DailyDrip - Integrated System Usage Guide

## Overview

The integrated system connects two agents:
1. **Core Agent** (`agent_core/agent.py`) - Generates personalized coffee brewing recipes
2. **Visualization Agent V2** (`agent_core/visualization_agent_v2.py`) - Creates beautiful visualizations

The **Integrated Agent** (`agent_core/integrated_agent.py`) combines both into a single workflow.

---

## Quick Start

### Method 1: Use the Integrated Agent (Recommended)

```bash
# Generate recipe and visualization in one command
python -m agent_core.integrated_agent \
  --bean demo_bean.json \
  --brewer V60 \
  --output-dir ./my_recipe \
  --show-ascii
```

This will:
- Load bean information from `demo_bean.json`
- Query RAG for similar recipes (if available)
- Generate a personalized recipe using OpenAI
- Create HTML, Mermaid, and ASCII visualizations
- Save everything to `./my_recipe/` directory

### Method 2: Manual Two-Step Process

**Step 1: Generate Recipe**
```bash
python -m agent_core.agent \
  --bean demo_bean.json \
  --brewer V60 \
  --output generated_recipe.json
```

**Step 2: Visualize Recipe**
```python
from agent_core.visualization_agent_v2 import CoffeeBrewVisualizationAgent
import json

# Load the generated recipe
with open('generated_recipe.json', 'r') as f:
    recipe = json.load(f)

# Add bean info (if not already in recipe)
with open('demo_bean.json', 'r') as f:
    bean_info = json.load(f)

complete_recipe = {
    "bean": bean_info,
    "brewing": recipe["brewing"],
    "evaluation": None
}

# Generate visualization
agent = CoffeeBrewVisualizationAgent()
agent.load_recipe(complete_recipe)
agent.save_visualization('my_recipe.html', format='html')
```

---

## Integrated Agent Options

### Basic Usage

```bash
python -m agent_core.integrated_agent --bean BEAN_FILE --brewer BREWER_NAME
```

### All Options

| Option | Description | Example |
|--------|-------------|---------|
| `--bean` | Path to bean JSON file or JSON string | `--bean demo_bean.json` |
| `--brewer` | Brewer name | `--brewer V60` |
| `--note` | Custom brewing instruction | `--note "I prefer lighter body"` |
| `--model` | OpenAI model | `--model gpt-4o-mini` |
| `--output-dir` | Directory to save outputs | `--output-dir ./outputs` |
| `--formats` | Visualization formats | `--formats html mermaid` |
| `--no-rag` | Disable RAG retrieval | `--no-rag` |
| `--rag-k` | Number of reference recipes | `--rag-k 5` |
| `--show-ascii` | Print ASCII to console | `--show-ascii` |

### Complete Example

```bash
python -m agent_core.integrated_agent \
  --bean demo_bean.json \
  --brewer Origami \
  --note "I want a sweeter cup with medium body" \
  --model gpt-4o-mini \
  --output-dir ./my_ethiopian_recipe \
  --formats html mermaid ascii \
  --rag-k 3 \
  --show-ascii
```

---

## Programming API

### Using Integrated Agent in Python

```python
from agent_core.integrated_agent import IntegratedCoffeeAgent
from pathlib import Path

# Create agent
agent = IntegratedCoffeeAgent(
    rag_enabled=True,
    rag_k=3
)

# Generate recipe and visualizations
result = agent.generate_and_visualize(
    bean_source="demo_bean.json",
    brewer="V60",
    custom_note="I prefer bright acidity",
    output_dir=Path("./my_recipe"),
    output_formats=["html", "mermaid", "ascii"],
    model="gpt-4o-mini"
)

# Access results
recipe = result["recipe"]
visualizations = result["visualizations"]
summary = result["summary"]

print(f"Recipe for {summary['bean_name']}:")
print(f"  Dose: {summary['coffee_dose']}g")
print(f"  Water: {summary['total_water']}ml")
print(f"  Time: {summary['total_time']}s")

# HTML is saved to file and also available in result
html_content = visualizations["html"]
```

### Using Only Recipe Generation

```python
from agent_core.integrated_agent import IntegratedCoffeeAgent
import json

agent = IntegratedCoffeeAgent()

# Load bean info
with open('demo_bean.json', 'r') as f:
    bean_info = json.load(f)

# Generate recipe only
recipe = agent.generate_complete_recipe(
    bean_info=bean_info,
    brewer="V60",
    custom_note="Medium grind, please"
)

print(json.dumps(recipe, indent=2))
```

### Using Only Visualization

```python
from agent_core.visualization_agent_v2 import CoffeeBrewVisualizationAgent

# Prepare complete recipe (with bean, brewing, evaluation)
recipe = {
    "bean": {
        "name": "Colombia Huila",
        "flavor_notes": ["caramel", "chocolate", "nutty"]
        # ... other bean fields
    },
    "brewing": {
        "brewer": "V60",
        "temperature": 92,
        "grinding_size": 20,
        "dose": 15,
        "target_water": 240,
        "pours": [
            {"start": 0, "end": 30, "water_added": 50},
            {"start": 30, "end": 80, "water_added": 90},
            {"start": 80, "end": 130, "water_added": 100}
        ]
    },
    "evaluation": None
}

# Generate visualization
agent = CoffeeBrewVisualizationAgent()
agent.load_recipe(recipe)
agent.save_visualization('colombia.html', format='html')
```

---

## Environment Setup

### Requirements

1. **Python 3.7+**
2. **OpenAI API Key** (for recipe generation)
3. **ChromaDB** (optional, for RAG retrieval)

### Setup Steps

1. **Set OpenAI API Key**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

2. **Install Dependencies** (if using RAG)
   ```bash
   pip install openai chromadb sentence-transformers
   ```

3. **Visualization Agent** (No dependencies!)
   - `visualization_agent_v2.py` uses only Python standard library

### Verify Setup

```bash
# Test visualization only (no API key needed)
python visualization_agent_v2.py

# Test full integration (requires API key)
python -m agent_core.integrated_agent --bean demo_bean.json --brewer V60 --no-rag
```

---

## File Outputs

When you run the integrated agent with `--output-dir ./my_recipe`, you'll get:

```
my_recipe/
├── Ethiopia_Sidamo_Natural_recipe.json     # Recipe JSON
├── Ethiopia_Sidamo_Natural_visualization.html   # HTML visualization
├── Ethiopia_Sidamo_Natural_visualization.md     # Mermaid diagram
└── Ethiopia_Sidamo_Natural_visualization.txt    # ASCII art
```

---
