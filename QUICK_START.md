# DailyDrip - Quick Start Guide

## 🚀 Get Started in 2 Minutes

### Step 1: View the New Visualization

```bash
cd "/Users/liyiwen/Desktop/215 agent"
open brew_recipe_v2.html
```

You'll see:
- ✅ Recipe parameters at top
- ✅ **NEW!** Single-line timeline chart
- ✅ Detailed brewing steps
- ✅ Flavor notes

### Step 2: Try the Integrated System

**Option A: Visualization Only (No API Key Needed)**
```bash
python visualization_agent_v2.py
```

**Option B: Full Integration (Requires OpenAI API Key)**
```bash
# Set your API key first
export OPENAI_API_KEY="your-key-here"

# Generate recipe + visualization
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --output-dir ./my_recipe \
  --no-rag
```

---

## 📁 Key Files

### Your Two Questions Answered

| File | Purpose |
|------|---------|
| **ANSWERS_TO_YOUR_QUESTIONS.md** | Direct answers to your questions |
| **integrated_agent.py** | Connects core + visualization agents |
| **visualization_agent_v2.py** | New visualization with timeline chart |

### Documentation

| File | What's Inside |
|------|---------------|
| **INTEGRATION_USAGE.md** | Complete usage guide with examples |
| **README.md** | Original visualization docs |
| **INTEGRATION_GUIDE.md** | Advanced integration patterns |

### Test Files

| File | Purpose |
|------|---------|
| **demo_bean.json** | Sample bean data for testing |
| **brew_recipe_v2.html** | Example new visualization |

---

## 🎯 Quick Commands

### Generate Recipe + Visualization

```bash
# Basic usage
python integrated_agent.py --bean demo_bean.json --brewer V60

# With custom note
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --note "I prefer sweeter flavor"

# Save to directory
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer Origami \
  --output-dir ./my_recipes/ethiopia_001

# Show ASCII preview
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --show-ascii
```

### Visualize Existing Recipe

```python
from visualization_agent_v2 import CoffeeBrewVisualizationAgent

agent = CoffeeBrewVisualizationAgent()
agent.load_recipe_from_file('coffee_brew_logs.jsonl', 0)
agent.save_visualization('output.html', format='html')
```

---

## 🔄 Workflow Comparison

### Before (Manual)

```
1. Run core agent → Get recipe JSON
2. Manually format bean + recipe
3. Run visualization agent
4. Open HTML file
```

### After (Integrated)

```
One command:
python integrated_agent.py --bean X --brewer Y
   ↓
Everything done!
```

---

## 📊 What's New in V2

### Timeline Visualization

**OLD (V1):** Only had detailed vertical timeline

**NEW (V2):** Added horizontal single-line timeline

```
        ▶️ START      💧 BLOOM     💧 POUR      ✓ FINISH
           0s           30s          70s          120s
           ●────────────●───────────●────────────●
```

### Layout Order (Top to Bottom)

1. ✅ **Parameters** - Recipe info cards
2. 🆕 **Timeline Chart** - Single horizontal line with markers
3. ✅ **Brewing Timeline** - Detailed step-by-step instructions
4. ✅ **Expected Flavor** - Flavor note tags

---

## 🔧 Troubleshooting

### "OPENAI_API_KEY is not set"

```bash
export OPENAI_API_KEY="sk-your-key-here"
```

### "chromadb is not installed"

```bash
# Option 1: Disable RAG
python integrated_agent.py --bean X --brewer Y --no-rag

# Option 2: Install ChromaDB
pip install chromadb sentence-transformers
```

### "RAG persist directory not found"

```bash
# Just disable RAG for now
python integrated_agent.py --bean X --brewer Y --no-rag
```

---

## 💡 Pro Tips

### 1. Save Your Recipes

```bash
python integrated_agent.py \
  --bean demo_bean.json \
  --brewer V60 \
  --output-dir "./recipes/$(date +%Y%m%d)_ethiopia"
```

### 2. Custom Instructions

```bash
--note "Use 16g dose, emphasize sweetness, medium body"
```

### 3. Batch Processing

```python
from integrated_agent import IntegratedCoffeeAgent

agent = IntegratedCoffeeAgent()
for bean_file in ["bean1.json", "bean2.json", "bean3.json"]:
    agent.generate_and_visualize(
        bean_source=bean_file,
        brewer="V60",
        output_dir=f"./outputs/{bean_file.stem}"
    )
```

### 4. Use in Your App

```python
from integrated_agent import IntegratedCoffeeAgent

agent = IntegratedCoffeeAgent()
result = agent.generate_and_visualize(
    bean_source=bean_data,
    brewer="V60"
)

html = result["visualizations"]["html"]
# Display html in your app
```

---

## 📝 File Structure

```
215 agent/
├── agent.py                    # Your core agent
├── integrated_agent.py         # 🆕 Connects both agents
├── visualization_agent_v2.py   # 🆕 New visualization
├── visualization_agent.py      # Original (still works)
│
├── ANSWERS_TO_YOUR_QUESTIONS.md   # 🆕 Read this first!
├── INTEGRATION_USAGE.md           # 🆕 Complete guide
├── QUICK_START.md                 # 🆕 This file
│
├── demo_bean.json              # 🆕 Test data
├── brew_recipe_v2.html         # 🆕 Example output
│
├── coffee_brew_logs.jsonl      # Your training data
├── README.md                   # Original docs
└── ...
```

---

## 🎓 Learning Path

1. **Read:** [ANSWERS_TO_YOUR_QUESTIONS.md](file:///Users/liyiwen/Desktop/215%20agent/ANSWERS_TO_YOUR_QUESTIONS.md)
   - Direct answers to your two questions

2. **Try:** Open `brew_recipe_v2.html` in browser
   - See the new timeline visualization

3. **Test:** Run the visualization agent
   ```bash
   python visualization_agent_v2.py
   ```

4. **Explore:** Read [INTEGRATION_USAGE.md](file:///Users/liyiwen/Desktop/215%20agent/INTEGRATION_USAGE.md)
   - Complete examples and API docs

5. **Integrate:** Use `integrated_agent.py` in your project
   - CLI or Python API

---

## 📞 Need Help?

### For Your Questions
- See: **ANSWERS_TO_YOUR_QUESTIONS.md** ⭐

### For Usage Examples
- See: **INTEGRATION_USAGE.md**

### For Original Visualization
- See: **README.md**

### For Advanced Integration
- See: **INTEGRATION_GUIDE.md**

---

## ✅ Checklist

- [ ] Viewed `brew_recipe_v2.html` in browser
- [ ] Ran `python visualization_agent_v2.py`
- [ ] Read `ANSWERS_TO_YOUR_QUESTIONS.md`
- [ ] Set `OPENAI_API_KEY` environment variable
- [ ] Tested `integrated_agent.py` with `demo_bean.json`
- [ ] Generated a recipe for your own bean
- [ ] Integrated into your project

---

## 🎉 You're Ready!

You now have:
- ✅ Integration with your core agent (`integrated_agent.py`)
- ✅ New visualization with timeline chart (`visualization_agent_v2.py`)
- ✅ Complete documentation
- ✅ Working examples

Start with:
```bash
python integrated_agent.py --bean demo_bean.json --brewer V60 --show-ascii
```

---

*Quick Start Guide | DailyDrip Project | October 2025*
