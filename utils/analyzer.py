import pandas as pd
import numpy as np
import logging
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)

class DataAnalyzer:
    
    # class to make financial and statistical analysis on sales data

    def __init__(self, df: pd.DataFrame):

        # initialize with sales data

        self.df = df.copy()
        self.results = {}

    def validate_data(self) -> bool:

        # validate required columns exist

        required_columns = [
            'Sell_Date', 'Headquarter', 'Model', 'Channel', 
            'Segment', 'Client_ID', 'Price_Without_IGV', 
            'IGV', 'Price_With_IGV'
        ]
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            logger.error(f"Missing required columns: {missing_columns}")
            return False
        
        if self.df.empty:
            logger.error("DataFrame is empty.")
            return False
    
        logger.info("Data validation passed.")
        return True
    
    # calculate total sales without IGV by headquarter
    
    def calculate_sales_without_igv(self) -> pd.Series:

        try: 
            sales_by_headquarter = self.df.groupby('Headquarter')['Price_Without_IGV'].sum().sort_values(ascending=False)
            logger.info("Ventas sin IGV calculadas por sede.")
            return sales_by_headquarter
        except KeyError as e:
            logger.error(f"Error calculando ventas sin IGV: {str(e)}")
            raise

    # get top N models (cars)

    def get_top_n_models(self) -> pd.Series:

        try:
            top_models = self.df['Model'].value_counts().head(5)
            logger.info("Top 5 modelos obtenidos.")
            return top_models
        except Exception as e:
            logger.error(f"Error obteniendo top modelos: {str(e)}")
            raise
    
    # analize sales by channel

    def analyze_sales_by_channel(self) -> pd.Series:

        try:
            sales_by_channel = self.df['Channel'].value_counts()
            logger.info("Análisis de ventas por canal completado.")
            return sales_by_channel
        except Exception as e:
            logger.error(f"Error analizando ventas por canal: {str(e)}")
            raise

    # segment sales by client (no IGV)

    def segment_sales_by_client(self) -> pd.Series:

        try:
            segmented_sales = self.df.groupby('Segment')['Price_Without_IGV'].sum()
            logger.info("Segmentación de ventas por cliente completada.")
            return segmented_sales
        except Exception as e:
            logger.error(f"Error segmentando ventas por cliente: {str(e)}")
            raise

    # summarize all analysis

    def summarize_analysis(self) -> Dict[str, Any]:

        try:
            metrics = {
                'unique_clients': self.df['Client_ID'].nunique(),
                'total_sales': len(self.df),
                'total_sales_without_igv': self.df['Price_Without_IGV'].sum(),
                'total_sales_with_igv': self.df['Price_With_IGV'].sum(),
                'total_igv_collected': self.df['IGV'].sum(),
                'average_sales_without_igv': self.df['Price_Without_IGV'].mean(),
                'max_sale_without_igv': self.df['Price_Without_IGV'].max(),
                'min_sale_without_igv': self.df['Price_Without_IGV'].min()
            }

            logger.info("Resumen del análisis completado.")
            return metrics
        except Exception as e:
            logger.error(f"Error resumiendo análisis: {str(e)}")
            raise
    
    # analyze temporal sales trends

    def analyze_temporal_trends(self) -> pd.Series:

        try: 
            # compute monthly sales trend if Sell_Date exists
            if 'Sell_Date' in self.df.columns:
                # ensure Sell_Date is datetime
                self.df['Sell_Date'] = pd.to_datetime(self.df['Sell_Date'], errors='coerce')
                # drop rows with invalid dates
                valid_df = self.df.dropna(subset=['Sell_Date']).copy()
                if valid_df.empty:
                    logger.warning("No hay fechas válidas en 'Sell_Date' para analizar tendencias temporales.")
                    return pd.Series(dtype=float)

                valid_df['Month'] = valid_df['Sell_Date'].dt.to_period('M')
                monthly_sales = valid_df.groupby('Month')['Price_Without_IGV'].sum()
                logger.info("Análisis de tendencias temporales completado.")
                return monthly_sales
            else:
                logger.error("La columna 'Sell_Date' no existe en el DataFrame.")
                return pd.Series(dtype=float)
        except Exception as e:
            logger.error(f"Error analizando tendencias temporales: {str(e)}")
            return pd.Series()
        
    # do full analysis

    def full_analysis(self) -> Dict[str, Any]:

        try: 
            if not self.validate_data():
                raise ValueError("Data validation failed.")
            logger.info("Iniciando análisis completo de datos.")

            # Use keys expected by the visualizer
            self.results = {
                'sales_by_headquarter': self.calculate_sales_without_igv(),
                'top_models': self.get_top_n_models(),
                'sales_by_channel': self.analyze_sales_by_channel(),
                'sales_by_segment': self.segment_sales_by_client(),
                'summary_metrics': self.summarize_analysis(),
                'monthly_sales_trend': self.analyze_temporal_trends()
            }

            logger.info("Análisis completo de datos finalizado.")
            return self.results
        
        except Exception as e:
            logger.error(f"Error en el análisis completo de datos: {str(e)}")
            raise
    
    # get text summary

    def get_text_summary(self) -> str:

        try:
            if not self.results:
                self.full_analysis()
            
            metrics = self.results['summary_metrics']
            top_models = self.results['top_models'].index[0]
            top_headquarter = self.results['sales_by_headquarter'].index[0]
            top_channel = self.results['sales_by_channel'].index[0]

            summary = f"""

Resumen del Análisis de Ventas:

Metricas Clave:
- Clientes Únicos: {metrics['unique_clients']:,}
- Total de Ventas: {metrics['total_sales']:,}
- Ventas Totales sin IGV: ${metrics['total_sales_without_igv']:,.2f}
- Ventas Totales con IGV: ${metrics['total_sales_with_igv']:,.2f}
- IGV Total Recaudado: ${metrics['total_igv_collected']:,.2f}
- Venta Promedio: ${metrics['average_sales_without_igv']:,.2f}

Mejores Desempeños:
- Modelo Más Vendido: {top_models}
- Sede con Más Ventas: {top_headquarter}
- Canal con Más Ventas: {top_channel}

Análisis de los ultimos 12 Meses:

            """
            
            return summary
        
        except Exception as e:
            logger.error(f"Error generando resumen de texto: {str(e)}")
            return "Error generando resumen de texto."

# aux function for direct use

def analyze_data(df: pd.DataFrame) -> Dict[str, Any]:

    analyzer = DataAnalyzer(df)
    return analyzer.full_analysis()