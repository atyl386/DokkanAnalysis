import numpy as np
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
from dokkanUnitConstants import NUM_SLOTS, ORB_COUNTS_NO_ORB_CHANGING, ORB_COUNTS_DOUBLE_ORB_CHANGING, ORB_COUNTS_TYPE_ORB_CHANGING
NUM_TYPE_ORBS = 5
NUM_ORB_TYPES = 6
NUM_TOTAL_ORBS = 23
NUM_TYPE_ORBS_NO_ORB_CHANGING = ORB_COUNTS_NO_ORB_CHANGING[0] + ORB_COUNTS_NO_ORB_CHANGING[1]
NUM_TYPE_ORBS_TYPE_ORB_CHANGING = ORB_COUNTS_TYPE_ORB_CHANGING[0] + ORB_COUNTS_TYPE_ORB_CHANGING[1]
NUM_TYPE_ORBS_DOUBLE_ORB_CHANGING = ORB_COUNTS_DOUBLE_ORB_CHANGING[0] + ORB_COUNTS_DOUBLE_ORB_CHANGING[1]
NUM_TYPE_ORBS_QUAD_TYPE_ORB_CHANGING = (NUM_TYPE_ORBS / NUM_ORB_TYPES * NUM_TOTAL_ORBS + (NUM_SLOTS - 1) * NUM_TYPE_ORBS_NO_ORB_CHANGING) / NUM_SLOTS

# Define the sigmoid function
def sigmoid(x, c, k, x0):
    return (NUM_TYPE_ORBS_QUAD_TYPE_ORB_CHANGING - c) / (1 + np.exp(-k * (x - x0))) + c

# Your data points
x_data = np.array([0, 1, 2, 4])
y_data = np.array([NUM_TYPE_ORBS_NO_ORB_CHANGING, NUM_TYPE_ORBS_TYPE_ORB_CHANGING, NUM_TYPE_ORBS_DOUBLE_ORB_CHANGING,  NUM_TYPE_ORBS_QUAD_TYPE_ORB_CHANGING])

# Initial guess for the parameters
initial_guess = [3.2, 2.5, 1.2]

# Perform the curve fitting
params, covariance = curve_fit(sigmoid, x_data, y_data, p0=initial_guess)

# Extract the fitted parameters
c, k, x0 = params

# Generate a curve using the fitted parameters
x_curve = np.linspace(min(x_data), max(x_data), 100)
y_curve = sigmoid(x_curve, c, k, x0)

# Plot the original data and the fitted curve
plt.scatter(x_data, y_data, label='Data points')
plt.plot(x_curve, y_curve, label='Fitted Sigmoid', color='red')
plt.xlabel('x')
plt.ylabel('f(x)')
plt.legend()
plt.show()

print(sigmoid(3, c, k, x0))