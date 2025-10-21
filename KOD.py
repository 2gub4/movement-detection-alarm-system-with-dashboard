import RPi.GPIO as GPIO
import time
import tm1637
from flask import Flask, request, render_template, send_file
import threading
from datetime import datetime
import random
from mailer import send_alarm_email


buzz = 8
GPIO.setup(buzz, GPIO.OUT)
GPIO.output(buzz, GPIO.LOW)

tm = tm1637.TM1637(clk=23, dio=24)
tm.brightness(3)

KEYPAD = [["1", "2", "3"],
          ["4", "5", "6"],
          ["7", "8", "9"],
          ["*", "0", "#"]]

ROW_PINS = [5, 6, 13, 19]
COL_PINS = [12, 16, 20]
echo = 3

rcwl = 21
led = 25
czerwony_led = 17
trigger = 2
failed_attempts = []
last_alarm = None
visit_log = []
LOG_FILE = "log.txt"


tm.show([" "," "," "," "])

GPIO.setup(trigger, GPIO.OUT)
GPIO.setup(echo, GPIO.IN)
GPIO.output(trigger, GPIO.LOW)

GPIO.setup(led, GPIO.OUT)
GPIO.output(led, GPIO.LOW)

GPIO.setup(czerwony_led, GPIO.OUT)
GPIO.output(czerwony_led, GPIO.LOW)

GPIO.setup(rcwl, GPIO.IN)
#GPIO.input(GPIO.LOW)

for col in COL_PINS:
    GPIO.setup(col, GPIO.OUT)
    GPIO.output(col, GPIO.HIGH)

for row in ROW_PINS:
    GPIO.setup(row, GPIO.IN, pull_up_down=GPIO.PUD_UP)


lock = threading.Lock()
display_lock = threading.Lock()

class Sensor:
    @staticmethod
    def distance_trigger():
        threshold = 1.5
        ruch = 0
        while True:
            GPIO.output(trigger, GPIO.HIGH)
            time.sleep(0.00001)
            GPIO.output(trigger, GPIO.LOW)
            start_time = time.time()
            ps_start = None
            ps_stop = None
            while GPIO.input(echo) == 0:
                ps_start = time.time()
                if time.time() - start_time > 0.02:
                    break
            start_time = time.time()
            while GPIO.input(echo) == 1:
                ps_stop = time.time()
                if time.time() - start_time > 0.02:
                    break
            if ps_start and ps_stop:
                dist = round((ps_stop-ps_start)*171.5, 2)
                print(f"{dist}")
            if GPIO.input(rcwl) == GPIO.HIGH:
                print(f"czy ruch: {GPIO.input(rcwl)}")
                ruch = 1
            if dist <= threshold and flag.armed and ruch == 1 and not flag.countdown_ongoing.is_set():
                flag.distance.set()
            time.sleep(0.2)

class PIN:
    def __init__(self):
        with open("pin.txt", "r") as p:
            self.pin = p.read().strip()
            if self.pin == ["0","0","0","0"]:
                self.pin = [random.randint(1, 9)] + [random.randint(0,9) for _ in range(3)]
            self.pin = ''.join(self.pin)[:4]
            print(self.pin)
            p.close()

