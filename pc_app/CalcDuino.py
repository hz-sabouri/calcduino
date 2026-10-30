import tkinter as tk
import serial
import serial.tools.list_ports
import time
import re
import ast
import operator
import threading

BAUD_RATE   = 9600
SERIAL_PORT = 'COM5='

SAFE_OPS = {
    ast.Add:  operator.add,
    ast.Sub:  operator.sub,
    ast.Mult: operator.mul,
    ast.Div:  operator.truediv,
}

def safe_eval(expr: str):

    try:
        tree = ast.parse(expr, mode='eval')
    except SyntaxError:
        raise ValueError("عبارت نامعتبر است")

    def _eval(node):
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
            return -_eval(node.operand)
        if isinstance(node, ast.BinOp):
            op_func = SAFE_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError("عملگر مجاز نیست")
            left  = _eval(node.left)
            right = _eval(node.right)
            if isinstance(node.op, ast.Div) and right == 0:
                raise ZeroDivisionError("تقسیم بر صفر")
            return op_func(left, right)
        raise ValueError("عبارت مجاز نیست")

    return _eval(tree)


class ArduinoSerial:

    def __init__(self):
        self.serial: serial.Serial | None = None
        self._tx_queue: list[str] = []
        self._ready     = True        
        self._lock      = threading.Lock()


    def connect(self, port: str, baud: int) -> bool:
        try:
            self.serial = serial.Serial(port, baud, timeout=1)
            time.sleep(2)
            print(f"[سریال] اتصال برقرار شد: {port}")
            return True
        except Exception as e:
            print(f"[سریال] خطا در اتصال: {e}")
            self.serial = None
            return False

    def disconnect(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            print("[سریال] پورت بسته شد.")

    @property
    def is_connected(self) -> bool:
        return self.serial is not None and self.serial.is_open

    def send(self, cmd: str):
        """اضافه کردن دستور به صف"""
        with self._lock:
            self._tx_queue.append(cmd)
        self._flush()

    def _flush(self):
        """ارسال اول صف در صورت آمادگی آردوینو"""
        with self._lock:
            if not self._ready or not self._tx_queue:
                return
            if not self.is_connected:
                self._tx_queue.clear()
                return
            cmd = self._tx_queue.pop(0)
            self._ready = False

        try:
            self.serial.write((cmd + "\n").encode('utf-8'))
            print(f"[ارسال] {cmd}")
        except Exception as e:
            print(f"[سریال] خطا در ارسال: {e}")
            with self._lock:
                self._ready = True


    def poll(self):
        
        if not self.is_connected:
            return
        try:
            while self.serial.in_waiting > 0:
                line = self.serial.readline().decode('utf-8').strip()
                print(f"[دریافت] {line}")
                if line == "DONE":
                    with self._lock:
                        self._ready = True
                    self._flush()
        except Exception as e:
            print(f"[سریال] خطا در دریافت: {e}")

def main():
    arduino = ArduinoSerial()
    connected = arduino.connect(SERIAL_PORT, BAUD_RATE)
    if not connected:
        print("[هشدار] بدون آردوینو ادامه می‌دهد.")

    window = tk.Tk()
    window.title("ماشین حساب هوشمند")
    window.resizable(False, False)

    expression = tk.StringVar(value="")

    display = tk.Entry(
        window,
        textvariable=expression,
        font=("Arial", 22),
        justify="right",
        bd=10,
        relief="sunken",
        state="readonly",          
    )
    display.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky="we")

    def get_last_number(expr: str) -> int | None:
        """استخراج آخرین عدد صحیح از عبارت"""
        parts = re.split(r'[+\-*/]', expr)
        last = parts[-1] if parts else ""
        if not last:
            return None
        try:
            val = int(float(last))
            return val if val > 0 else None
        except ValueError:
            return None

    def add_char(value: str):
        current = expression.get()

        if value == '.':
            parts = re.split(r'[+\-*/]', current)
            if parts and '.' in parts[-1]:
                return

        if value in '+-*/' and current and current[-1] in '+-*/':
            expression.set(current[:-1] + value)
            return

        if value in '+-*/':
            num = get_last_number(current)
            if num is not None:
                arduino.send(f"B:{num}")

        expression.set(current + value)

    def clear_expression():
        expression.set("")

    def backspace():
        current = expression.get()
        expression.set(current[:-1])

    def calculate():
        expr = expression.get().strip()
        if not expr:
            return

        num = get_last_number(expr)
        if num is not None:
            arduino.send(f"B:{num}")

        try:
            result_val = safe_eval(expr)
            if isinstance(result_val, float) and result_val.is_integer():
                result_str = str(int(result_val))
            else:
                result_str = f"{result_val:.6g}"
            expression.set(result_str)
            arduino.send(f"D:{expr}={result_str}")

        except ZeroDivisionError:
            expression.set("خطا: تقسیم بر صفر")
        except Exception as e:
            print(f"[خطا] {e}")
            expression.set("خطا")


    BUTTONS = [
        ("7", 1, 0, 1), ("8",  1, 1, 1), ("9",  1, 2, 1), ("/",  1, 3, 1),
        ("4", 2, 0, 1), ("5",  2, 1, 1), ("6",  2, 2, 1), ("*",  2, 3, 1),
        ("1", 3, 0, 1), ("2",  3, 1, 1), ("3",  3, 2, 1), ("-",  3, 3, 1),
        ("0", 4, 0, 1), ("00", 4, 1, 1), (".",  4, 2, 1), ("+",  4, 3, 1),
        ("C", 5, 0, 1), ("⌫",  5, 1, 1), ("=",  5, 2, 2),
    ]

    COLOR_MAP = {
        "digits":    "#50BBE2",
        "operator":  "#395F26",
        "equals":    "#ADD8E6",
        "clear":     "#FF6B6B",
        "backspace": "#FFD93D",
        "decimal":   "#FFFF99",
        "default":   "#f0f0f0",
    }

    def btn_color(text):
        if text.lstrip("-").replace(".", "").isdigit() or text == "00":
            return COLOR_MAP["digits"], "white" if text not in ("00",) else "black"
        if text in "+-*/":
            return COLOR_MAP["operator"], "white"
        if text == "=":
            return COLOR_MAP["equals"], "black"
        if text == "C":
            return COLOR_MAP["clear"], "white"
        if text == "⌫":
            return COLOR_MAP["backspace"], "black"
        if text == ".":
            return COLOR_MAP["decimal"], "black"
        return COLOR_MAP["default"], "black"

    for (text, row, col, colspan) in BUTTONS:
        if text == "C":
            cmd = clear_expression
        elif text == "=":
            cmd = calculate
        elif text == "⌫":
            cmd = backspace
        else:
            cmd = lambda v=text: add_char(v)

        bg, fg = btn_color(text)

        tk.Button(
            window,
            text=text,
            font=("Arial", 18),
            width=4,
            height=1,
            command=cmd,
            bg=bg,
            fg=fg,
            activebackground=bg,
            relief="raised",
            bd=3,
        ).grid(row=row, column=col, columnspan=colspan,
               sticky="nsew", padx=5, pady=5)

    for i in range(6):
        window.rowconfigure(i, weight=1)
    for j in range(4):
        window.columnconfigure(j, weight=1)

    def serial_poll_loop():
        arduino.poll()
        window.after(50, serial_poll_loop)

    def on_close():
        arduino.disconnect()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", on_close)

    window.after(50, serial_poll_loop)
    window.mainloop()

if __name__ == "__main__":
    main()
