"""Floorplan tab for visual room and seat management.

Provides a canvas-based interface for editing room layouts and seat positions with drag-and-drop support.
"""

import tkinter as tk
from tkinter import messagebox, simpledialog
import logging
from typing import Optional, Dict, Any, Tuple

from config import (
    UI_TEXTS, COLOR_PRIMARY, COLOR_ACCENT, COLOR_LIGHT,
    COLOR_FREE, COLOR_OCCUPIED, COLOR_CONFLICT,
    DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, DEFAULT_SEAT_SIZE
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

        # Create GUI
        self._create_widgets()

    def _create_widgets(self) -> None:
        """Create the tab widgets."""
        # Toolbar frame
        toolbar = tk.Frame(self.parent, bg=COLOR_PRIMARY, height=40)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=0, pady=0)

        add_room_btn = tk.Button(
            toolbar, text=UI_TEXTS["add_room"],
            command=self._add_room, bg=COLOR_ACCENT, fg="white"
        )
        add_room_btn.pack(side=tk.LEFT, padx=5, pady=5)

        add_seat_btn = tk.Button(
            toolbar, text=UI_TEXTS["add_seat"],
            command=self._add_seat, bg=COLOR_ACCENT, fg="white"
        )
        add_seat_btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Canvas frame
        canvas_frame = tk.Frame(self.parent, bg=COLOR_LIGHT)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            width=DEFAULT_CANVAS_WIDTH,
            height=DEFAULT_CANVAS_HEIGHT,
            bg="white",
            cursor="crosshair"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bind canvas events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_canvas_release)
        self.canvas.bind("<Button-3>", self._on_canvas_right_click)

        self.refresh()

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
        self.drag_start = (event.x, event.y)
        # Select object at click position
        self.selected_object = self._get_object_at(event.x, event.y)

    def _on_canvas_drag(self, event: tk.Event) -> None:
        """Handle canvas drag event.

        Args:
            event: Drag event
        """
        if self.selected_object and self.drag_start:
            # Move object
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
        if self.selected_object and self.drag_start:
            try:
                data = self.data_manager.get_data()
                # Save state for undo
                self.undo_manager.push_state(data)
                self.data_manager.save_data()
                self.main_window._update_status("Object moved")
            except Exception as e:
                logger.error(f"Error saving position: {e}")
                messagebox.showerror("Error", f"Failed to save position: {e}")

        self.selected_object = None
        self.drag_start = None

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

    def refresh(self) -> None:
        """Refresh the canvas with current data."""
        if not self.canvas:
            return

        self.canvas.delete("all")

        try:
            data = self.data_manager.get_data()

            # Draw rooms
            rooms = data.get("floorplan", {}).get("rooms", [])
            for room in rooms:
                self.canvas.create_rectangle(
                    room["x"], room["y"],
                    room["x"] + room["width"], room["y"] + room["height"],
                    fill=COLOR_LIGHT, outline=COLOR_PRIMARY, width=2
                )
                self.canvas.create_text(
                    room["x"] + 5, room["y"] + 5,
                    text=room.get("name", "Unknown"),
                    anchor="nw", font=("Arial", 10, "bold")
                )

            # Draw seats
            seats = data.get("floorplan", {}).get("seats", [])
            for seat in seats:
                self.canvas.create_oval(
                    seat["x"] - DEFAULT_SEAT_SIZE,
                    seat["y"] - DEFAULT_SEAT_SIZE,
                    seat["x"] + DEFAULT_SEAT_SIZE,
                    seat["y"] + DEFAULT_SEAT_SIZE,
                    fill=COLOR_FREE, outline=COLOR_PRIMARY, width=1
                )
                self.canvas.create_text(
                    seat["x"], seat["y"],
                    text=str(seat.get("number", "?")),
                    font=("Arial", 8, "bold")
                )

        except Exception as e:
            logger.error(f"Error refreshing canvas: {e}")
