import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter
from matplotlib.gridspec import GridSpec


# ─────────────────────────────────────────────────────────────────────────────
#  Regression functions  (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────

def linear_least_squares(x, y):
    n = len(x)
    m = (np.sum(x * y) - np.sum(x) * np.sum(y) / n) / (np.sum(x**2) - (np.sum(x)**2) / n)
    b = np.mean(y) - m * np.mean(x)
    return m, b

def inverted_least_squares(x, y):
    n = len(x)
    m_inv = (np.sum(x * y) - np.sum(x) * np.sum(y) / n) / (np.sum(y**2) - (np.sum(y)**2) / n)
    m_inv1 = (np.sum(x * y) - np.sum(x) * np.sum(y) / n) / (np.sum(y**2) - (np.sum(y)**2) / n)
    b_inv = np.mean(x) - m_inv * np.mean(y)
    m_inv = 1 / m_inv
    b_inv = -b_inv / m_inv1
    return m_inv, b_inv

def orthogonal_regression(x, y, error_variance_ratio):
    x_mean, y_mean = np.mean(x), np.mean(y)
    Sxx = np.sum((x - x_mean)**2)
    Syy = np.sum((y - y_mean)**2)
    Sxy = np.sum((x - x_mean) * (y - y_mean))
    lambda_param = error_variance_ratio
    numerator = Syy - lambda_param * Sxx + np.sqrt((Syy - lambda_param * Sxx)**2 + 4 * lambda_param * Sxy**2)
    denominator = 2 * Sxy
    m_orth = numerator / denominator
    b_orth = y_mean - m_orth * x_mean
    return m_orth, b_orth

def standard_deviation(x, y, m, b):
    residuals = y - (m * x + b)
    return np.std(residuals)

def calculate_r_squared(x, y, m, b):
    y_pred = m * x + b
    ss_total = np.sum((y - np.mean(y))**2)
    ss_residual = np.sum((y - y_pred)**2)
    return 1 - (ss_residual / ss_total)

def calculate_errors(x, std_dev):
    n = len(x)
    x_mean = np.mean(x)
    slope_error = std_dev / np.sqrt(np.sum((x - x_mean)**2))
    intercept_error = std_dev * np.sqrt(1 / n + (x_mean**2) / np.sum((x - x_mean)**2))
    return slope_error, intercept_error

def calculate_confidence_intervals(x, y, m, b, std_dev):
    y_pred = m * x + b
    ci_upper = y_pred + 1.96 * std_dev
    ci_lower = y_pred - 1.96 * std_dev
    return ci_lower, ci_upper

def plot_and_save(x, y, m, b, ci_lower, ci_upper, title, color, filename):
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color='black', label='Data Points', alpha=0.7)
    plt.plot(x, m * x + b, label='Regression Line', color=color)
    plt.fill_between(x, ci_lower, ci_upper, color=color, alpha=0.2, label='95% Confidence Interval')
    legend = plt.legend(fontsize=15, frameon=True, edgecolor='black', facecolor='white')
    legend.get_frame().set_linewidth(2.5)
    plt.xlabel(x_axis_label, fontsize=20, fontweight='bold')
    plt.ylabel(y_axis_label, fontsize=20, fontweight='bold')
    plt.xticks(fontsize=12, fontweight='bold')
    plt.yticks(fontsize=12, fontweight='bold')
    plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
    plt.title(title, fontsize=14)
    plt.grid(True)
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    plt.close()


# ─────────────────────────────────────────────────────────────────────────────
#  NEW  ──  Residual analysis helpers
# ─────────────────────────────────────────────────────────────────────────────

def compute_residuals_obs(x_obs, y_obs, m, b):
    """
    Standard residuals against the observed y values.
    Used for Linear LS, Inverted LS, and Orthogonal.
    """
    return y_obs - (m * x_obs + b)

