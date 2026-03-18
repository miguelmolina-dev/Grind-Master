import os.path
import datetime
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Si modificas estos SCOPES, elimina el archivo token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class CalendarHandler:
    def __init__(self):
        self.creds = None
        # 1. Intentar cargar token existente
        if os.path.exists('token.json'):
            self.creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        # 2. Si no hay credenciales o han expirado
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                try:
                    self.creds.refresh(Request())
                except Exception:
                    # Si el refresco falla, forzamos nuevo login
                    self.creds = None

            if not self.creds:
                # AQUÍ SE DEFINE 'flow' ANTES DE USARLO
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                
                # Ejecución del servidor local para autorización
                self.creds = flow.run_local_server(
                    port=0,
                    authorization_prompt_message="Comandante, autorice el acceso en su navegador...",
                    success_message="Acceso concedido. Puede cerrar esta pestaña.",
                    open_browser=True
                )
            
            # 3. Guardar el token para la próxima vez
            with open('token.json', 'w') as token:
                token.write(self.creds.to_json())

        self.service = build('calendar', 'v3', credentials=self.creds)
        self.grind_calendar_id = "54215f94b37e4daaaf808d5fee68c04cecf64f1244efdf607d8ec05643068b83@group.calendar.google.com"

    def get_upcoming_events(self, max_results=10):
        """Lee los eventos próximos con el estándar moderno."""
        # Genera el timestamp en formato ISO con la 'Z' que espera Google API
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        
        events_result = self.service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=max_results, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    def create_event(self, summary, start_time, end_time, description=""):
        """Inserta un bloque de trabajo del Grind Master."""
        event = {
            'summary': f'[GM] {summary}',
            'description': description,
            'start': {'dateTime': start_time, 'timeZone': 'America/Caracas'},
            'end': {'dateTime': end_time, 'timeZone': 'America/Caracas'},
            'colorId': '11', # Color grafito/negro para el "Grind"
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()
    
    def get_last_workout_date(self):
        """Busca el último entrenamiento usando el formato compatible."""
        now = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
        
        # Calculamos 10 días atrás de forma segura
        ten_days_ago = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=10)).isoformat().replace("+00:00", "Z")
        
        events = self.service.events().list(
            calendarId='primary', 
            q='[GM] Entrenamiento',
            timeMin=ten_days_ago, 
            timeMax=now
        ).execute()
        
        items = events.get('items', [])
        if not items:
            return None
            
        # Ordenar por fecha de inicio descendente
        last_event = sorted(items, key=lambda x: x['start'].get('dateTime', x['start'].get('date')), reverse=True)[0]
        return last_event['start'].get('dateTime')
    
    def get_available_deepwork_slots(self):
        """Calcula horas libres entre 08:00 y 18:00 en Caracas."""
        now = datetime.datetime.now(datetime.timezone.utc)
        # Definir jornada laboral teórica
        start_day = now.replace(hour=8, minute=0, second=0, microsecond=0)
        end_day = now.replace(hour=18, minute=0, second=0, microsecond=0)
        
        # Obtener eventos de hoy
        events = self.get_upcoming_events(max_results=50)
        total_busy_minutes = 0
        
        for event in events:
            start_str = event['start'].get('dateTime')
            end_str = event['end'].get('dateTime')
            
            if start_str and end_str:
                ev_start = datetime.datetime.fromisoformat(start_str.replace('Z', '+00:00'))
                ev_end = datetime.datetime.fromisoformat(end_str.replace('Z', '+00:00'))
                
                # Solo contar si el evento ocurre dentro de la jornada (8am - 6pm)
                if ev_start < end_day and ev_end > start_day:
                    # Ajustar límites al horario de jornada
                    actual_start = max(ev_start, start_day)
                    actual_end = min(ev_end, end_day)
                    duration = (actual_end - actual_start).total_seconds() / 60
                    total_busy_minutes += duration

        total_work_minutes = (end_day - start_day).total_seconds() / 60
        available_hours = (total_work_minutes - total_busy_minutes) / 60
        
        return max(0, round(available_hours, 1))
    
    def get_today_busy_blocks(self):
        """Devuelve una lista de strings con los rangos horarios ocupados hoy."""
        now = datetime.datetime.now(datetime.timezone.utc)
        start_day = now.replace(hour=0, minute=0, second=0).isoformat().replace("+00:00", "Z")
        end_day = now.replace(hour=23, minute=59, second=59).isoformat().replace("+00:00", "Z")

        events = self.service.events().list(
            calendarId='primary',
            timeMin=start_day,
            timeMax=end_day,
            singleEvents=True,
            orderBy='startTime'
        ).execute().get('items', [])

        bloques = []
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))
            
            # Extraer solo la hora HH:MM para el prompt
            h_start = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')).strftime("%H:%M")
            h_end = datetime.datetime.fromisoformat(end.replace('Z', '+00:00')).strftime("%H:%M")
            
            bloques.append(f"{h_start} - {h_end} ({event.get('summary', 'Ocupado')})")
        
        return bloques
    
    def push_plan_to_calendar(self, plan_json):
        """
        Inserta los bloques y devuelve una lista de IDs de Google Calendar.
        """
        # Limpiar eventos previos del Agente para evitar duplicados
        self.clear_grind_events()
        
        event_ids = []
        cronograma = plan_json.get('plan', [])
        
        for slot in cronograma:
            # Lógica de tiempo (Caracas)
            inicio = datetime.datetime.strptime(slot['hora'], "%H:%M")
            # Ajustar a la fecha de hoy
            ahora = datetime.datetime.now()
            inicio = ahora.replace(hour=inicio.hour, minute=inicio.minute, second=0, microsecond=0)
            fin = inicio + datetime.timedelta(minutes=slot.get('duracion_min', 60))

            event = {
                'summary': f"🛡️ {slot.get('tarea')}",
                'description': f"Tipo: {slot.get('tipo')} | Prioridad: P{slot.get('prio')}",
                'start': {'dateTime': inicio.isoformat(), 'timeZone': 'America/Caracas'},
                'end': {'dateTime': fin.isoformat(), 'timeZone': 'America/Caracas'},
                'colorId': '5', # Color inicial (Amarillo/Banana)
            }

            # Insertar en el calendario secundario
            created_event = self.service.events().insert(
                calendarId=self.grind_calendar_id, 
                body=event
            ).execute()
            
            # Guardamos el ID para la base de datos
            event_ids.append(created_event.get('id'))
            
        return event_ids

    def marcar_evento_completado(self, event_id):
        """Cambia el color del evento a Verde (colorId '10') para indicar éxito."""
        event = self.service.events().get(calendarId=self.grind_calendar_id, eventId=event_id).execute()
        event['colorId'] = '10' 
        self.service.events().update(calendarId=self.grind_calendar_id, eventId=event_id, body=event).execute()

    def clear_grind_events(self):
        """Elimina eventos con el prefijo 🛡️ para el día actual."""
        now = datetime.datetime.now().replace(hour=0, minute=0).isoformat() + 'Z'
        events = self.service.events().list(
            calendarId=self.grind_calendar_id, 
            timeMin=now,
            q="🛡️"
        ).execute().get('items', [])
        
        for event in events:
            self.service.events().delete(
                calendarId=self.grind_calendar_id, 
                eventId=event['id']
            ).execute()