export const eventTypeLabels = {
  lecture: 'Лекция',
  seminar: 'Семинар',
  practice: 'Практика',
  exam: 'Экзамен',
  study: 'Занятие',
  reservation: 'Бронирование',
  booking: 'Бронирование'
};

export function eventTypeLabel(value) {
  return eventTypeLabels[String(value || '').toLowerCase()] || value || 'Занятие';
}

export function toIsoDate(value) {
  if (!value) return '';
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(value))) return value;
  const match = String(value).match(/^(\d{2})\.(\d{2})\.(\d{4})$/);
  if (match) return `${match[3]}-${match[2]}-${match[1]}`;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function formatRussianDate(value) {
  const iso = toIsoDate(value);
  const match = iso.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  return match ? `${match[3]}.${match[2]}.${match[1]}` : value || '';
}

export function isScheduleBooking(booking) {
  return String(booking?.event_description || '').startsWith('Published from schedule');
}
