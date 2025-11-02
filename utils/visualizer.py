import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os 
import logging
from matplotlib import rcParams
from typing import Dict, Any, List

from tomlkit import date

logger = logging.getLogger(__name__)

class DataVisualizer:
    
    # class to generate graphs from sales data

    def __init__(self, results: Dict[str, Any]):

        # initialize with analysis results

        self.results = results
        
        # styles

        self.configure_styles()

    # configure graph styles

    def configure_styles(self):

        plt.style.use('seaborn-v0_8')
        rcParams['figure.figsize'] = (12, 8)
        rcParams['font.size'] = 12
        rcParams['axes.titlesize'] = 16
        rcParams['axes.labelsize'] = 14

        # colors

        self.colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#3B1F2B', 
                       '#6B8E23', '#20B2AA', '#FF6B6B', '#4ECDC4', '#45B7D1']
        
    # save graph to file

    def save_graph(self, filename: str, dpi: int = 300):

        # verify route exists

        try: 
            abs_path = os.path.join('outputs', 'graphs', filename)
            plt.savefig(abs_path, dpi=dpi, bbox_inches='tight', facecolor= 'white', edgecolor='white')
            plt.close()
            logger.info(f"Graph saved to {abs_path}")
        except Exception as e:
            logger.error(f"Error saving graph: {str(e)}")
            raise

    # create graph for sales by headquarter

    def create_sales_by_headquarter_graph(self):

        try:
            
            data= self.results['sales_by_headquarter']

            fig, ax = plt.subplots(figsize=(14,8))
            bars = ax.bar(data.index, data.values, color=self.colors[:len(data)], edgecolor='black', linewidth=0.5)
        
            # customize graphs
            ax.set_title('VENTAS SIN IGV POR SEDE', fontsize=18, fontweight='bold', pad=20)
            ax.set_xlabel('Sede', fontweight='bold')
            ax.set_ylabel('Ventas Sin IGV ($)', fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.3)

            # add value to bars

            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'S/ {height:,.0f}', ha='center', va='bottom', fontweight='bold')
                
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

            self.save_graph('sales_by_headquarter.png')

        except Exception as e:
            logger.error(f"Error creando gráfico de ventas por sede: {str(e)}")
            raise

    # create graph for top n models

    def create_top_models_graph(self):

        try:

            data = self.results['top_models']

            fig, ax = plt.subplots(figsize=(14,8))
            bars = ax.barh(range(len(data)), data.values, color=self.colors[:len(data)], edgecolor='black', linewidth=0.5)

            # customize graphs
            ax.set_title('TOP MODELOS MÁS VENDIDOS (SIN IGV)', fontsize=18, fontweight='bold', pad=20)
            ax.set_xlabel('Ventas Sin IGV ($)', fontweight='bold')
            ax.set_ylabel('Modelo', fontweight='bold')
            ax.set_yticks(range(len(data)))
            ax.set_yticklabels(data.index)
            ax.grid(axis='x', linestyle='--', alpha=0.3)

            # add value to bars
            for i, bar in enumerate(bars):
                width = bar.get_width()
                ax.text(width + width*0.01, bar.get_y() + bar.get_height()/2.,
                       f'S/ {width:,.0f}', ha='left', va='center', fontweight='bold')
                
            plt.tight_layout()
            self.save_graph('top_models.png')
        
        except Exception as e:
            logger.error(f"Error creando gráfico de los mejores modelos: {str(e)}")
            raise

    # create graph for sales by channel

    def create_sales_by_channel_graph(self):

        try: 

            data = self.results['sales_by_channel'] 

            fig, ax = plt.subplots(figsize=(14,8))
            bars= ax.bar(data.index, data.values, color=self.colors[4:4+len(data)], edgecolor='black', linewidth=0.5)

            # customize graphs
            ax.set_title('ANÁLISIS DE VENTAS POR CANAL', fontsize=18, fontweight='bold', pad=20)
            ax.set_xlabel('Canal', fontweight='bold')
            ax.set_ylabel('Número de Ventas', fontweight='bold')
            ax.grid(axis='y', linestyle='--', alpha=0.3)

            # add value to bars
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                       f'{int(height)}', ha='center', va='bottom', fontweight='bold')
                
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            self.save_graph('sales_by_channel.png')

        except Exception as e:
            logger.error(f"Error creando gráfico de ventas por canal: {str(e)}")
            raise

    # create graph for sales by segment

    def create_sales_by_segment_graph(self):

        try: 

            data= self.results['sales_by_segment']
            fig, ax = plt.subplots(figsize=(12,12))

            # create pie chart

            wedges, texts, autotexts = ax.pie(data.values, labels=data.index, autopct='%1.1f%%', startangle=90, colors=self.colors[2:2+len(data)], textprops={'fontsize': 12})

            # personalize pie chart

            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(11)

            # personalize labels

            for text in texts:
                text.set_fontsize(13)
                text.set_fontweight('bold')

            ax.set_title('SEGMENTACIÓN DE VENTAS POR CLIENTE (SIN IGV)', fontsize=18, fontweight='bold', pad=20)

            # add legend

            legend_labels = [f'{label}: S/ {value:,.0f}' 
                           for label, value in zip(data.index, data.values)]
            ax.legend(wedges, legend_labels, title="Montos Totales", 
                     loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))
            
            plt.tight_layout()
            self.save_graph('sales_by_segment.png')

        except Exception as e:
            logger.error(f"Error creando gráfico de ventas por segmento: {str(e)}")
            raise
    
    # create monthly sales trend graph

    def create_monthly_sales_trend_graph(self):

        try:

            data = self.results['monthly_sales_trend']
            
            if data is None or data.empty:
                logger.warning("No hay datos para crear la gráfica de tendencia de ventas mensuales.")
                return
            
            fig, ax = plt.subplots(figsize=(15,8))

            # convert period to string for better x-axis labels

            months = data.index.astype(str)

            ax.plot(months, data.values, marker='o', color=self.colors[0], linewidth=3, markersize=8, markerfacecolor='white', markeredgecolor='black')

            # customize graphs
            ax.set_title('TENDENCIA MENSUAL DE VENTAS SIN IGV', fontsize=18, fontweight='bold', pad=20)
            ax.set_xlabel('Mes', fontweight='bold')
            ax.set_ylabel('Ventas Sin IGV ($)', fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.3)

            # rotate x labels for better visibility

            plt.xticks(rotation=45, ha='right')

            # add value for each point

            for i, (months, value) in enumerate(zip(months, data.values)):
                ax.annotate(f'S/ {value:,.0f}', (months, value),
                           textcoords="offset points", xytext=(0,10),
                           ha='center', fontweight='bold')

            plt.tight_layout()
            self.save_graph('monthly_sales_trend.png')
        
        except Exception as e:
            logger.error(f"Error creando gráfico de tendencia mensual de ventas: {str(e)}")
            # dont do raise to avoid stopping the whole process    

    # create dashboard summary

    def create_dashboard_summary(self):

        try:

            metrics = self.results['summary_metrics']

            fig, ax = plt.subplots(figsize=(10,6))
            ax.axis('off')

            # main title

            ax.text(0.5, 0.9, 'RESUMEN DEL ANÁLISIS DE VENTAS', fontsize=24, fontweight='bold', ha='center', va='center',
                    transform=ax.transAxes)

            # subtitle

            ax.text(0.5, 0.8, 'Métricas Clave', fontsize=18, fontweight='bold', ha='center', va='center', transform=ax.transAxes)

            # define positions

            positions = [
                (0.25, 0.75), (0.75, 0.75),
                (0.25, 0.60), (0.75, 0.60),
                (0.25, 0.45), (0.75, 0.45),
                (0.25, 0.30), (0.75, 0.30)
            ]

            metrics_data = [
                ('Clientes Únicos', f"{metrics['unique_clients']}"),
                ('Total Ventas', f"S/ {metrics['total_sales_without_igv']:,.2f}"),
                ('Ventas sin IGV', f"S/ {metrics['total_sales_without_igv']:,.2f}"),
                ('Ventas con IGV', f"S/ {metrics['total_sales_with_igv']:,.2f}"),
                ('IGV Recaudado', f"S/ {metrics['total_igv_collected']:,.2f}"),
                ('Venta Promedio', f"S/ {metrics['average_sales_without_igv']:,.2f}"),
                ('Venta Maxima', f"S/ {metrics['max_sale_without_igv']:,.2f}"),
                ('Venta Minima', f"S/ {metrics['min_sale_without_igv']:,.2f}")
            ]

            # create box for each metric
            for (x, y), (title, value) in zip(positions, metrics_data):

                # background box

                rect = plt.Rectangle((x-0.15, y-0.08), 0.3, 0.12, 
                                   fill=True, color=self.colors[0], alpha=0.2,
                                   transform=ax.transAxes)
                
                ax.add_patch(rect)

                # title

                ax.text(x, y+0.02, title, ha='center', va='center', 
                       fontsize=12, fontweight='bold', transform=ax.transAxes)
                
                # value

                ax.text(x, y-0.02, value, ha='center', va='center', 
                       fontsize=14, fontweight='bold', color=self.colors[0],
                       transform=ax.transAxes)
                
                # extra info box

                ax.text(0.5, 0.15, f" Período Analizado: Últimos 12 meses", 
                   ha='center', va='center', fontsize=12, style='italic',
                   transform=ax.transAxes)
            
                ax.text(0.5, 0.10, f" Generado automáticamente por RPA Python", 
                   ha='center', va='center', fontsize=10, color='gray',
                   transform=ax.transAxes)
                
            plt.tight_layout()
            self.save_graph('dashboard_summary.png')

        except Exception as e:
            logger.error(f"Error creando resumen del dashboard: {str(e)}")
            raise

    # create all graphs

    def generate_all_graphs(self):

        try:
            logger.info("Iniciando generación de gráficos.")

            # verify path
            os.makedirs('outputs/graphs', exist_ok=True)

            self.create_sales_by_headquarter_graph()
            self.create_top_models_graph()
            self.create_sales_by_channel_graph()
            self.create_sales_by_segment_graph()
            self.create_monthly_sales_trend_graph()
            self.create_dashboard_summary()

            logger.info("Generación de gráficos finalizada.")

        except Exception as e:
            logger.error(f"Error generando todos los gráficos: {str(e)}")
            raise

# aux function for direct use

def generate_visualizations(results: Dict[str, Any]):

    visualizer = DataVisualizer(results)
    visualizer.generate_all_graphs()