def compute_residuals_gor1(x_obs, y_obs, y_true, m_gor1, b_gor1):
    """
    GOR1 is fitted on (x_obs, y_true).
    • Fitted residuals (for the fit itself)  = y_true  - (m*x_obs + b)
    • Observed residuals (vs raw data)       = y_obs   - (m*x_obs + b)
    We plot BOTH so the user can see how well the line sits against
    the original data as well as the projected points.
    """
    res_fit = y_true - (m_gor1 * x_obs + b_gor1)   # residuals of the GOR1 fit
    res_obs = y_obs  - (m_gor1 * x_obs + b_gor1)   # residuals vs observed y
    return res_fit, res_obs

def residual_statistics(residuals):
    n   = len(residuals)
    mu  = np.mean(residuals)
    std = np.std(residuals, ddof=1)
    rmse = np.sqrt(np.mean(residuals**2))
    mae  = np.mean(np.abs(residuals))
    return {"n": n, "mean": mu, "std": std, "rmse": rmse, "mae": mae}


def _style_ax(ax):
    """Apply a clean, consistent look to a residual sub-axis."""
    ax.set_facecolor("#F8F9FB")
    ax.grid(True, color="#E4E7EE", linewidth=0.7, zorder=0)
    for sp in ax.spines.values():
        sp.set_edgecolor('#CBD0DC')
        sp.set_linewidth(0.6)
    ax.tick_params(labelsize=9)


def _stats_panel(ax, stats, color):
    """Draw a mini statistics table inside an axes."""
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_facecolor("#F8F9FB")
    for sp in ax.spines.values():
        sp.set_edgecolor('#CBD0DC'); sp.set_linewidth(0.6)
    ax.set_title("Statistics", fontsize=10, fontweight='bold', color='#2C2C2A')

    rows = [
        ("n",        f"{stats['n']}"),
        ("Mean",     f"{stats['mean']:+.5f}"),
        ("Std Dev",  f"{stats['std']:.5f}"),
        ("RMSE",     f"{stats['rmse']:.5f}"),
        ("MAE",      f"{stats['mae']:.5f}"),
    ]
    cell_h, y0 = 0.14, 0.87
    for label, val in rows:
        ax.text(0.07, y0, label, fontsize=9, color='#555', va='center',
                transform=ax.transAxes)
        ax.text(0.93, y0, val,   fontsize=9, color='#2C2C2A', va='center',
                ha='right', fontweight='bold', transform=ax.transAxes)
        sep = y0 - cell_h * 0.4
        ax.plot([0.04, 0.96], [sep, sep], color='#E4E7EE', lw=0.6,
                transform=ax.transAxes, clip_on=False)
        y0 -= cell_h


