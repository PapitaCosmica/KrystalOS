"""
KrystalOS — cli/commands/dev_guide.py
Phase 5: DX Documentation
Provides an interactive CLI guide for Junior Developers on how to 
forge their first widgets.
"""

from rich.console import Console
from rich.markdown import Markdown

console = Console()

GUIDE_MD = """
# 🔷 KrystalOS Developer Guide

Congratulations on starting your journey to build KrystalOS Widgets!
This guide will give you a 30-second crash course on how the ecosystem works.

## 1. 🏗️ The Structure
Every widget lives in the `widgets/` directory.

When you run `krystal make:widget`, we generate three critical files:
- `krystal.json`: The brain. Tells KrystalOS your language, grid size, and color.
- `index.[ext]`: The heart. Your backend logic (Python, PHP, Node) that runs hidden in the background.
- `ui.html`: The face. Rendered safely inside a Web Component (Shadow DOM).

## 2. 📡 The Nervous System (Event Bus)
KrystalOS modules don't talk directly to each other; they broadcast events.
Use the `KrystalBridge` included automatically in your `ui.html`:

**To send data:**
```javascript
Krystal.emit('my_widget:status', { battery: 90 });
```

**To listen to the Core or other Widgets:**
```javascript
Krystal.on('theme:change', (data) => console.log(data));
```

*(Remember to declare your events in `krystal.json`'s `capabilities`!)*

## 3. 🚀 The Launch (Phase 5)
Once your widget is beautiful and ready, share it with the world:
```bash
krystal deploy -w my-widget https://github.com/myuser/my-repo
```
This automatically scaffolds an ecosystem-compliant Git repository for you.
"""

def show_dev_guide() -> None:
    """Print the markdown dev guide."""
    console.print(Markdown(GUIDE_MD))
