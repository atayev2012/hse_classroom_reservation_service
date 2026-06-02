import { CheckCircle2, CircleX } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import { bookingApi } from '../utils/api.js';
import { timeSlots } from '../utils/mockData.js';

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

function firstSlot(booking) {
  return Array.isArray(booking?.event_time_slot)
    ? booking.event_time_slot[0]
    : booking?.event_time_slot || timeSlots[0];
}

function equipmentLabel(room) {
  if (!room?.equipment?.length) return 'Без оборудования';
  return room.equipment
    .map((item) => `${item.name}${item.qty ? ` x${item.qty}` : ''}`)
    .join(', ');
}

function bookingErrorMessage(error) {
  const message = error?.message || '';
  if (/conflict|booked|booking|duplicate|already/i.test(message)) {
    return 'На это время есть конфликт с расписанием';
  }
  return message || 'Не удалось сохранить бронирование';
}

export default function BookingModal({
  booking,
  buildings,
  rooms,
  currentUserId,
  mode,
  onClose,
  onSubmit
}) {
  const activeBuildings = buildings.length ? buildings : [{ id: 1, name: 'Костина' }];
  const initialBuildingId = booking?.building_id || activeBuildings[0]?.id || '';
  const [form, setForm] = useState({
    building_id: String(initialBuildingId || ''),
    room_id: String(booking?.room_id || ''),
    event_date: booking?.event_date || todayIso(),
    event_time_slot: firstSlot(booking),
    event_title: booking?.event_title || 'Бронирование аудитории',
    event_description: booking?.event_description || ''
  });
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState('');
  const [slotBookings, setSlotBookings] = useState([]);
  const [isLoadingRooms, setIsLoadingRooms] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function loadSlotBookings() {
      if (!form.building_id || !form.event_date) {
        setSlotBookings([]);
        return;
      }

      setIsLoadingRooms(true);
      const response = await bookingApi.bookings.list({
        building_id: Number(form.building_id),
        event_date: form.event_date,
        limit: 1000
      }).catch(() => null);

      if (!mounted) return;
      setSlotBookings(response?.bookings || []);
      setIsLoadingRooms(false);
    }

    loadSlotBookings();
    return () => { mounted = false; };
  }, [form.building_id, form.event_date]);

  const occupiedRoomIds = useMemo(() => new Set(
    slotBookings
      .filter((item) => (
        item.is_active !== false &&
        Number(item.id) !== Number(booking?.id) &&
        (Array.isArray(item.event_time_slot) ? item.event_time_slot : [item.event_time_slot]).includes(form.event_time_slot)
      ))
      .map((item) => Number(item.room_id))
  ), [booking?.id, form.event_time_slot, slotBookings]);

  const availableRooms = useMemo(
    () => rooms.filter((room) => (
      String(room.building_id) === form.building_id &&
      room.is_active !== false &&
      !occupiedRoomIds.has(Number(room.id))
    )),
    [form.building_id, occupiedRoomIds, rooms]
  );

  const selectedRoomId = availableRooms.some((room) => String(room.id) === String(form.room_id))
    ? form.room_id
    : availableRooms[0]?.id || '';

  function updateForm(field, value) {
    setForm((current) => ({
      ...current,
      [field]: value,
      ...(field === 'building_id' ? { room_id: '' } : {})
    }));
    setError('');
  }

  async function submitForm() {
    const roomId = Number(selectedRoomId);
    if (!form.building_id || !roomId || !form.event_date || !form.event_time_slot || !form.event_title.trim()) {
      setError('Заполните корпус, аудиторию, дату, слот и название');
      return;
    }

    setIsSaving(true);
    setError('');
    try {
      await onSubmit({
        event_type: booking?.event_type || 'reservation',
        event_title: form.event_title.trim(),
        event_description: form.event_description.trim(),
        event_date: form.event_date,
        event_time_slot: [form.event_time_slot],
        user_id: currentUserId || booking?.user_id || 1,
        building_id: Number(form.building_id),
        room_id: roomId
      });
    } catch (requestError) {
      setError(bookingErrorMessage(requestError));
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="modal-backdrop">
      <div className="booking-modal">
        <h2>{mode === 'edit' ? 'Редактирование бронирования' : 'Новое бронирование'}</h2>
        <div className="booking-form-box booking-form-box--expanded">
          <label>
            <span>Корпус</span>
            <select value={form.building_id} onChange={(event) => updateForm('building_id', event.target.value)}>
              {activeBuildings.map((building) => (
                <option value={building.id} key={building.id}>{building.name}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Дата</span>
            <input type="date" value={form.event_date} onChange={(event) => updateForm('event_date', event.target.value)} />
          </label>
          <label>
            <span>Временной слот</span>
            <select value={form.event_time_slot} onChange={(event) => updateForm('event_time_slot', event.target.value)}>
              {timeSlots.map((slot) => (
                <option value={slot} key={slot}>{slot}</option>
              ))}
            </select>
          </label>
          <label>
            <span>Название</span>
            <input value={form.event_title} onChange={(event) => updateForm('event_title', event.target.value)} />
          </label>
          <label>
            <span>Комментарий</span>
            <textarea value={form.event_description} onChange={(event) => updateForm('event_description', event.target.value)} />
          </label>
        </div>
        <div className="available-title">Доступные аудитории</div>
        <div className="rooms-picker">
          <div className="rooms-picker__head">
            <span>Аудитория</span>
            <span>Zoom</span>
            <span>Оборудование</span>
          </div>
          {isLoadingRooms ? (
            <div className="rooms-picker__empty">Проверяем доступные аудитории...</div>
          ) : availableRooms.length ? availableRooms.map((room) => (
            <button
              className={`rooms-picker__row ${String(selectedRoomId) === String(room.id) ? 'is-selected' : ''}`}
              key={room.id}
              type="button"
              onClick={() => updateForm('room_id', String(room.id))}
            >
              <span>{room.room_number}</span>
              <span>{room.is_zoom ? 'Да' : 'Нет'}</span>
              <span>{equipmentLabel(room)}</span>
            </button>
          )) : (
            <div className="rooms-picker__empty">Нет доступных аудиторий на выбранные дату и слот</div>
          )}
        </div>
        {error && <div className="modal-error">{error}</div>}
        <div className="modal-actions">
          <button className="button button--danger" type="button" onClick={onClose} disabled={isSaving}>
            <CircleX size={17} />
            Отменить
          </button>
          <button className="button button--primary" type="button" onClick={submitForm} disabled={isSaving}>
            <CheckCircle2 size={17} />
            {mode === 'edit' ? 'Сохранить' : 'Забронировать'}
          </button>
        </div>
      </div>
    </div>
  );
}