def plot_residual_panel(x_obs, y_fit, residuals, label, color, out_path,
                        x_axis_label, y_axis_label,
                        extra_label=None, extra_residuals=None):
    """
    Four-panel residual diagnostic figure for one regression method.

    Panels:
      1 – Residuals vs Fitted
      2 – Residuals vs X (x_obs)
      3 – Histogram of residuals
      4 – Summary statistics table

    For GOR1 an optional second residual series (vs observed y) is overlaid.
    """
    fig = plt.figure(figsize=(18, 5), facecolor='white')
    fig.suptitle(f"Residual Analysis — {label}",
                 fontsize=14, fontweight='bold', color='#2C2C2A', y=1.01)

    gs = GridSpec(1, 4, figure=fig, wspace=0.38)

    # ── Panel 1 : Residuals vs Fitted ────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    _style_ax(ax1)
    ax1.scatter(y_fit, residuals, color=color, s=28, alpha=0.75,
                edgecolors='white', linewidths=0.4, zorder=3, label=label)
    if extra_residuals is not None:
        ax1.scatter(y_fit, extra_residuals, color='#888888', s=18, alpha=0.5,
                    edgecolors='white', linewidths=0.3, zorder=2,
                    label=extra_label, marker='^')
        ax1.legend(fontsize=7, frameon=True)
    ax1.axhline(0, color='#333', lw=0.9, ls='--', zorder=4)
    ax1.set_xlabel("Fitted values", fontsize=9, color='#2C2C2A')
    ax1.set_ylabel("Residuals",     fontsize=9, color='#2C2C2A')
    ax1.set_title("Residuals vs Fitted", fontsize=10, fontweight='bold', color='#2C2C2A')

    # ── Panel 2 : Residuals vs X ─────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    _style_ax(ax2)
    ax2.scatter(x_obs, residuals, color=color, s=28, alpha=0.75,
                edgecolors='white', linewidths=0.4, zorder=3, label=label)
    if extra_residuals is not None:
        ax2.scatter(x_obs, extra_residuals, color='#888888', s=18, alpha=0.5,
                    edgecolors='white', linewidths=0.3, zorder=2,
                    label=extra_label, marker='^')
        ax2.legend(fontsize=7, frameon=True)
    ax2.axhline(0, color='#333', lw=0.9, ls='--', zorder=4)
    ax2.set_xlabel(x_axis_label, fontsize=9, color='#2C2C2A')
    ax2.set_ylabel("Residuals",   fontsize=9, color='#2C2C2A')
    ax2.set_title("Residuals vs X", fontsize=10, fontweight='bold', color='#2C2C2A')

    # ── Panel 3 : Histogram ───────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    _style_ax(ax3)
    n_bins = max(8, int(np.sqrt(len(residuals))))
    ax3.hist(residuals, bins=n_bins, color=color, alpha=0.70,
             edgecolor='white', lw=0.5, zorder=3, label=label)
    if extra_residuals is not None:
        ax3.hist(extra_residuals, bins=n_bins, color='#888888', alpha=0.45,
                 edgecolor='white', lw=0.5, zorder=2, label=extra_label)
        ax3.legend(fontsize=7, frameon=True)
    ax3.axvline(0, color='#333', lw=0.9, ls='--', zorder=4)
    ax3.set_xlabel("Residual", fontsize=9, color='#2C2C2A')
    ax3.set_ylabel("Count",    fontsize=9, color='#2C2C2A')
    ax3.set_title("Residual Distribution", fontsize=10, fontweight='bold', color='#2C2C2A')

    # ── Panel 4 : Statistics ──────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[0, 3])
    _stats_panel(ax4, residual_statistics(residuals), color)

    fig.savefig(out_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  Residual plot saved: {out_path}")


def plot_combined_residuals(methods_data, out_path):
    """
    One figure with one row per method, each row having 3 sub-panels:
      Residuals vs Fitted  |  Residuals vs X  |  Histogram
    Plus a colour-coded title strip per row.
    """
    n = len(methods_data)
    fig, axes = plt.subplots(n, 3, figsize=(15, 4.5 * n), facecolor='white')
    fig.suptitle("Residual Analysis — All Methods",
                 fontsize=16, fontweight='bold', color='#2C2C2A', y=1.005)

    if n == 1:
        axes = [axes]          # ensure 2-D indexing

    for row, md in enumerate(methods_data):
        label     = md["label"]
        color     = md["color"]
        x         = md["x_obs"]
        y_fit     = md["y_fit"]
        residuals = md["residuals"]

        for col in range(3):
            _style_ax(axes[row][col])

        # row label
        axes[row][0].set_ylabel(label, fontsize=11, fontweight='bold',
                                color=color, labelpad=10)

        # residuals vs fitted
        axes[row][0].scatter(y_fit, residuals, color=color, s=25,
                             alpha=0.75, edgecolors='white', lw=0.4, zorder=3)
        axes[row][0].axhline(0, color='#333', lw=0.8, ls='--', zorder=4)
        axes[row][0].set_xlabel("Fitted values", fontsize=8)
        axes[row][0].set_ylabel("Residuals",     fontsize=8)
        if row == 0:
            axes[row][0].set_title("Residuals vs Fitted",
                                   fontsize=10, fontweight='bold')

        # residuals vs x
        axes[row][1].scatter(x, residuals, color=color, s=25,
                             alpha=0.75, edgecolors='white', lw=0.4, zorder=3)
        axes[row][1].axhline(0, color='#333', lw=0.8, ls='--', zorder=4)
        axes[row][1].set_xlabel("X (observed)", fontsize=8)
        axes[row][1].set_ylabel("Residuals",    fontsize=8)
        if row == 0:
            axes[row][1].set_title("Residuals vs X",
                                   fontsize=10, fontweight='bold')

        # histogram
        n_bins = max(8, int(np.sqrt(len(residuals))))
        axes[row][2].hist(residuals, bins=n_bins, color=color, alpha=0.72,
                          edgecolor='white', lw=0.5, zorder=3)
        axes[row][2].axvline(0, color='#333', lw=0.8, ls='--', zorder=4)
        axes[row][2].set_xlabel("Residual", fontsize=8)
        axes[row][2].set_ylabel("Count",    fontsize=8)
        if row == 0:
            axes[row][2].set_title("Residual Distribution",
                                   fontsize=10, fontweight='bold')

        # GOR1 special note
        if "note" in md:
            axes[row][0].text(0.98, 0.97, md["note"],
                              transform=axes[row][0].transAxes,
                              fontsize=7, ha='right', va='top',
                              color='#555', style='italic')

    plt.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"  Combined residual plot saved: {out_path}")


