"""Desktop launcher for the Windows build: runs the local server, opens the browser and shows
a small window to reopen or stop Erisma (falls back to a console if Tk is missing)."""

import socket
import sys
import threading
import time
import webbrowser


def free_port(start: int = 8000) -> int:
    for p in range(start, start + 50):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return start


def main() -> None:
    import uvicorn

    from erisma.web.app import app

    port = free_port()
    url = f"http://127.0.0.1:{port}"
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning"))
    threading.Thread(target=server.run, daemon=True).start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    webbrowser.open(url)
    try:
        import tkinter as tk
    except ImportError:  # console fallback
        print(f"Erisma: {url} — close this window to stop.")
        while True:
            time.sleep(3600)
    root = tk.Tk()
    root.title("Erisma")
    root.geometry("340x150")
    root.resizable(False, False)
    tk.Label(root, text="Erisma — στατικοί υπολογισμοί", font=("Segoe UI", 12, "bold")).pack(pady=(14, 2))
    tk.Label(root, text=f"Το πρόγραμμα τρέχει στο {url}", font=("Segoe UI", 9)).pack()
    row = tk.Frame(root)
    row.pack(pady=14)
    tk.Button(row, text="Άνοιγμα", width=12, command=lambda: webbrowser.open(url)).pack(side="left", padx=6)

    def stop() -> None:
        server.should_exit = True
        root.destroy()
    tk.Button(row, text="Τερματισμός", width=12, command=stop).pack(side="left", padx=6)
    root.protocol("WM_DELETE_WINDOW", stop)
    root.mainloop()
    sys.exit(0)


if __name__ == "__main__":
    main()