class CodeEvent:
    @staticmethod
    def initial_code_set():
        print("Podaj poprawny kod PIN: ")
        confirm = False
        ok = False
        while not ok:
            ok, pin = CodeEvent.double_code_input()
            if not ok:
                print("Rozne PINy. Sprobuj ponownie")
                for i in range(3):
                    with display_lock:
                        tm.show(["-","5","E","7"])
                    time.sleep(0.3)
                    with display_lock:
                        tm.show([" "," "," "," "])
            if ok:
                print("Pomyslnie ustawiono kod PIN")
                for i in range(3):
                    with display_lock:
                        tm.show(["5","E","7","*"])
                        time.sleep(0.3)
                        tm.show([" "," "," "," "])
                break
        print("Oczekiwanie na potwierdzenie (#)")
        while not confirm:
            key = read_keypad()
            if key:
                if key == "#":
                    confirm = True
        if confirm:
            print("Pin ustawiony")
            with open("pin.txt", "w") as f:
                f.write(''.join(pin))
                f.close()

    @staticmethod
    def double_code_input():
        code1 = []
        code2 = []
        for i in range(3):
            with display_lock:
                tm.show(["0"," "," ","0"], colon = True)
            time.sleep(0.2)
            with display_lock:
                tm.show([" "," "," "," "], colon = False)
            time.sleep(0.2)
        with display_lock:
            tm.show([" ", "1", " ", " "], colon = True)
        time.sleep(0.5)
        with display_lock:
            tm.show([" ", " ", " ", " "], colon = False)
        while not len(code1) == 4 and code1 != ["0","0","0","0"]:
            key = read_keypad()
            if key:
                if key.isnumeric():
                    code1.append(key)
                    disp = code1 + [" "] * (4 - len(code1))
                    tm.show(disp)
        time.sleep(0.8)
        with display_lock:
            tm.show([" ", " ", " ", " "], colon = False)
        time.sleep(0.5)
        with display_lock:
            tm.show([" ", "2", " ", " "], colon = True)
        time.sleep(0.5)
        with display_lock:
             tm.show([" ", " ", " ", " "], colon = False)
        while not len(code2) == 4 and code1 != ["0","0","0","0"]:
            key = read_keypad()
            if key:
                if key.isnumeric():
                    code2.append(key)
                    disp2 = code2 + [" "] * (4 - len(code2))
                    tm.show(disp2)
        time.sleep(1)
        with display_lock:
            tm.show([" ", " ", " ", " "])
        print(f"Kody zgodne: {code1 == code2}")
        return code1 == code2, code1

    @staticmethod
    def code_management():
        global input_code, wrong_inputs, flag, correct_code, failed_attempts
        while True:
            if flag.set_new_code and not flag.armed:
                print("Ustawiam pin")
                new_code = CodeEvent.ustawianie()
                if new_code[0]:
                    with display_lock:
                        tm.show(["5", "E", "7", " "])
                    time.sleep(1)
                    with display_lock:
                        tm.show([" ", " ", " ", " "])
                    CodeEvent.nowy_pin(new_code[1])
                    correct_code = PIN.pin
                else:
                    with display_lock:
                        tm.show(["-", "5", "E", "7"])
                    time.sleep(1)
                    with display_lock:
                        tm.show([" ", " ", " ", " "])
                input_code = []
                flag.set_new_code = False

            if flag.set_new_code is False:
                key = read_keypad()
                if key:
                    if key == "#" and len(input_code) == 4:
                        print(f"Podany kod: {input_code}\nPoprawny kod: {correct_code}")
                        time.sleep(0.3)
                        if ''.join(input_code) == correct_code:
                            if flag.verify is False:
                                if flag.alarm_active:
                                    print("Poprawny PIN -> wylaczanie alarmu")
                                    flag.alarm_stop.set()
                                flag.successful_validation.set()
                                CodeEvent.poprawny()
                            else:
                                flag.set_new_code = True
                                flag.verify = False
                        else:
                            with lock:
                                wrong_inputs += 1
                            failed_attempts.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                            trigger_alarm("zla proba PIN")
                            if wrong_inputs == 3 and not flag.alarm_active:
                                flag.failed_validation.set()
                            CodeEvent.blad()
                        time.sleep(1)
                        input_code = []
                        flag.no_input = True
                        CodeEvent.show_code()
                    elif key == "#" and len(input_code) == 0 and not flag.armed:
                        flag.set_init = True
                        print("#")
                    elif key == "*" and flag.set_init and not flag.armed:
                        print("#* - ustawianie nowego kodu")
                        flag.set_init = False
                        time.sleep(1)
                        flag.verify = True
                    elif key == "*" and len(input_code) >= 1:
                        if input_code:
                            input_code.pop()
                            CodeEvent.show_code()
                    elif key == "*" and not flag.armed and len(input_code) == 0:
                        CodeEvent.arm()
                    else:
                        if len(input_code) < 4:
                            input_code.append(key)
                            CodeEvent.show_code()
        time.sleep(0.05)


    @staticmethod
    def blad():
        print("Bledny PIN")
        time.sleep(0.2)
        for i in range(3):
            with display_lock:
                tm.show(['-','-','-','-'])
            GPIO.output(czerwony_led, GPIO.HIGH)
            GPIO.output(buzz, GPIO.HIGH)
            time.sleep(0.2)
            with display_lock:
                tm.show([' ',' ',' ',' '])
            GPIO.output(czerwony_led, GPIO.LOW)
            GPIO.output(buzz, GPIO.LOW)
            time.sleep(0.2)

    @staticmethod
    def poprawny():
        print("Poprawny PIN")
        time.sleep(0.2)
        for i in range(3):
            with display_lock:
                tm.show(["0","0","0","0"])
            GPIO.output(led, GPIO.HIGH)
            GPIO.output(buzz, GPIO.HIGH)
            time.sleep(0.15)
            with display_lock:
                tm.show([" "," "," "," "])
            GPIO.output(led, GPIO.LOW)
            GPIO.output(buzz, GPIO.LOW)
            time.sleep(0.15)

    @staticmethod
    def nowy_pin(nc):
        PIN.pin = ''.join(nc)
        with open("pin.txt", "w") as f:
            f.write(PIN.pin)
            f.close()

    @staticmethod
    def ustawianie():
        if not flag.alarm_active and not flag.countdown_finished.is_set():
            return CodeEvent.double_code_input()

    @staticmethod


    def alarm():
        print("Rozpoczeto alarm")
        send_alarm_email()
        for i in range(3):
            GPIO.output(czerwony_led, GPIO.HIGH)
            time.sleep(0.15)
            GPIO.output(czerwony_led, GPIO.LOW)
        start = time.time()
        while not flag.alarm_stop.is_set():
            with display_lock:
                tm.show(["-", "-", "-", "-"], colon = True)
            GPIO.output(czerwony_led, GPIO.HIGH)
            GPIO.output(buzz, GPIO.HIGH)
            print("Alarm!")
            time.sleep(0.25)
            with display_lock:
                tm.show([" ", " ", " ", " "], colon = False)
            GPIO.output(czerwony_led, GPIO.LOW)
            GPIO.output(buzz, GPIO.LOW)
            time.sleep(0.25)
            if time.time() - start >= 300:
                break
        print("Koniec alarmu")

    @staticmethod
    def arm():
        global input_code
        armer = ["*"]
        i = 3
        tm.show(armer + [" "," "," "])
        print(armer)
        if armer == ["*"]:
            while i >= 1:
                k = read_keypad()
                if k:
                    i -= 1
                    if k == '#' and len(armer) == 3-i:
                        armer.append("H")
                        tm.show(armer + (2-i) * [" "])
                    else:
                        armer = []
                        with display_lock:
                            tm.show([" "," "," "," "])
                        return
                time.sleep(0.02)
            time.sleep(0.02)
        with display_lock:
            tm.show([" "," "," "," "])
        try:
            if armer == ["*","H","H","H"] and len(armer) == 4:
                flag.armed = True
                print("Pomyslne uzbrojenie systemu")
            else:
                print("Niepowodzenie w uzbrojeniu")
                return
        finally:
            input_code = []

    @staticmethod
    def countdown(buffer=60):
        print("Rozpoczeto odliczanie")
        while buffer >= 1:
            time.sleep(1)
            if flag.successful_validation.is_set():
                return
            if flag.alarm_active or flag.alarm_stop.is_set() or flag.failed_validation.is_set():
                return
            print(f"Pozostalo {buffer}s")
            buffer -= 1
        if not flag.successful_validation.is_set():
            flag.countdown_finished.set()

    @staticmethod
    def show_code():
        with display_lock:
            tm.show(input_code + (4 - len(input_code)) * [" "])

