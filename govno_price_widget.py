import tkinter as tk
from PIL import Image, ImageTk
import requests
from datetime import datetime
import time
from typing import Optional, Dict, Any
from threading import Thread
import io
import os
from dataclasses import dataclass


@dataclass
class WidgetConfig:
    """Configuration settings for the price widget."""
    API_URL: str = "https://api.geckoterminal.com/api/v2/networks/ton/pools/EQAf2LUJZMdxSAGhlp-A60AN9bqZeVM994vCOXH05JFo-7dc"
    API_HEADERS: Dict[str, str] = None
    UPDATE_INTERVAL: int = 30  # seconds
    WINDOW_ALPHA: float = 0.85
    LOGO_SIZE: tuple[int, int] = (64, 64)

    def __post_init__(self):
        if self.API_HEADERS is None:
            self.API_HEADERS = {"accept": "application/json"}


class CryptoPriceWidget(tk.Tk):
    """A floating widget that displays cryptocurrency price information."""

    def __init__(self, config: Optional[WidgetConfig] = None):
        super().__init__()
        self.config = config or WidgetConfig()
        self.previous_price: Optional[float] = None
        self.running = True

        self._setup_window()
        self._create_widgets()
        self._bind_events()
        self._position_window()
        self._start_price_updates()

    def _setup_window(self) -> None:
        """Configure the main window properties."""
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', self.config.WINDOW_ALPHA)
        self.configure(bg='black')

        # Main container frames
        self.main_frame = tk.Frame(self, bg='black')
        self.main_frame.pack(padx=5, pady=5)

        self.container = tk.Frame(self.main_frame, bg='black')
        self.container.pack()

        self.text_container = tk.Frame(self.container, bg='black')
        self.text_container.pack(side='left', padx=(5, 0))

    def _create_widgets(self) -> None:
        """Create and configure all UI elements."""
        self._load_logo()
        self._create_price_labels()

    def _load_logo(self) -> None:
        """Load and display the logo image."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            image_path = os.path.join(script_dir, "logo.png")

            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Logo not found at {image_path}")

            image = Image.open(image_path)
            image = image.resize(self.config.LOGO_SIZE,
                                 Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(image)

            self.image_label = tk.Label(
                self.container,
                image=self.photo,
                bg='black'
            )
            self.image_label.pack(side='left')

        except Exception as e:
            print(f"Error loading logo: {e}")

    def _create_price_labels(self) -> None:
        """Create price and percentage change labels."""
        self.price_label = tk.Label(
            self.text_container,
            text="Loading...",
            font=('Consolas', 14, 'bold'),
            fg='white',
            bg='black',
            padx=10,
            pady=2
        )
        self.price_label.pack()

        self.percent_label = tk.Label(
            self.text_container,
            text="",
            font=('Consolas', 12),
            fg='white',
            bg='black',
            padx=10,
            pady=2
        )
        self.percent_label.pack()

    def _bind_events(self) -> None:
        """Bind mouse events for window dragging and closing."""
        for widget in (self.price_label, self.percent_label, self.image_label):
            widget.bind('<Button-1>', self._start_drag)
            widget.bind('<B1-Motion>', self._on_drag)
            widget.bind('<ButtonRelease-1>', self._stop_drag)
            widget.bind('<Button-3>', lambda e: self.quit())

    def _position_window(self) -> None:
        """Position the window in the top-right corner of the screen."""
        self.update_idletasks()
        width = self.winfo_width()
        self.geometry(f'+{self.winfo_screenwidth()-width-20}+20')

    def _start_price_updates(self) -> None:
        """Start the price update thread."""
        self.update_thread = Thread(
            target=self._update_price_loop, daemon=True)
        self.update_thread.start()

    # Window dragging functionality
    def _start_drag(self, event) -> None:
        self.drag_data = {
            'x': event.x_root - self.winfo_x(),
            'y': event.y_root - self.winfo_y()
        }

    def _on_drag(self, event) -> None:
        if hasattr(self, 'drag_data'):
            x = event.x_root - self.drag_data['x']
            y = event.y_root - self.drag_data['y']
            self.geometry(f'+{x}+{y}')

    def _stop_drag(self, event) -> None:
        if hasattr(self, 'drag_data'):
            del self.drag_data

    # Price update functionality
    def _fetch_price_data(self) -> Optional[Dict[str, Any]]:
        """Fetch price data from the API."""
        try:
            response = requests.get(
                self.config.API_URL,
                headers=self.config.API_HEADERS
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    def _update_price_display(self, price: float, change: float) -> None:
        """Update the price and percentage change display."""
        price_color = '#00ff00' if self.previous_price is None or price >= self.previous_price else '#ff0000'
        percent_color = '#00ff00' if change >= 0 else '#ff0000'

        self.price_label.configure(
            text=f"${price:.6f}",
            fg=price_color
        )

        self.percent_label.configure(
            text=f"{'↑' if change >= 0 else '↓'}{abs(change):.2f}%",
            fg=percent_color
        )

        self.previous_price = price

    def _update_price_loop(self) -> None:
        """Main price update loop."""
        while self.running:
            data = self._fetch_price_data()

            if data and "data" in data:
                token_data = data["data"]["attributes"]
                price = float(token_data["base_token_price_usd"])
                change = float(token_data["price_change_percentage"]["h24"])

                self._update_price_display(price, change)

            time.sleep(self.config.UPDATE_INTERVAL)

    def quit(self) -> None:
        """Clean up and close the application."""
        self.running = False
        super().quit()


def main():
    app = CryptoPriceWidget()
    app.mainloop()


if __name__ == "__main__":
    main()
