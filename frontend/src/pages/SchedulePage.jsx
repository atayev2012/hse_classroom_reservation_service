import { useEffect, useMemo, useState } from 'react';

import ScheduleGrid from '../components/ScheduleGrid.jsx';
import { scheduleApi } from '../utils/api.js';
import { toIsoDate } from '../utils/formatters.js';

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

function weekRange(anchor) {
  const start = weekStart(anchor);
  return {
    start,
    startIso: toIsoDate(start),
    endIso: toIsoDate(addDays(start, 6))
  };
}

function flattenScheduleItems(schedules = []) {
  return schedules.flatMap((schedule) => (
    (schedule.schedule_items || []).map((item) => ({
      ...item,
      schedule_id: schedule.id,
      group_id: schedule.group_id,
      module_id: schedule.module_id
    }))
  ));
}

function inRange(item, startIso, endIso) {
  const date = toIsoDate(item.date);
  return date >= startIso && date <= endIso;
}

export default function SchedulePage() {
  const [weekAnchor, setWeekAnchor] = useState(() => weekStart(new Date()));
  const week = useMemo(() => weekRange(weekAnchor), [weekAnchor]);
  const [items, setItems] = useState([]);
  const [groups, setGroups] = useState([]);
  const [selectedGroupId, setSelectedGroupId] = useState('');
  const [isLoading, setIsLoading] = useState(true);

  const groupOptions = groups.length
    ? groups.map((group) => ({
      id: String(group.id),
      label: group.programme_name ? `${group.programme_name} / ${group.name}` : group.name
    }))
    : [{ id: '', label: 'Группа' }];

  useEffect(() => {
    let mounted = true;

    async function loadGroupedSchedules() {
      setIsLoading(true);
      const [programmesResponse, groupsResponse] = await Promise.all([
        scheduleApi.programmes.list({ limit: 1000 }).catch(() => null),
        scheduleApi.groups.list({ limit: 1000 }).catch(() => null)
      ]);
      const programmes = programmesResponse?.programmes || [];
      const programmeById = new Map(programmes.map((programme) => [Number(programme.id), programme.name]));
      const sortedGroups = (groupsResponse?.groups || [])
        .map((group) => ({
          ...group,
          programme_name: programmeById.get(Number(group.programme_id)) || ''
        }))
        .sort((left, right) => (
          `${left.programme_name} ${left.name}`.localeCompare(`${right.programme_name} ${right.name}`)
        ));
      const nextGroupId = selectedGroupId || String(sortedGroups[0]?.id || '');
      const schedulesResponse = nextGroupId
        ? await scheduleApi.schedules.list({ group_id: nextGroupId, limit: 1000 }).catch(() => null)
        : null;
      const scheduleItems = flattenScheduleItems((schedulesResponse?.schedules || []).filter((schedule) => schedule.is_published !== false))
        .filter((item) => inRange(item, week.startIso, week.endIso));

      if (!mounted) return;
      setGroups(sortedGroups);
      setSelectedGroupId(nextGroupId);
      setItems(scheduleItems);
      setIsLoading(false);
    }

    loadGroupedSchedules();

    return () => { mounted = false; };
  }, [selectedGroupId, week.endIso, week.startIso]);

  return (
    <ScheduleGrid
      items={items}
      weekAnchor={week.start}
      groupOptions={groupOptions}
      selectedGroupId={selectedGroupId}
      onGroupChange={setSelectedGroupId}
      onPrevWeek={() => setWeekAnchor((current) => addDays(current, -7))}
      onNextWeek={() => setWeekAnchor((current) => addDays(current, 7))}
      isLoading={isLoading}
    />
  );
}