# ─────────────────────────────────────────────────────────────────────────────
#  User input  (unchanged from original)
# ─────────────────────────────────────────────────────────────────────────────

input_file = input("Enter the earthquake data file (e.g., '302_d.dat'): ")
x_main      = input("Enter the main part of the X-axis label (e.g., 'm'): ")
x_subscript = input("Enter the subscript for the X-axis label (e.g., 'b,ISC'): ")
y_main      = input("Enter the main part of the Y-axis label (e.g., 'M'): ")
y_subscript = input("Enter the subscript for the Y-axis label (e.g., 'w,gmt'): ")

def format_label(main, subscript):
    return f"${main}_{{{subscript}}}$"

x_axis_label = format_label(x_main, x_subscript)
y_axis_label = format_label(y_main, y_subscript)

# ─────────────────────────────────────────────────────────────────────────────
#  Load data  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

data  = np.loadtxt(input_file)
x_obs = data[:, 0]
y_obs = data[:, 1]

file_name_without_extension = os.path.splitext(input_file)[0]

base_dir = r"C:\Users\Beto\Desktop\Informatica\Investigación científica\scientific-research\figures"
output_dir = os.path.join(base_dir, file_name_without_extension)
os.makedirs(output_dir, exist_ok=True)

save_paths = {
    "SLR":      os.path.join(output_dir, "b.jpeg"),
    "ISLR":     os.path.join(output_dir, "c.jpeg"),
    "GOR2":     os.path.join(output_dir, "d.jpeg"),
    "GOR1":     os.path.join(output_dir, "e.jpeg"),
    "Combined": os.path.join(output_dir, "a.jpeg"),
    "Results":  os.path.join(output_dir, "results1.dat"),
    # ── NEW residual plot paths ──────────────────────────────────────────
    "Res_SLR":      os.path.join(output_dir, "residuals_SLR.jpeg"),
    "Res_ISLR":     os.path.join(output_dir, "residuals_ISLR.jpeg"),
    "Res_GOR2":     os.path.join(output_dir, "residuals_GOR2.jpeg"),
    "Res_GOR1":     os.path.join(output_dir, "residuals_GOR1.jpeg"),
    "Res_Combined": os.path.join(output_dir, "residuals_all_methods.jpeg"),
}

# ─────────────────────────────────────────────────────────────────────────────
#  Regressions  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

m_ls, b_ls = linear_least_squares(x_obs, y_obs)
std_dev_ls  = standard_deviation(x_obs, y_obs, m_ls, b_ls)
ci_lower_ls, ci_upper_ls = calculate_confidence_intervals(x_obs, y_obs, m_ls, b_ls, std_dev_ls)

m_inv, b_inv = inverted_least_squares(x_obs, y_obs)
std_dev_inv   = standard_deviation(x_obs, y_obs, m_inv, b_inv)
ci_lower_inv, ci_upper_inv = calculate_confidence_intervals(x_obs, y_obs, m_inv, b_inv, std_dev_inv)

error_variance_ratio = float(input("Enter the error variance ratio for Orthogonal Regression (e.g., 1): "))

