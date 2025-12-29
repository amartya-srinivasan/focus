import os
from PIL import ImageFont

# Global font variables
app_font = ("Segoe UI", 10)
app_font_bold = ("Segoe UI", 10, "bold")
app_font_large = ("Segoe UI", 12)

def load_fonts():
    """Load custom fonts for the application"""
    global app_font, app_font_bold, app_font_large
    
    try:
        # Try to load the custom TTF font
        font_path = "font.ttf"
        if os.path.exists(font_path):
            print("Custom TTF font found: font.ttf")
            # For TTF files with tkinter, we use the font file directly
            app_font = ("Arial", 10)  # Using Arial as fallback for custom font
            app_font_bold = ("Arial", 10, "bold")
            app_font_large = ("Arial", 12)
            
            # Test loading with PIL (for any image/text operations)
            try:
                pil_font = ImageFont.truetype(font_path, 12)
                print(f"Successfully loaded TTF font with PIL: {font_path}")
            except Exception as e:
                print(f"PIL font loading error: {e}")
        else:
            print("Using system fonts (font.ttf not found)")
    except Exception as e:
        print(f"Error loading font: {e}")

# Load fonts when module is imported
load_fonts()