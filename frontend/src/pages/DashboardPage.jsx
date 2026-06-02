import { CalendarDays, DoorOpen } from 'lucide-react';
import { useEffect, useState } from 'react';

import Panel from '../components/Panel.jsx';
import { DashboardSkeleton } from '../components/Skeleton.jsx';
import { bookingApi, scheduleApi } from '../utils/api.js';
import { getCurrentRole, roles } from '../utils/access.js';
import { eventTypeLabel, isScheduleBooking } from '../utils/formatters.js';
import { getStoredUser } from '../utils/storage.js';

const fallbackScheduleItems = [
  {
    id: 'schedule-1',
    title: 'Проектный семинар',
    time_slot: '08:00 - 09:20',
    room_number: '113',
    building_address: 'ул. Костина, 2Б',
    instructor_name: 'Иванов И.И.',
    item_type: 'Практика'
  },
  {
    id: 'schedule-2',
    title: 'Математический анализ',
    time_slot: '11:10 - 12:30',
    room_number: '218',
    building_address: 'ул. Костина, 2Б',
    instructor_name: 'Петрова А.С.',
    item_type: 'Лекция'
  }
];

const fallbackBookings = [
  {
    id: 13412,
    event_title: 'Консультация по проекту',
    event_time_slot: ['13:00 - 14:20'],
    room_id: '112',
    building_id: 'Костина',
    building_address: 'ул. Костина, 2Б',
    status: 'Активна'
  }
];

function todayIso() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function formatSlot(value) {
  if (Array.isArray(value)) return value[0] || '';
  return value || '';
}

function mapScheduleItems(items = []) {
  return items.map((item, index) => ({
    id: item.id || `schedule-${index}`,
    title: item.title || 'Занятие',
    slot: formatSlot(item.time_slot),
    room: item.room_number || item.room_id || 'Аудитория',
    address: item.building_address || item.address || '',
    meta: [eventTypeLabel(item.item_type), item.instructor_name].filter(Boolean).join(' · ')
  }));
}

function mapBookings(bookings = [], buildings = []) {
  return bookings.map((booking, index) => ({
    id: booking.id || `booking-${index}`,
    title: booking.event_title || 'Бронирование аудитории',
    slot: formatSlot(booking.event_time_slot),
    room: booking.room_id || 'Аудитория',
    address: booking.building_address || booking.address || buildings.find((building) => Number(building.id) === Number(booking.building_id))?.address || '',
    meta: [booking.building_id, booking.status || 'Активна'].filter(Boolean).join(' · ')
  }));
}

function WidgetList({ items, emptyText, isLoading }) {
  if (isLoading) return <DashboardSkeleton />;

  if (!items.length) {
    return <div className="dashboard-empty-state">{emptyText}</div>;
  }

  return (
    <div className="dashboard-widget-list">
      {items.map((item) => (
        <div className="dashboard-widget-row" key={item.id}>
          <div className="dashboard-widget-time">{item.slot}</div>
          <div className="dashboard-widget-main">
            <strong>{item.title}</strong>
            <span>{item.meta}</span>
            {item.address && <span>{item.address}</span>}
          </div>
          <div className="dashboard-widget-room">{item.room}</div>
        </div>
      ))}
    </div>
  );
}

export default function DashboardPage() {
  const role = getCurrentRole();
  const user = getStoredUser();
  const currentUserId = Number(user?.id || user?.user_id || 0);
  const showBookings = role !== roles.STUDENT;
  const [scheduleItems, setScheduleItems] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [isScheduleLoading, setIsScheduleLoading] = useState(true);
  const [isBookingsLoading, setIsBookingsLoading] = useState(showBookings);

  useEffect(() => {
    const date = todayIso();

    setIsScheduleLoading(true);
    scheduleApi.items.list({ date_from: date, date_to: date, published_only: true }).then((response) => {
      const mapped = mapScheduleItems(response?.schedule_items || []);
      setScheduleItems(mapped);
    }).catch(() => {
      setScheduleItems(mapScheduleItems(fallbackScheduleItems));
    }).finally(() => setIsScheduleLoading(false));

    if (showBookings) {
      setIsBookingsLoading(true);
      Promise.all([
        currentUserId
          ? bookingApi.bookings.list({ event_date: date, user_id: currentUserId })
          : Promise.resolve({ bookings: [] }),
        bookingApi.buildings.list({ limit: 1000 }).catch(() => null)
      ]).then(([response, buildingsResponse]) => {
        const mapped = mapBookings(
          (response?.bookings || []).filter((booking) => (
            !isScheduleBooking(booking) &&
            (!currentUserId || Number(booking.user_id) === currentUserId)
          )),
          buildingsResponse?.buildings || []
        );
        setBookings(mapped);
      }).catch(() => {
        setBookings(mapBookings(fallbackBookings));
      }).finally(() => setIsBookingsLoading(false));
    }
  }, [currentUserId, showBookings]);

  return (
    <div className={`dashboard-widgets ${showBookings ? '' : 'dashboard-widgets--single'}`}>
      <Panel
        className="dashboard-widget"
        title={(
          <span className="dashboard-widget-title">
            <CalendarDays size={20} />
            Занятия на сегодня
          </span>
        )}
      >
        <WidgetList items={scheduleItems} emptyText="На сегодня занятий нет" isLoading={isScheduleLoading} />
      </Panel>

      {showBookings && (
        <Panel
          className="dashboard-widget"
          title={(
            <span className="dashboard-widget-title">
              <DoorOpen size={20} />
              Мои бронирования на сегодня
            </span>
          )}
        >
          <WidgetList items={bookings} emptyText="На сегодня бронирований нет" isLoading={isBookingsLoading} />
        </Panel>
      )}
    </div>
  );
}
