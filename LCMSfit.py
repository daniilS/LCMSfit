# /// script
# dependencies = [
#   "numpy",
#   "scipy",
#   "pybaselines",
#   "matplotlib",
# ]
# ///


import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from tkinter.filedialog import askopenfilename, asksaveasfilename

try:
    import numpy as np
    import pybaselines
    from matplotlib.backend_bases import _Mode
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    from matplotlib.figure import Figure
    from scipy.optimize import curve_fit
except ImportError:
    import pip
    import platform
    import sys
    
    pip_command = "pip" if platform.system == "Windows" else "python3 -m pip"
    
    if sys.argv[0] != "" and pip.__version__.split(".")[0] >= 26:
        install_command = f"{install --requirements-from-script {sys.argv[0]}"
    else:
        install_command = "install numpy scipy pybaselines matplotlib"

    message = f"Failed to import dependencies. Please install them using the following command:\n\n{pip_command} {install_command}"
    
    messagebox.showerror("Error", message)
    raise
    

ICON_DATA =  r"R0lGODlhMAAwAPUAAAAAAJa5oJW6oJS7oJW7oJS6oZW6oZW7oZa7oJa6oZa7oZe7oZS6opS7opW7opa6ope7ope7o5W8oJS8oZW8oZa8oZW8opa8opi7o5i8pJm8pJ+7qJ+7qaC7qaK7qqK7q6S7raW7rae7rq+7s7K7trO7t7S7uLe7u7m5ubi6urm6uri7u7m7u7q6urq7u7i8vLm8vLm9vbq8vLu8vAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACH5BAEAAAAALAAAAAAwADAAAAbTQIBwSCwaj8ikcslsOp/QqHRKrVqv2Kx2y+0CYDCVt6kqm8Vj5PkMSxvXa3cRHpcL6Wf7HV/Wf/l+e3BtSggIZDAmS3R3RoaPkG+DhEdlYUOWQ5Cbj0NhfCqUS2GEFZynGaB1T6anpyKqZqJLra6cGCSxfU62th26u7S9tibATcO2sMZLyK6/y4XNnM+6TNKcG8Bo0deP1LHW3Y/K1czihrnl4d3Z0MLdI7qXvNfk4FDSqe6syEKfoFUM1Yo0h86sgAJHgdkWqKHDhxAjSpxIsWKTIAA7"


