"""Funciones de series de tiempo implementadas a mano con numpy.

Se usan en la Parte 0 (simulaciones) y se reutilizan en las Partes 3 y 4.
"""
import numpy as np
from scipy import stats


def acf(y, kmax):
    """Autocorrelación muestral r_1, ..., r_kmax.

    y puede ser un vector (n,) o una matriz (réplicas, n); en el segundo caso
    se calcula una ACF por fila. Fórmula:
        r_k = sum_{t=k+1}^n (y_t - ybar)(y_{t-k} - ybar) / sum_{t=1}^n (y_t - ybar)^2
    """
    y = np.asarray(y, dtype=float)
    vector = y.ndim == 1
    if vector:
        y = y[None, :]
    d = y - y.mean(axis=1, keepdims=True)
    denom = (d ** 2).sum(axis=1)
    r = np.empty((y.shape[0], kmax))
    for k in range(1, kmax + 1):
        r[:, k - 1] = (d[:, k:] * d[:, :-k]).sum(axis=1) / denom
    return r[0] if vector else r


def ljung_box(y, m, gl_restar=0):
    """Estadístico de Ljung-Box Q(m) y su valor-p con m - gl_restar grados de libertad.

    Acepta un vector o una matriz (réplicas, n). Devuelve (Q, p).
    """
    y = np.asarray(y, dtype=float)
    n = y.shape[-1]
    r = acf(y, m)
    k = np.arange(1, m + 1)
    Q = n * (n + 2) * (r ** 2 / (n - k)).sum(axis=-1)
    p = stats.chi2.sf(Q, m - gl_restar)
    return Q, p


def ar1_ols(y):
    """OLS de y_t contra (1, y_{t-1}). Devuelve (c, phi). Acepta vector o matriz."""
    y = np.asarray(y, dtype=float)
    x, z = y[..., :-1], y[..., 1:]
    xm = x.mean(axis=-1, keepdims=True)
    zm = z.mean(axis=-1, keepdims=True)
    phi = ((x - xm) * (z - zm)).sum(axis=-1) / ((x - xm) ** 2).sum(axis=-1)
    c = zm[..., 0] - phi * xm[..., 0]
    return c, phi


def simular_ar1(phi, n=300, reps=1, c=0.0, sigma=1.0, burn=200, rng=None):
    """Simula `reps` trayectorias de un AR(1) de largo n, descartando `burn` pasos.

    Empieza en Y_0 = 0. Para phi = 1 (caminata aleatoria) el burn-in no logra
    olvidar el valor inicial, pero eso no cambia r_k (ver Parte 0.2).
    """
    rng = np.random.default_rng() if rng is None else rng
    total = n + burn
    eps = rng.normal(0.0, sigma, size=(reps, total))
    y = np.zeros((reps, total))
    prev = np.zeros(reps)
    for t in range(total):
        prev = c + phi * prev + eps[:, t]
        y[:, t] = prev
    return y[:, burn:]


def bandas(n):
    """Bandas de ruido blanco ±1.96/sqrt(n)."""
    return 1.96 / np.sqrt(n)


def graficar_acf(ax, r, n, titulo=""):
    """Gráfica de barras de la ACF con bandas ±1.96/sqrt(n)."""
    k = np.arange(1, len(r) + 1)
    b = bandas(n)
    fuera = np.abs(r) > b
    ax.bar(k, r, color=np.where(fuera, "#B04A4A", "#2F5D8A"), width=0.6)
    ax.axhline(b, ls="--", color="gray", lw=1)
    ax.axhline(-b, ls="--", color="gray", lw=1)
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(k)
    ax.set_xlabel("Rezago k")
    ax.set_ylabel("$r_k$")
    ax.set_title(titulo)
    return int(fuera.sum())
