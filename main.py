import os
import sys
from utils.data_loader import load_and_validate_data    
from utils.analyzer import DataAnalyzer, analyze_data
from utils.visualizer import generate_visualizations

# create directories if not exist
def setup_directories():

    directories = ['data', 'outputs/graphs', 'utils']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Carpeta '{directory}' creada/verificada")

def main():
    print("Iniciando RPA")
    print("="*50)

    # setup directories
    setup_directories()

    # verify if file exists
    data_file = 'data/Ventas_Fundamentos.xlsx'

    if not os.path.exists(data_file):
        print(f"Archivo de datos no encontrado: {data_file}")
        print("Por favor, ejecute 'create_sample_data.py' para generar el archivo de datos de muestra.")
        sys.exit(1)
    
    # load and validate data
    print("Cargando y validando datos...")
    df, validation = load_and_validate_data(data_file)

    if df is not None and validation['is_valid']:
        print("Datos cargados y validados exitosamente.")
        print(f"Total registros: {len(df)}")
        print(f"Sedes: {df['Headquarter'].nunique()}")
        print(f"Modelos: {df['Model'].nunique()}")
        print(f'Clientes Únicos: {df["Client_ID"].nunique()}')
    else:
        print("Error en la carga de datos")
        if 'error' in validation:
            print(f"Error: {validation['error']}")
        sys.exit(1)

    # analyze data
    print("Iniciando análisis de datos...")
    try:
        analyzer = DataAnalyzer(df)
        results = analyzer.full_analysis()
        
        # show summary

        print("\n" + "="*50)
        print("Resumen del Análisis:")
        print("="*50)
        metrics = results['summary_metrics']
        print(f"Clientes Únicos: {metrics['unique_clients']:,}")
        print(f"Total de Ventas: {metrics['total_sales']:,}")
        print(f"Ventas Totales sin IGV: ${metrics['total_sales_without_igv']:,.2f}")
        print(f"Ventas Totales con IGV: ${metrics['total_sales_with_igv']:,.2f}")
        print(f"Ventas Promedio: ${metrics['average_sales_without_igv']:,.2f}")

        print(f"Modelo Más Vendido: {results['top_models'].index[0]}")
        print(f"Sede con Más Ventas: {results['sales_by_headquarter'].index[0]}")
        print(f"Canal con Más Ventas: {results['sales_by_channel'].index[0]}")
    except Exception as e:
        print(f"Error durante el análisis de datos: {str(e)}")
        sys.exit(1)

    # generate graphs
    print("Generando visualizaciones...")
    try:
        generate_visualizations(results)
        print("Visualizaciones generadas exitosamente en 'outputs/graphs'.")
    except Exception as e:
        print(f"Error durante la generación de visualizaciones: {str(e)}")
        sys.exit(1)

        print ("\n Módulo de analisis y visualización completado correctamente.")
        #todo implementar envío por whatsapp
    
if __name__ == "__main__":
    main()