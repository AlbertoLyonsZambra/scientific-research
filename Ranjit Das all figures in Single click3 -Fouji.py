import os  # Add this import to handle directory operations
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FormatStrFormatter


# Functions for Linear, Inverted, and Orthogonal Regressions
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
    """
    Plots the regression and saves the figure.
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, color='black', label='Data Points', alpha=0.7)
    plt.plot(x, m * x + b, label='Regression Line', color=color)
    plt.fill_between(x, ci_lower, ci_upper, color=color, alpha=0.2, label='95% Confidence Interval')
    legend = plt.legend(
        fontsize=15,
        frameon=True,
        edgecolor='black',
        facecolor='white'
    )
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

# User input for file name and axis labels

input_file = input("Enter the earthquake data file (e.g., '302_d.dat'): ")  # User enters file name
x_main = input("Enter the main part of the X-axis label (e.g., 'm'): ")  # User enters main part (e.g., 'm')
x_subscript = input("Enter the subscript for the X-axis label (e.g., 'b,ISC'): ")  # User enters subscript part (e.g., 'b,ISC')
y_main = input("Enter the main part of the Y-axis label (e.g., 'M'): ")  # User enters main part (e.g., 'M')
y_subscript = input("Enter the subscript for the Y-axis label (e.g., 'w,gmt'): ")  # User enters subscript part (e.g., 'w,gmt')

# Formatting for X-axis and Y-axis labels
def format_label(main, subscript):
    return f"${main}_{{{subscript}}}$"  # LaTeX-style formatting for subscript

# Apply formatting
x_axis_label = format_label(x_main, x_subscript)
y_axis_label = format_label(y_main, y_subscript)





# Read data from the file
data = np.loadtxt(input_file)  # Assumes the file has two columns: x and y
x_obs = data[:, 0]
y_obs = data[:, 1]


# Extract the filename without extension
file_name_without_extension = os.path.splitext(input_file)[0]

# Define the base directory and dynamically create a subdirectory
base_dir = r"C:\Users\yamca\OneDrive\Desktop\Yamir\Universidad\Semestre 9\Investigación Científica\Code\Figures"
output_dir = os.path.join(base_dir, file_name_without_extension)

# Create the directory if it doesn't exist
os.makedirs(output_dir, exist_ok=True)

# Update save paths to use the new output directory
save_paths = {
    "SLR": os.path.join(output_dir, "b.jpeg"),
    "ISLR": os.path.join(output_dir, "c.jpeg"),
    "GOR2": os.path.join(output_dir, "d.jpeg"),
    "GOR1": os.path.join(output_dir, "e.jpeg"),
    "Combined": os.path.join(output_dir, "a.jpeg"),
    "Results": os.path.join(output_dir, "results1.dat")
}

# Perform Linear Least Squares Regression
m_ls, b_ls = linear_least_squares(x_obs, y_obs)
std_dev_ls = standard_deviation(x_obs, y_obs, m_ls, b_ls)
ci_lower_ls, ci_upper_ls = calculate_confidence_intervals(x_obs, y_obs, m_ls, b_ls, std_dev_ls)

# Perform Inverted Least Squares Regression
m_inv, b_inv = inverted_least_squares(x_obs, y_obs)
std_dev_inv = standard_deviation(x_obs, y_obs, m_inv, b_inv)
ci_lower_inv, ci_upper_inv = calculate_confidence_intervals(x_obs, y_obs, m_inv, b_inv, std_dev_inv)

# Ask user for the error variance ratio for Orthogonal Regression
error_variance_ratio = float(input("Enter the error variance ratio for Orthogonal Regression (e.g., 1): "))

# Perform Orthogonal Regression
m_orth, b_orth = orthogonal_regression(x_obs, y_obs, error_variance_ratio)
std_dev_orth = standard_deviation(x_obs, y_obs, m_orth, b_orth)
ci_lower_orth, ci_upper_orth = calculate_confidence_intervals(x_obs, y_obs, m_orth, b_orth, std_dev_orth)

# Perform GOR1 Regression
x_true = (m_orth * (y_obs - b_orth) + error_variance_ratio * x_obs) / (error_variance_ratio + m_orth**2)
y_true = x_true * m_orth + b_orth
m_gor1, b_gor1 = linear_least_squares(x_obs, y_true)
std_dev_gor1 = standard_deviation(x_obs, y_true, m_gor1, b_gor1)
ci_lower_gor1, ci_upper_gor1 = calculate_confidence_intervals(x_obs, y_obs, m_gor1, b_gor1, std_dev_gor1)

# Calculate additional metrics for each regression
slope_error_ls, intercept_error_ls = calculate_errors(x_obs, std_dev_ls)
r_squared_ls = calculate_r_squared(x_obs, y_obs, m_ls, b_ls)

slope_error_inv, intercept_error_inv = calculate_errors(y_obs, std_dev_inv)
r_squared_inv = calculate_r_squared(x_obs, y_obs, m_inv, b_inv)

slope_error_orth, intercept_error_orth = calculate_errors(x_obs, std_dev_orth)
r_squared_orth = calculate_r_squared(x_obs, y_obs, m_orth, b_orth)

slope_error_gor1, intercept_error_gor1 = calculate_errors(x_obs, std_dev_gor1)
r_squared_gor1 = calculate_r_squared(x_obs, y_true, m_gor1, b_gor1)

# Write results to the dynamically created folder
with open(save_paths["Results"], "w") as file:
    file.write("Method\t\tSlope\tSlope Error\tIntercept\tIntercept Error\tStd Dev\t\tR^2\n")
    file.write(f"Linear LS\t{m_ls:.6f}\t{slope_error_ls:.6f}\t{b_ls:.6f}\t{intercept_error_ls:.6f}\t{std_dev_ls:.6f}\t{r_squared_ls:.6f}\n")
    file.write(f"Inverted LS\t{m_inv:.6f}\t{slope_error_inv:.6f}\t{b_inv:.6f}\t{intercept_error_inv:.6f}\t{std_dev_inv:.6f}\t{r_squared_inv:.6f}\n")
    file.write(f"Orthogonal\t{m_orth:.6f}\t{slope_error_orth:.6f}\t{b_orth:.6f}\t{intercept_error_orth:.6f}\t{std_dev_orth:.6f}\t{r_squared_orth:.6f}\n")
    file.write(f"GOR1\t\t{m_gor1:.6f}\t{slope_error_gor1:.6f}\t{b_gor1:.6f}\t{intercept_error_gor1:.6f}\t{std_dev_gor1:.6f}\t{r_squared_gor1:.6f}\n")

# Save plots
plot_and_save(x_obs, y_obs, m_ls, b_ls, ci_lower_ls, ci_upper_ls, "SLR", "blue", save_paths["SLR"])
plot_and_save(x_obs, y_obs, m_inv, b_inv, ci_lower_inv, ci_upper_inv, "ISLR", "red", save_paths["ISLR"])
plot_and_save(x_obs, y_obs, m_orth, b_orth, ci_lower_orth, ci_upper_orth, "GOR2", "green", save_paths["GOR2"])
plot_and_save(x_obs, y_obs, m_gor1, b_gor1, ci_lower_gor1, ci_upper_gor1, "GOR1", "purple", save_paths["GOR1"])

# Combined Plot
plt.figure(figsize=(15, 10))
plt.scatter(x_obs, y_obs, color='black', label='Data Points', alpha=0.7)
plt.plot(x_obs, m_ls * x_obs + b_ls, label='SLR', color='blue')
plt.plot(x_obs, m_inv * x_obs + b_inv, label='ISLR', color='red')
plt.plot(x_obs, m_orth * x_obs + b_orth, label='GOR2', color='green')
plt.plot(x_obs, m_gor1 * x_obs + b_gor1, label='GOR1', color='purple')
legend = plt.legend(
    fontsize=25,
    frameon=True,
    edgecolor='black',     # Border color
    facecolor='white'      # Optional: white background
)
legend.get_frame().set_linewidth(2.5)  # Make the border bold

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

# Define the extended range for X (5% beyond observed range)
x_extended = np.linspace(min(x_obs) - 0.05 * (max(x_obs) - min(x_obs)),
                          max(x_obs) + 0.05 * (max(x_obs) - min(x_obs)), 500)

# Compute confidence intervals for the extended range
ci_lower_ls_ext = m_ls * x_extended + b_ls - 1.96 * std_dev_ls
ci_upper_ls_ext = m_ls * x_extended + b_ls + 1.96 * std_dev_ls

ci_lower_inv_ext = m_inv * x_extended + b_inv - 1.96 * std_dev_inv
ci_upper_inv_ext = m_inv * x_extended + b_inv + 1.96 * std_dev_inv

ci_lower_orth_ext = m_orth * x_extended + b_orth - 1.96 * std_dev_orth
ci_upper_orth_ext = m_orth * x_extended + b_orth + 1.96 * std_dev_orth

ci_lower_gor1_ext = m_gor1 * x_extended + b_gor1 - 1.96 * std_dev_gor1
ci_upper_gor1_ext = m_gor1 * x_extended + b_gor1 + 1.96 * std_dev_gor1

# Add a plot showing all confidence intervals with extended range
plt.figure(figsize=(15, 10))

# Ensure colors for fill_between match regression lines in the legend
plt.fill_between(x_extended, ci_lower_ls_ext, ci_upper_ls_ext, color='blue', alpha=0.3, label='SLR CI')
plt.fill_between(x_extended, ci_lower_inv_ext, ci_upper_inv_ext, color='red', alpha=0.3, label='ISLR CI')
plt.fill_between(x_extended, ci_lower_orth_ext, ci_upper_orth_ext, color='green', alpha=0.3, label='GOR2 CI')
plt.fill_between(x_extended, ci_lower_gor1_ext, ci_upper_gor1_ext, color='purple', alpha=0.3, label='GOR1 CI')


# Configure labels, title, and legend
plt.xlabel(x_axis_label, fontsize=20)  # Use user-defined X-axis label
plt.ylabel(y_axis_label, fontsize=20)  # Use user-defined Y-axis label
plt.title("Regression Confidence Intervals with Extended Range", fontsize=20)
plt.legend()
plt.grid(True)

# Save the new figure
f_save_path = os.path.join(output_dir, "f.jpeg")
plt.savefig(f_save_path, dpi=300, bbox_inches='tight')
plt.show()
