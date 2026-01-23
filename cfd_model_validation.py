import numpy as np
import matplotlib.pyplot as plt
import matplotlib as mpl

# Configuración para gráficos de calidad de publicación
# Si no tienes LaTeX instalado, cambia 'text.usetex' a False
try:
    mpl.rcParams['text.usetex'] = True
    mpl.rcParams['font.family'] = 'serif'
    mpl.rcParams['font.serif'] = ['Computer Modern']
except:
    mpl.rcParams['text.usetex'] = False
    print("LaTeX no encontrado, usando fuentes estándar.")

def plot_convergence():
    """
    Genera un gráfico Log-Log comparando la convergencia de torque 
    para diferentes modelos de turbulencia (RANS).
    """
    # Grid sizes (m) - Representative grid sizes
    h = np.array([0.004645563, 0.00651851, 0.009174173])

    # K-Epsilon data
    torque_ke = np.array([0.613, 0.604, 0.598])
    GCI_ke = 7.34

    # SST data
    torque_sst = np.array([0.661, 0.632, 0.577])
    GCI_sst = 38.12

    # BSL data
    torque_bsl = np.array([0.730, 0.620, 0.612])
    GCI_bsl = 48.49

    plt.figure(figsize=(10, 8))

    # Plotting Models
    plt.loglog(h, torque_ke, 'bo-', markersize=8, linewidth=2, label=r'K-Epsilon (GCI$\approx$7.3\%)')
    plt.loglog(h, torque_sst, 'gs-', markersize=8, linewidth=2, label=r'SST (GCI$\approx$38.1\%)')
    plt.loglog(h, torque_bsl, 'm^-', markersize=8, linewidth=2, label=r'BSL (GCI$\approx$48.5\%)')

    # Theoretical Max Torque
    plt.axhline(y=0.6638, color='red', linestyle='--', linewidth=2, label='Theoretical Max Torque')

    # Formatting
    plt.gca().invert_xaxis()
    plt.xlabel(r'Representative Grid Size $h$ (m)')
    plt.ylabel('Torque (Nm)')
    plt.title(r'\textbf{Comparison of Turbulence Models & Mesh Convergence}')
    plt.legend()
    plt.grid(True, which="both", linestyle='--', linewidth=0.5)
    
    # Remove scientific notation
    ax = plt.gca()
    for axis in [ax.xaxis, ax.yaxis]:
        axis.set_major_formatter(plt.ScalarFormatter())
        axis.set_minor_formatter(plt.ScalarFormatter())

    plt.tight_layout()
    print("Generando gráfico de convergencia...")
    plt.savefig('convergence_plot.png', dpi=300)
    plt.show()

def plot_gci_comparison():
    """
    Compara el índice de convergencia de malla (GCI) entre malla fina y gruesa.
    """
    models = ['K-Epsilon', 'SST', 'BSL']
    GCI_fine = [7.341, 38.124, 48.493]
    GCI_coarse = [7.450, 39.873, 57.097]

    x = np.arange(len(models))
    width = 0.35

    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(x - width/2, GCI_fine, width, label='GCI Fine (21)', color='skyblue', edgecolor='black')
    ax.bar(x + width/2, GCI_coarse, width, label='GCI Coarse (32)', color='lightgreen', edgecolor='black')

    ax.set_xticks(x)
    ax.set_xticklabels(models)
    ax.set_ylabel('GCI (%)')
    ax.set_title('Uncertainty Quantification: GCI Fine vs Coarse')
    ax.legend()
    ax.grid(axis='y', linestyle='--', alpha=0.7)

    plt.tight_layout()
    print("Generando gráfico de GCI...")
    plt.savefig('gci_comparison.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    plot_convergence()
    plot_gci_comparison()