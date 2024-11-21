#  Color constants
COLORS = {
    'TEXT_PRIMARY': '#FFFFFF',
    'TEXT_SECONDARY': '#A0A0A0',
    'BUTTON_PRIMARY': '#007AFF',
    'BUTTON_SECONDARY': '#3A3A3C',
    'WINDOW_BG': '#1E1E1E',
    'HEADER_BG': '#2D2D2D'
}

# Font constants
FONTS = {
    'TITLE': {
        'family': 'Inter',
        'size': 16,
        'weight': 'bold'
    },
    'BODY': {
        'family': 'Inter',
        'size': 14,
        'weight': 'normal'
    },
    'BUTTON': {
        'family': 'Inter',
        'size': 12,
        'weight': 'normal'
    },
    'CAPTION': {
        'family': 'Inter',
        'size': 11,
        'weight': 'normal'
    }
}

# Layout spacing configurations
LAYOUT = {
    'PADDING': {
        'HEADER': 12,    
        'WINDOW': 12     
    }
}

# Window style  
def get_window_style():
    return f"""
        QMainWindow {{
            background-color: {COLORS['WINDOW_BG']};
        }}
    """

# Header style
def get_header_style():
    return f"""
        QWidget#header {{
            background-color: {COLORS['HEADER_BG']};
            min-height: 60px;
        }}
    """