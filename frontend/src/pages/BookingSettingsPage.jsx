import { ChevronLeft, ChevronRight, Edit3, Plus, Trash2 } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import ConfirmModal from '../components/ConfirmModal.jsx';
import Panel from '../components/Panel.jsx';
import { SkeletonRows } from '../components/Skeleton.jsx';
import { bookingApi } from '../utils/api.js';
import { formatRussianDate } from '../utils/formatters.js';

const pageSize = 5;

const emptyBuilding = { name: '', address: '' };
const emptyEquipment = { name: '', description: '' };
const emptyRoom = {
  building_id: '',
  room_number: '',
  is_zoom: false,
  is_active: true,
  equipment: []
};

const emptyFilters = {
  buildings: { id: '', name: '', address: '' },
  equipment: { id: '', name: '', description: '' },
  rooms: { id: '', building_id: '', room_number: '', equipment: '', is_zoom: '', is_active: '' },
  bookings: { id: '', event_date: '', event_title: '', user_id: '', room_id: '', event_time_slot: '', is_active: '' }
};

const fallbackBuildings = [
  { id: 1, name: 'Костина', address: 'ул. Костина, 2Б' }
];

const fallbackEquipment = [
  { id: 1, name: 'Компьютер', description: 'Рабочее место преподавателя' },
  { id: 2, name: 'Проектор', description: 'Потолочный проектор' },
  { id: 3, name: 'Умная доска', description: 'Интерактивная доска' }
];

const fallbackRooms = [
  { id: 103, building_id: 1, room_number: '103', equipment: [{ name: 'Компьютер', qty: 1 }], is_zoom: false, is_active: true },
  { id: 112, building_id: 1, room_number: '112', equipment: [{ name: 'Проектор', qty: 1 }, { name: 'Умная доска', qty: 1 }], is_zoom: true, is_active: true }
];

const fallbackBookings = [
  {
    id: 13412,
    event_type: 'study',
    event_title: 'Проектный семинар',
    event_date: '2026-05-18',
    event_time_slot: ['08:00 - 09:20'],
    user_id: 1,
    building_id: 1,
    room_id: 112,
    is_active: true
  }
];

function totalPages(total) {
  return Math.max(Math.ceil(total / pageSize), 1);
}

function equipmentText(items = []) {
  return items.length ? items.map((item) => `${item.name} x${item.qty || 1}`).join(', ') : '-';
}

function bookingStatus(booking) {
  return booking.is_active === false ? 'Отменена' : 'Активна';
}

function isScheduleBooking(booking) {
  return String(booking.event_description || '').startsWith('Published from schedule');
}

function normalizeResponseItem(response, key) {
  return response?.[key] || null;
}

function matchesText(value, query) {
  if (!query) return true;
  return String(value ?? '').toLowerCase().includes(String(query).toLowerCase());
}

function applyFilters(rows, filters, matchers) {
  return rows.filter((row) => Object.entries(filters).every(([key, value]) => (
    value === '' || (matchers[key] || ((item, query) => matchesText(item[key], query)))(row, value)
  )));
}

function paginateRows(rows, page) {
  const start = (page - 1) * pageSize;
  return rows.slice(start, start + pageSize);
}

