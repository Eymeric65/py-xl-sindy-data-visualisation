import numpy as np
import cupy as cp
from sklearn.linear_model import Lasso as skLasso
from cuml.linear_model import Lasso as cuLasso

# --- Create Sample Data ---
# Use a fixed random state for reproducibility
np.random.seed(42)
n_samples = 1000
n_features = 50
X_np = np.random.randn(n_samples, n_features) 
y_np = X_np[:, 0] * 2.5 - X_np[:, 5] * 1.8 + np.random.randn(n_samples) * 0.5

# --- Use the EXACT SAME parameters you are using ---
# Replace these with your actual values if they are different
test_alpha = 0.1
test_max_iter = 10000
test_tol = 1e-5

print("--- Running a controlled comparison with identical settings ---")

# --- 1. Scikit-learn Version ---
print("\n1. Running scikit-learn Lasso...")
# CRITICAL: Force all parameters to match cuML's defaults and the GPU environment
lasso_sklearn = skLasso(
    alpha=test_alpha,
    fit_intercept=True,  # <--- FORCING THE MODELS TO SOLVE THE SAME PROBLEM
    max_iter=test_max_iter,
    tol=test_tol
)
# Convert data to float32 for a fair precision comparison
lasso_sklearn.fit(X_np.astype(np.float32), y_np.astype(np.float32))
coef_sklearn = lasso_sklearn.coef_


# --- 2. cuML Version ---
print("2. Running cuML Lasso...")
X_gpu = cp.asarray(X_np, dtype=cp.float32)
y_gpu = cp.asarray(y_np, dtype=cp.float32)

lasso_cuml = cuLasso(
    alpha=test_alpha,
    fit_intercept=True, # <--- This is the default, but we state it for clarity
    max_iter=test_max_iter,
    tol=test_tol
)
lasso_cuml.fit(X_gpu, y_gpu)
coef_cuml = cp.asnumpy(lasso_cuml.coef_)


# --- 3. Compare the Results ---
print("\n3. Comparing Results...")
diff = np.abs(coef_sklearn - coef_cuml)

print(f"{'Feature':>10} | {'Scikit-learn Coef':>20} | {'cuML Coef':>20} | {'Difference':>20}")
print("-" * 75)
for i in range(n_features):
    # Only print features where at least one model found a non-zero coefficient
    if abs(coef_sklearn[i]) > 1e-6 or abs(coef_cuml[i]) > 1e-6:
        print(f"{i:>10} | {coef_sklearn[i]:>20.8f} | {coef_cuml[i]:>20.8f} | {diff[i]:>20.8f}")

print("-" * 75)
print(f"Sum of absolute differences: {np.sum(diff):.8f}")
print(f"Maximum single difference: {np.max(diff):.8f}")