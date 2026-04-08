import numpy as np
from scipy.integrate import solve_ivp

m = 98e-3
g = 9.81
dt = 2.6
c = 340
k = 1.6e-3

def f(t,X):
    global m,g,k
    return [X[1], g-k*X[1]**2/m]

X0 = [0,0]
tspan = [0, dt]
teval = np.linspace(0, dt, 1000)

sol = solve_ivp(f, tspan, X0, t_eval=teval)

tp = sol.t+sol.y[0]/c
h = sol.y[0][np.where(tp>dt)[0][0]]
print(f"{h}m")