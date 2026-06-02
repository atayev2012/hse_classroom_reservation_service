import { ChevronLeft, ChevronRight } from 'lucide-react';

import { SkeletonLine } from './Skeleton.jsx';
import { eventTypeLabel, formatRussianDate } from '../utils/formatters.js';
import { groups as fallbackGroups, timeSlots, weekDays } from '../utils/mockData.js';

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}

function weekStart(value) {
  const date = new Date(value);
  const day = date.getDay() || 7;
  return addDays(date, 1 - day);
}

function dayIndex(value) {
  if (!value) return -1;
  const index = (new Date(value).getDay() || 7) - 1;
  return index >= 0 && index < weekDays.length ? index : -1;
}

export default function ScheduleGrid({
  editable = false,
  items = [],
  weekAnchor = weekStart(new Date()),
  groupOptions = fallbackGroups.map((group) => ({ id: group, label: group })),
  selectedGroupId = groupOptions[0]?.id || '',
  onGroupChange,
  onPrevWeek,
  onNextWeek,
  isLoading = false
}) {
  return (
    <PanellessScheduleGrid
      editable={editable}
      items={items}
      weekAnchor={weekAnchor}
      groupOptions={groupOptions}
      selectedGroupId={selectedGroupId}
      onGroupChange={onGroupChange}
      onPrevWeek={onPrevWeek}
      onNextWeek={onNextWeek}
      isLoading={isLoading}
    />
  );
}

function PanellessScheduleGrid({ editable, items, weekAnchor, groupOptions, selectedGroupId, onGroupChange, onPrevWeek, onNextWeek, isLoading }) {
  const weekEnd = addDays(weekAnchor, 6);
  const weekDates = Array.from({ length: weekDays.length }, (_, index) => addDays(weekAnchor, index));
  return (
    <section className="schedule-panel">
      <div className="schedule-toolbar">
        <div className="week-control">
          <button className="icon-ghost" type="button" aria-label="Предыдущая неделя" onClick={onPrevWeek}>
            <ChevronLeft size={22} />
          </button>
          <span>{formatRussianDate(weekAnchor)} - {formatRussianDate(weekEnd)}</span>
          <button className="icon-ghost" type="button" aria-label="Следующая неделя" onClick={onNextWeek}>
            <ChevronRight size={22} />
          </button>
        </div>
        <label className="group-select">
          <span>Группа</span>
          <select value={selectedGroupId || ''} onChange={(event) => onGroupChange?.(event.target.value)}>
            {groupOptions.map((group) => <option value={group.id} key={group.id}>{group.label}</option>)}
          </select>
        </label>
      </div>
      <div className="schedule-grid">
        <div className="schedule-grid__header schedule-grid__header--time">Время</div>
        {weekDays.map((day, index) => (
          <div className="schedule-grid__header schedule-grid__header--day" key={day}>
            <span>{day}</span>
            <small>{formatRussianDate(weekDates[index])}</small>
          </div>
        ))}
        {timeSlots.map((slot) => (
          <ScheduleRow key={slot} slot={slot} editable={editable} items={items} isLoading={isLoading} />
        ))}
      </div>
    </section>
  );
}

function ScheduleRow({ slot, editable, items, isLoading }) {
  return (
    <>
      <div className="schedule-cell schedule-time">{slot}</div>
      {weekDays.map((day) => {
        const cellItems = items.filter((entry) => (
          entry.time_slot === slot &&
          (entry.day === day || dayIndex(entry.date) === weekDays.indexOf(day))
        ));
        return (
          <div className={`schedule-cell schedule-empty ${cellItems.length ? 'has-item' : ''}`} key={`${slot}-${day}`}>
            {isLoading ? (
              <SkeletonLine />
            ) : cellItems.map((item) => (
              <div className="schedule-item-card" key={item.id || `${item.title}-${item.date}-${slot}`}>
                <strong>{item.title}</strong>
                <span>{eventTypeLabel(item.item_type || item.type)}</span>
                <span>{item.building_address || '-'}, ауд. {item.room_number || '-'}</span>
              </div>
            ))}
            {editable && !isLoading && !cellItems.length && <button type="button" aria-label="Добавить занятие" />}
          </div>
        );
      })}
    </>
  );
}
