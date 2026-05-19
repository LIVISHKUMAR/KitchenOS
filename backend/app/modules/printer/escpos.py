"""ESC/POS Thermal Printer Driver.

Supports network (TCP) and USB printing for thermal receipt printers.
Compatible with: Epson TM-T82, TVS RP3160, Bixolon SRP-350, Gprinter GP-80250
"""

import socket
import time
import logging
from typing import Optional, List
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger("kitchenos.printer")


# ESC/POS Commands
class ESCPOS:
    # Initialize printer
    INIT = b'\x1b\x40'

    # Text alignment
    ALIGN_LEFT = b'\x1b\x61\x00'
    ALIGN_CENTER = b'\x1b\x61\x01'
    ALIGN_RIGHT = b'\x1b\x61\x02'

    # Text size
    TEXT_NORMAL = b'\x1d\x21\x00'
    TEXT_DOUBLE_HEIGHT = b'\x1d\x21\x01'
    TEXT_DOUBLE_WIDTH = b'\x1d\x21\x10'
    TEXT_DOUBLE_BOTH = b'\x1d\x21\x11'

    # Text style
    BOLD_ON = b'\x1b\x45\x01'
    BOLD_OFF = b'\x1b\x45\x00'
    UNDERLINE_ON = b'\x1b\x2d\x01'
    UNDERLINE_OFF = b'\x1b\x2d\x00'

    # Paper cut
    CUT_FULL = b'\x1d\x56\x00'
    CUT_PARTIAL = b'\x1d\x56\x01'

    # Cash drawer
    DRAWER_OPEN = b'\x1b\x70\x00\x19\xfa'

    # Line feed
    LF = b'\x0a'

    # Feed and cut
    FEED_CUT = b'\x0a\x0a\x0a\x1d\x56\x00'


@dataclass
class PrinterConfig:
    """Printer configuration."""
    name: str
    host: str
    port: int = 9100
    paper_width: int = 80  # mm (80 or 58)
    char_per_line: int = 48  # characters per line for 80mm
    timeout: float = 5.0
    retries: int = 3
    retry_delay: float = 1.0