m_orth, b_orth = orthogonal_regression(x_obs, y_obs, error_variance_ratio)
std_dev_orth    = standard_deviation(x_obs, y_obs, m_orth, b_orth)
ci_lower_orth, ci_upper_orth = calculate_confidence_intervals(x_obs, y_obs, m_orth, b_orth, std_dev_orth)

# GOR1 — uses x_obs and y_true (projected points on the orthogonal line)
x_true  = (m_orth * (y_obs - b_orth) + error_variance_ratio * x_obs) / (error_variance_ratio + m_orth**2)
y_true  = x_true * m_orth + b_orth
m_gor1, b_gor1 = linear_least_squares(x_obs, y_true)
std_dev_gor1    = standard_deviation(x_obs, y_true, m_gor1, b_gor1)
ci_lower_gor1, ci_upper_gor1 = calculate_confidence_intervals(x_obs, y_obs, m_gor1, b_gor1, std_dev_gor1)

# ─────────────────────────────────────────────────────────────────────────────
#  Metrics  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

slope_error_ls, intercept_error_ls = calculate_errors(x_obs, std_dev_ls)
r_squared_ls = calculate_r_squared(x_obs, y_obs, m_ls, b_ls)

slope_error_inv, intercept_error_inv = calculate_errors(y_obs, std_dev_inv)
r_squared_inv = calculate_r_squared(x_obs, y_obs, m_inv, b_inv)

slope_error_orth, intercept_error_orth = calculate_errors(x_obs, std_dev_orth)
r_squared_orth = calculate_r_squared(x_obs, y_obs, m_orth, b_orth)

slope_error_gor1, intercept_error_gor1 = calculate_errors(x_obs, std_dev_gor1)
r_squared_gor1 = calculate_r_squared(x_obs, y_obs, m_gor1, b_gor1)

# ─────────────────────────────────────────────────────────────────────────────
#  Write results  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

with open(save_paths["Results"], "w") as file:
    file.write("Method\t\tSlope\tSlope Error\tIntercept\tIntercept Error\tStd Dev\t\tR^2\n")
    file.write(f"Linear LS\t{m_ls:.6f}\t{slope_error_ls:.6f}\t{b_ls:.6f}\t{intercept_error_ls:.6f}\t{std_dev_ls:.6f}\t{r_squared_ls:.6f}\n")
    file.write(f"Inverted LS\t{m_inv:.6f}\t{slope_error_inv:.6f}\t{b_inv:.6f}\t{intercept_error_inv:.6f}\t{std_dev_inv:.6f}\t{r_squared_inv:.6f}\n")
    file.write(f"Orthogonal\t{m_orth:.6f}\t{slope_error_orth:.6f}\t{b_orth:.6f}\t{intercept_error_orth:.6f}\t{std_dev_orth:.6f}\t{r_squared_orth:.6f}\n")
    file.write(f"GOR1\t\t{m_gor1:.6f}\t{slope_error_gor1:.6f}\t{b_gor1:.6f}\t{intercept_error_gor1:.6f}\t{std_dev_gor1:.6f}\t{r_squared_gor1:.6f}\n")

# ─────────────────────────────────────────────────────────────────────────────
#  Original plots  (unchanged)
# ─────────────────────────────────────────────────────────────────────────────

plot_and_save(x_obs, y_obs, m_ls,   b_ls,   ci_lower_ls,   ci_upper_ls,   "SLR",  "blue",   save_paths["SLR"])
plot_and_save(x_obs, y_obs, m_inv,  b_inv,  ci_lower_inv,  ci_upper_inv,  "ISLR", "red",    save_paths["ISLR"])
plot_and_save(x_obs, y_obs, m_orth, b_orth, ci_lower_orth, ci_upper_orth, "GOR2", "green",  save_paths["GOR2"])
plot_and_save(x_obs, y_obs, m_gor1, b_gor1, ci_lower_gor1, ci_upper_gor1, "GOR1", "purple", save_paths["GOR1"])

