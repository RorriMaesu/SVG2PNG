import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
import threading
import asyncio
from playwright.async_api import async_playwright
import logging
from queue import Queue
import tempfile
import shutil
import platform
import traceback

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SVGToPNGConverterPro:
    def __init__(self, master):
        self.master = master
        master.title("SVG to PNG Converter Pro")
        master.geometry("750x450")
        master.resizable(False, False)
        
        self.temp_dir = Path(tempfile.mkdtemp(prefix="svg_convert_"))
        self.user_data_dir = self.temp_dir / "browser_data"
        
        self.queue = Queue()
        self.conversion_running = False
        self.shutting_down = False

        self.create_widgets()
        self.master.protocol("WM_DELETE_WINDOW", self.safe_shutdown)
        self.master.after(100, self.process_queue)

    def create_widgets(self):
        self.master.grid_columnconfigure(1, weight=1)
        
        ttk.Label(self.master, text="Input SVG File:").grid(row=0, column=0, padx=10, pady=5, sticky="w")
        self.input_entry = ttk.Entry(self.master, width=50)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.master, text="Browse", command=self.browse_svg).grid(row=0, column=2, padx=5, pady=5)

        ttk.Label(self.master, text="Output PNG File:").grid(row=1, column=0, padx=10, pady=5, sticky="w")
        self.output_entry = ttk.Entry(self.master, width=50)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(self.master, text="Browse", command=self.browse_png).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(self.master, text="DPI (72-600):").grid(row=2, column=0, padx=10, pady=5, sticky="w")
        self.dpi_combobox = ttk.Combobox(self.master, values=[72, 96, 150, 300, 600], width=8)
        self.dpi_combobox.set(300)
        self.dpi_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.transparent_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.master, text="Transparent Background", variable=self.transparent_var).grid(
            row=3, column=1, padx=5, pady=5, sticky="w")

        self.convert_btn = ttk.Button(
            self.master, 
            text="Convert to PNG", 
            command=self.start_conversion,
            state=tk.NORMAL
        )
        self.convert_btn.grid(row=4, column=1, pady=15)

        self.status_frame = ttk.Frame(self.master)
        self.status_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=10)
        
        self.progress = ttk.Progressbar(
            self.status_frame, 
            orient=tk.HORIZONTAL, 
            mode='indeterminate'
        )
        self.progress.pack(fill=tk.X, expand=True)
        
        self.status_label = ttk.Label(
            self.status_frame, 
            text="Ready", 
            foreground="gray",
            anchor=tk.W
        )
        self.status_label.pack(fill=tk.X, expand=True)

    def browse_svg(self):
        try:
            path = filedialog.askopenfilename(
                filetypes=[("SVG Files", "*.svg"), ("All Files", "*.*")]
            )
            if path:
                self.validate_svg(path)
                self.input_entry.delete(0, tk.END)
                self.input_entry.insert(0, path)
                self.suggest_output_path(path)
        except Exception as e:
            self.queue.put(("error", f"File selection error: {str(e)}"))

    def browse_png(self):
        try:
            default = self.output_entry.get() or "converted_image.png"
            path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG Files", "*.png"), ("All Files", "*.*")],
                initialfile=default
            )
            if path:
                self.output_entry.delete(0, tk.END)
                self.output_entry.insert(0, path)
        except Exception as e:
            self.queue.put(("error", f"Output path error: {str(e)}"))

    def suggest_output_path(self, input_path):
        try:
            input_path = Path(input_path)
            output_path = input_path.with_suffix('.png')
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, str(output_path))
        except Exception as e:
            logging.error(f"Path suggestion error: {str(e)}")

    def validate_svg(self, path):
        try:
            with open(path, 'rb') as f:
                header = f.read(1024).decode('utf-8', 'ignore').lower()
                if not ('<svg' in header and 'xmlns="http://www.w3.org/2000/svg"' in header):
                    raise ValueError("File doesn't contain valid SVG declaration")
                if '<!--' in header and '-->' not in header:
                    raise ValueError("Malformed SVG comment syntax")
        except UnicodeDecodeError:
            raise ValueError("File is not text-based SVG")
        except Exception as e:
            raise ValueError(f"File validation failed: {str(e)}")

    def start_conversion(self):
        if self.conversion_running:
            return

        input_path = self.input_entry.get().strip()
        output_path = self.output_entry.get().strip()
        
        try:
            self.validate_paths(input_path, output_path)
            dpi = int(self.dpi_combobox.get())
            if not 72 <= dpi <= 600:
                raise ValueError("DPI must be between 72 and 600")
            
            self.conversion_running = True
            self.convert_btn.config(state=tk.DISABLED)
            self.progress.start()
            self.status_label.config(text="Initializing conversion...", foreground="blue")
            
            threading.Thread(
                target=self.run_async_conversion,
                args=(input_path, output_path, dpi),
                daemon=True
            ).start()
            
        except Exception as e:
            self.queue.put(("error", f"Validation error: {str(e)}"))
            self.reset_ui_state()

    def validate_paths(self, input_path, output_path):
        errors = []
        if not input_path:
            errors.append("Input file path is required")
        if not output_path:
            errors.append("Output file path is required")
        
        if errors:
            raise ValueError("\n".join(errors))
        
        input_path = Path(input_path)
        if not input_path.exists():
            raise ValueError(f"Input file not found: {input_path}")
        if input_path.suffix.lower() != ".svg":
            raise ValueError("Input file must be an SVG file")
        
        output_path = Path(output_path)
        if not output_path.parent.exists():
            raise ValueError(f"Output directory does not exist: {output_path.parent}")
        if output_path.exists():
            if not messagebox.askyesno("Overwrite?", "Output file exists. Overwrite?"):
                raise ValueError("Conversion canceled by user")

    async def perform_conversion(self, input_path, output_path, dpi):
        browser = None
        temp_html = None
        try:
            async with async_playwright() as p:
                # Create HTML wrapper for SVG content
                svg_path = Path(input_path)
                svg_content = svg_path.read_text(encoding='utf-8', errors='ignore')
                temp_html = self.temp_dir / "temp_conversion.html"
                temp_html.write_text(f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <style>
                        body {{
                            margin: 0;
                            padding: 20px;
                            background: {"transparent" if self.transparent_var.get() else "white"};
                        }}
                        svg {{
                            max-width: 100%;
                            height: auto;
                        }}
                    </style>
                </head>
                <body>
                    {svg_content}
                </body>
                </html>
                """, encoding='utf-8')

                browser = await p.chromium.launch_persistent_context(
                    str(self.user_data_dir),
                    headless=True,
                    args=[
                        "--disable-gpu",
                        "--disable-dev-shm-usage",
                        "--no-sandbox"
                    ],
                    device_scale_factor=dpi/96,
                    viewport=None,
                    java_script_enabled=False,
                    timeout=60000
                )
                
                page = await browser.new_page()
                await page.goto(f"file://{temp_html.resolve()}", wait_until="load", timeout=30000)

                dimensions = await page.evaluate('''() => {
                    const svg = document.querySelector('svg');
                    if (!svg) return null;

                    let width = 300;
                    let height = 150;
                    const padding = 20;

                    try {
                        if (svg.viewBox && svg.viewBox.baseVal) {
                            width = svg.viewBox.baseVal.width || width;
                            height = svg.viewBox.baseVal.height || height;
                        }
                        if (svg.width && svg.width.baseVal) {
                            width = svg.width.baseVal.value || width;
                        }
                        if (svg.height && svg.height.baseVal) {
                            height = svg.height.baseVal.value || height;
                        }
                    } catch(e) {
                        console.warn('Dimension detection error:', e);
                    }

                    return {
                        width: Math.ceil(width + padding * 2),
                        height: Math.ceil(height + padding * 2)
                    };
                }''')

                if not dimensions:
                    raise RuntimeError("Failed to measure SVG dimensions")

                await page.set_viewport_size(dimensions)
                await page.wait_for_timeout(250)
                
                screenshot_params = {
                    "type": "png",
                    "omit_background": self.transparent_var.get(),
                    "path": output_path,
                    "timeout": 60000,
                    "full_page": False
                }

                retries = 3
                for attempt in range(retries):
                    try:
                        await page.screenshot(**screenshot_params)
                        return True
                    except Exception as e:
                        if attempt == retries - 1:
                            raise
                        await page.wait_for_timeout(500)
                        
        except Exception as e:
            logger.error(f"Conversion error: {traceback.format_exc()}")
            return False
        finally:
            try:
                if browser:
                    await browser.close()
                if temp_html and temp_html.exists():
                    temp_html.unlink()
                if (self.user_data_dir.exists() and 
                    not platform.system().startswith("Windows")):
                    shutil.rmtree(self.user_data_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Cleanup error: {str(e)}")

    def run_async_conversion(self, input_path, output_path, dpi):
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                self.perform_conversion(input_path, output_path, dpi)
            )
            
            if result:
                self.queue.put(("success", f"Successfully saved:\n{output_path}"))
            else:
                self.queue.put(("error", "Conversion failed - check logs for details"))
                
        except Exception as e:
            logger.error(f"Critical error in conversion thread: {traceback.format_exc()}")
            self.queue.put(("error", f"Conversion system error: {str(e)}"))
        finally:
            self.queue.put(("reset", None))
            loop.close()

    def process_queue(self):
        try:
            while not self.queue.empty():
                msg_type, content = self.queue.get_nowait()
                
                if msg_type == "success":
                    self.status_label.config(text=content, foreground="green")
                elif msg_type == "error":
                    self.status_label.config(text=content, foreground="red")
                    messagebox.showerror("Error", content)
                elif msg_type == "reset":
                    self.reset_ui_state()
                    
        finally:
            if not self.shutting_down:
                self.master.after(100, self.process_queue)

    def reset_ui_state(self):
        self.progress.stop()
        self.convert_btn.config(state=tk.NORMAL)
        self.conversion_running = False

    def safe_shutdown(self):
        if self.shutting_down:
            return

        def shutdown_async():
            try:
                self.shutting_down = True
                if self.temp_dir.exists():
                    shutil.rmtree(self.temp_dir, ignore_errors=True)
            except Exception as e:
                logger.error(f"Shutdown error: {str(e)}")
            finally:
                self.master.destroy()

        if self.conversion_running:
            if messagebox.askokcancel(
                "Quit", 
                "Conversion in progress. Are you sure you want to quit?"
            ):
                threading.Thread(target=shutdown_async).start()
        else:
            shutdown_async()

if __name__ == "__main__":
    root = tk.Tk()
    try:
        converter = SVGToPNGConverterPro(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start:\n{str(e)}")
        root.destroy()