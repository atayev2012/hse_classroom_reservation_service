import { ChevronLeft, ChevronRight, Edit3, Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import BookingModal from '../components/BookingModal.jsx';
import ConfirmModal from '../components/ConfirmModal.jsx';
import Panel from '../components/Panel.jsx';
import { SkeletonRows } from '../components/Skeleton.jsx';
import { bookingApi } from '../utils/api.js';
import { formatRussianDate, isScheduleBooking, toIsoDate } from '../utils/formatters.js';
import { sampleBookings } from '../utils/mockData.js';
import { getStoredUser } from '../utils/storage.js';

const PAGE_SIZE = 5;

const emptyFilters = {
  id: '',
  event_date: '',
  building_id: '',
  room_number: '',
  event_time_slot: '',
  event_title: '',
  status: ''
};

function normalizeSlot(value) {
  const slot = Array.isArray(value) ? value[0] : value;
  return slot || '';
}

function sortNewestFirst(a, b) {
  const dateCompare = toIsoDate(b.event_date).localeCompare(toIsoDate(a.event_date));
  if (dateCompare !== 0) return dateCompare;
  return Number(b.id || 0) - Number(a.id || 0);
}

function bookingStatus(booking) {
  if (booking.is_active === false) return 'Отменена';
  const iso = toIsoDate(booking.event_date);
  if (iso && iso < new Date().toISOString().slice(0, 10)) return 'Завершена';
  return 'Активна';
}

function bookingMatches(booking, filters, roomById) {
  const status = bookingStatus(booking);
  const slot = normalizeSlot(booking.event_time_slot);
  const filterDate = toIsoDate(filters.event_date.trim());
  const roomNumber = roomById.get(Number(booking.room_id))?.room_number || booking.room_id || '';
  return (
    String(booking.id || '').includes(filters.id.trim()) &&
    (!filterDate || toIsoDate(booking.event_date) === filterDate) &&
    (!filters.building_id || String(booking.building_id) === filters.building_id) &&
    (!filters.room_number || String(roomNumber).toLowerCase().includes(filters.room_number.trim().toLowerCase())) &&
    (!filters.event_time_slot || slot === filters.event_time_slot) &&
    (!filters.status || status === filters.status) &&
    String(booking.event_title || '').toLowerCase().includes(filters.event_title.trim().toLowerCase())
  );
}

function buildingLabel(building) {
  if (!building) return '';
  return building.address ? `${building.name}\n(${building.address})` : building.name;
}

function mapSampleBooking(booking, buildings, rooms, fallbackBuildingId, fallbackRoomId, userId) {
  const room = rooms.find((item) => String(item.room_number) === String(booking.room));
  const building = buildings.find((item) => item.name === String(booking.building).split('\n')[0]);
  return {
    id: booking.id,
    event_type: 'reservation',
    event_title: 'Бронирование аудитории',
    event_description: '',
    event_date: toIsoDate(booking.date),
    event_time_slot: [booking.slot],
    building_id: building?.id || fallbackBuildingId,
    room_id: room?.id || fallbackRoomId || booking.room,
    user_id: userId,
    is_active: booking.status !== 'Отменена'
  };
}

export default function BookingPage() {
  const user = getStoredUser();
  const currentUserId = Number(user?.id || user?.user_id || 0);
  const [bookings, setBookings] = useState([]);
  const [buildings, setBuildings] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [filters, setFilters] = useState(emptyFilters);
  const [page, setPage] = useState(1);
  const [modalMode, setModalMode] = useState(null);
  const [editingBooking, setEditingBooking] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const buildingById = useMemo(
    () => new Map(buildings.map((building) => [Number(building.id), building])),
    [buildings]
  );
  const roomById = useMemo(
    () => new Map(rooms.map((room) => [Number(room.id), room])),
    [rooms]
  );

  async function loadBookingData() {
    setIsLoading(true);
    setError('');
    try {
      const [buildingsResponse, roomsResponse, bookingsResponse] = await Promise.all([
        bookingApi.buildings.list({ limit: 1000 }),
        bookingApi.rooms.list({ limit: 1000 }),
        currentUserId
          ? bookingApi.bookings.list({ user_id: currentUserId, limit: 1000 })
          : Promise.resolve({ bookings: [] })
      ]);
      const nextBuildings = buildingsResponse.buildings || [];
      const nextRooms = roomsResponse.rooms || [];
      const nextBookings = (bookingsResponse.bookings || [])
        .filter((booking) => (
          !isScheduleBooking(booking) &&
          (!currentUserId || Number(booking.user_id) === currentUserId)
        ))
        .sort(sortNewestFirst);
      setBuildings(nextBuildings);
      setRooms(nextRooms);
      setBookings(nextBookings);
    } catch (requestError) {
      const fallbackBuilding = { id: 1, name: 'Костина', address: 'ул. Костина, 2Б' };
      const fallbackRooms = [
        { id: 103, building_id: 1, room_number: '103', is_zoom: false, is_active: true, equipment: [] },
        { id: 112, building_id: 1, room_number: '112', is_zoom: false, is_active: true, equipment: [] },
        { id: 113, building_id: 1, room_number: '113', is_zoom: false, is_active: true, equipment: [] }
      ];
      setBuildings([fallbackBuilding]);
      setRooms(fallbackRooms);
      setBookings(
        currentUserId
          ? sampleBookings
            .map((booking) => mapSampleBooking(booking, [fallbackBuilding], fallbackRooms, 1, 112, currentUserId))
            .sort(sortNewestFirst)
          : []
      );
      setError(requestError.message || 'Не удалось загрузить бронирования');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadBookingData();
  }, [currentUserId]);

  const filteredBookings = useMemo(
    () => bookings.filter((booking) => bookingMatches(booking, filters, roomById)),
    [bookings, filters, roomById]
  );
  const totalPages = Math.max(1, Math.ceil(filteredBookings.length / PAGE_SIZE));
  const visibleBookings = filteredBookings.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  useEffect(() => {
    setPage(1);
  }, [filters]);

  useEffect(() => {
    if (page > totalPages) setPage(totalPages);
  }, [page, totalPages]);

  function updateFilter(field, value) {
    setFilters((current) => ({ ...current, [field]: value }));
  }

  function openCreateModal() {
    setEditingBooking(null);
    setModalMode('create');
  }

  function openEditModal(booking) {
    setEditingBooking(booking);
    setModalMode('edit');
  }

  async function saveBooking(payload) {
    let response;
    if (modalMode === 'edit' && editingBooking?.id) {
      response = await bookingApi.bookings.update(editingBooking.id, payload);
    } else {
      response = await bookingApi.bookings.create(payload);
    }
    if (response?.success === false) {
      throw new Error(response.status || 'Не удалось сохранить бронирование');
    }
    setModalMode(null);
    setEditingBooking(null);
    await loadBookingData();
  }

  async function removeBooking(booking) {
    const response = await bookingApi.bookings.remove(booking.id);
    if (response?.success === false) {
      setError(response.status || 'Не удалось удалить бронирование');
      return;
    }
    setBookings((current) => current.filter((item) => item.id !== booking.id));
    setConfirmDelete(null);
  }

  function requestRemoveBooking(booking) {
    setConfirmDelete({
      title: 'Удаление бронирования',
      message: 'Вы уверены, что хотите удалить это бронирование?',
      onConfirm: () => removeBooking(booking)
    });
  }

  const tableColumns = '12ch 0.9fr 1.2fr 0.75fr 1fr 1.2fr 0.8fr 116px';

  return (
    <>
      <Panel
        title="История бронирований аудиторий"
        action={(
          <button className="button button--primary widget-action-button" type="button" onClick={openCreateModal}>
            <Plus size={17} />
            Новое бронирование
          </button>
        )}
      >
        {error && <div className="inline-alert">{error}</div>}
        <div className="booking-history-table user-table">
          <div className="user-table__head" style={{ gridTemplateColumns: tableColumns }}>
            <div className="user-table__head-cell">
              <span>ID</span>
              <input value={filters.id} onChange={(event) => updateFilter('id', event.target.value)} />
            </div>
            <div className="user-table__head-cell">
              <span>Дата</span>
              <input type="date" value={filters.event_date} onChange={(event) => updateFilter('event_date', event.target.value)} />
            </div>
            <div className="user-table__head-cell">
              <span>Корпус</span>
              <select value={filters.building_id} onChange={(event) => updateFilter('building_id', event.target.value)}>
                <option value="">Все</option>
                {buildings.map((building) => (
                  <option value={building.id} key={building.id}>{building.name}</option>
                ))}
              </select>
            </div>
            <div className="user-table__head-cell">
              <span>Аудитория</span>
              <input value={filters.room_number} onChange={(event) => updateFilter('room_number', event.target.value)} />
            </div>
            <div className="user-table__head-cell">
              <span>Временной слот</span>
              <input value={filters.event_time_slot} onChange={(event) => updateFilter('event_time_slot', event.target.value)} />
            </div>
            <div className="user-table__head-cell">
              <span>Название</span>
              <input value={filters.event_title} onChange={(event) => updateFilter('event_title', event.target.value)} />
            </div>
            <div className="user-table__head-cell">
              <span>Статус</span>
              <select value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
                <option value="">Все</option>
                <option value="Активна">Активна</option>
                <option value="Отменена">Отменена</option>
                <option value="Завершена">Завершена</option>
              </select>
            </div>
            <div className="user-table__head-cell">
              <span>Действия</span>
            </div>
          </div>

          {isLoading ? (
            <SkeletonRows rows={5} />
          ) : visibleBookings.length ? (
            visibleBookings.map((booking) => {
              const room = roomById.get(Number(booking.room_id));
              const building = buildingById.get(Number(booking.building_id));
              const status = bookingStatus(booking);
              return (
                <div className="user-table__row" style={{ gridTemplateColumns: tableColumns }} key={booking.id}>
                  <div>{booking.id}</div>
                  <div>{formatRussianDate(booking.event_date)}</div>
                  <div className="pre-line">{buildingLabel(building) || booking.building_id}</div>
                  <div>{room?.room_number || booking.room_id}</div>
                  <div>{normalizeSlot(booking.event_time_slot)}</div>
                  <div>{booking.event_title || 'Бронирование аудитории'}</div>
                  <div><span className={`status status--${status}`}>{status}</span></div>
                  <div className="table-actions">
                    <button className="action-button action-button--edit" type="button" aria-label="Редактировать" onClick={() => openEditModal(booking)}>
                      <Edit3 size={15} />
                    </button>
                    <button className="action-button action-button--delete" type="button" aria-label="Удалить" onClick={() => requestRemoveBooking(booking)}>
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              );
            })
          ) : (
            <div className="user-table__empty">Бронирования не найдены</div>
          )}
        </div>

        <div className="user-pagination">
          <span>{filteredBookings.length ? `${(page - 1) * PAGE_SIZE + 1}-${Math.min(page * PAGE_SIZE, filteredBookings.length)} из ${filteredBookings.length}` : '0 из 0'}</span>
          <div className="user-pagination__buttons">
            <button className="icon-ghost" type="button" aria-label="Назад" disabled={page === 1} onClick={() => setPage((current) => Math.max(1, current - 1))}>
              <ChevronLeft size={18} />
            </button>
            <span>{page} / {totalPages}</span>
            <button className="icon-ghost" type="button" aria-label="Вперед" disabled={page === totalPages} onClick={() => setPage((current) => Math.min(totalPages, current + 1))}>
              <ChevronRight size={18} />
            </button>
          </div>
        </div>
      </Panel>

      {modalMode && (
        <BookingModal
          booking={editingBooking}
          buildings={buildings}
          rooms={rooms}
          currentUserId={currentUserId}
          mode={modalMode}
          onClose={() => {
            setModalMode(null);
            setEditingBooking(null);
          }}
          onSubmit={saveBooking}
        />
      )}
      {confirmDelete && (
        <ConfirmModal
          title={confirmDelete.title}
          message={confirmDelete.message}
          confirmLabel="Да"
          cancelLabel="Нет"
          onCancel={() => setConfirmDelete(null)}
          onConfirm={confirmDelete.onConfirm}
        />
      )}
    </>
  );
}
