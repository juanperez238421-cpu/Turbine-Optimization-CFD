# 🌊 Optimización de Turbinas Hidráulicas: CFD & Data Analytics

Este proyecto combina **Simulación Numérica (CFD)** y **Análisis de Datos Experimentales** para optimizar el diseño de rotores en turbinas de vórtice gravitacional. El objetivo es maximizar la eficiencia energética mediante la validación estadística de modelos de turbulencia y la cuantificación precisa de pérdidas mecánicas.

## 🎯 Objetivos del Proyecto
1.  **Validación Numérica:** Comparar modelos de turbulencia RANS (k-ε, SST, BSL) utilizando el Índice de Convergencia de Malla (GCI).
2.  **Análisis Experimental:** Procesar datos de sensores para calcular el torque de fricción real y corregir las curvas de eficiencia teórica.
3.  **Toma de Decisiones:** Seleccionar la configuración óptima basada en la minimización de la incertidumbre (Richardson Extrapolation).

## 🛠 Metodología y Tecnologías

### 1. Validación de Modelos CFD (Python + Matplotlib)
Se analizaron tres modelos de turbulencia para predecir el torque hidráulico. Se aplicó el método de **Extrapolación de Richardson** para calcular la incertidumbre numérica.

*   **Resultados de Convergencia:**
    *   **Modelo k-ε:** GCI ≈ 7.34% (El más robusto y preciso).
    *   **Modelo SST:** GCI ≈ 38.12%.
    *   **Modelo BSL:** GCI ≈ 48.49%.

> *El script `cfd_model_validation.py` genera las curvas de convergencia grid-to-grid.*

### 2. Cuantificación de Fricción Experimental (Pandas + NumPy)
Para obtener la eficiencia neta, es necesario restar las pérdidas mecánicas. Se procesaron datos crudos de sensores (`RPM` vs `Time`) de pruebas de desaceleración inercial.

*   **Física aplicada:** $T_{fricción} = I \cdot \alpha$
*   **Procesamiento:**
    *   Limpieza de series temporales y cálculo de derivadas numéricas ($\alpha = d\omega/dt$).
    *   Cálculo del momento de inercia ($I$) para eje de acero.
*   **Hallazgo:** Se determinó un torque de fricción promedio de **0.0666 N·m**, lo que representa una pérdida de potencia de **~0.7 W** a 100 RPM.

## 📂 Estructura del Repositorio
*   `cfd_model_validation.py`: Script para visualización de convergencia GCI y comparación de torque numérico.
*   `experimental_friction_analysis.py`: Algoritmo para procesar logs de sensores y calcular pérdidas mecánicas.
*   `VP1_100_0.txt`: (Data Sample) Archivo de log crudo utilizado para el análisis de fricción.

## 🚀 Impacto
La combinación de estos dos análisis permitió corregir las estimaciones de eficiencia de la turbina en un **12%**, asegurando que los prototipos finales cumplieran con los requerimientos energéticos reales antes de la fabricación.

---
*Autor: Juan Diego Pérez | Ingeniero Mecatrónico & Data Analyst*
