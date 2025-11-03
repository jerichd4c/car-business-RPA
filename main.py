import os
import sys
from utils.data_loader import load_and_validate_data    
from utils.analyzer import DataAnalyzer, analyze_data
from utils.visualizer import generate_visualizations
from utils.whatsapp_sender import WhatsAppSender, send_whatsapp_report

# create directories if not exist

def setup_directories():

    directories = ['data', 'outputs/graphs', 'utils']
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Carpeta '{directory}' creada/verificada")

# load enviroment variables

def load_env_variables():
    try: 
        from dotenv import load_dotenv
        # load default .env first
        load_dotenv()
        # if a project-specific env file exists, load it (whatsapp_config.env)
        env_file = 'whatsapp_config.env'
        if os.path.exists(env_file):
            load_dotenv(env_file, override=True)
            print(f"Variables de entorno cargadas desde {env_file}.")
        else:
            print("Variables de entorno cargadas (desde .env si existe).")
    except ImportError:
        print("python-dotenv no está instalado. Asegúrese de que las variables de entorno estén configuradas manualmente.")

def main():
    print("Iniciando RPA")
    print("="*50)

    # setup directories and load env variables
    setup_directories()
    load_env_variables()

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


    # send whatsapp report
    print("Enviando reporte por WhatsApp...")
    try:
        # get whatsapp destiny
        destiny = os.getenv("WHATSAPP_DESTINY")
        method = os.getenv("WHATSAPP_METHOD", "simulation")  # default to simulation

        print(f"Metodo de envío: {method.upper()}")
        if destiny:
            print(f"Número de destino: {destiny}")
        else:
            print("Número de destino no encontrado.")

        # normalize destiny (strip whitespace) before using
        if destiny:
            destiny = destiny.strip()

        # send report
        if send_whatsapp_report(results, destiny):
            print("Reporte enviado exitosamente por WhatsApp.")

            # show simulation message if apllicable
            if method == "simulation":
                print("MODO SIMULACION: El reporte no se enviará realmente.")
                print("Para enviar mensajes reales:")
                print("1. Configura TWILIO_ACCOUNT_SID y TWILIO_AUTH_TOKEN en .env")
                print("2. Obtén un número de WhatsApp de Twilio")
                print("3. Cambia WHATSAPP_METHOD a 'twilio'")
                print("4. Configura WHATSAPP_DESTINY con tu número")
        
        else:
            print("Error al enviar el reporte por WhatsApp.")
    except Exception as e:
        print(f"Error durante el envío del reporte por WhatsApp: {e}")
        # exit program

    print("PROYECTO COMPLETADO")

if __name__ == "__main__":
    main()