class Flag:
    def __init__(self):
        self.set_init = False
        self.arm_init = False
        self.armed = False
        self.verify = False
        self.first_measurement = True
        self.set_new_code = False
        self.alarm_active = False
        self.successful_validation = threading.Event()
        self.failed_validation = threading.Event()
        self.countdown_finished = threading.Event()
        self.alarm_stop = threading.Event()
        self.distance = threading.Event()
        self.countdown_ongoing = threading.Event()

    @staticmethod
    def reset_system():
        global input_code, wrong_inputs
        flag.successful_validation.clear()
        flag.failed_validation.clear()
        flag.countdown_finished.clear()
        flag.alarm_stop.clear()
        flag.distance.clear()
        flag.countdown_ongoing.clear()
        flag.alarm_active = False

def read_keypad():
    for col_num, col_pin in enumerate(COL_PINS):
        GPIO.output(col_pin, GPIO.LOW)
        for row_num, row_pin in enumerate(ROW_PINS):
            if GPIO.input(row_pin) == GPIO.LOW:
                key = KEYPAD[row_num][col_num]
                while GPIO.input(row_pin) == GPIO.LOW:
                    time.sleep(0.01)
                time.sleep(0.05)
                return key
        GPIO.output(col_pin, GPIO.HIGH)
    return None


