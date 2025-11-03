import os
import logging
import requests
from typing import Dict, Any
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class WhatsAppSender:

    # class for sending WhatsApp messages via Twilio API

    def __init__(self):

        # initialize sender

        self.config = self._load_config()
        self.twilio_client = None
        self._initialize_twilio_client()    

    def _load_config(self) -> Dict[str, Any]:

       # config loader

        # Read environment configuration. Normalize and strip whitespace.
        config = {
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,
            # allow both names for destination to be flexible
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),
            'send_method': (os.getenv('WHATSAPP_METHOD') or 'simulation').strip(),
            'webhook_url': os.getenv('WHATSAPP_WEBHOOK_URL', '').strip(),
        }

        logger.info("Configuracion del WhatsAppSender cargada.")
        return config
    
    # initialize Twilio client

    def _initialize_twilio_client(self):
        
        # if credentials are available, initialize client
        if (self.config['twilio_account_sid'] and 
            self.config['twilio_auth_token'] and
            self.config['twilio_whatsapp_from']):

            try:

                self.twilio_client = Client(
                    self.config['twilio_account_sid'], 
                    self.config['twilio_auth_token']
                )
                logger.info("Cliente de Twilio inicializado con éxito.")
            except Exception as e:
                logger.error(f"Error al inicializar el cliente de Twilio: {str(e)}")
                self.twilio_client = None
    
    # send message using twilio API

    def send_twilio_message(self, message: str, destiny: str) -> bool:

        try: 
            if not self.twilio_client:
                logger.error("El cliente de Twilio no está inicializado.")
                return False

            # format whatsapp numbers

            from_whatsapp = f'whatsapp:{self.config["twilio_whatsapp_from"]}'
            to_whatsapp = f'whatsapp:{destiny}'

            # send message
            message = self.twilio_client.messages.create(
                body=message,
                from_=from_whatsapp,
                to=to_whatsapp
            )

            logger.info(f"Mensaje enviado via Twilio a {destiny}. SID: {message.sid}")
            return True
        except TwilioRestException as e:
            logger.error(f"Error de twilio {e}")
            return False
        except Exception as e:
            logger.error(f"Error enviando mensaje via Twilio: {e}")
            return False
        
    # send picture

    def send_twilio_image(self, url_image: str, message: str, destiny: str) -> bool:

        try: 
            if not self.twilio_client:
                logger.error("El cliente de Twilio no está inicializado.")
                return False

            from_whatsapp = f'whatsapp:{self.config["twilio_whatsapp_from"]}'
            to_whatsapp = f'whatsapp:{destiny}'

            message = self.twilio_client.messages.create(
                body=message,
                from_=from_whatsapp,
                media_url=[url_image],
                to=to_whatsapp
            )

            logger.info(f"Imagen enviada via Twilio a {destiny}. SID: {message.sid}")
            return True
        
        except TwilioRestException as e:
            logger.error(f"Error de twilio {e}")
            return False
        
    # send message using webhook

    def send_webhook_message(self, message: str, destiny: str) -> bool:

        try: 
            if not self.config['webhook_url']:
                logger.error("La URL del webhook no está configurada.")
                return False

            payload = {
                'to': destiny,
                'message': message,
                'type': 'text'
            }

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {os.getenv("WEBHOOK_TOKEN","")}'
            }

            response = requests.post(
                self.config['webhook_url'],
                json= payload,
                headers= headers,
                timeout=30
            )

            if response.status_code == 200:
                logger.info(f"Mensaje enviado via Webhook a {destiny}.")
                return True
            else:
                logger.error(f"Error enviando mensaje via Webhook: {response.status_code} - {response.text}")
                return False
            
        except Exception as e:
            logger.error(f"Error enviando mensaje via Webhook: {e}")
            return False
    
    # simulate send message

    def simulate_send_message(self, message: str, destiny: str) -> bool:

        try: 
            logger.info("MODO SIMULACION")
            logger.info(f"Destino: {destiny}")
            logger.info(f"Mensaje: {message}")
            logger.info("Mensaje simulado enviado con éxito.")

            # save file log

            with open('outputs/simulation_log.txt', 'w', encoding='utf-8') as f:
                f.write(f"Destino: {destiny}\n")
                f.write(f"Mensaje: {message}\n")
                f.write("="*50 + "\n")

            return True
    
        except Exception as e:
            logger.error(f"Error en la simulación de envío de mensaje: {e}")
            return False
        
    # send summary

    def send_summary(self, results: Dict[str, Any], destiny: str) -> bool:

        try: 

            message = self._format_summary(results)

            method = self.config['send_method']

            if method == 'twilio' and self.twilio_client:
                return self.send_twilio_message(message, destiny)
            elif method == 'webhook':
                return self.send_webhook_message(message, destiny)
            else:
                return self.simulate_send_message(message, destiny)
            
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")
            return False
    
    # send whatsapp graph 

    def send_graph(self, results: Dict[str, Any], destiny: str) -> bool:

        try:
            graph_message ="""

Graficos Generados:

Se han generado varios graficos para visualizar el analisis de ventas.
Puede encontrarlos en la carpeta 'outputs/graphs' del proyecto.

"""
            method = self.config['send_method']

            if method == 'twilio' and self.twilio_client:
                # NT: to send images via twilio, we need a public URL
                return self.send_twilio_message(graph_message, destiny)
            else: 
                return self.simulate_send_message(graph_message, destiny)
        
        except Exception as e:
            logger.error(f"Error enviando graficos: {e}")
            return False
        
    # format summary message
    def _format_summary(self, results: Dict[str, Any]) -> str:

        try:
            metrics = results['summary_metrics']
            top_models = results['top_models'].index[0]
            top_headquarter = results['sales_by_headquarter'].index[0]
            top_channel = results['sales_by_channel'].index[0]
           
            message = f""" 

Reporte de analisis de ventas:

Metricas Prinicipales:
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

Detalles de sedes: 
"""
            # sales by headquarter details
            for headquarter, sales in results['sales_by_headquarter'].items():
                message += f"  - {headquarter}: ${sales:,.2f}\n"

            message += f"""
TOP 5 Modelos Más Vendidos:
"""
            # top 5 models details
            for i, (model, sales) in enumerate(results['top_models'].items(), 1):
                message += f"  {i}. {model}: ${sales:,.2f}\n"

            message += f"""

Generado por el sistema de análisis de ventas.
Fecha de generacion: {self._get_today_date()}

"""
            return message.strip()
        
        except Exception as e:
            logger.error(f"Error formateando resumen: {e}")
            return "Error formateando resumen."
        
    # get today date
    def _get_today_date(self) -> str:
        
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # send full report

    def send_full_report(self, results: Dict[str, Any], destiny: str = None) -> bool:

        try:
            if not destiny:
                destiny = self.config['destination_whatsapp']
            
            if not destiny:
                logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
                return False

            logger.info(f"Enviando reporte completo a {destiny}...")

            sucess_summary = self.send_summary(results, destiny)

            # short pauses
            import time
            time.sleep(2)

            # send graph info
            sucess_graph = self.send_graph(results, destiny)

            return sucess_summary and sucess_graph
        
        except Exception as e:
            logger.error(f"Error enviando reporte completo: {e}")
            return False
        
# aux function for direct use
def send_whatsapp_report(results: Dict[str, Any], destiny: str= None) -> bool:

    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp: {e}")
        return False
        
    