# Combined plot (unchanged)
plt.figure(figsize=(15, 10))
plt.scatter(x_obs, y_obs, color='black', label='Data Points', alpha=0.7)
plt.plot(x_obs, m_ls   * x_obs + b_ls,   label='SLR',  color='blue')
plt.plot(x_obs, m_inv  * x_obs + b_inv,  label='ISLR', color='red')
plt.plot(x_obs, m_orth * x_obs + b_orth, label='GOR2', color='green')
plt.plot(x_obs, m_gor1 * x_obs + b_gor1, label='GOR1', color='purple')
legend = plt.legend(fontsize=25, frameon=True, edgecolor='black', facecolor='white')
legend.get_frame().set_linewidth(2.5)
plt.xlabel(x_axis_label, fontsize=25, fontweight='bold')
plt.ylabel(y_axis_label, fontsize=25, fontweight='bold')
plt.gca().xaxis.set_major_formatter(FormatStrFormatter('%.1f'))
plt.gca().yaxis.set_major_formatter(FormatStrFormatter('%.1f'))
plt.title("Comparison of Regression Methods", fontsize=16, fontweight='bold')
plt.xticks(fontsize=15, fontweight='bold')
plt.yticks(fontsize=15, fontweight='bold')
plt.grid(True)
plt.savefig(save_paths["Combined"], dpi=300, bbox_inches='tight')
plt.close()

# Confidence interval plot with extended range (unchanged)
x_extended = np.linspace(min(x_obs) - 0.05 * (max(x_obs) - min(x_obs)),
                          max(x_obs) + 0.05 * (max(x_obs) - min(x_obs)), 500)

ci_lower_ls_ext   = m_ls   * x_extended + b_ls   - 1.96 * std_dev_ls
ci_upper_ls_ext   = m_ls   * x_extended + b_ls   + 1.96 * std_dev_ls
ci_lower_inv_ext  = m_inv  * x_extended + b_inv  - 1.96 * std_dev_inv
ci_upper_inv_ext  = m_inv  * x_extended + b_inv  + 1.96 * std_dev_inv
ci_lower_orth_ext = m_orth * x_extended + b_orth - 1.96 * std_dev_orth
ci_upper_orth_ext = m_orth * x_extended + b_orth + 1.96 * std_dev_orth
ci_lower_gor1_ext = m_gor1 * x_extended + b_gor1 - 1.96 * std_dev_gor1
ci_upper_gor1_ext = m_gor1 * x_extended + b_gor1 + 1.96 * std_dev_gor1

plt.figure(figsize=(15, 10))
plt.fill_between(x_extended, ci_lower_ls_ext,   ci_upper_ls_ext,   color='blue',   alpha=0.3, label='SLR CI')
plt.fill_between(x_extended, ci_lower_inv_ext,  ci_upper_inv_ext,  color='red',    alpha=0.3, label='ISLR CI')
plt.fill_between(x_extended, ci_lower_orth_ext, ci_upper_orth_ext, color='green',  alpha=0.3, label='GOR2 CI')
plt.fill_between(x_extended, ci_lower_gor1_ext, ci_upper_gor1_ext, color='purple', alpha=0.3, label='GOR1 CI')
plt.xlabel(x_axis_label, fontsize=20)
plt.ylabel(y_axis_label, fontsize=20)
plt.title("Regression Confidence Intervals with Extended Range", fontsize=20)
plt.legend()
plt.grid(True)
f_save_path = os.path.join(output_dir, "f.jpeg")
plt.savefig(f_save_path, dpi=300, bbox_inches='tight')
plt.show()


# ─────────────────────────────────────────────────────────────────────────────
#  NEW  ──  Residual analysis plots
# ─────────────────────────────────────────────────────────────────────────────
print("\nGenerating residual analysis plots …")

# ── Compute residuals ────────────────────────────────────────────────────────
#
#  Linear LS   : fit on (x_obs, y_obs)  → residuals vs observed y
#  Inverted LS : fit on (x_obs, y_obs)  → residuals vs observed y
#  Orthogonal  : fit on (x_obs, y_obs)  → residuals vs observed y
#  GOR1        : fit on (x_obs, y_true) → TWO residual series
#                  res_fit  = y_true  - predicted   (residuals of the GOR1 fit itself)
#                  res_obs  = y_obs   - predicted   (residuals vs original observed y)

