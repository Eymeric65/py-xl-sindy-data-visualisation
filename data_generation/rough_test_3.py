import time
import numpy as np
import cupy as cp

# --- Scikit-learn (CPU) imports ---
from sklearn.datasets import make_regression
from sklearn.model_selection import GridSearchCV as skGridSearchCV
from sklearn.linear_model import Lasso as skLasso

# --- RAPIDS cuML (GPU) imports ---
# It's good practice to alias them to avoid confusion
from cuml.model_selection import GridSearchCV as cuGridSearchCV
from cuml.linear_model import Lasso as cuLasso

# --- 1. Generate a shared dataset ---
# We create a dataset that is large enough to show a meaningful performance difference.
n_samples = 376
n_features = 93
n_informative = 20

print(f"--- 1. Generating sample data with shape ({n_samples}, {n_features}) ---")
# The data starts as numpy arrays on the CPU
X_cpu, y_cpu = make_regression(
    n_samples=n_samples, 
    n_features=n_features, 
    n_informative=n_informative, 
    random_state=42
)
print("Data generation complete.")

# --- 2. Define a shared parameter grid ---
# We use the same grid for both models to ensure a fair comparison.
# cuml often performs best with float32, so we'll cast the grid to that type.
param_grid = {
    'alpha': np.logspace(-4, 2, 40).astype(np.float32)
}

# ===================================================================
#                        RAPIDS cuML (GPU) Benchmark
# ===================================================================

print("\n--- 3. Starting RAPIDS cuML (GPU) GridSearchCV ---")
# Record the start time
start_time_cuml = time.time()

# --- Host-to-Device Transfer ---
# Move the data from CPU memory (numpy) to GPU memory (cupy)
print("   - Moving data from CPU to GPU...")
X_gpu = cp.asarray(X_cpu)
y_gpu = cp.asarray(y_cpu)

print("shape of element :", X_gpu.shape, y_gpu.shape)
print("   - Data transfer complete.")

# Initialize the cuML Lasso model
estimator_cuml = cuLasso(fit_intercept=False)

# Initialize the cuML GridSearchCV object
# This object understands cupy arrays and runs the entire CV process on the GPU
grid_search_cuml = cuGridSearchCV(estimator_cuml, param_grid, cv=5, verbose=1)

# Perform the grid search on the GPU cupy data
grid_search_cuml.fit(X_gpu, y_gpu)

# Record the end time and calculate duration
end_time_cuml = time.time()
duration_cuml = end_time_cuml - start_time_cuml

print("\n--- RAPIDS cuML Run Complete ---")
print(f"Best parameters found: {grid_search_cuml.best_params_}")
print(f"Best R^2 score: {grid_search_cuml.best_score_:.4f}")
print(f"Execution Time: {duration_cuml:.4f} seconds")

# ===================================================================
#                      Scikit-learn (CPU) Benchmark
# ===================================================================

print("\n--- 2. Starting Scikit-learn (CPU) GridSearchCV ---")
# Record the start time
start_time_sklearn = time.time()

# Initialize the scikit-learn Lasso model
estimator_sklearn = skLasso(fit_intercept=False)

# Initialize the scikit-learn GridSearchCV object
# verbose=1 provides progress updates
grid_search_sklearn = skGridSearchCV(estimator_sklearn, param_grid, cv=5, verbose=1, n_jobs=1)

# Perform the grid search on the CPU numpy data
grid_search_sklearn.fit(X_cpu, y_cpu)

# Record the end time and calculate duration
end_time_sklearn = time.time()
duration_sklearn = end_time_sklearn - start_time_sklearn

print("\n--- Scikit-learn Run Complete ---")
print(f"Best parameters found: {grid_search_sklearn.best_params_}")
print(f"Best R^2 score: {grid_search_sklearn.best_score_:.4f}")
print(f"Execution Time: {duration_sklearn:.4f} seconds")



# ===================================================================
#                             Final Summary
# ===================================================================
print("\n--- 4. Final Performance Comparison ---")
if duration_cuml > 0:
    speedup = duration_sklearn / duration_cuml
    print(f"Scikit-learn (CPU) Time: {duration_sklearn:.4f} s")
    print(f"RAPIDS cuML (GPU) Time:  {duration_cuml:.4f} s")
    print(f"\nGPU Speedup: {speedup:.2f}x faster")
else:
    print("Could not calculate speedup due to zero execution time for cuML.")