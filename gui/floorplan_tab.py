"""Floorplan tab for visual room and seat management.

Provides a canvas-based interface for editing room layouts and seat positions with drag-and-drop support.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import logging
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PIL import Image, ImageTk

from config import (
    UI_TEXTS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_LIGHT,
    COLOR_FREE, COLOR_OCCUPIED, COLOR_CONFLICT,
    DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, DEFAULT_SEAT_SIZE,
    ASSETS_DIR, FLOORPLAN_IMAGE, MODE_SELECT, MODE_DRAW_ROOM
)
from data.data_manager import DataManager
from data.undo_manager import UndoManager

logger = logging.getLogger(__name__)


class FloorplanTab:
    """Tab for visualizing and editing the classroom floorplan."""

    def __init__(
        self,
        parent: tk.Frame,
        data_manager: DataManager,
        undo_manager: UndoManager,
        main_window: Any
    ) -> None:
        """Initialize the FloorplanTab.

        Args:
            parent: Parent frame
            data_manager: Data manager instance
            undo_manager: Undo manager instance
            main_window: Reference to main window for callbacks
        """
        self.parent = parent
        self.data_manager = data_manager
        self.undo_manager = undo_manager
        self.main_window = main_window

        # Canvas state
        self.canvas: Optional[tk.Canvas] = None
        self.selected_object: Optional[Dict[str, Any]] = None
        self.drag_start: Optional[Tuple[float, float]] = None
        self.preview_rect: Optional[int] = None  # Canvas item ID for preview rectangle
        self.background_image: Optional[ImageTk.PhotoImage] = None  # Background image

        # Editing mode
        self.current_mode = MODE_SELECT
        self.mode_button: Optional[tk.Button] = None

        # Create GUI
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the tab widgets."""
        # Toolbar frame with improved styling
        toolbar = tk.Frame(self.parent, bg=COLOR_PRIMARY, height=50)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)
        toolbar.pack_propagate(False)

        # Toolbar buttons with improved styling for macOS compatibility
        button_style = {
            "bg": COLOR_ACCENT,
            "fg": "white",
            "font": ("Helvetica", 11, "bold"),
            "relief": tk.RAISED,
            "bd": 1,
            "activebackground": "#b5181b",
            "activeforeground": "white",
            "padx": 12,
            "pady": 8,
            "highlightthickness": 0
        }

        mode_button_style = {
            "bg": COLOR_PRIMARY,
            "fg": "white",
            "font": ("Helvetica", 11, "bold"),
            "relief": tk.SUNKEN,
            "bd": 2,
            "activebackground": COLOR_ACCENT,
            "activeforeground": "white",
            "padx": 12,
            "pady": 8,
            "highlightthickness": 0
        }

        # Mode toggle button
        self.mode_button = tk.Button(
            toolbar, text=UI_TEXTS["select_mode"],
            command=self._toggle_mode, **mode_button_style
        )
        self.mode_button.pack(side=tk.LEFT, padx=5, pady=5)

        # Separator
        sep1 = tk.Frame(toolbar, bg="white", width=2, height=30)
        sep1.pack(side=tk.LEFT, padx=5, pady=10)

        add_room_btn = tk.Button(
            toolbar, text=UI_TEXTS["add_room"],
            command=self._add_room, **button_style
        )
        add_room_btn.pack(side=tk.LEFT, padx=5, pady=5)

        add_seat_btn = tk.Button(
            toolbar, text=UI_TEXTS["add_seat"],
            command=self._add_seat, **button_style
        )
        add_seat_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Canvas frame with minimal padding
        canvas_frame = tk.Frame(self.parent, bg=COLOR_LIGHT)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)

        # Canvas with white background for drawing
        self.canvas = tk.Canvas(
            canvas_frame,
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            bg="white",
            cursor="arrow",
            highlightthickness=0
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)
        self.canvas.bind("<Motion>", self._on_canvas_motion)

        self.refresh()

    def _toggle_mode(self) -> None:
        """Toggle between Select and Draw Room modes."""
        if self.current_mode == MODE_SELECT:
            self.current_mode = MODE_DRAW_ROOM
            self.mode_button.config(text=UI_TEXTS["draw_room_mode"], bg=COLOR_ACCENT)
            if self.canvas:
                self.canvas.config(cursor="crosshair")
            self.main_window._update_status("Mode: Raum zeichnen")
            logger.info("Switched to Draw Room mode")
        else:
            self.current_mode = MODE_SELECT
            self.mode_button.config(text=UI_TEXTS["select_mode"], bg=COLOR_PRIMARY)
            if self.canvas:
                self.canvas.config(cursor="arrow")
            self.main_window._update_status("Mode: Auswählen")
            logger.info("Switched to Select mode")

    def _add_room(self) -> None:
        """Add a new room to the floorplan."""
        room_name = simpledialog.askstring("New Room", "Enter room name:")
        if room_name:
            try:
                data = self.data_manager.get_data()
                rooms = data.get("floorplan", {}).get("rooms", [])

                new_room = {
                    "id": f"room_{len(rooms) + 1}",
                    "name": room_name,
                    "x": 50,
                    "y": 50,
                    "width": 300,
                    "height": 200
                }

                rooms.append(new_room)
                data["floorplan"]["rooms"] = rooms

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data()

                self.refresh()
                self.main_window._update_status(f"Room added: {room_name}")
                logger.info(f"Room added: {room_name}")

            except Exception as e:
                logger.error(f"Error adding room: {e}")
                messagebox.showerror("Error", f"Failed to add room: {e}")

    def _add_seat(self) -> None:
        """Add a new seat to the floorplan."""
        room_id = simpledialog.askstring("Add Seat", "Enter room ID:")
        if room_id:
            seat_number = simpledialog.askinteger("Seat Number", "Enter seat number:")
            if seat_number:
                try:
                    data = self.data_manager.get_data()
                    seats = data.get("floorplan", {}).get("seats", [])

                    new_seat = {
                        "id": f"seat_{len(seats) + 1}",
                        "number": seat_number,
                        "room_id": room_id,
                        "x": 100,
                        "y": 100
                    }

                    seats.append(new_seat)
                    data["floorplan"]["seats"] = seats

                    # Save state for undo
                    self.undo_manager.push_state(data)
                    self.data_manager.save_data()

                    self.refresh()
                    self.main_window._update_status(f"Seat {seat_number} added")
                    logger.info(f"Seat {seat_number} added to room {room_id}")

                except Exception as e:
                    logger.error(f"Error adding seat: {e}")
                    messagebox.showerror("Error", f"Failed to add seat: {e}")

    def _on_canvas_click(self, event: tk.Event) -> None:
        """Handle canvas click event.

        Args:
            event: Click event
        """
        if self.current_mode == MODE_DRAW_ROOM:
            # In draw mode, just record start position for rectangle
            self.drag_start = (event.x, event.y)
        else:
            # In select mode, select object at click position
            self.drag_start = (event.x, event.y)
            self.selected_object = self._get_object_at(event.x, event.y)

    def _on_canvas_drag(self, event: tk.Event) -> None:
        """Handle canvas drag event.

        Args:
            event: Drag event
        """
        if self.current_mode == MODE_DRAW_ROOM and self.drag_start:
            # In draw mode, draw preview rectangle
            if self.preview_rect:
                self.canvas.delete(self.preview_rect)

            x1, y1 = self.drag_start
            x2, y2 = event.x, event.y

            # Ensure x1 < x2 and y1 < y2
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            # Draw preview rectangle with dashed outline
            self.preview_rect = self.canvas.create_rectangle(
                x1, y1, x2, y2,
                fill="", outline=COLOR_ACCENT, width=2, dash=(4, 4)
            )
        elif self.current_mode == MODE_SELECT and self.selected_object and self.drag_start:
            # In select mode, move object
            dx = event.x - self.drag_start[0]
            dy = event.y - self.drag_start[1]

            self.selected_object["x"] += dx
            self.selected_object["y"] += dy

            self.drag_start = (event.x, event.y)
            self.refresh()

    def _on_canvas_release(self, event: tk.Event) -> None:
        """Handle canvas release event.

        Args:
            event: Release event
        """
        # Remove preview rectangle if it exists
        if self.preview_rect:
            self.canvas.delete(self.preview_rect)
            self.preview_rect = None

        if self.current_mode == MODE_DRAW_ROOM and self.drag_start:
            # Create new room from drawn rectangle
            x1, y1 = self.drag_start
            x2, y2 = event.x, event.y

            # Normalize coordinates
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)

            # Minimum size check
            width = x2 - x1
            height = y2 - y1

            if width > 30 and height > 30:  # Minimum room size
                room_name = simpledialog.askstring(
                    "Neuer Raum",
                    "Raumname eingeben:"
                )
                if room_name:
                    try:
                        data = self.data_manager.get_data()
                        rooms = data.get("floorplan", {}).get("rooms", [])

                        new_room = {
                            "id": f"room_{len(rooms) + 1}",
                            "name": room_name,
                            "x": x1,
                            "y": y1,
                            "width": width,
                            "height": height
                        }

                        rooms.append(new_room)
                        data["floorplan"]["rooms"] = rooms

                        # Save state for undo
                        self.undo_manager.push_state(data)
                        self.data_manager.save_data()

                        self.refresh()
                        self.main_window._update_status(f"Raum hinzugefügt: {room_name}")
                        logger.info(f"Room created via drag: {room_name}")

                    except Exception as e:
                        logger.error(f"Error creating room: {e}")
                        messagebox.showerror("Fehler", f"Fehler beim Erstellen des Raums: {e}")
            else:
                messagebox.showinfo(
                    "Zu klein",
                    "Bitte einen größeren Bereich für den Raum zeichnen"
                )
        elif self.current_mode == MODE_SELECT and self.selected_object and self.drag_start:
            # Save position changes for moved object
            try:
                data = self.data_manager.get_data()
                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data()
                self.main_window._update_status("Objekt verschoben")
            except Exception as e:
                logger.error(f"Error saving position: {e}")
                messagebox.showerror("Fehler", f"Fehler beim Speichern: {e}")

        self.selected_object = None
        self.drag_start = None

    def _on_canvas_motion(self, event: tk.Event) -> None:
        """Handle canvas mouse motion event.

        Args:
            event: Motion event
        """
        # Update cursor based on mode
        if self.current_mode == MODE_DRAW_ROOM:
            self.canvas.config(cursor="crosshair")
        else:
            # Check if hovering over an object
            obj = self._get_object_at(event.x, event.y)
            if obj:
                self.canvas.config(cursor="hand2")
            else:
                self.canvas.config(cursor="arrow")

    def _on_canvas_right_click(self, event: tk.Event) -> None:
        """Handle canvas right-click event for context menu.

        Args:
            event: Right-click event
        """
        obj = self._get_object_at(event.x, event.y)
        if obj:
            context_menu = tk.Menu(self.canvas, tearoff=0)
            context_menu.add_command(label="Delete", command=lambda: self._delete_object(obj))
            context_menu.add_command(label="Properties", command=lambda: self._show_properties(obj))
            context_menu.post(event.x_root, event.y_root)

    def _get_object_at(self, x: float, y: float) -> Optional[Dict[str, Any]]:
        """Get the object at the given canvas coordinates.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Object dict or None
        """
        data = self.data_manager.get_data()

        # Check rooms
        rooms = data.get("floorplan", {}).get("rooms", [])
        for room in rooms:
            if (room["x"] <= x <= room["x"] + room["width"] and
                room["y"] <= y <= room["y"] + room["height"]):
                return room

        # Check seats
        seats = data.get("floorplan", {}).get("seats", [])
        for seat in seats:
            if (abs(seat["x"] - x) <= DEFAULT_SEAT_SIZE and
                abs(seat["y"] - y) <= DEFAULT_SEAT_SIZE):
                return seat

        return None

    def _delete_object(self, obj: Dict[str, Any]) -> None:
        """Delete an object from the floorplan.

        Args:
            obj: Object to delete
        """
        if messagebox.askyesno("Delete", f"Delete {obj.get('name', obj.get('number'))}?"):
            try:
                data = self.data_manager.get_data()

                if "name" in obj:  # Room
                    rooms = data.get("floorplan", {}).get("rooms", [])
                    rooms[:] = [r for r in rooms if r["id"] != obj["id"]]
                else:  # Seat
                    seats = data.get("floorplan", {}).get("seats", [])
                    seats[:] = [s for s in seats if s["id"] != obj["id"]]

                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data()

                self.refresh()
                self.main_window._update_status("Object deleted")
                logger.info(f"Object deleted: {obj.get('id')}")

            except Exception as e:
                logger.error(f"Error deleting object: {e}")
                messagebox.showerror("Error", f"Failed to delete object: {e}")

    def _show_properties(self, obj: Dict[str, Any]) -> None:
        """Show properties dialog for an object.

        Args:
            obj: Object to show properties for
        """
        # Placeholder for properties dialog
        messagebox.showinfo("Properties", f"Object ID: {obj.get('id')}\n\nFull properties dialog coming soon")

    def _load_background_image(self) -> None:
        """Load and display the background floorplan image."""
        try:
            # Try to find the image in assets directory first
            image_paths = [
                Path(ASSETS_DIR) / FLOORPLAN_IMAGE,
                Path(FLOORPLAN_IMAGE),  # Fallback to root directory
            ]

            image_path = None
            for path in image_paths:
                if path.exists():
                    image_path = path
                    break

            if image_path:
                # Load image
                img = Image.open(image_path)

                # Get canvas dimensions
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()

                # If canvas not yet drawn, use defaults
                if canvas_width <= 1:
                    canvas_width = DEFAULT_CANVAS_WIDTH
                if canvas_height <= 1:
                    canvas_height = DEFAULT_CANVAS_HEIGHT

                # Scale image to fit canvas while maintaining aspect ratio
                img.thumbnail((canvas_width, canvas_height), Image.Resampling.LANCZOS)

                # Convert to PhotoImage
                self.background_image = ImageTk.PhotoImage(img)

                # Display image on canvas
                self.canvas.create_image(
                    0, 0,
                    image=self.background_image,
                    anchor="nw",
                    tags="background"
                )

                logger.info(f"Background image loaded: {image_path}")
            else:
                logger.debug(f"Background image not found (graceful degradation)")

        except Exception as e:
            logger.warning(f"Could not load background image: {e}")
            # Continue without image - graceful degradation

    def refresh(self) -> None:
        """Refresh the canvas with current data."""
        if not self.canvas:
            return

        self.canvas.delete("all")

        try:
            # Load and display background image
            self._load_background_image()

            data = self.data_manager.get_data()

            # Draw rooms
            rooms = data.get("floorplan", {}).get("rooms", [])
            for room in rooms:
                self.canvas.create_rectangle(
                    room["x"], room["y"],
                    room["x"] + room["width"], room["y"] + room["height"],
                    fill=COLOR_LIGHT, outline=COLOR_PRIMARY, width=2,
                    tags="room"
                )
                self.canvas.create_text(
                    room["x"] + 5, room["y"] + 5,
                    text=room.get("name", "Unknown"),
                    anchor="nw", font=("Arial", 10, "bold"),
                    tags="room_text"
                )

            # Draw seats
            seats = data.get("floorplan", {}).get("seats", [])
            for seat in seats:
                self.canvas.create_oval(
                    seat["x"] - DEFAULT_SEAT_SIZE,
                    seat["y"] - DEFAULT_SEAT_SIZE,
                    seat["x"] + DEFAULT_SEAT_SIZE,
                    seat["y"] + DEFAULT_SEAT_SIZE,
                    fill=COLOR_FREE, outline=COLOR_PRIMARY, width=1,
                    tags="seat"
                )
                self.canvas.create_text(
                    seat["x"], seat["y"],
                    text=str(seat.get("number", "?")),
                    font=("Arial", 8, "bold"),
                    tags="seat_text"
                )

        except Exception as e:
            logger.error(f"Error refreshing canvas: {e}")
