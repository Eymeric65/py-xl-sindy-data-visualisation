#!/usr/bin/env python3
"""Display seaborn deep palette with RGB values."""
import matplotlib.pyplot as plt
import seaborn as sns

# Get the deep palette (10 colors)
palette = sns.color_palette("deep", 10)

# Create figure
fig, ax = plt.subplots(figsize=(12, 3))

# Display each color as a patch
for i, color in enumerate(palette):
    # Draw color patch
    ax.add_patch(plt.Rectangle((i, 0), 1, 1, facecolor=color))
    
    # Convert to RGB 0-255
    rgb = tuple(int(c * 255) for c in color)
    
    # Add RGB text below
    ax.text(i + 0.5, -0.2, f"RGB({rgb[0]},{rgb[1]},{rgb[2]})", 
            ha='center', va='top', fontsize=9)

# Set axis properties
ax.set_xlim(0, len(palette))
ax.set_ylim(-0.5, 1)
ax.axis('off')
ax.set_aspect('equal')

plt.title("Seaborn Deep Palette (10 colors)", pad=20)
plt.tight_layout()
plt.show()
