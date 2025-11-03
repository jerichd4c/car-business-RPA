import os
import os
import logging
import requests
import json
import time
import schedule
from typing import Dict, List, Any, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import pywhatkit as pwk
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class WhatsAppSender:

    # class for sending WhatsApp messages using Twilio API

    def __init__(self):

        # initialize sender

        self.config = self._load_config()
        self.twilio_client = None
        self.selenium_driver = None
        self._initialize_twilio_client()    

    def _load_config(self) -> Dict[str, Any]:

       # config loader

        # Read environment configuration. Normalize and strip whitespace.
        config = {
            
            'send_method': (os.getenv('WHATSAPP_METHOD') or 'simulation').strip(),
            # allow both names for destination to be flexible
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),

            # 1. twilio config
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,

            # 2. selenium config
            'chrome_driver_path': os.getenv('CHROME_DRIVER_PATH', '/usr/local/bin/chromedriver'),
            'whatsapp_web_delay': int(os.getenv('WHATSAPP_WEB_DELAY', '30')),

            # 3. general config
            'max_retries': int(os.getenv('WHATSAPP_MAX_RETRIES', '3')),
            'wait_time': int(os.getenv('WHATSAPP_WAIT_TIME', '5')),

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
    
    # METHOD 1: send message using twilio API

    def send_twilio_message(self, message: str, destiny: str, linked_file: List[str] = None) -> bool:

        try: 
            if not self.twilio_client:
                logger.error("El cliente de Twilio no está inicializado.")
                return False

            # format whatsapp numbers

            from_whatsapp = f'whatsapp:{self.config["twilio_whatsapp_from"]}'
            to_whatsapp = f'whatsapp:{destiny}'

            # send message
            message_params = {
                'body': message,
                'from_': from_whatsapp,
                'to': to_whatsapp
            }

            # add url if exists

            if linked_file:
                message_params['media_url'] = linked_file

            # send message

            message = self.twilio_client.messages.create(**message_params)

            logger.info(f"Mensaje enviado via Twilio a {destiny}. SID: {message.sid}")
            logger.info(f"Estado del mensaje: {message.status}")

            # verify status
            time.sleep(2)
            message = message.fetch()
            logger.info(f"📊 Estado actualizado: {message.status}")

            return message.status in ['queued', 'sent', 'delivered']
   
        except TwilioRestException as e:
            logger.error(f"Error de twilio {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado en Twilio: {e}")
            return False
        
    # METHOD 2: send message using PYWHATKIT 

    def send_pywhatkit_message(self, message: str, destiny: str) -> bool:

        try:
            # format destiny
            clean_destiny = destiny.replace('+', '').strip()

            # get current time
            right_now = datetime.now()
            hour = right_now.hour
            minute = right_now.minute + 2

            if minute >= 60:
                hour += 1
                minute -= 60

            # send message
            pwk.sendwhatmsg(f"+{clean_destiny}", message, hour, minute, wait_time=15)

            logger.info(f"Mensaje enviado via pywhatkit a {destiny}.")
            return True
        
        except Exception as e:
            logger.error(f"Error enviando mensaje via pywhatkit: {e}")
            return False

    #METHOD 3: send message using SELENIUM

    def initialoize_selenium(self) -> bool:

        try: 
            chrome_options = Options()

            # config for better performance
            chrome_options.add_argument("--user-data-dir=./whatsapp_profile")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # init driver

            self.selenium_driver = webdriver.Chrome(
                executable_path=self.config['chrome_driver_path'],
                options=chrome_options
            )   

            # open whatsapp web
            self.selenium_driver.get("https://web.whatsapp.com")

            # wait for manual QR scan
            logger.info("Por favor, escanee el código QR en WhatsApp Web.")
            WebDriverWait(self.selenium_driver, self.config['whatsapp_web_delay']).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )

            logger.info("WhatsApp Web listo para enviar mensajes.")
            return True
        
        except Exception as e:
            logger.error(f"Error inicializando Selenium: {e}")
            return False
    
    def send_selenium_message(self, message: str, destiny: str) -> bool:

        try: 
            # init driver if not ready
            if not self.selenium_driver:
                if not self.initialoize_selenium():
                    return False
                
            # search chat 
            search_box = WebDriverWait(self.selenium_driver, 15).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )

            search_box.clear()
            search_box.send_keys(destiny)
            time.sleep(2)  # wait for search results

            # select chat
            try:
                chat = WebDriverWait(self.selenium_driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f'//span[@title="{destiny}"]'))
                )
                chat.click()
            except:
                logger.error(f"No se pudo encontrar el chat para {destiny}")
                return False
            
            # write and send message
            message_box = WebDriverWait(self.selenium_driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
            )

            message_box.send_keys(message)
            time.sleep(1)

            # send button   

            send_button = self.selenium_driver.find_element(By.XPATH, '//button[@data-icon="send"]')
            send_button.click()

            logger.info(f"Mensaje enviado via Selenium a {destiny}.")
            return True
        except Exception as e:
            logger.error(f"Error enviando mensaje via Selenium: {e}")
            return False
        
    def close_selenium(self):
        if self.selenium_driver:
            self.selenium_driver.quit()
            self.selenium_driver = None
            logger.info("Selenium WebDriver cerrado.")

    # METHOD 4: simulate send message

    def simulate_send_message(self, message: str, destiny: str) -> bool:

        try: 
            logger.info("MODO SIMULACION")
            logger.info(f"Destino: {destiny}")
            logger.info(f"Mensaje: {message}")
            logger.info("Mensaje simulado enviado con éxito.")

            # save file log

            os.makedirs('outputs', exist_ok=True)
            with open('outputs/simulation_log.txt', 'w', encoding='utf-8') as f:
                f.write(f"=== {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
                f.write(f"Destino: {destiny}\n")
                f.write(f"Mensaje: {message}\n")
                f.write("="*50 + "\n")

            return True
    
        except Exception as e:
            logger.error(f"Error en la simulación de envío de mensaje: {e}")
            return False
        

    # MAIN SEND METHOD

    def send_message(self, message: str, destiny: str = None, retry: bool = True) -> bool:

        if not destiny:
            destiny = self.config['destination_whatsapp']

        if not destiny:
            logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
            return False
        
        method = self.config['send_method'].lower()
        max_retries = self.config['max_retries'] if retry else 1

        for attempt in range(max_retries):

            try:

                logger.info(f"Intentando envío (intento {attempt + 1}/{max_retries})...")

                if method == 'twilio':
                    result = self.send_twilio_message(message, destiny)
                elif method == 'pywhatkit':
                    result = self.send_pywhatkit_message(message, destiny)
                elif method == 'selenium':
                    result = self.send_selenium_message(message, destiny)
                else:  # simulation
                    result = self.simulate_send_message(message, destiny)

                if result:
                    return True
                else:
                    logger.warning(f"Intento {attempt + 1} fallido.")
                    if attempt < max_retries - 1:
                        time.sleep(self.config['wait_time'])

            except Exception as e:
                logger.error(f"Error en el intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                        time.sleep(self.config['wait_time'])

        logger.error("Todos los intentos de envío han fallado.")
        return False

    # send summary

    def send_summary(self, results: Dict[str, Any], destiny: str= None) -> bool:

        try: 

            message = self._format_summary(results)
            return self.send_message(message, destiny)
        
        except Exception as e:
            logger.error(f"Error enviando resumen: {e}")
            return False
    
    # send whatsapp graph 

    def send_graph(self, results: Dict[str, Any], destiny: str= None) -> bool:

        try:
            graph_message ="""

Graficos Generados:

Se han generado varios graficos para visualizar el analisis de ventas.
Puede encontrarlos en la carpeta 'outputs/graphs' del proyecto.

"""
            return self.send_message(graph_message, destiny)
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
            time.sleep(2)

            # send graph info
            sucess_graph = self.send_graph(results, destiny)

            # close selenium if used
            if self.config['send_method'] == 'selenium':
                self.close_selenium()

            return sucess_summary and sucess_graph
        
        except Exception as e:
            logger.error(f"Error enviando reporte completo: {e}")
            # close selenium if error
            if self.config['send_method'] == 'selenium':
                self.close_selenium()
            return False
        
# aux function for direct use
def send_whatsapp_report(results: Dict[str, Any], destiny: str= None) -> bool:

    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp: {e}")
        return False