class ESCPOSPrinter:
    """ESC/POS thermal printer client."""

    def __init__(self, config: PrinterConfig):
        self.config = config
        self._socket: Optional[socket.socket] = None

    def connect(self) -> bool:
        """Connect to printer via TCP."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.config.timeout)
            self._socket.connect((self.config.host, self.config.port))
            logger.info(f"Connected to printer {self.config.name} at {self.config.host}:{self.config.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to printer {self.config.name}: {e}")
            self._socket = None
            return False

    def disconnect(self):
        """Disconnect from printer."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def is_connected(self) -> bool:
        """Check if printer is connected."""
        return self._socket is not None

    def send(self, data: bytes) -> bool:
        """Send raw data to printer with retry."""
        for attempt in range(self.config.retries):
            try:
                if not self._socket:
                    if not self.connect():
                        continue

                self._socket.sendall(data)
                return True
            except Exception as e:
                logger.warning(f"Printer send attempt {attempt + 1} failed: {e}")
                self.disconnect()
                if attempt < self.config.retries - 1:
                    time.sleep(self.config.retry_delay)

        logger.error(f"Failed to send to printer {self.config.name} after {self.config.retries} attempts")
        return False

    def print_text(self, text: str, align: str = "left",
                   bold: bool = False, double: bool = False) -> bool:
        """Print text with formatting."""
        commands = bytearray()
        commands.extend(ESCPOS.INIT)

        # Alignment
        if align == "center":
            commands.extend(ESCPOS.ALIGN_CENTER)
        elif align == "right":
            commands.extend(ESCPOS.ALIGN_RIGHT)
        else:
            commands.extend(ESCPOS.ALIGN_LEFT)

        # Style
        if bold:
            commands.extend(ESCPOS.BOLD_ON)
        if double:
            commands.extend(ESCPOS.TEXT_DOUBLE_BOTH)

        # Text
        commands.extend(text.encode('utf-8', errors='replace'))
        commands.extend(ESCPOS.LF)

        # Reset
        commands.extend(ESCPOS.TEXT_NORMAL)
        commands.extend(ESCPOS.BOLD_OFF)

        return self.send(bytes(commands))

    def print_line(self, char: str = "-", width: int = None) -> bool:
        """Print a separator line."""
        w = width or self.config.char_per_line
        return self.print_text(char * w)

    def print_kv(self, key: str, value: str, width: int = None) -> bool:
        """Print a key-value pair aligned."""
        w = width or self.config.char_per_line
        padding = w - len(key) - len(value)
        if padding < 1:
            padding = 1
        line = f"{key}{' ' * padding}{value}"
        return self.print_text(line)

    def cut(self, partial: bool = False) -> bool:
        """Cut paper."""
        cmd = ESCPOS.CUT_PARTIAL if partial else ESCPOS.CUT_FULL
        return self.send(cmd)

    def feed(self, lines: int = 3) -> bool:
        """Feed paper."""
        return self.send(ESCPOS.LF * lines)

    def open_drawer(self) -> bool:
        """Open cash drawer."""
        return self.send(ESCPOS.DRAWER_OPEN)

    def print_kot(self, order_data: dict) -> bool:
        """Print a Kitchen Order Ticket."""
        commands = bytearray()
        commands.extend(ESCPOS.INIT)
        commands.extend(ESCPOS.ALIGN_CENTER)
        commands.extend(ESCPOS.TEXT_DOUBLE_BOTH)
        commands.extend(ESCPOS.BOLD_ON)
        commands.extend(b"KOT")
        commands.extend(ESCPOS.LF)
        commands.extend(ESCPOS.TEXT_NORMAL)
        commands.extend(ESCPOS.BOLD_OFF)
        commands.extend(b"=" * self.config.char_per_line)
        commands.extend(ESCPOS.LF)

        # Order info
        commands.extend(ESCPOS.ALIGN_LEFT)
        commands.extend(f"Order: {order_data.get('order_number', '')}".encode())
        commands.extend(ESCPOS.LF)

        table = order_data.get('table_id', 'N/A')
        order_type = order_data.get('order_type', 'dine_in').replace('_', ' ').title()
        commands.extend(f"Table: {table}  Type: {order_type}".encode())
        commands.extend(ESCPOS.LF)

        commands.extend(b"-" * self.config.char_per_line)
        commands.extend(ESCPOS.LF)

        # Items
        for item in order_data.get('items', []):
            qty = item.get('quantity', 1)
            name = item.get('item_name', '')[:30]
            commands.extend(ESCPOS.BOLD_ON)
            commands.extend(f"  {qty}x {name}".encode())
            commands.extend(ESCPOS.BOLD_OFF)
            commands.extend(ESCPOS.LF)

            if item.get('cooking_instructions'):
                note = item['cooking_instructions'][:40]
                commands.extend(f"    Note: {note}".encode())
                commands.extend(ESCPOS.LF)

        commands.extend(b"-" * self.config.char_per_line)
        commands.extend(ESCPOS.LF)

        # Time
        now = datetime.now().strftime("%H:%M:%S")
        commands.extend(f"Time: {now}".encode())
        commands.extend(ESCPOS.LF)

        # Cut
        commands.extend(ESCPOS.FEED_CUT)

        return self.send(bytes(commands))

    def print_bill(self, order_data: dict, restaurant_name: str = "",
                   gstin: str = "", address: str = "") -> bool:
        """Print a GST-compliant bill."""
        w = self.config.char_per_line
        commands = bytearray()
        commands.extend(ESCPOS.INIT)

        # Header
        commands.extend(ESCPOS.ALIGN_CENTER)
        commands.extend(ESCPOS.TEXT_DOUBLE_BOTH)
        commands.extend(ESCPOS.BOLD_ON)
        commands.extend(restaurant_name.encode('utf-8', errors='replace')[:w])
        commands.extend(ESCPOS.LF)
        commands.extend(ESCPOS.TEXT_NORMAL)
        commands.extend(ESCPOS.BOLD_OFF)

        if address:
            commands.extend(address.encode('utf-8', errors='replace')[:w])
            commands.extend(ESCPOS.LF)

        if gstin:
            commands.extend(f"GSTIN: {gstin}".encode())
            commands.extend(ESCPOS.LF)

        commands.extend(b"=" * w)
        commands.extend(ESCPOS.LF)

        # Order info
        commands.extend(ESCPOS.ALIGN_LEFT)
        commands.extend(f"Bill No: {order_data.get('order_number', '')}".encode())
        commands.extend(ESCPOS.LF)
        commands.extend(f"Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}".encode())
        commands.extend(ESCPOS.LF)
        commands.extend(f"Type: {order_data.get('order_type', 'dine_in').replace('_', ' ').title()}".encode())
        commands.extend(ESCPOS.LF)

        commands.extend(b"-" * w)
        commands.extend(ESCPOS.LF)

        # Items header
        commands.extend(ESCPOS.BOLD_ON)
        commands.extend(f"{'Item':<20} {'Qty':>4} {'Rate':>7} {'Amt':>7}".encode())
        commands.extend(ESCPOS.BOLD_OFF)
        commands.extend(ESCPOS.LF)
        commands.extend(b"-" * w)
        commands.extend(ESCPOS.LF)

        # Items
        for item in order_data.get('items', []):
            name = item.get('item_name', '')[:20]
            qty = str(int(item.get('quantity', 1)))
            rate = f"{float(item.get('unit_price', 0)):.2f}"
            amt = f"{float(item.get('total', 0)):.2f}"
            commands.extend(f"{name:<20} {qty:>4} {rate:>7} {amt:>7}".encode())
            commands.extend(ESCPOS.LF)

        commands.extend(b"-" * w)
        commands.extend(ESCPOS.LF)

        # Totals
        subtotal = float(order_data.get('subtotal', 0))
        tax = float(order_data.get('tax_amount', 0))
        discount = float(order_data.get('discount_amount', 0))
        total = float(order_data.get('total', 0))

        commands.extend(ESCPOS.ALIGN_RIGHT)
        commands.extend(self._kv_line("Subtotal:", f"₹{subtotal:.2f}", w).encode())
        commands.extend(ESCPOS.LF)

        if discount > 0:
            commands.extend(self._kv_line("Discount:", f"-₹{discount:.2f}", w).encode())
            commands.extend(ESCPOS.LF)

        # Tax breakdown (CGST + SGST)
        cgst = tax / 2
        commands.extend(self._kv_line("CGST (9%):", f"₹{cgst:.2f}", w).encode())
        commands.extend(ESCPOS.LF)
        commands.extend(self._kv_line("SGST (9%):", f"₹{cgst:.2f}", w).encode())
        commands.extend(ESCPOS.LF)

        commands.extend(b"=" * w)
        commands.extend(ESCPOS.LF)
        commands.extend(ESCPOS.BOLD_ON)
        commands.extend(ESCPOS.TEXT_DOUBLE_WIDTH)
        commands.extend(self._kv_line("TOTAL:", f"₹{total:.2f}", w).encode())
        commands.extend(ESCPOS.LF)
        commands.extend(ESCPOS.TEXT_NORMAL)
        commands.extend(ESCPOS.BOLD_OFF)
        commands.extend(b"=" * w)
        commands.extend(ESCPOS.LF)

        # Footer
        commands.extend(ESCPOS.ALIGN_CENTER)
        commands.extend(b"Thank you! Visit again!")
        commands.extend(ESCPOS.LF)
        commands.extend(b"This is a computer generated invoice.")
        commands.extend(ESCPOS.LF)
        commands.extend(ESCPOS.FEED_CUT)

        return self.send(bytes(commands))

    def _kv_line(self, key: str, value: str, width: int) -> str:
        """Format a key-value line."""
        padding = width - len(key) - len(value)
        if padding < 1:
            padding = 1
        return f"{key}{' ' * padding}{value}"