def trigger_alarm(reason="?"):
    global last_alarm
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    last_alarm = f"{timestamp} - {reason}"

    with open(LOG_FILE , "a") as f:
        f.write("[ALARM]" + "\n")

    print("ALARM!!!", last_alarm)


app = Flask(__name__)

@app.route('/')
def dashboard():
    try:
        ip = request.remote_addr or "unknown"
    except Exception:
        ip = "unknow"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} - IP: {ip}"
    visit_log.append(log_entry)
    with open(LOG_FILE, "a") as f:
        f.write("[ODWIEDZONE]" + log_entry + "\n")


    status = "Uzbrojony" if flag.armed else "Rozbrojony"
    return render_template(
        "dashboard.html",
        status=status,
        failed_attempts=failed_attempts,
        visits=len(visit_log),
        last_alarm=last_alarm
    )

@app.route('/download-log')
def download_log():
    try:
        return send_file(LOG_FILE, as_attachment=True)
    except Exception:
        return "Nie ma pliku log.txt", 404


@app.route('/favicon.ico')
def favicon():
    return '', 204

def start_flask():
    app.run(host='0.0.0.0', port=5000)

try:
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    with display_lock:
        tm.show(["H","I"," "," "])
    time.sleep(0.5)
    with display_lock:
        tm.show([" "," "," "," "])
    flag = Flag()
    CodeEvent.initial_code_set()
    Pin = PIN()
    correct_code = Pin.pin
    #correct_code = "1111"
    print(f"Aktualny kod: {correct_code}")
    input_code = []
    wrong_inputs = 0
    pomiar = threading.Thread(target=Sensor.distance_trigger, daemon=True)
    pomiar.start()
    code_thread = threading.Thread(target=CodeEvent.code_management, daemon=True)
    code_thread.start()
    with display_lock:
        tm.show([" "," "," "," "])
    cntr = 0
    while True:
        if flag.distance.is_set() and flag.armed:
                print("Wykryto niepozadany ruch.")
                print("rozpoczecie odliczania")
                countdown_thread = threading.Thread(target=CodeEvent.countdown)
                countdown_thread.start()
                flag.countdown_ongoing.set()
                cntr += 1
                print(f"po raz: {cntr}")
                time.sleep(1)
                flag.distance.clear()

        if flag.successful_validation.is_set() and flag.armed:
                flag.armed = False
                print("Poprawny PIN")

        elif flag.failed_validation.is_set() or flag.countdown_finished.is_set() and flag.armed:
                print("Rozpoczeto alarm i druga walidacje")
                flag.alarm_active = True
                trigger_alarm("timer dobiegl konca")
                alarm_thread = threading.Thread(target=CodeEvent.alarm, daemon=True)
                alarm_thread.start()
                if flag.failed_validation.is_set():
                    flag.countdown_finished.set()
                while not flag.alarm_stop.is_set():
                    time.sleep(0.05)
                if flag.alarm_stop.is_set():
                    alarm_thread.join()
                flag.armed = False
                print("Koniec alarmu")

        while not flag.armed or flag.set_init:
                print("Oczekuje na uzbrojenie lub zmiane pinu")
                time.sleep(0.1)
                Flag.reset_system()

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nProgram interrupted")
finally:
    #tm.show([" "," "," "," "])
    tm.write([0,0,0,0])
    GPIO.cleanup()

