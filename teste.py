import numpy as np
from scipy.stats import linregress
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import interp1d

#valor de steps (encoder) e valores em mm
x = np.array([0, 1200, 1800, 2500, 3500, 5000, 7000, 10000, 13000, 16000, 20000, 24500, 29000, 31250, 37000, 45000, 57000])
y = np.array([0, 5, 27, 46, 55, 79, 111, 171, 236, 282, 334, 395, 489, 517, 602, 732, 911])

def polynomial_function(x, a, b, c):
    return a * x**2 + b * x + c

# regressao linear
slope, intercept, r_value, p_value, std_err = linregress(x, y)

print(f"Slope (m): {slope}")
print(f"Intercept (b): {intercept}")

params, covariance = curve_fit(polynomial_function, x, y)

# Get the fitted parameters (coefficients)
a_fit, b_fit, c_fit = params

# Generate y values based on the fitted curve
y_fit = polynomial_function(x, a_fit, b_fit, c_fit)
# Print the coefficients of the fitted curve
print(f"Fitted curve coefficients: a = {a_fit}, b = {b_fit}, c = {c_fit}")

# Perform linear interpolation
interp_func = interp1d(x, y, kind='linear')

# Generate x values for a smoother curve
x_smooth = np.linspace(x.min(), x.max(), 1000)

# Calculate interpolated y values
y_interp = interp_func(31250)
print(type(y_interp), int(y_interp))

# # Plot the original data and the interpolated curve
# plt.scatter(x, y, label='Original data')
# plt.plot(x_smooth, y_interp, color='red', label='Interpolated curve (Linear)')
# plt.xlabel('x')
# plt.ylabel('y')
# plt.legend()
# plt.show()