class LCMSfit(tk.Tk):
    def __init__(self):
        super().__init__()        
        self.withdraw()
        
        icon_image = tk.PhotoImage(data=ICON_DATA)
        self.iconphoto(True, icon_image)

        self.load_data()
        self.populate()

        self.deiconify()
        self.mainloop()

    def load_data(self):
        self.filename = askopenfilename(
            filetypes=(("CSV files", "*.csv"), ("All files", "*.*"))
        )
        if not self.filename:
            raise SystemExit("No file selected")

        self.xdata, self.ydata = np.genfromtxt(self.filename, delimiter=",", encoding="utf-8-sig").T
        self.peaks = []
        self.peak_artists = []

    def populate(self):
        self.fig = Figure(layout="tight", figsize=(6.4, 3.6))
        self.ax = self.fig.add_subplot(111)
        self.ax.plot(self.xdata, self.ydata)

        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.mpl_connect("button_press_event", self.onclick)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, columnspan=3, sticky="nesw")

        self.toolbar = NavigationToolbar2Tk(self.canvas, self, pack_toolbar=False)
        self.toolbar.grid(row=1, column=0, columnspan=3, sticky="nesw")

        self.baseline_label = ttk.Label(self, text="Baseline smoothness:")
        self.baseline_label.grid(row=2, column=0, sticky="nesw", pady=10, padx=(10, 0))

        self.slider = ttk.Scale(
            self, from_=-2, to=11, value=5, command=self.fit_baseline
        )
        self.slider.grid(row=2, column=1, columnspan=2, sticky="nesw", pady=10, padx=20)
        self.fit_baseline()

        self.fit_button = ttk.Button(self, text="Fit", command=self.fitpeaks)
        self.fit_button.grid(row=4, column=0, sticky="w", padx=(10, 0), pady=(0, 10))

        self.save_button = ttk.Button(
            self, text="Save peaks", command=self.savepeaks, state="disabled"
        )
        self.save_button.grid(row=4, column=1, sticky="w", padx=(10, 0), pady=(0, 10))
        
        self.save_curves_button = ttk.Button(
            self, text="Save baseline corrected trace", command=self.savecurves, state="disabled"
        )
        self.save_curves_button.grid(row=4, column=2, sticky="w", padx=(10, 0), pady=(0, 10))

        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)

        self.title("Select peaks to fit")

    def find_nearest(self, x, y, xdata, ydata):
        dist = np.hypot(x - xdata, (y - ydata) / self.ax.get_data_ratio())
        indmin = dist.argmin()
        return indmin

    def onclick(self, event):
        if event.inaxes is None or self.toolbar.mode != _Mode.NONE:
            return
        if event.button == 3:
            # remove the closest peak to the click
            if len(self.peaks) == 0:
                return
            indmin = self.find_nearest(
                event.xdata, event.ydata, self.xdata[self.peaks], self.ydata[self.peaks]
            )
            self.peaks.pop(indmin)
            self.peak_artists.pop(indmin).remove()
        else:
            indmin = self.find_nearest(event.xdata, event.ydata, self.xdata, self.ydata)
            self.peaks.append(indmin)
            datacoord = self.xdata[indmin], self.ydata[indmin]
            self.peak_artists.append(self.ax.plot(datacoord[0], datacoord[1], "ko")[0])
        self.canvas.draw()

    def sigmoid(self, x, range, bias, midpoint, scale):
        return range / (1 + np.exp(-scale * (x - midpoint))) + bias

    def gaussian(self, x, amplitude, midpoint, stddev):
        return amplitude * np.exp(-((x - midpoint) ** 2) / (2 * stddev**2))

    def gaussian_integral(self, amplitude, midpoint, stddev):
        return amplitude * np.sqrt(2 * np.pi) * np.abs(stddev)

    @property
    def lambda_baseline(self):
        return 10 ** self.slider.get()

    def fit_baseline(self, *args, **kwargs):
        self.baseline, _ = pybaselines.whittaker.derpsalsa(
            self.ydata, lam=self.lambda_baseline, x_data=self.xdata, k=max(self.ydata)/2
        )
        if hasattr(self, "baseline_plot"):
            try:
                self.baseline_plot.remove()
            except NotImplementedError:
                pass
        self.baseline_plot = self.ax.plot(
            self.xdata, self.baseline, color="red", linewidth=0.5
        )[0]
        self.canvas.draw()

    def fitpeaks(self):
        try:
            self.tk.eval("tk busy .")
            self.update()
            p0 = []
            lb = []
            ub = []
            for index in sorted(self.peaks):
                p0.extend(
                    [self.ydata[index] - self.baseline[index], self.xdata[index], 0.025]
                )
                lb.extend([0, -np.inf, -np.inf])
                ub.extend([np.inf, np.inf, np.inf])
            for i in range(1 + 3, 1 + len(p0) - 3, 3):
                lb[i] = p0[i - 3]
                ub[i] = p0[i + 3]
            self.last_popt, _ = curve_fit(
                self.model_function, self.xdata, self.ydata, p0=p0, bounds=(lb, ub)
            )
            self.show_fit(self.last_popt)
        finally:
            self.tk.eval("tk busy forget .")

    def show_fit(self, popt):
        self.ax.clear()
        self.ax.plot(self.xdata, self.ydata)
        self.ax.plot(self.xdata, self.model_function(self.xdata, *popt), color="black")

        for i in range(0, len(popt), 3):
            peak = self.gaussian(self.xdata, *popt[i : i + 3])
            self.ax.plot(self.xdata, self.baseline + peak, color="gray", linewidth=0.5)

        self.peak_artists = []
        for indmin in self.peaks:
            datacoord = self.xdata[indmin], self.ydata[indmin]
            self.peak_artists.append(self.ax.plot(datacoord[0], datacoord[1], "ko")[0])

        self.fit_baseline()
        self.canvas.draw()

        self.save_button["state"] = "!disabled"
        self.save_curves_button["state"] = "!disabled"

    def model_function(self, x, *args):
        peaks = np.zeros_like(x)
        for i in range(0, len(args), 3):
            peaks += self.gaussian(x, *args[i : i + 3])
        return self.baseline + peaks

    def savepeaks(self):
        input_path = Path(self.filename)
        output_filename = asksaveasfilename(
            filetypes=[["CSV file", "*.csv"]],
            defaultextension=".csv",
            initialdir=input_path.parent,
            initialfile=input_path.stem + "_areas.csv",
        )
        if not output_filename:
            return
        try:
            with open(output_filename, "w") as f:
                f.write("time,area\n")

                times = [
                    self.last_popt[i + 1] for i in range(0, len(self.last_popt), 3)
                ]
                areas = [
                    self.gaussian_integral(*self.last_popt[i : i + 3])
                    for i in range(0, len(self.last_popt), 3)
                ]
                for time, area in sorted(zip(times, areas)):
                    f.write(f"{time},{area}\n")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def savecurves(self):
            input_path = Path(self.filename)
            output_filename = asksaveasfilename(
                filetypes=[["CSV file", "*.csv"]],
                defaultextension=".csv",
                initialdir=input_path.parent,
                initialfile=input_path.stem + "_baseline_corrected_trace.csv",
            )
            if not output_filename:
                return
            try:
                with open(output_filename, "w") as f:
                    f.write("time,raw trace,baseline curve,corrected trace\n")
                    for time, raw_data, baseline_data, corrected_data in zip(self.xdata, self.ydata, self.baseline, self.ydata-self.baseline):
                        f.write(f"{time},{raw_data},{baseline_data},{corrected_data}\n")
            except Exception as e:
                messagebox.showerror("Error", str(e))


if __name__ == "__main__":
    LCMSfit()

# TODO:
# - select new file after fitting
