import os
import json
import threading
from pathlib import Path
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox, font as tkfont
from tkinter.scrolledtext import ScrolledText

selected_base_path = None
next_folder_name = None


def get_next_output_folder(base_name="Applied from Base"):
    if not os.path.exists(base_name):
        return base_name
    counter = 2
    while True:
        candidate = f"{base_name}({counter})"
        if not os.path.exists(candidate):
            return candidate
        counter += 1


def generate_vehicle_jsons(log, base_path):
    if not os.path.exists(base_path):
        log(f"❌ Base.json not found at: {base_path}\n")
        return

    with open(base_path, "r") as f:
        base_json = json.load(f)

    vehicle_list_path = "VehicleList.ini"
    if not os.path.exists(vehicle_list_path):
        log("❌ VehicleList.ini not found!\n")
        return

    output_dir = "Applied jsons"
    os.makedirs(output_dir, exist_ok=True)

    with open(vehicle_list_path, "r") as f:
        vehicle_lines = f.readlines()

    vehicle_dict = {}
    for line in vehicle_lines:
        if '=' in line:
            name, hash_str = line.strip().split("=")
            vehicle_dict[name] = int(hash_str)

    for i, (vehicle_name, model_hash) in enumerate(vehicle_dict.items(), 1):
        new_json = dict(base_json)
        new_json["model"] = model_hash
        output_path = os.path.join(output_dir, f"{vehicle_name.lower()}.json")
        with open(output_path, "w") as out_file:
            json.dump(new_json, out_file, indent=4)
        log(f"✔ [{i}] Created: {vehicle_name}.json\n")

    log(f"\n✅ Generated {len(vehicle_dict)} vehicle JSONs in /vehicle_jsons\n")


def categorize_vehicle_jsons(log, output_folder):
    txt_file = "categorized_vehicle_list.txt"
    src_dir = Path("Applied jsons")
    dst_root = Path(output_folder)
    dst_root.mkdir(exist_ok=True)

    if not os.path.exists(txt_file):
        log("❌ categorized_vehicle_list.txt not found!\n")
        return

    class_vehicle_map = defaultdict(list)
    current_class = None

    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("[") and line.endswith("]"):
                current_class = line[1:-1].strip()
            else:
                class_vehicle_map[current_class].append(line.strip().lower())

    for class_name, vehicles in class_vehicle_map.items():
        class_folder = dst_root / class_name
        class_folder.mkdir(exist_ok=True)
        for vehicle in vehicles:
            src_path = src_dir / f"{vehicle}.json"
            if src_path.exists():
                dst_path = class_folder / src_path.name
                os.rename(src_path, dst_path)
                log(f"📁 {class_name}/ <- {vehicle}.json\n")
            else:
                log(f"⚠️ Missing: {vehicle}.json\n")

    try:
        src_dir.rmdir()
        log(f"\n🧹 Cleaned up: {src_dir}\n")
    except OSError:
        log(f"❌ Could not delete {src_dir} (not empty)\n")


def run_all(log, base_path, button):
    def task():
        global next_folder_name
        button.config(state=tk.DISABLED)
        log("🚦 Starting vehicle generation and categorization...\n\n")
        generate_vehicle_jsons(log, base_path)
        log("\n🔁 Categorizing into class folders...\n\n")
        output_folder = get_next_output_folder("Applied from Base")
        next_folder_name = output_folder
        categorize_vehicle_jsons(log, output_folder)
        log(f"\n✅ Done! Files saved to: {output_folder}/\n")
        button.config(state=tk.NORMAL)

    threading.Thread(target=task).start()


def build_gui():
    global selected_base_path

    window = tk.Tk()
    window.title("Cherax Vehicle Copy/Paste")
    window.geometry("850x650")
    window.configure(bg="#101010")

    title_font = tkfont.Font(family="Impact", size=20, weight="bold")
    label_font = tkfont.Font(family="Courier New", size=11, weight="bold")
    note_font = tkfont.Font(family="Courier New", size=9)
    log_font = tkfont.Font(family="Courier New", size=10)

    title = tk.Label(window, text="Cherax Vehicle Copy/Paste", fg="#0f0", bg="#101010", font=title_font)
    title.pack(pady=(15, 0))

    subtitle = tk.Label(window, text="Copies your vehicle paint, tires, lights, plate and such and applies to all vehicles",
                        fg="#aaaaaa", bg="#101010", font=label_font)
    subtitle.pack(pady=(0, 0))

    note = tk.Label(window, text="(Livery, spoiler, and cosmetic mods will be different per vehicle)",
                    fg="#555", bg="#101010", font=note_font)
    note.pack(pady=(0, 10))

    output_box = ScrolledText(
        window, wrap=tk.WORD, height=25, width=100,
        bg="#111", fg="#00ff00", insertbackground="#0f0", font=log_font, borderwidth=2, relief="flat"
    )
    output_box.configure(state=tk.DISABLED)
    output_box.pack(padx=20, pady=(0, 10), fill=tk.BOTH, expand=True)

    def log(msg):
        output_box.after(0, lambda: append_log(msg))

    def append_log(msg):
        output_box.configure(state=tk.NORMAL)
        output_box.insert(tk.END, msg)
        output_box.see(tk.END)
        output_box.configure(state=tk.DISABLED)

    status_label = tk.Label(
        window, text="📂 Click here to load your Base.json",
        bg="#1e1e1e", fg="#888", font=label_font,
        relief="ridge", bd=2, padx=10, pady=6, cursor="hand2"
    )
    status_label.pack(pady=(0, 10))

    apply_btn = tk.Button(
        window, text="▶ APPLY FROM BASE", state=tk.DISABLED,
        bg="#00ff00", fg="#000", font=label_font,
        padx=30, pady=10, bd=0,
        activebackground="#55ff55", activeforeground="#000",
        cursor="hand2"
    )
    apply_btn.pack(pady=(0, 20))

    def pick_base_file():
        global selected_base_path
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if path and path.lower().endswith("base.json"):
            selected_base_path = path
            status_label.config(text=f"✔ Base.json loaded", fg="#0f0")
            apply_btn.config(state=tk.NORMAL)
            log(f"📥 Loaded Base.json from: {path}\n\n")
        elif path:
            messagebox.showerror("Invalid File", "Please select a valid Base.json file.")

    status_label.bind("<Button-1>", lambda e: pick_base_file())
    apply_btn.config(command=lambda: run_all(log, selected_base_path, apply_btn))

    window.mainloop()


if __name__ == "__main__":
    build_gui()
