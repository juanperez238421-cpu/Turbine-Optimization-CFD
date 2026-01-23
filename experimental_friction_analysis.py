import pandas as pd
import numpy as np

def calculate_friction_losses(filename):
    """
    Procesa datos experimentales de desaceleración para calcular 
    el torque de fricción y pérdidas de potencia en el eje.
    """
    
    # Parámetros Físicos del Rotor (Acero)
    DENSITY_STEEL = 7850  # kg/m^3
    DIAMETER = 0.0127     # 0.5 inch in meters
    LENGTH = 0.9          # 900 mm in meters
    RADIUS = DIAMETER / 2
    
    # 1. Cálculo de Inercia (Cilindro Sólido)
    # I = (1/12)*m*L^2 + (1/4)*m*R^2
    volume = np.pi * (RADIUS**2) * LENGTH
    mass = DENSITY_STEEL * volume
    I = (1.0/12.0)*mass*(LENGTH**2) + 0.25*mass*(RADIUS**2)
    
    print(f"--- Parámetros del Sistema ---")
    print(f"Masa del eje: {mass:.4f} kg")
    print(f"Momento de Inercia (I): {I:.6e} kg·m²")

    try:
        # 2. Carga y Limpieza de Datos
        df = pd.read_csv(filename, sep="\t", header=0)
        
        # Filtro de rango de RPM para análisis de desaceleración (-105 a -95)
        df = df[(df["RPM"] >= -105) & (df["RPM"] <= -95)].copy()
        
        # Procesamiento temporal
        df["TimeSec"] = pd.to_timedelta(df["Time Elapsed"]).dt.total_seconds()
        df.drop_duplicates(subset=["TimeSec"], inplace=True)
        df.sort_values("TimeSec", inplace=True)
        
        # Cálculo de Cinemática (RPM -> rad/s -> alpha)
        df["omega"] = df["RPM"] * (2 * np.pi / 60)
        df["domega"] = df["omega"].diff()
        df["dt"] = df["TimeSec"].diff()
        df["alpha"] = df["domega"] / df["dt"]
        
        # Segmentación para obtener desaceleración promedio válida
        # Solo tomamos valores negativos (desaceleración)
        valid_alpha = df[df["alpha"] < 0]["alpha"]
        avg_alpha = valid_alpha.mean()
        
        print(f"\n--- Resultados Experimentales ---")
        print(f"Desaceleración Angular Promedio: {avg_alpha:.4f} rad/s²")

        # 3. Cálculo de Torque y Potencia
        # T = I * alpha
        friction_torque = I * abs(avg_alpha)
        
        # Potencia a 100 RPM
        omega_100 = 100 * (2 * np.pi / 60)
        power_loss = friction_torque * omega_100
        
        print(f"Torque de Fricción (Mecánico): {friction_torque:.6f} N·m")
        print(f"Pérdida de Potencia @ 100 RPM: {power_loss:.4f} W")
        
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo '{filename}'.")
    except Exception as e:
        print(f"Error en el procesamiento: {e}")

if __name__ == "__main__":
    # Asegúrate de tener el archivo VP1_100_0.txt en la misma carpeta
    calculate_friction_losses("VP1_100_0.txt")