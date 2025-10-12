# DailyDrip - Integrated System Usage Guide

## Overview

The integrated system connects two agents:
1. **Core Agent** (`agent.py`) - Generates personalized coffee brewing recipes
2. **Visualization Agent V2** (`visualization_agent_v2.py`) - Creates beautiful visualizations

The **Integrated Agent** (`integrated_agent.py`) combines both into a single workflow.

---

## Quick Start

### Method 1: Use the Integrated Agent (Recommended)

```bash
# Generate recipe and visualization in one command
python integrated_agent.py \
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
python agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --output generated_recipe.json
```

**Step 2: Visualize Recipe**
```python
from visualization_agent_v2 import CoffeeBrewVisualizationAgent
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
python integrated_agent.py --bean BEAN_FILE --brewer BREWER_NAME
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
python integrated_agent.py \
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
from integrated_agent import IntegratedCoffeeAgent
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
from integrated_agent import IntegratedCoffeeAgent
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
from visualization_agent_v2 import CoffeeBrewVisualizationAgent

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

## New Visualization Features (V2)

### Layout Structure

The new HTML visualization has 4 sections in order:

1. **Parameters** (Top)
   - Temperature, grind size, dose, water, ratio, brewer
   - Displayed as cards with icons

2. **Timeline Chart** (Single Line)
   - Horizontal timeline showing all events
   - Markers at: START, BLOOM, POUR #2, POUR #3, ..., FINISH
   - Alternating above/below positions
   - Hover effects for interactivity

3. **Brewing Timeline** (Detailed Steps)
   - Step-by-step instructions
   - Progress bars showing water addition
   - Duration and timing information

4. **Expected Flavor Notes** (Bottom)
   - Color-coded flavor tags
   - Hover effects

### Example Output Structure

```
┌─────────────────────────────────────┐
│          RECIPE HEADER              │
│     Ethiopia Sidamo Natural         │
└─────────────────────────────────────┘

┌───────┬───────┬───────┬──────┬──────┐
│ Temp  │ Grind │ Dose  │Water │Ratio │
│ 93°C  │  22   │ 15g   │225ml │1:15.0│
└───────┴───────┴───────┴──────┴──────┘

════ Timeline Chart ════
           💧          💧         ✓
    ▶️ ────●────────●──────●─────●
   START  0s       30s    70s  120s
          BLOOM   POUR#2  FINAL

════ Brewing Timeline ════
 ① BLOOM          (0s - 30s)
    Add 50ml → Progress: 50/225ml
 ② POUR #2        (30s - 70s)
    Add 75ml → Progress: 125/225ml
 ③ FINAL POUR     (70s - 120s)
    Add 100ml → Progress: 225/225ml

════ Flavor Notes ════
🌸 blueberry | strawberry | floral | honey
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
python integrated_agent.py --bean demo_bean.json --brewer V60 --no-rag
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

## Troubleshooting

### Issue: "OPENAI_API_KEY is not set"

**Solution:** Set your API key
```bash
export OPENAI_API_KEY="sk-..."
```

### Issue: "chromadb is not installed"

**Solution 1:** Disable RAG
```bash
python integrated_agent.py --bean demo_bean.json --brewer V60 --no-rag
```

**Solution 2:** Install ChromaDB
```bash
pip install chromadb sentence-transformers
```

### Issue: "RAG persist directory not found"

**Solution:** The RAG database hasn't been created yet. Either:
- Run with `--no-rag` to skip RAG retrieval
- Create the RAG database using your team's ingest script

### Issue: "Recipe validation failed"

**Solution:** The model sometimes generates invalid recipes. Try:
- Running again (model is non-deterministic)
- Adjusting the `--temperature` parameter
- Providing more specific `--note` instructions

---

## Examples

### Example 1: Quick Recipe Generation

```bash
# Simplest usage - uses defaults
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60
```

### Example 2: Save Everything

```bash
# Generate and save all formats
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer Origami \
  --output-dir ./saved_recipes/ethiopia_001 \
  --formats html mermaid ascii
```

### Example 3: Custom Instructions

```bash
# Provide custom brewing preferences
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --note "I prefer 16g dose and want to emphasize sweetness" \
  --output-dir ./custom_recipe
```

### Example 4: Batch Processing