res_ls   = compute_residuals_obs(x_obs, y_obs, m_ls,   b_ls)
res_inv  = compute_residuals_obs(x_obs, y_obs, m_inv,  b_inv)
res_orth = compute_residuals_obs(x_obs, y_obs, m_orth, b_orth)

res_gor1_fit, res_gor1_obs = compute_residuals_gor1(x_obs, y_obs, y_true, m_gor1, b_gor1)

# Fitted (predicted) y values for each method
y_fit_ls   = m_ls   * x_obs + b_ls
y_fit_inv  = m_inv  * x_obs + b_inv
y_fit_orth = m_orth * x_obs + b_orth
y_fit_gor1 = m_gor1 * x_obs + b_gor1

# ── Individual residual plots ────────────────────────────────────────────────

plot_residual_panel(
    x_obs, y_fit_ls, res_ls,
    label="Linear LS (SLR)", color="blue",
    out_path=save_paths["Res_SLR"],
    x_axis_label=x_axis_label, y_axis_label=y_axis_label
)

plot_residual_panel(
    x_obs, y_fit_inv, res_inv,
    label="Inverted LS (ISLR)", color="red",
    out_path=save_paths["Res_ISLR"],
    x_axis_label=x_axis_label, y_axis_label=y_axis_label
)

plot_residual_panel(
    x_obs, y_fit_orth, res_orth,
    label="Orthogonal (GOR2)", color="green",
    out_path=save_paths["Res_GOR2"],
    x_axis_label=x_axis_label, y_axis_label=y_axis_label
)

# GOR1: fit was on (x_obs, y_true) → residuals = y_true − (m_gor1·x_obs + b_gor1)
plot_residual_panel(
    x_obs, y_fit_gor1, res_gor1_fit,
    label="GOR1", color="purple",
    out_path=save_paths["Res_GOR1"],
    x_axis_label=x_axis_label, y_axis_label=y_axis_label
)

# ── Combined residual overview (one row per method, uses y_obs residuals) ────
#    For GOR1 the "observed residuals" (y_obs - predicted) are used
#    so the comparison is on the same footing as the other three methods.

methods_data = [
    {"label": "Linear LS (SLR)",      "color": "blue",
     "x_obs": x_obs, "y_fit": y_fit_ls,   "residuals": res_ls},
    {"label": "Inverted LS (ISLR)",   "color": "red",
     "x_obs": x_obs, "y_fit": y_fit_inv,  "residuals": res_inv},
    {"label": "Orthogonal (GOR2)",    "color": "green",
     "x_obs": x_obs, "y_fit": y_fit_orth, "residuals": res_orth},
    {"label": "GOR1",                 "color": "purple",
     "x_obs": x_obs, "y_fit": y_fit_gor1, "residuals": res_gor1_fit,
     "note": "residuals = y_true − ŷ  (fit: x_obs vs y_true)"},
]

plot_combined_residuals(methods_data, save_paths["Res_Combined"])

# ── Print residual statistics to console ─────────────────────────────────────
print("\n" + "="*72)
print(f"{'RESIDUAL STATISTICS':^72}")
print("="*72)
header = f"{'Method':<22} {'n':>5} {'Mean':>12} {'Std Dev':>12} {'RMSE':>12} {'MAE':>12}"
print(header)
print("-"*72)

for label, residuals in [
    ("Linear LS (SLR)",    res_ls),
    ("Inverted LS (ISLR)", res_inv),
    ("Orthogonal (GOR2)",  res_orth),
    ("GOR1",               res_gor1_fit),
]:
    st = residual_statistics(residuals)
    print(f"{label:<22} {st['n']:>5} {st['mean']:>+12.6f} {st['std']:>12.6f} "
          f"{st['rmse']:>12.6f} {st['mae']:>12.6f}")

print("="*72)
print("\nAll files saved to:", output_dir)