class PrintQueue:
    """Print job queue with retry logic."""

    def __init__(self):
        self._queue: List[dict] = []
        self._printers: dict = {}

    def register_printer(self, printer_id: str, config: PrinterConfig):
        """Register a printer."""
        self._printers[printer_id] = ESCPOSPrinter(config)

    def get_printer(self, printer_id: str) -> Optional[ESCPOSPrinter]:
        """Get a printer by ID."""
        return self._printers.get(printer_id)

    def queue_kot(self, printer_id: str, order_data: dict) -> dict:
        """Queue a KOT print job."""
        printer = self.get_printer(printer_id)
        if not printer:
            return {"error": f"Printer {printer_id} not found"}

        success = printer.print_kot(order_data)
        return {
            "printer_id": printer_id,
            "type": "kot",
            "order_number": order_data.get("order_number"),
            "status": "printed" if success else "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

    def queue_bill(self, printer_id: str, order_data: dict,
                   restaurant_name: str = "", gstin: str = "",
                   address: str = "") -> dict:
        """Queue a bill print job."""
        printer = self.get_printer(printer_id)
        if not printer:
            return {"error": f"Printer {printer_id} not found"}

        success = printer.print_bill(order_data, restaurant_name, gstin, address)
        return {
            "printer_id": printer_id,
            "type": "bill",
            "order_number": order_data.get("order_number"),
            "status": "printed" if success else "failed",
            "timestamp": datetime.utcnow().isoformat()
        }

    def open_drawer(self, printer_id: str) -> dict:
        """Open cash drawer via printer."""
        printer = self.get_printer(printer_id)
        if not printer:
            return {"error": f"Printer {printer_id} not found"}

        success = printer.open_drawer()
        return {
            "printer_id": printer_id,
            "type": "drawer",
            "status": "opened" if success else "failed"
        }

    def get_status(self) -> list:
        """Get status of all printers."""
        return [
            {
                "printer_id": pid,
                "name": printer.config.name,
                "host": printer.config.host,
                "connected": printer.is_connected()
            }
            for pid, printer in self._printers.items()
        ]


# Global print queue
print_queue = PrintQueue()