```python
# Process multiple beans
from integrated_agent import IntegratedCoffeeAgent
from pathlib import Path
import json

agent = IntegratedCoffeeAgent()

beans = [
    "ethiopia_bean.json",
    "colombia_bean.json",
    "kenya_bean.json"
]

for bean_file in beans:
    result = agent.generate_and_visualize(
        bean_source=bean_file,
        brewer="V60",
        output_dir=Path(f"./outputs/{bean_file.stem}"),
        output_formats=["html"]
    )
    print(f"✓ Processed {bean_file}")
```

### Example 5: Web API Integration

```python
from flask import Flask, request, jsonify
from integrated_agent import IntegratedCoffeeAgent

app = Flask(__name__)
agent = IntegratedCoffeeAgent()

@app.route('/generate-recipe', methods=['POST'])
def generate_recipe():
    data = request.json

    result = agent.generate_and_visualize(
        bean_source=json.dumps(data['bean']),
        brewer=data['brewer'],
        custom_note=data.get('note'),
        output_formats=['html']
    )

    return jsonify({
        'recipe': result['recipe'],
        'html': result['visualizations']['html'],
        'summary': result['summary']
    })

if __name__ == '__main__':
    app.run(port=5000)
```

---

## Comparison: V1 vs V2 Visualization

### V1 (Original)
- Parameters at top
- Detailed timeline with vertical layout
- Mermaid flowchart (requires internet/CDN)
- Flavor notes at bottom

### V2 (New - Improved)
- Parameters at top ✅ (same)
- **Single-line horizontal timeline** ✅ (NEW!)
- Detailed timeline (moved below single-line)
- Flavor notes at bottom ✅ (same)
- No Mermaid in HTML (cleaner) ✅ (NEW!)

### When to Use Which

- **Use V2** for end-user recipes (cleaner, better timeline)
- **Use V1** if you need Mermaid embedded in HTML
- Both generate standalone Mermaid `.md` files for documentation

---

## Tips & Best Practices

### 1. Bean Information Quality
- Include all flavor_notes for better RAG matching
- Accurate roast_level helps temperature selection
- Recent roasted_days affects extraction parameters

### 2. Custom Notes
- Be specific: "15g dose" vs "smaller dose"
- Mention taste preferences: "bright acidity" or "sweet and smooth"
- Brewer-specific: "slower drawdown" for flat-bottom brewers

### 3. RAG Optimization
- Use `--rag-k 5` for more diverse references
- Disable RAG for experimental beans (`--no-rag`)
- RAG works best with complete bean information

### 4. Output Organization
- Use dated directories: `--output-dir ./recipes/2025-10-10/ethiopia`
- Include bean name in path for easy identification
- Keep recipe JSON for later re-visualization

### 5. Visualization Formats
- **HTML**: Best for sharing, viewing in browser
- **Mermaid**: Best for documentation, GitHub/GitLab
- **ASCII**: Best for terminal, logs, quick preview

---

## Workflow Diagrams

### Full Workflow

```
User Input (Bean + Brewer)
         ↓
   Integrated Agent
         ↓
    ┌────┴────┐
    ↓         ↓
Core Agent  RAG DB
(OpenAI)   (ChromaDB)
    ↓
Generated Recipe JSON
    {
      "brewing": {
        "brewer": "V60",
        "temperature": 93,
        "pours": [...]
      }
    }
         ↓
  Visualization Agent V2
         ↓
    ┌────┼────┐
    ↓    ↓    ↓
  HTML Mermaid ASCII
    ↓
Display to User
```

### Programmatic Usage

```python
# Option A: All-in-One
agent = IntegratedCoffeeAgent()
result = agent.generate_and_visualize(bean, brewer)

# Option B: Step-by-Step
agent = IntegratedCoffeeAgent()
recipe = agent.generate_complete_recipe(bean, brewer)
viz = agent.visualize_recipe(recipe)

# Option C: Manual
from agent import generate_recipe
from visualization_agent_v2 import CoffeeBrewVisualizationAgent

recipe = generate_recipe(bean, brewer)
viz_agent = CoffeeBrewVisualizationAgent()
viz_agent.load_recipe({"bean": bean, "brewing": recipe["brewing"]})
html = viz_agent.generate_html_visualization()
```

---

## Next Steps

1. **Try the integrated agent** with `demo_bean.json`
2. **Open the HTML** visualization in your browser
3. **Experiment with custom notes** to see how the recipe adapts
4. **Integrate into your frontend** using the API examples

For more help, see:
- `README.md` - Original visualization documentation
- `INTEGRATION_GUIDE.md` - Advanced integration patterns
- `QUICK_REFERENCE.md` - Command quick reference

---

*Generated for DailyDrip Project | October 2025*
