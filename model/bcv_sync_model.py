import logging
import threading
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from model.tasa_cambio_model import TasaCambioModel

def _resolve_caracas_tz():
    try:
        return ZoneInfo("America/Caracas")
    except ZoneInfoNotFoundError:
        return timezone(timedelta(hours=-4), name="America/Caracas")


CARACAS_TZ = _resolve_caracas_tz()
BCV_SYNC_HOUR = 16
BCV_AUTO_SOURCE = "BCV automatico"

logger = logging.getLogger(__name__)


def _is_auto_source(source_value):
    return str(source_value or "").strip().lower() == BCV_AUTO_SOURCE.lower()


def sync_bcv_rate_if_needed(force=False, now=None):
    current = now.astimezone(CARACAS_TZ) if now else datetime.now(CARACAS_TZ)
    target_date = current.date().isoformat()
    result = {
        'synced': False,
        'action': 'skipped',
        'reason': None,
        'id': None,
        'fecha': target_date,
        'monto': None,
    }

    if not force and current.hour < BCV_SYNC_HOUR:
        result['reason'] = 'before_schedule'
        return result

    model = TasaCambioModel()
    existing = model.get_by_date(target_date)
    if existing and not force and _is_auto_source(existing.get('fuente')):
        result['reason'] = 'already_synced'
        result['id'] = existing.get('id')
        try:
            result['monto'] = float(existing.get('monto') or 0)
        except (TypeError, ValueError):
            result['monto'] = None
        return result

    from model.bcv_rate_model import get_bcv_rates

    rates = get_bcv_rates(targets=['usd'], verify=False)
    monto = float(rates.get('usd') or 0)
    if monto <= 0:
        raise ValueError("No se pudo obtener tasa BCV valida")

    db_result = model.upsert_from_scraping(monto, fecha=target_date, fuente=BCV_AUTO_SOURCE)
    if db_result.get('action') == 'lock_busy':
        result['reason'] = 'lock_busy'
        return result

    result['synced'] = True
    result['action'] = db_result.get('action') or 'updated'
    result['id'] = db_result.get('id')
    result['monto'] = monto
    return result


class BCVAutoSyncScheduler:
    def __init__(self, interval_seconds=60):
        self.interval_seconds = max(30, int(interval_seconds))
        self._stop_event = threading.Event()
        self._thread = None
        self._lock = threading.Lock()
        self._last_completed_date = None

    def start(self):
        with self._lock:
            if self._thread and self._thread.is_alive():
                return False
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run_loop, name='bcv-auto-sync', daemon=True)
            self._thread.start()
            return True

    def stop(self):
        self._stop_event.set()

    def _run_loop(self):
        while not self._stop_event.wait(self.interval_seconds):
            self._run_once()

    def _run_once(self):
        now = datetime.now(CARACAS_TZ)
        if now.hour < 16 or (now.hour == 16 and now.minute < 1):
            return
        today = now.date().isoformat()
        if self._last_completed_date == today:
            return
        try:
            result = sync_bcv_rate_if_needed(force=True, now=now)
            if result.get('synced') or result.get('reason') == 'already_synced':
                self._last_completed_date = today
                logger.info("BCV auto-sync %s para %s", result.get('action') or result.get('reason'), today)
        except Exception as exc:
            logger.exception("Error en auto-sync BCV diario: %s", exc)


_scheduler = BCVAutoSyncScheduler()


def start_bcv_auto_sync_scheduler():
    return _scheduler.start()
