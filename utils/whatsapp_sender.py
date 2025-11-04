import os
import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

logger = logging.getLogger(__name__)

class TwilioDailyLimitExceeded(Exception):
    """Raised when Twilio returns error 63038 (daily messages limit exceeded)."""
    pass


class WhatsAppSender:

    # class for sending WhatsApp messages using Twilio API

    def __init__(self):

        # initialize sender

        self.config = self._load_config()
        self.twilio_client = None
        self._initialize_twilio_client()    

    def _load_config(self) -> Dict[str, Any]:

       # config loader

        # Read environment configuration. Normalize and strip whitespace.
        config = {
            'destination_whatsapp': (os.getenv('WHATSAPP_DESTINY') or os.getenv('DESTINATION_WHATSAPP') or '').strip(),
            # Twilio config
            'twilio_account_sid': os.getenv('TWILIO_ACCOUNT_SID', '').strip() or None,
            'twilio_auth_token': os.getenv('TWILIO_AUTH_TOKEN', '').strip() or None,
            'twilio_whatsapp_from': os.getenv('TWILIO_WHATSAPP_FROM', '').strip() or None,
            # Simulation mode (to avoid using Twilio while testing)
            'simulate': (os.getenv('WHATSAPP_SIMULATE', 'false').strip().lower() in {'1','true','yes','y'}),
            # Retry config
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
            # Detect daily limit exceed to avoid useless retries
            try:
                code = getattr(e, 'code', None)
            except Exception:
                code = None

            if code == 63038 or 'daily messages limit' in str(e).lower():
                logger.error("Twilio: límite diario de mensajes excedido (63038). Deteniendo reintentos hasta que el límite se reinicie.")
                raise TwilioDailyLimitExceeded(str(e))
            else:
                logger.error(f"Error de Twilio: {e}")
                return False
        except Exception as e:
            logger.error(f"Error inesperado en Twilio: {e}")
            return False
        
    # MAIN SEND METHOD (Twilio-only)

    def send_message(self, message: str, destiny: str = None, retry: bool = True, linked_file: Optional[List[str]] = None) -> bool:

        if not destiny:
            destiny = self.config['destination_whatsapp']

        if not destiny:
            logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
            return False

        max_retries = self.config['max_retries'] if retry else 1

        for attempt in range(max_retries):
            try:
                logger.info(f"Intentando envío via Twilio (intento {attempt + 1}/{max_retries})...")
                result = self.send_twilio_message(message, destiny, linked_file)
                if result:
                    return True
                logger.warning(f"Intento {attempt + 1} fallido.")
                if attempt < max_retries - 1:
                    time.sleep(self.config['wait_time'])
            except TwilioDailyLimitExceeded as e:
                # stop retrying immediately on daily limit errors
                logger.error(f"Envio detenido: {e}")
                # re-raise to allow caller to handle fallback (simulation)
                raise
            except Exception as e:
                logger.error(f"Error en el intento {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(self.config['wait_time'])

        logger.error("Todos los intentos de envío via Twilio han fallado.")
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
        
    # format summary message (multi-line, readable)
    def _format_summary(self, results: Dict[str, Any]) -> str:

        try:
            metrics = results['summary_metrics']
            top_models = results['top_models'].index[0]
            top_headquarter = results['sales_by_headquarter'].index[0]
            top_channel = results['sales_by_channel'].index[0]

            # multi-line structure for better readability
            lines: List[str] = []
            lines.append("📊 Reporte de análisis de ventas")
            lines.append(f"👥 Clientes únicos: {metrics['unique_clients']:,}")
            lines.append(f"🧾 Total de ventas: {metrics['total_sales']:,}")
            lines.append(f"💵 Ventas sin IGV: ${metrics['total_sales_without_igv']:,.2f}")
            lines.append(f"💰 Ventas con IGV: ${metrics['total_sales_with_igv']:,.2f}")
            lines.append(f"🧮 IGV recaudado: ${metrics['total_igv_collected']:,.2f}")
            lines.append(f"📈 Venta promedio: ${metrics['average_sales_without_igv']:,.2f}")

            lines.append("")
            lines.append(f"🏆 Modelo más vendido: {top_models}")
            lines.append(f"📍 Sede con más ventas: {top_headquarter}")
            lines.append(f"📣 Canal con más ventas: {top_channel}")

            # sales by headquarter (one per line)
            lines.append("")
            lines.append("📍 Ventas por sede:")
            for hq, sales in results['sales_by_headquarter'].items():
                lines.append(f"• 🏢 {hq}: ${sales:,.2f}")

            # top 5 models
            lines.append("")
            lines.append("🔝 Top 5 modelos:")
            for i, (model, sales) in enumerate(results['top_models'].items(), 1):
                num_emoji = {1:"1️⃣",2:"2️⃣",3:"3️⃣",4:"4️⃣",5:"5️⃣"}.get(i, f"{i}.")
                lines.append(f"{num_emoji} {model}: ${sales:,.2f}")
                if i >= 5:
                    break

            lines.append("")
            lines.append(f"🗓️ Generado: {self._get_today_date()}")

            return "\n".join(lines)
        
        except Exception as e:
            logger.error(f"Error formateando resumen: {e}")
            return "Error formateando resumen."
        
    # get today date
    def _get_today_date(self) -> str:
        
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # send full report

    def send_full_report(self, results: Dict[str, Any], destiny: str = None, simulate: Optional[bool] = None) -> bool:

        try:
            if not destiny:
                destiny = self.config['destination_whatsapp']
            
            if not destiny:
                logger.error("No se ha proporcionado un destino para el mensaje de WhatsApp.")
                return False

            logger.info(f"Enviando reporte completo a {destiny}...")

            # build a multi-line message combining summary and graph note
            message = self._format_summary(results)

            # honor simulate flag (parameter overrides env/config)
            if simulate is None:
                simulate = bool(self.config.get('simulate'))

            # optionally upload graphs to imgbb and include ALL links in the message text only
            media_urls: Optional[List[str]] = None
            try:
                imgbb_key = os.getenv('IMGBB_API_KEY', '').strip()
                graphs_dir = os.path.join('outputs', 'graphs')
                if imgbb_key and os.path.isdir(graphs_dir):
                    from utils.image_uploader import upload_images_to_imgbb
                    # Get graph files in a fixed semantic order
                    graph_title_and_paths = self._get_graphs_in_order(graphs_dir)
                    ordered_paths = [p for (_t, p) in graph_title_and_paths]
                    uploaded = upload_images_to_imgbb(ordered_paths, imgbb_key, name_prefix='carbiz-report', max_count=len(ordered_paths))
                    if uploaded:
                        # Compose a formatted, numbered list of links
                        message += "\n\n🖼️ Gráficos en línea:\n"
                        for idx, ((title, _path), url) in enumerate(zip(graph_title_and_paths, uploaded), start=1):
                            message += f"{idx}. {title}: {url}\n"
                else:
                    message += "\n\n🖼️ Los gráficos del análisis se guardaron en la carpeta outputs/graphs."
            except Exception as e:
                logging.warning(f"No se pudieron subir los gráficos a imgbb: {e}")
                message += "\n\n🖼️ Los gráficos del análisis se guardaron en la carpeta outputs/graphs."

            # if simulate, skip Twilio and write simulation output
            if simulate:
                logger.info("Modo simulación activo: no se enviará mensaje por Twilio.")
                return self.simulate_send_with_graph_urls(message)

            try:
                # send only text with links; do not attach media
                success = self.send_message(message, destiny, linked_file=None)
                return success
            except TwilioDailyLimitExceeded:
                # fallback to simulation including ALL graph URLs
                logger.warning("Límite diario de Twilio alcanzado: simulando envío e incluyendo URLs de todos los gráficos.")
                return self.simulate_send_with_graph_urls(message)
        
        except Exception as e:
            logger.error(f"Error enviando reporte completo: {e}")
            return False
        
    # aux method to simulate send with all graph URLs (when Twilio limit exceeded)

    def simulate_send_with_graph_urls(self, base_message: str) -> bool:
        """Simulate sending by writing a log that includes ALL graph URLs via imgbb if possible."""
        try:
            graphs_dir = os.path.join('outputs', 'graphs')
            os.makedirs('outputs', exist_ok=True)

            # collect images in fixed semantic order
            graph_title_and_paths = self._get_graphs_in_order(graphs_dir)
            graph_files: List[str] = [p for (_t, p) in graph_title_and_paths]

            urls: List[str] = []
            imgbb_key = os.getenv('IMGBB_API_KEY', '').strip()
            if imgbb_key and graph_files:
                try:
                    from utils.image_uploader import upload_images_to_imgbb
                    # upload ALL collected images preserving order
                    urls = upload_images_to_imgbb(graph_files, imgbb_key, name_prefix='carbiz-report', max_count=len(graph_files))
                except Exception as e:
                    logging.warning(f"Falló la subida a imgbb en modo simulación: {e}")

            # compose simulated message
            message = base_message
            if urls:
                message += "\n\n🖼️ Gráficos en línea (simulado):\n"
                for idx, ((title, _path), url) in enumerate(zip(graph_title_and_paths, urls), start=1):
                    message += f"{idx}. {title}: {url}\n"
            else:
                if graph_files:
                    # Fallback to local file paths if no URLs
                    message += "\n\n🗂️ Gráficos locales (simulado):\n" + "\n".join(graph_files)
                else:
                    message += "\n\n⚠️ No se encontraron gráficos para adjuntar."

            # write simulation log and message snapshot
            ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            with open('outputs/simulation_log.txt', 'a', encoding='utf-8') as f:
                f.write(f"=== {ts} ===\n")
                f.write(message + "\n")
                f.write("="*50 + "\n")

            with open('outputs/simulation_message.txt', 'w', encoding='utf-8') as f:
                f.write(message)

            logger.info("🧪 MODO SIMULACIÓN: Mensaje preparado con URLs de gráficos.")
            return True
        except Exception as e:
            logger.error(f"Error en simulación con URLs: {e}")
            return False

    def _get_graphs_in_order(self, graphs_dir: str) -> List[Tuple[str, str]]:
        """Return a list of (title, absolute_path) for graph images in a fixed, user-friendly order.
        Only include files that exist.
        Order:
          1. Resumen del Dashboard (dashboard_summary.png)
          2. Tendencia Mensual (monthly_sales_trend.png)
          3. Ventas por Segmento (sales_by_segment.png)
          4. Ventas por Canal (sales_by_channel.png)
          5. Top Modelos (top_models.png)
          6. Ventas por Sede (sales_by_headquarter.png)
        """
        mapping = [
            ("Resumen del Dashboard", "dashboard_summary.png"),
            ("Tendencia Mensual", "monthly_sales_trend.png"),
            ("Ventas por Segmento", "sales_by_segment.png"),
            ("Ventas por Canal", "sales_by_channel.png"),
            ("Top Modelos", "top_models.png"),
            ("Ventas por Sede", "sales_by_headquarter.png"),
        ]
        result: List[Tuple[str, str]] = []
        for title, fname in mapping:
            path = os.path.join(graphs_dir, fname)
            if os.path.isfile(path):
                result.append((title, path))
        return result
        
# aux function for direct use
def send_whatsapp_report(results: Dict[str, Any], destiny: str= None) -> bool:

    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp: {e}")
        return False

# aux function to force simulation (no Twilio usage)
def send_whatsapp_report_simulated(results: Dict[str, Any], destiny: str = None) -> bool:
    try:
        sender = WhatsAppSender()
        return sender.send_full_report(results, destiny, simulate=True)
    except Exception as e:
        logging.error(f"Error enviando reporte de WhatsApp en modo simulación: {e}")
        return False