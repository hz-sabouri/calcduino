# CalcDuino

A smart calculator that links a desktop GUI with an Arduino. You type an expression in a Tkinter calculator on your PC, the app evaluates it safely, and the Arduino shows the expression and result on a 16×2 LCD, while an LED and a buzzer react to the numbers you enter.

> Computer Architecture Laboratory course project, built in **June 2026**.

## How it works

```
 PC (Python / Tkinter)                     Arduino (C++)
┌──────────────────────┐   USB serial   ┌─────────────────────────────┐
│ calculator GUI       │ ─────────────► │ parses one command per line │
│ safe expression eval │   9600 baud    │ 16×2 LCD · LED · buzzer     │
│ command queue        │ ◄───────────── │ replies DONE when finished  │
└──────────────────────┘                └─────────────────────────────┘
```

- Pressing an operator key or `=` sends the last number you typed. The Arduino beeps and blinks the LED that many times (capped at 20).
- Pressing `=` evaluates the expression and sends it to the Arduino, which prints the expression on LCD line 1 and the result on line 2 (long values are truncated to 16 characters with a trailing `~`).
- The PC sends one command at a time and waits for the Arduino's `DONE` reply, so commands never overlap.

## Serial protocol

Commands are plain text, one per line, at 9600 baud.

| Command (PC → Arduino) | Effect |
|---|---|
| `B:<n>` | Short beep, then blink the LED `n` times (1–20). Arduino replies `DONE` after the last blink |
| `D:<expression>=<result>` | Clear the LCD and show the expression and the result. Arduino replies `DONE` |
| anything else | Ignored. Arduino replies `DONE` |

The Arduino also sends `DONE` once on start-up.

## Features

- Calculator GUI with digits, `+ − × ÷`, decimal point, clear and backspace
- Safe expression evaluation using Python's `ast` module (only numbers, `+ - * /` and unary minus are allowed; `eval` is never used)
- Division-by-zero and invalid-expression handling
- Non-blocking serial communication: the GUI polls the port every 50 ms, so it stays responsive
- The GUI also works without an Arduino connected (it just prints a warning)

## Hardware

- Arduino board (USB serial at 9600 baud)
- 16×2 character LCD (HD44780-compatible, 4-bit mode)
- LED (with a current-limiting resistor)
- Passive buzzer or piezo
- Breadboard, jumper wires and an LCD contrast potentiometer

| Component | Arduino pin |
|---|---|
| LCD RS | 12 |
| LCD E | 11 |
| LCD D4 | 5 |
| LCD D5 | 4 |
| LCD D6 | 3 |
| LCD D7 | 2 |
| Buzzer | 8 |
| LED | 9 |

## Getting started

1. **Wire** the components as in the table above.
2. **Upload the firmware.** Open `firmware/CalcDuino/CalcDuino.ino` in the Arduino IDE, choose your board and port, and upload. It uses the `LiquidCrystal` library that ships with the IDE. Close the Serial Monitor afterwards, because only one program can use the port.
3. **Install the PC dependency** (Python 3.10 or newer; Tkinter comes with the standard Python installer):
   ```bash
   pip install -r requirements.txt
   ```
4. **Set the serial port.** In `pc_app/CalcDuino.py`, set `SERIAL_PORT` to your Arduino's port, e.g. `COM5` on Windows or `/dev/ttyACM0` on Linux.
5. **Run:**
   ```bash
   python pc_app/CalcDuino.py
   ```

## Project structure

```
calcduino/
├── firmware/
│   └── CalcDuino/
│       └── CalcDuino.ino     # Arduino sketch (folder name must match the sketch name)
├── pc_app/
│   └── CalcDuino.py          # Tkinter GUI + serial communication
├── requirements.txt
├── README.md
├── LICENSE
└── .gitignore
```

## Tech

Python (Tkinter, pyserial, `ast`), Arduino C++ (`LiquidCrystal`), serial (UART) communication

## License

MIT, see [LICENSE](LICENSE).