export default function BookingSettingsPage() {
  const [buildings, setBuildings] = useState(fallbackBuildings);
  const [rooms, setRooms] = useState(fallbackRooms);
  const [equipment, setEquipment] = useState(fallbackEquipment);
  const [allBuildings, setAllBuildings] = useState(fallbackBuildings);
  const [allRooms, setAllRooms] = useState(fallbackRooms);
  const [allEquipment, setAllEquipment] = useState(fallbackEquipment);
  const [allBookings, setAllBookings] = useState(fallbackBookings);
  const [buildingOptions, setBuildingOptions] = useState(fallbackBuildings);
  const [equipmentOptions, setEquipmentOptions] = useState(fallbackEquipment);
  const [bookings, setBookings] = useState(fallbackBookings);
  const [buildingTotal, setBuildingTotal] = useState(fallbackBuildings.length);
  const [roomTotal, setRoomTotal] = useState(fallbackRooms.length);
  const [equipmentTotal, setEquipmentTotal] = useState(fallbackEquipment.length);
  const [bookingTotal, setBookingTotal] = useState(fallbackBookings.length);
  const [pages, setPages] = useState({ buildings: 1, rooms: 1, equipment: 1, bookings: 1 });
  const [filters, setFilters] = useState(emptyFilters);
  const [modal, setModal] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => { applyBuildingFilters(); }, [filters.buildings, allBuildings, pages.buildings]);
  useEffect(() => { applyEquipmentFilters(); }, [filters.equipment, allEquipment, pages.equipment]);
  useEffect(() => { applyRoomFilters(); }, [filters.rooms, allRooms, pages.rooms, buildingOptions]);
  useEffect(() => { applyBookingFilters(); }, [filters.bookings, allBookings, pages.bookings]);
  useEffect(() => {
    async function loadInitial() {
      setIsLoading(true);
      const [buildingsResponse, equipmentResponse, roomsResponse, bookingsResponse] = await Promise.all([
        bookingApi.buildings.list({ limit: 1000 }).catch(() => null),
        bookingApi.equipment.list({ limit: 1000 }).catch(() => null),
        bookingApi.rooms.list({ limit: 1000 }).catch(() => null),
        bookingApi.bookings.list({ limit: 1000 }).catch(() => null)
      ]);
      if (buildingsResponse?.buildings) {
        setAllBuildings(buildingsResponse.buildings);
        setBuildingOptions(buildingsResponse.buildings);
      }
      if (equipmentResponse?.equipment) {
        setAllEquipment(equipmentResponse.equipment);
        setEquipmentOptions((current) => equipmentResponse.equipment.length ? equipmentResponse.equipment : current);
      }
      if (roomsResponse?.rooms) setAllRooms(roomsResponse.rooms);
      if (bookingsResponse?.bookings) setAllBookings(bookingsResponse.bookings.filter((booking) => !isScheduleBooking(booking)));
      setIsLoading(false);
    }

    loadInitial();
  }, []);

  function setPage(key, value) {
    setPages((current) => ({ ...current, [key]: value }));
  }

  function setFilter(kind, key, value) {
    setPages((current) => ({ ...current, [kind]: 1 }));
    setFilters((current) => ({
      ...current,
      [kind]: { ...current[kind], [key]: value }
    }));
  }

  async function loadBuildings() {
    const response = await bookingApi.buildings.list({ limit: 1000 }).catch(() => null);
    if (response?.buildings) {
      setAllBuildings(response.buildings);
      setBuildingOptions(response.buildings);
    }
  }

  async function loadRooms() {
    const response = await bookingApi.rooms.list({ limit: 1000 }).catch(() => null);
    if (response?.rooms) {
      setAllRooms(response.rooms);
    }
  }

  async function loadEquipment() {
    const response = await bookingApi.equipment.list({ limit: 1000 }).catch(() => null);
    if (response?.equipment) {
      setAllEquipment(response.equipment);
      setEquipmentOptions(response.equipment);
    }
  }

  async function loadBookings() {
    const response = await bookingApi.bookings.list({ limit: 1000 }).catch(() => null);
    if (response?.bookings) {
      setAllBookings(response.bookings.filter((booking) => !isScheduleBooking(booking)));
    }
  }

  function applyBuildingFilters() {
    const filtered = applyFilters(allBuildings, filters.buildings, {});
    setBuildingTotal(filtered.length);
    setBuildings(paginateRows(filtered, pages.buildings));
  }

  function applyEquipmentFilters() {
    const filtered = applyFilters(allEquipment, filters.equipment, {});
    setEquipmentTotal(filtered.length);
    setEquipment(paginateRows(filtered, pages.equipment));
  }

  function applyRoomFilters() {
    const filtered = applyFilters(allRooms, filters.rooms, {
      building_id: (row, value) => matchesText(
        buildingOptions.find((building) => Number(building.id) === Number(row.building_id))?.name || row.building_id,
        value
      ),
      equipment: (row, value) => matchesText(equipmentText(row.equipment), value),
      is_zoom: (row, value) => String(row.is_zoom) === value,
      is_active: (row, value) => String(row.is_active) === value
    });
    setRoomTotal(filtered.length);
    setRooms(paginateRows(filtered, pages.rooms));
  }

  function applyBookingFilters() {
    const filtered = applyFilters(allBookings, filters.bookings, {
      event_time_slot: (row, value) => matchesText(row.event_time_slot?.[0], value),
      is_active: (row, value) => String(row.is_active !== false) === value
    });
    setBookingTotal(filtered.length);
    setBookings(paginateRows(filtered, pages.bookings));
  }

  async function saveBuilding(form) {
    const saved = modal.item
      ? normalizeResponseItem(await bookingApi.buildings.update(modal.item.id, form), 'building')
      : normalizeResponseItem(await bookingApi.buildings.create(form), 'building');
    if (saved) {
      await loadBuildings();
    }
    setModal(null);
  }

  async function saveEquipment(form) {
    const saved = modal.item
      ? normalizeResponseItem(await bookingApi.equipment.update(modal.item.id, form), 'equipment')
      : normalizeResponseItem(await bookingApi.equipment.create(form), 'equipment');
    if (saved) {
      await loadEquipment();
    }
    setModal(null);
  }

  async function saveRoom(form) {
    const payload = {
      building_id: Number(form.building_id),
      room_number: form.room_number,
      is_zoom: form.is_zoom,
      is_active: form.is_active,
      equipment: form.equipment.map((item) => ({ name: item.name, qty: Number(item.qty) || 1 }))
    };
    const saved = modal.item
      ? normalizeResponseItem(await bookingApi.rooms.update(modal.item.id, payload), 'room')
      : normalizeResponseItem(await bookingApi.rooms.create(payload), 'room');
    if (saved) {
      await loadRooms();
    }
    setModal(null);
  }

  async function remove(kind, item) {
    const api = {
      buildings: bookingApi.buildings,
      rooms: bookingApi.rooms,
      equipment: bookingApi.equipment,
      bookings: bookingApi.bookings
    }[kind];
    await api.remove(item.id).catch(() => {});
    if (kind === 'buildings') {
      setAllBuildings((current) => current.filter((row) => row.id !== item.id));
      setBuildingOptions((current) => current.filter((row) => row.id !== item.id));
      setAllRooms((current) => current.filter((row) => Number(row.building_id) !== Number(item.id)));
      setRooms((current) => current.filter((row) => Number(row.building_id) !== Number(item.id)));
    }
    if (kind === 'rooms') setAllRooms((current) => current.filter((row) => row.id !== item.id));
    if (kind === 'equipment') setAllEquipment((current) => current.filter((row) => row.id !== item.id));
    if (kind === 'bookings') setAllBookings((current) => current.filter((row) => row.id !== item.id));
    setConfirmDelete(null);
  }

  function requestRemove(kind, item) {
    setConfirmDelete({
      title: 'Удаление',
      message: 'Вы уверены, что хотите удалить этот элемент?',
      onConfirm: () => remove(kind, item)
    });
  }

  async function updateBookingStatus(booking, isActive) {
    const updated = normalizeResponseItem(
      await bookingApi.bookings.update(booking.id, { is_active: isActive }).catch(() => null),
      'booking'
    );
    setBookings((current) => current.map((item) => (
      item.id === booking.id ? { ...item, ...(updated || {}), is_active: isActive } : item
    )));
    setAllBookings((current) => current.map((item) => (
      item.id === booking.id ? { ...item, ...(updated || {}), is_active: isActive } : item
    )));
  }

  return (
    <>
      <div className="booking-settings-grid">
        <CrudWidget
          title="Корпуса"
          addLabel="Добавить корпус"
          rows={buildings}
          filters={filters.buildings}
          total={buildingTotal}
          page={pages.buildings}
          onPageChange={(page) => setPage('buildings', page)}
          onFilterChange={(key, value) => setFilter('buildings', key, value)}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr', filterKey: 'id', filterType: 'number' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'address', label: 'Адрес', filterKey: 'address' }
          ]}
          onAdd={() => setModal({ kind: 'building' })}
          onEdit={(item) => setModal({ kind: 'building', item })}
          onRemove={(item) => requestRemove('buildings', item)}
          isLoading={isLoading}
        />

        <CrudWidget
          title="Оборудование"
          addLabel="Добавить оборудование"
          rows={equipment}
          filters={filters.equipment}
          total={equipmentTotal}
          page={pages.equipment}
          onPageChange={(page) => setPage('equipment', page)}
          onFilterChange={(key, value) => setFilter('equipment', key, value)}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr', filterKey: 'id', filterType: 'number' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'description', label: 'Описание', filterKey: 'description', render: (row) => row.description || '-' }
          ]}
          onAdd={() => setModal({ kind: 'equipment' })}
          onEdit={(item) => setModal({ kind: 'equipment', item })}
          onRemove={(item) => requestRemove('equipment', item)}
          isLoading={isLoading}
        />

        <CrudWidget
          title="Аудитории"
          addLabel="Добавить аудиторию"
          rows={rooms}
          filters={filters.rooms}
          total={roomTotal}
          page={pages.rooms}
          onPageChange={(page) => setPage('rooms', page)}
          onFilterChange={(key, value) => setFilter('rooms', key, value)}
          columns={[
            { key: 'id', label: 'ID', width: '0.45fr', filterKey: 'id', filterType: 'number' },
            { key: 'building_id', label: 'Корпус', filterKey: 'building_id', render: (row) => buildingOptions.find((building) => Number(building.id) === Number(row.building_id))?.name || row.building_id },
            { key: 'room_number', label: 'Аудитория', filterKey: 'room_number' },
            { key: 'equipment', label: 'Оборудование', filterKey: 'equipment', render: (row) => equipmentText(row.equipment) },
            { key: 'is_zoom', label: 'Zoom', filterKey: 'is_zoom', filterType: 'yesNo', render: (row) => row.is_zoom ? 'Да' : 'Нет' },
            { key: 'is_active', label: 'Статус', filterKey: 'is_active', filterType: 'roomStatus', render: (row) => row.is_active ? 'Активна' : 'Выключена' }
          ]}
          onAdd={() => setModal({ kind: 'room' })}
          onEdit={(item) => setModal({ kind: 'room', item })}
          onRemove={(item) => requestRemove('rooms', item)}
          isLoading={isLoading}
        />

        <CrudWidget
          title="Все бронирования"
          rows={bookings}
          filters={filters.bookings}
          total={bookingTotal}
          page={pages.bookings}
          onPageChange={(page) => setPage('bookings', page)}
          onFilterChange={(key, value) => setFilter('bookings', key, value)}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr', filterKey: 'id', filterType: 'number' },
            { key: 'event_date', label: 'Дата', filterKey: 'event_date', filterType: 'date', render: (row) => formatRussianDate(row.event_date) },
            { key: 'event_title', label: 'Событие', filterKey: 'event_title' },
            { key: 'user_id', label: 'Пользователь', filterKey: 'user_id', filterType: 'number' },
            { key: 'room_id', label: 'Аудитория', filterKey: 'room_id', filterType: 'number' },
            { key: 'event_time_slot', label: 'Слот', filterKey: 'event_time_slot', render: (row) => row.event_time_slot?.[0] || '-' },
            {
              key: 'is_active',
              label: 'Статус',
              filterKey: 'is_active',
              filterType: 'bookingStatus',
              render: (row) => (
                <select
                  className="booking-status-select"
                  value={row.is_active === false ? 'false' : 'true'}
                  onChange={(event) => updateBookingStatus(row, event.target.value === 'true')}
                >
                  <option value="true">Активна</option>
                  <option value="false">Отменена</option>
                </select>
              )
            }
          ]}
          onRemove={(item) => requestRemove('bookings', item)}
          statusClass={(row) => row.is_active === false ? 'is-muted' : ''}
          isLoading={isLoading}
        />
      </div>

      {modal?.kind === 'building' && (
        <SimpleModal
          title={modal.item ? 'Редактирование корпуса' : 'Новый корпус'}
          initialValues={modal.item || emptyBuilding}
          fields={[
            { key: 'name', label: 'Название' },
            { key: 'address', label: 'Адрес' }
          ]}
          onClose={() => setModal(null)}
          onSubmit={saveBuilding}
        />
      )}

      {modal?.kind === 'equipment' && (
        <SimpleModal
          title={modal.item ? 'Редактирование оборудования' : 'Новое оборудование'}
          initialValues={modal.item || emptyEquipment}
          fields={[
            { key: 'name', label: 'Название' },
            { key: 'description', label: 'Описание' }
          ]}
          onClose={() => setModal(null)}
          onSubmit={saveEquipment}
        />
      )}

      {modal?.kind === 'room' && (
        <RoomModal
          initialValues={modal.item ? {
            ...emptyRoom,
            ...modal.item,
            building_id: String(modal.item.building_id || ''),
            equipment: modal.item.equipment || []
          } : emptyRoom}
          buildings={buildingOptions}
          equipmentOptions={equipmentOptions}
          onClose={() => setModal(null)}
          onSubmit={saveRoom}
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

function CrudWidget({ title, addLabel, rows, columns, filters = {}, total, page, onPageChange, onFilterChange, onAdd, onEdit, onRemove, statusClass, isLoading }) {
  const template = `${columns.map((column) => (column.key === 'id' ? '12ch' : column.width || '1fr')).join(' ')} 116px`;
  return (
    <Panel
      className="booking-settings-widget"
      title={title}
      action={addLabel && (
        <button className="button button--primary widget-action-button" type="button" onClick={onAdd}>
          <Plus size={17} />
          {addLabel}
        </button>
      )}
    >
      <div className="user-table booking-settings-table">
        <div className="user-table__head" style={{ gridTemplateColumns: template }}>
          {columns.map((column) => (
            <div className="user-table__head-cell" key={column.key}>
              <span>{column.label}</span>
              {column.filterKey && (
                <FilterControl
                  column={column}
                  value={filters[column.filterKey] || ''}
                  onChange={(value) => onFilterChange?.(column.filterKey, value)}
                />
              )}
            </div>
          ))}
          <div className="user-table__head-cell"><span>Действия</span></div>
        </div>
        {isLoading ? (
          <SkeletonRows rows={5} />
        ) : rows.length ? rows.map((row) => (
          <div className={`data-table__row ${statusClass ? statusClass(row) : ''}`} style={{ gridTemplateColumns: template }} key={row.id}>
            {columns.map((column) => <div key={column.key}>{column.render ? column.render(row) : row[column.key]}</div>)}
            <RowActions row={row} onEdit={onEdit} onRemove={onRemove} />
          </div>
        )) : <div className="user-table__empty">Ничего не найдено</div>}
      </div>
      <Pagination page={page} total={total} onPageChange={onPageChange} />
    </Panel>
  );
}

function FilterControl({ column, value, onChange }) {
  if (column.filterType === 'yesNo') {
    return (
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Все</option>
        <option value="true">Да</option>
        <option value="false">Нет</option>
      </select>
    );
  }

  if (column.filterType === 'roomStatus') {
    return (
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Все</option>
        <option value="true">Активна</option>
        <option value="false">Выключена</option>
      </select>
    );
  }

  if (column.filterType === 'bookingStatus') {
    return (
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">Все</option>
        <option value="true">Активна</option>
        <option value="false">Отменена</option>
      </select>
    );
  }

  return (
    <input
      type={column.filterType === 'number' || column.filterType === 'date' ? column.filterType : 'text'}
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  );
}

function RowActions({ row, onEdit, onRemove }) {
  return (
    <div className="table-actions">
      {onEdit && (
        <button className="action-button action-button--edit" type="button" aria-label="Редактировать" onClick={() => onEdit(row)}>
          <Edit3 size={15} />
        </button>
      )}
      <button className="action-button action-button--delete" type="button" aria-label="Удалить" onClick={() => onRemove(row)}>
        <Trash2 size={15} />
      </button>
    </div>
  );
}

function SimpleModal({ title, initialValues, fields, onClose, onSubmit }) {
  const [form, setForm] = useState(initialValues);
  const canSubmit = useMemo(() => fields.every((field) => field.key === 'description' || String(form[field.key] || '').trim()), [fields, form]);

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    if (canSubmit) await onSubmit(form);
  }

  return (
    <div className="modal-backdrop">
      <form className="user-modal" onSubmit={submit}>
        <h2>{title}</h2>
        <div className="user-form-grid">
          {fields.map((field) => (
            <label key={field.key}>
              <span>{field.label}</span>
              <input value={form[field.key] || ''} onChange={(event) => setField(field.key, event.target.value)} />
            </label>
          ))}
        </div>
        <ModalActions canSubmit={canSubmit} onClose={onClose} />
      </form>
    </div>
  );
}

function RoomModal({ initialValues, buildings, equipmentOptions, onClose, onSubmit }) {
  const [form, setForm] = useState(initialValues);
  const canSubmit = buildings.length > 0 && form.building_id && form.room_number.trim();

  function setField(key, value) {
    setForm((current) => ({ ...current, [key]: value }));
  }

  function updateEquipment(index, key, value) {
    setForm((current) => ({
      ...current,
      equipment: current.equipment.map((item, itemIndex) => itemIndex === index ? { ...item, [key]: value } : item)
    }));
  }

  function addEquipment() {
    const first = equipmentOptions[0]?.name || '';
    if (!first) return;
    setForm((current) => ({ ...current, equipment: [...current.equipment, { name: first, qty: 1 }] }));
  }

  function removeEquipment(index) {
    setForm((current) => ({ ...current, equipment: current.equipment.filter((_, itemIndex) => itemIndex !== index) }));
  }

  async function submit(event) {
    event.preventDefault();
    if (canSubmit) await onSubmit(form);
  }

  return (
    <div className="modal-backdrop">
      <form className="user-modal" onSubmit={submit}>
        <h2>{initialValues.id ? 'Редактирование аудитории' : 'Новая аудитория'}</h2>
        <div className="user-form-grid">
          <label>
            <span>Корпус</span>
            <select value={form.building_id} onChange={(event) => setField('building_id', event.target.value)} disabled={!buildings.length}>
              <option value="">{buildings.length ? 'Выберите корпус' : 'Нет доступных корпусов'}</option>
              {buildings.map((building) => <option key={building.id} value={building.id}>{building.name}</option>)}
            </select>
          </label>
          <label>
            <span>Аудитория</span>
            <input value={form.room_number} onChange={(event) => setField('room_number', event.target.value)} />
          </label>
          <label className="user-toggle">
            <input type="checkbox" checked={form.is_zoom} onChange={(event) => setField('is_zoom', event.target.checked)} />
            <span>Zoom</span>
          </label>
          <label className="user-toggle">
            <input type="checkbox" checked={form.is_active} onChange={(event) => setField('is_active', event.target.checked)} />
            <span>Активная аудитория</span>
          </label>
        </div>

        <div className="room-equipment-editor">
          <div className="room-equipment-editor__header">
            <span>Оборудование аудитории</span>
            <button className="button button--primary" type="button" onClick={addEquipment} disabled={!equipmentOptions.length}>
              <Plus size={15} />
              Добавить
            </button>
          </div>
          {form.equipment.map((item, index) => (
            <div className="room-equipment-row" key={`${item.name}-${index}`}>
              <select value={item.name} onChange={(event) => updateEquipment(index, 'name', event.target.value)}>
                {equipmentOptions.map((option) => <option key={option.id || option.name} value={option.name}>{option.name}</option>)}
              </select>
              <input type="number" min="1" value={item.qty || 1} onChange={(event) => updateEquipment(index, 'qty', event.target.value)} />
              <button className="action-button action-button--delete" type="button" aria-label="Удалить оборудование" onClick={() => removeEquipment(index)}>
                <Trash2 size={15} />
              </button>
            </div>
          ))}
          {!equipmentOptions.length && <div className="user-table__empty">Сначала добавьте оборудование в базу</div>}
        </div>

        <ModalActions canSubmit={canSubmit} onClose={onClose} />
      </form>
    </div>
  );
}

function ModalActions({ canSubmit, onClose }) {
  return (
    <div className="modal-actions">
      <button className="button button--danger" type="button" onClick={onClose}>Отменить</button>
      <button className="button button--primary" type="submit" disabled={!canSubmit}>Сохранить</button>
    </div>
  );
}

function Pagination({ page, total, onPageChange }) {
  const pages = totalPages(total);
  const from = total === 0 ? 0 : ((page - 1) * pageSize) + 1;
  const to = Math.min(page * pageSize, total);

  return (
    <div className="user-pagination">
      <span>{from}-{to} из {total}</span>
      <div className="user-pagination__buttons">
        <button className="icon-ghost" type="button" disabled={page <= 1} onClick={() => onPageChange(page - 1)}><ChevronLeft size={18} /></button>
        <span>{page} / {pages}</span>
        <button className="icon-ghost" type="button" disabled={page >= pages} onClick={() => onPageChange(page + 1)}><ChevronRight size={18} /></button>
      </div>
    </div>
  );
}
