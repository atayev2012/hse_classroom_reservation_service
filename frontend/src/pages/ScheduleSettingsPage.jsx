import { ChevronLeft, ChevronRight, Edit3, Plus, Trash2, X } from 'lucide-react';
import { useEffect, useMemo, useState } from 'react';

import ConfirmModal from '../components/ConfirmModal.jsx';
import Panel from '../components/Panel.jsx';
import { SkeletonRows } from '../components/Skeleton.jsx';
import { authApi, bookingApi, scheduleApi } from '../utils/api.js';
import { timeSlots, weekDays } from '../utils/mockData.js';

const pageSize = 5;
const itemTypes = ['lecture', 'seminar', 'practice', 'exam', 'study'];
const itemTypeLabels = {
  lecture: 'Лекция',
  seminar: 'Семинар',
  practice: 'Практика',
  exam: 'Экзамен',
  study: 'Занятие',
  booking: 'Бронирование'
};
const fallbackAcademicYears = [{ id: 1, name: '2025/2026', start_date: '2025-09-01', end_date: '2026-06-30' }];
const fallbackModules = [{ id: 1, name: 'Модуль 4', start_date: '2026-04-01', end_date: '2026-06-30', academic_year_id: 1 }];
const fallbackProgrammes = [{ id: 1, name: 'Прикладная информатика', description: '' }];
const fallbackGroups = [{ id: 1, name: '22ПИ-3', email: '22pi-3@edu.hse.ru', programme_id: 1 }];
const fallbackBuildings = [{ id: 1, name: 'Костина', address: 'ул. Костина, 2Б' }];
const fallbackRooms = [{ id: 112, building_id: 1, room_number: '112', is_active: true }];
const fallbackEmployees = [{ id: 1, first_name: 'Преподаватель', last_name: 'HSE', type: 'employee' }];
const fallbackCourses = [{ id: 1, name: 'Математический анализ', description: '', programme_id: 1, instructors: [{ id: 1, course_id: 1, instructor_id: 1, instructor_name: 'HSE Преподаватель' }] }];

function addDays(date, amount) {
  const next = new Date(date);
  next.setDate(next.getDate() + amount);
  return next;
}

function isoDate(value) {
  return value ? new Date(value).toISOString().slice(0, 10) : '';
}

function formatDate(value) {
  if (!value) return '';
  const [year, month, day] = isoDate(value).split('-');
  return `${day}.${month}.${year}`;
}

function weekStart(value) {
  const date = new Date(value);
  const day = date.getDay() || 7;
  return addDays(date, 1 - day);
}

function datesInRange(start, end, stepDays = 7) {
  const dates = [];
  let cursor = new Date(start);
  const last = new Date(end);
  while (cursor <= last) {
    dates.push(isoDate(cursor));
    cursor = addDays(cursor, stepDays);
  }
  return dates;
}

function fullName(user) {
  if (!user) return '';
  return [user.last_name, user.first_name, user.middle_name].filter(Boolean).join(' ') || user.email || `ID ${user.id}`;
}

function totalPages(total) {
  return Math.max(Math.ceil(total / pageSize), 1);
}

function matchesText(value, query) {
  return !query || String(value ?? '').toLowerCase().includes(String(query).toLowerCase());
}

function paginate(rows, page) {
  return rows.slice((page - 1) * pageSize, page * pageSize);
}

function hasRequiredItemFields(item) {
  return ['title', 'item_type', 'instructor_id', 'instructor_name', 'building_id', 'building_address', 'room_id', 'room_number', 'date', 'time_slot', 'schedule_id']
    .every((key) => item[key] !== undefined && item[key] !== null && item[key] !== '');
}

function dayIndex(value) {
  const index = (new Date(value).getDay() || 7) - 1;
  return index >= 0 && index < weekDays.length ? index : -1;
}

function dateInRange(date, startDate, endDate) {
  return isoDate(date) >= isoDate(startDate) && isoDate(date) <= isoDate(endDate);
}

function firstDateForWeekday(startDate, endDate, targetIndex) {
  if (!startDate || !endDate) return '';
  const start = new Date(startDate);
  const end = new Date(endDate);
  let cursor = new Date(start);

  while (cursor <= end && dayIndex(cursor) !== targetIndex) {
    cursor = addDays(cursor, 1);
  }

  return cursor <= end ? isoDate(cursor) : '';
}

function itemGroupKey(item) {
  return [
    item.title,
    item.item_type,
    item.instructor_id || item.instructor_name,
    item.building_id || item.building_address,
    item.room_id || item.room_number,
    item.time_slot
  ].join('|');
}

function itemIdentity(item) {
  return item.__draftId || item.id || `${item.date}-${item.time_slot}-${item.title}`;
}

function scheduleItemPayload(item) {
  return {
    title: item.title,
    item_type: item.item_type,
    instructor_id: Number(item.instructor_id),
    instructor_name: item.instructor_name,
    building_id: Number(item.building_id),
    building_address: item.building_address,
    room_id: Number(item.room_id),
    room_number: item.room_number,
    date: item.date,
    time_slot: item.time_slot,
    schedule_id: Number(item.schedule_id),
    booking_id: item.booking_id || undefined,
    course_id: item.course_id || undefined
  };
}

export default function ScheduleSettingsPage() {
  const [academicYears, setAcademicYears] = useState(fallbackAcademicYears);
  const [modules, setModules] = useState(fallbackModules);
  const [holidays, setHolidays] = useState([]);
  const [programmes, setProgrammes] = useState(fallbackProgrammes);
  const [courses, setCourses] = useState(fallbackCourses);
  const [groups, setGroups] = useState(fallbackGroups);
  const [schedules, setSchedules] = useState([]);
  const [scheduleItems, setScheduleItems] = useState([]);
  const [draftItems, setDraftItems] = useState([]);
  const [bookingConflictItems, setBookingConflictItems] = useState([]);
  const [buildings, setBuildings] = useState(fallbackBuildings);
  const [rooms, setRooms] = useState(fallbackRooms);
  const [employees, setEmployees] = useState(fallbackEmployees);
  const [conflicts, setConflicts] = useState({});
  const [selectedProgrammeId, setSelectedProgrammeId] = useState(1);
  const [selectedGroupId, setSelectedGroupId] = useState(1);
  const [selectedScheduleId, setSelectedScheduleId] = useState(null);
  const [selectedModuleId, setSelectedModuleId] = useState(1);
  const [weekAnchor, setWeekAnchor] = useState(weekStart(new Date()));
  const [modal, setModal] = useState(null);
  const [workspaceOpen, setWorkspaceOpen] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [pages, setPages] = useState({
    years: 1,
    modules: 1,
    holidays: 1,
    programmes: 1,
    courses: 1,
    groups: 1,
    schedules: 1
  });
  const [filters, setFilters] = useState({
    years: { name: '', period: '' },
    modules: { name: '', academic_year: '', period: '' },
    holidays: { name: '', academic_year: '', date: '' },
    programmes: { name: '', description: '' },
    courses: { name: '', programme: '', instructor: '' },
    groups: { name: '', email: '', programme: '' },
    schedules: { name: '', group: '', module: '', status: '' }
  });
  const [notice, setNotice] = useState('');

  const selectedModule = modules.find((module) => Number(module.id) === Number(selectedModuleId)) || modules[0];
  const selectedSchedule = schedules.find((schedule) => Number(schedule.id) === Number(selectedScheduleId));
  const selectedGroup = groups.find((group) => Number(group.id) === Number(selectedGroupId));
  const selectedProgramme = programmes.find((programme) => Number(programme.id) === Number(selectedProgrammeId));
  const filteredGroups = groups.filter((group) => Number(group.programme_id) === Number(selectedProgrammeId));
  const filteredCourses = courses.filter((course) => Number(course.programme_id) === Number(selectedProgrammeId));
  const currentItems = useMemo(() => {
    const scheduleDrafts = draftItems.filter((item) => Number(item.schedule_id) === Number(selectedScheduleId));
    const deletedIds = new Set(scheduleDrafts.filter((item) => item.__draftAction === 'delete').map((item) => Number(item.originalId)));
    const updatedIds = new Set(scheduleDrafts.filter((item) => item.__draftAction === 'update').map((item) => Number(item.originalId)));
    const persisted = scheduleItems.filter((item) => (
      Number(item.schedule_id) === Number(selectedScheduleId) &&
      !deletedIds.has(Number(item.id)) &&
      !updatedIds.has(Number(item.id))
    ));
    const visibleDrafts = scheduleDrafts.filter((item) => item.__draftAction !== 'delete');
    return [...persisted, ...visibleDrafts];
  }, [draftItems, scheduleItems, selectedScheduleId]);
  const visibleCalendarItems = useMemo(() => [...currentItems, ...bookingConflictItems], [currentItems, bookingConflictItems]);
  const weekDates = Array.from({ length: 6 }, (_, index) => (
    firstDateForWeekday(selectedModule?.start_date, selectedModule?.end_date, index) ||
    isoDate(addDays(weekAnchor, index))
  ));
  const hasDraftChanges = draftItems.some((item) => Number(item.schedule_id) === Number(selectedScheduleId));
  const hasConflicts = currentItems.some((item) => conflicts[item.id || `${item.date}-${item.time_slot}`]);
  const hasMissing = currentItems.some((item) => !hasRequiredItemFields(item));
  const canPublish = Boolean(selectedSchedule && currentItems.length && !hasConflicts && !hasMissing && !hasDraftChanges && !selectedSchedule.is_published);
  const canCreateModule = academicYears.length > 0;
  const canCreateHoliday = academicYears.length > 0;
  const canCreateGroup = programmes.length > 0;
  const canCreateCourse = programmes.length > 0 && employees.length > 0;
  const canCreateScheduleEntity = academicYears.length > 0 && modules.length > 0 && programmes.length > 0 && groups.length > 0 && courses.length > 0;

  useEffect(() => { loadAll(); }, []);
  useEffect(() => {
    if (filteredGroups.length && !filteredGroups.some((group) => Number(group.id) === Number(selectedGroupId))) {
      setSelectedGroupId(filteredGroups[0].id);
    }
  }, [selectedProgrammeId, groups]);
  useEffect(() => { if (selectedModule?.start_date) setWeekAnchor(weekStart(selectedModule.start_date)); }, [selectedModuleId]);
  useEffect(() => { verifyConflicts(); }, [currentItems, selectedScheduleId]);

  async function loadAll() {
    setIsLoading(true);
    const [
      yearsResponse,
      modulesResponse,
      holidaysResponse,
      programmesResponse,
      coursesResponse,
      groupsResponse,
      schedulesResponse,
      itemsResponse,
      buildingsResponse,
      roomsResponse,
      usersResponse
    ] = await Promise.all([
      scheduleApi.academicYears.list({ limit: 1000 }).catch(() => null),
      scheduleApi.modules.list({ limit: 1000 }).catch(() => null),
      scheduleApi.holidays.list({ limit: 1000 }).catch(() => null),
      scheduleApi.programmes.list({ limit: 1000 }).catch(() => null),
      scheduleApi.courses.list({ limit: 1000 }).catch(() => null),
      scheduleApi.groups.list({ limit: 1000 }).catch(() => null),
      scheduleApi.schedules.list({ limit: 1000 }).catch(() => null),
      scheduleApi.items.list({ limit: 1000 }).catch(() => null),
      bookingApi.buildings.list({ limit: 1000 }).catch(() => null),
      bookingApi.rooms.list({ limit: 1000 }).catch(() => null),
      authApi.users.list({ types: ['employee', 'manager', 'admin'], limit: 1000 }).catch(() => null)
    ]);
    if (yearsResponse?.academic_years) setAcademicYears(yearsResponse.academic_years);
    if (modulesResponse?.modules) {
      setModules(modulesResponse.modules);
      if (modulesResponse.modules.length) setSelectedModuleId((current) => current || modulesResponse.modules[0].id);
    }
    if (holidaysResponse?.holidays) setHolidays(holidaysResponse.holidays);
    if (programmesResponse?.programmes) {
      setProgrammes(programmesResponse.programmes);
      if (programmesResponse.programmes.length) setSelectedProgrammeId((current) => current || programmesResponse.programmes[0].id);
    }
    if (coursesResponse?.courses) setCourses(coursesResponse.courses);
    if (groupsResponse?.groups) {
      setGroups(groupsResponse.groups);
      if (groupsResponse.groups.length) setSelectedGroupId((current) => current || groupsResponse.groups[0].id);
    }
    if (schedulesResponse?.schedules) setSchedules(schedulesResponse.schedules);
    if (itemsResponse?.schedule_items) setScheduleItems(itemsResponse.schedule_items);
    if (buildingsResponse?.buildings?.length) setBuildings(buildingsResponse.buildings);
    if (roomsResponse?.rooms?.length) setRooms(roomsResponse.rooms);
    if (usersResponse?.users?.length) setEmployees(usersResponse.users);
    setIsLoading(false);
  }

  async function reloadSchedules() {
    const [schedulesResponse, itemsResponse] = await Promise.all([
      scheduleApi.schedules.list({ limit: 1000 }).catch(() => null),
      scheduleApi.items.list({ limit: 1000 }).catch(() => null)
    ]);
    if (schedulesResponse?.schedules) setSchedules(schedulesResponse.schedules);
    if (itemsResponse?.schedule_items) setScheduleItems(itemsResponse.schedule_items);
  }

  async function verifyConflicts() {
    const next = {};
    const nextBookingItems = [];
    const items = currentItems.filter((item) => !item.__booking);
    await Promise.all(items.map(async (item) => {
      const response = await bookingApi.bookings.list({
        room_id: item.room_id,
        event_date: item.date,
        limit: 100
      }).catch(() => null);
      const bookings = (response?.bookings || []).filter((booking) => (
        booking.is_active !== false &&
        Number(booking.id) !== Number(item.booking_id) &&
        (booking.event_time_slot || []).includes(item.time_slot)
      ));
      bookings.forEach((booking) => {
        const bookingItem = {
          id: `booking-${booking.id}-${itemIdentity(item)}`,
          __booking: true,
          title: booking.event_title || 'Бронирование аудитории',
          item_type: 'booking',
          instructor_name: booking.user_id ? `Пользователь ${booking.user_id}` : '',
          building_address: item.building_address,
          room_number: item.room_number,
          room_id: item.room_id,
          date: item.date,
          time_slot: item.time_slot,
          schedule_id: item.schedule_id
        };
        next[bookingItem.id] = true;
        nextBookingItems.push(bookingItem);
      });
      const scheduleConflict = items.some((other) => (
        itemIdentity(other) !== itemIdentity(item) &&
        Number(other.room_id) === Number(item.room_id) &&
        other.date === item.date &&
        other.time_slot === item.time_slot
      ));
      if (bookings.length || scheduleConflict) next[item.id || `${item.date}-${item.time_slot}`] = true;
    }));
    setConflicts(next);
    setBookingConflictItems(nextBookingItems);
  }

  async function saveSimple(kind, payload, item) {
    const api = {
      academicYear: scheduleApi.academicYears,
      module: scheduleApi.modules,
      holiday: scheduleApi.holidays,
      programme: scheduleApi.programmes,
      course: scheduleApi.courses,
      group: scheduleApi.groups
    }[kind];
    const response = item ? await api.update(item.id, payload) : await api.create(payload);
    if (response?.success === false) throw new Error(response.status);
    setModal(null);
    await loadAll();
  }

  async function removeSimple(kind, item) {
    const api = {
      academicYear: scheduleApi.academicYears,
      module: scheduleApi.modules,
      holiday: scheduleApi.holidays,
      programme: scheduleApi.programmes,
      course: scheduleApi.courses,
      group: scheduleApi.groups,
      schedule: scheduleApi.schedules,
      item: scheduleApi.items
    }[kind];
    await api.remove(item.id).catch(() => {});
    await loadAll();
  }

  function requestRemoveSimple(kind, item) {
    setConfirmDelete({
      title: 'Удаление',
      message: 'Вы уверены, что хотите удалить этот элемент?',
      onConfirm: async () => {
        await removeSimple(kind, item);
        setConfirmDelete(null);
      }
    });
  }

  async function createSchedule(form, item = null) {
    const payload = {
      name: form.name,
      module_id: Number(form.module_id),
      group_id: Number(form.group_id)
    };
    const response = item
      ? await scheduleApi.schedules.update(item.id, payload)
      : await scheduleApi.schedules.create(payload);
    if (response?.success === false) throw new Error(response.status);
    const schedule = response.schedule;
    setModal(null);
    await reloadSchedules();
    if (schedule?.id) {
      setSelectedScheduleId(schedule.id);
      setSelectedGroupId(schedule.group_id);
      setSelectedModuleId(schedule.module_id);
      setSelectedProgrammeId(groups.find((group) => Number(group.id) === Number(schedule.group_id))?.programme_id || selectedProgrammeId);
      setWorkspaceOpen(true);
    }
  }

  async function saveScheduleItem(form, editingItem) {
    const selectedRoom = rooms.find((room) => Number(room.id) === Number(form.room_id));
    const selectedBuilding = buildings.find((building) => Number(building.id) === Number(form.building_id));
    const selectedCourse = courses.find((course) => Number(course.id) === Number(form.course_id));
    const instructor = employees.find((employee) => Number(employee.id) === Number(form.instructor_id));
    const basePayload = {
      title: form.title || selectedCourse?.name || 'Занятие',
      item_type: form.item_type,
      course_id: form.course_id ? Number(form.course_id) : undefined,
      instructor_id: Number(form.instructor_id),
      instructor_name: form.instructor_name || fullName(instructor),
      building_id: Number(form.building_id),
      building_address: form.building_address || selectedBuilding?.address || '',
      room_id: Number(form.room_id),
      room_number: form.room_number || selectedRoom?.room_number || '',
      time_slot: form.time_slot,
      schedule_id: Number(selectedScheduleId)
    };
    const dates = itemDates(form);
    if (!dates.length) {
      throw new Error('Укажите дату занятия');
    }
    const outOfRange = dates.find((date) => selectedModule && !dateInRange(date, selectedModule.start_date, selectedModule.end_date));
    if (outOfRange) {
      throw new Error(`Дата ${formatDate(outOfRange)} вне периода модуля`);
    }
    const nextDrafts = dates.map((date, index) => {
      const draftAction = editingItem && !editingItem.__draftAction ? 'update' : 'create';
      return {
        ...(editingItem?.__draftAction === 'create' ? editingItem : {}),
        ...basePayload,
        date,
        id: editingItem?.__draftAction === 'create' ? editingItem.id : editingItem?.id,
        originalId: editingItem?.originalId || editingItem?.id,
        __draftAction: draftAction,
        __draftId: editingItem?.__draftId || `${draftAction}-${editingItem?.id || Date.now()}-${index}`
      };
    });
    setDraftItems((current) => {
      const editingKey = editingItem ? itemIdentity(editingItem) : null;
      const withoutEdited = editingKey
        ? current.filter((item) => itemIdentity(item) !== editingKey && Number(item.originalId) !== Number(editingItem?.id))
        : current;
      return [...withoutEdited, ...nextDrafts];
    });
    setModal(null);
    if (dates[0]) setWeekAnchor(weekStart(dates[0]));
  }

  function itemDates(form) {
    const start = isoDate(form.date);
    if (form.recurrence === 'weekly' && selectedModule) return datesInRange(start, selectedModule.end_date, 7);
    if (form.recurrence === 'biweekly' && selectedModule) return datesInRange(start, selectedModule.end_date, 14);
    if (form.recurrence === 'specific') {
      return form.specific_dates.split(',').map((date) => isoDate(date.trim())).filter(Boolean);
    }
    return [start];
  }

  function openCellChoice(date, slot, items) {
    if (!items.length) {
      setModal({ kind: 'scheduleItem', date, slot });
      return;
    }
    setModal({ kind: 'cellChoice', date, slot, items });
  }

  function deleteScheduleItemDraft(item) {
    if (item.__booking) return;
    setModal(null);
    setDraftItems((current) => {
      if (item.__draftAction === 'create') {
        return current.filter((draft) => itemIdentity(draft) !== itemIdentity(item));
      }
      const withoutExistingMarkers = current.filter((draft) => Number(draft.originalId) !== Number(item.id));
      return [
        ...withoutExistingMarkers,
        {
          ...item,
          originalId: item.id,
          __draftAction: 'delete',
          __draftId: `delete-${item.id}`
        }
      ];
    });
  }

  function requestDeleteScheduleItemDraft(item) {
    if (item.__booking) return;
    setConfirmDelete({
      title: 'Удаление занятия',
      message: 'Вы уверены, что хотите удалить это занятие?',
      onConfirm: () => {
        deleteScheduleItemDraft(item);
        setConfirmDelete(null);
      }
    });
  }

  async function saveDraft() {
    const scheduleDrafts = draftItems.filter((item) => Number(item.schedule_id) === Number(selectedScheduleId));
    for (const item of scheduleDrafts) {
      if (item.__draftAction === 'delete') {
        await scheduleApi.items.remove(item.originalId || item.id);
      } else if (item.__draftAction === 'update') {
        await scheduleApi.items.update(item.originalId || item.id, scheduleItemPayload(item));
      } else {
        await scheduleApi.items.create(scheduleItemPayload(item));
      }
    }
    setDraftItems((current) => current.filter((item) => Number(item.schedule_id) !== Number(selectedScheduleId)));
    setNotice('Черновик сохранен');
    await reloadSchedules();
  }

  async function publishSchedule() {
    setNotice('');
    if (!canPublish) return;
    const response = await scheduleApi.schedules.publish(selectedScheduleId);
    if (response?.success === false) {
      setNotice(response.status || 'Не удалось опубликовать расписание');
      return;
    }
    setNotice('Расписание опубликовано');
    await reloadSchedules();
  }

  async function unpublishSchedule() {
    setNotice('');
    const response = await scheduleApi.schedules.unpublish(selectedScheduleId);
    if (response?.success === false) {
      setNotice(response.status || 'Не удалось снять расписание с публикации');
      return;
    }
    setNotice('Расписание снято с публикации');
    await reloadSchedules();
  }

  const yearRows = academicYears
    .map((year) => ({ ...year, rowKind: 'academicYear', period: `${formatDate(year.start_date)} - ${formatDate(year.end_date)}` }))
    .filter((row) => matchesText(row.name, filters.years.name) && matchesText(row.period, filters.years.period));

  const moduleRows = modules
    .map((module) => ({
      ...module,
      rowKind: 'module',
      academic_year: academicYears.find((year) => Number(year.id) === Number(module.academic_year_id))?.name || module.academic_year_id,
      period: `${formatDate(module.start_date)} - ${formatDate(module.end_date)}`
    }))
    .filter((row) => (
      matchesText(row.name, filters.modules.name) &&
      matchesText(row.academic_year, filters.modules.academic_year) &&
      matchesText(row.period, filters.modules.period)
    ));

  const holidayRows = holidays
    .map((holiday) => ({
      ...holiday,
      rowKind: 'holiday',
      title: holiday.name || 'Выходной день',
      academic_year: academicYears.find((year) => Number(year.id) === Number(holiday.academic_year_id))?.name || holiday.academic_year_id,
      formatted_date: formatDate(holiday.date)
    }))
    .filter((row) => (
      matchesText(row.title, filters.holidays.name) &&
      matchesText(row.academic_year, filters.holidays.academic_year) &&
      matchesText(row.formatted_date, filters.holidays.date)
    ));

  const programmeRows = programmes
    .map((programme) => ({ ...programme, rowKind: 'programme', description: programme.description || '-' }))
    .filter((row) => matchesText(row.name, filters.programmes.name) && matchesText(row.description, filters.programmes.description));

  const courseRows = courses
    .map((course) => ({
      ...course,
      rowKind: 'course',
      programme: programmes.find((programme) => Number(programme.id) === Number(course.programme_id))?.name || course.programme_id,
      instructor: (course.instructors || []).map((instructor) => instructor.instructor_name).join(', ') || '-'
    }))
    .filter((row) => (
      matchesText(row.name, filters.courses.name) &&
      matchesText(row.programme, filters.courses.programme) &&
      matchesText(row.instructor, filters.courses.instructor)
    ));

  const groupRows = groups
    .map((group) => ({
      ...group,
      rowKind: 'group',
      programme: programmes.find((programme) => Number(programme.id) === Number(group.programme_id))?.name || group.programme_id
    }))
    .filter((row) => (
      matchesText(row.name, filters.groups.name) &&
      matchesText(row.email, filters.groups.email) &&
      matchesText(row.programme, filters.groups.programme)
    ));

  const scheduleRows = schedules.filter((schedule) => (
    matchesText(schedule.name, filters.schedules.name) &&
    matchesText(groups.find((group) => Number(group.id) === Number(schedule.group_id))?.name || schedule.group_id, filters.schedules.group) &&
    matchesText(modules.find((module) => Number(module.id) === Number(schedule.module_id))?.name || schedule.module_id, filters.schedules.module) &&
    (!filters.schedules.status || String(Boolean(schedule.is_published)) === filters.schedules.status)
  ));

  return (
    <>
      <div className="schedule-settings-layout">
        <CatalogWidget
          title="Учебные годы"
          addActions={[
            { label: 'Учебный год', onClick: () => setModal({ kind: 'academicYear' }) }
          ]}
          rows={paginate(yearRows, pages.years)}
          total={yearRows.length}
          page={pages.years}
          onPageChange={(page) => setPages((current) => ({ ...current, years: page }))}
          filters={filters.years}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, years: { ...current.years, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'period', label: 'Период', filterKey: 'period' }
          ]}
          onEdit={(row) => setModal({ kind: 'academicYear', item: row })}
          onRemove={(row) => requestRemoveSimple('academicYear', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Модули"
          addActions={[
            { label: 'Модуль', onClick: () => setModal({ kind: 'module' }), disabled: !canCreateModule }
          ]}
          rows={paginate(moduleRows, pages.modules)}
          total={moduleRows.length}
          page={pages.modules}
          onPageChange={(page) => setPages((current) => ({ ...current, modules: page }))}
          filters={filters.modules}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, modules: { ...current.modules, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'academic_year', label: 'Учебный год', filterKey: 'academic_year' },
            { key: 'period', label: 'Период', filterKey: 'period' }
          ]}
          onEdit={(row) => setModal({ kind: 'module', item: row })}
          onRemove={(row) => requestRemoveSimple('module', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Праздники и каникулы"
          addActions={[
            { label: 'Праздник', onClick: () => setModal({ kind: 'holiday' }), disabled: !canCreateHoliday }
          ]}
          rows={paginate(holidayRows, pages.holidays)}
          total={holidayRows.length}
          page={pages.holidays}
          onPageChange={(page) => setPages((current) => ({ ...current, holidays: page }))}
          filters={filters.holidays}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, holidays: { ...current.holidays, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'title', label: 'Название', filterKey: 'name' },
            { key: 'academic_year', label: 'Учебный год', filterKey: 'academic_year' },
            { key: 'formatted_date', label: 'Дата', filterKey: 'date' }
          ]}
          onEdit={(row) => setModal({ kind: 'holiday', item: row })}
          onRemove={(row) => requestRemoveSimple('holiday', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Учебные программы"
          addActions={[
            { label: 'Программа', onClick: () => setModal({ kind: 'programme' }) }
          ]}
          rows={paginate(programmeRows, pages.programmes)}
          total={programmeRows.length}
          page={pages.programmes}
          onPageChange={(page) => setPages((current) => ({ ...current, programmes: page }))}
          filters={filters.programmes}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, programmes: { ...current.programmes, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'description', label: 'Описание', filterKey: 'description' }
          ]}
          onEdit={(row) => setModal({ kind: 'programme', item: row })}
          onRemove={(row) => requestRemoveSimple('programme', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Курсы"
          addActions={[
            { label: 'Курс', onClick: () => setModal({ kind: 'course' }), disabled: !canCreateCourse }
          ]}
          rows={paginate(courseRows, pages.courses)}
          total={courseRows.length}
          page={pages.courses}
          onPageChange={(page) => setPages((current) => ({ ...current, courses: page }))}
          filters={filters.courses}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, courses: { ...current.courses, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'programme', label: 'Программа', filterKey: 'programme' },
            { key: 'instructor', label: 'Преподаватель', filterKey: 'instructor' }
          ]}
          onEdit={(row) => setModal({ kind: 'course', item: row })}
          onRemove={(row) => requestRemoveSimple('course', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Учебные группы"
          addActions={[
            { label: 'Группа', onClick: () => setModal({ kind: 'group' }), disabled: !canCreateGroup }
          ]}
          rows={paginate(groupRows, pages.groups)}
          total={groupRows.length}
          page={pages.groups}
          onPageChange={(page) => setPages((current) => ({ ...current, groups: page }))}
          filters={filters.groups}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, groups: { ...current.groups, [key]: value } }))}
          columns={[
            { key: 'id', label: 'ID', width: '0.5fr' },
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'email', label: 'Email', filterKey: 'email' },
            { key: 'programme', label: 'Программа', filterKey: 'programme' }
          ]}
          onEdit={(row) => setModal({ kind: 'group', item: row })}
          onRemove={(row) => requestRemoveSimple('group', row)}
          isLoading={isLoading}
        />

        <CatalogWidget
          title="Расписания"
          addActions={[
            { label: 'Расписание', onClick: () => setModal({ kind: 'schedule' }), disabled: !canCreateScheduleEntity }
          ]}
          rows={paginate(scheduleRows, pages.schedules)}
          total={scheduleRows.length}
          page={pages.schedules}
          onPageChange={(page) => setPages((current) => ({ ...current, schedules: page }))}
          filters={filters.schedules}
          onFilterChange={(key, value) => setFilters((current) => ({ ...current, schedules: { ...current.schedules, [key]: value } }))}
          columns={[
            { key: 'name', label: 'Название', filterKey: 'name' },
            { key: 'group_id', label: 'Группа', filterKey: 'group', render: (row) => groups.find((group) => Number(group.id) === Number(row.group_id))?.name || row.group_id },
            { key: 'module_id', label: 'Модуль', filterKey: 'module', render: (row) => modules.find((module) => Number(module.id) === Number(row.module_id))?.name || row.module_id },
            { key: 'is_published', label: 'Статус', filterKey: 'status', filterType: 'status', render: (row) => row.is_published ? 'Опубликовано' : 'Черновик' }
          ]}
          onEdit={(row) => {
            setSelectedScheduleId(row.id);
            setSelectedGroupId(row.group_id);
            setSelectedModuleId(row.module_id);
            setSelectedProgrammeId(groups.find((group) => Number(group.id) === Number(row.group_id))?.programme_id || selectedProgrammeId);
            setWorkspaceOpen(true);
          }}
          onRemove={(row) => requestRemoveSimple('schedule', row)}
          isLoading={isLoading}
        />
      </div>

      {workspaceOpen && selectedSchedule && (
        <ScheduleWorkspaceModal
          schedules={schedules}
          selectedSchedule={selectedSchedule}
          selectedScheduleId={selectedScheduleId}
          selectedProgrammeId={selectedProgrammeId}
          selectedGroupId={selectedGroupId}
          selectedModuleId={selectedModuleId}
          selectedProgramme={selectedProgramme}
          selectedGroup={selectedGroup}
          selectedModule={selectedModule}
          programmes={programmes}
          courses={courses}
          groups={groups}
          modules={modules}
          filteredGroups={filteredGroups}
          filteredCourses={filteredCourses}
          currentItems={currentItems}
          visibleCalendarItems={visibleCalendarItems}
          conflicts={conflicts}
          weekDates={weekDates}
          weekAnchor={weekAnchor}
          hasConflicts={hasConflicts}
          hasMissing={hasMissing}
          hasDraftChanges={hasDraftChanges}
          canPublish={canPublish}
          notice={notice}
          onClose={() => setWorkspaceOpen(false)}
          onProgrammeChange={setSelectedProgrammeId}
          onGroupChange={setSelectedGroupId}
          onModuleChange={setSelectedModuleId}
          onScheduleChange={(id) => {
            const schedule = schedules.find((row) => Number(row.id) === Number(id));
            setSelectedScheduleId(id);
            if (schedule) {
              setSelectedGroupId(schedule.group_id);
              setSelectedModuleId(schedule.module_id);
              setSelectedProgrammeId(groups.find((group) => Number(group.id) === Number(schedule.group_id))?.programme_id || selectedProgrammeId);
            }
          }}
          onPrevWeek={() => setWeekAnchor((current) => addDays(current, -7))}
          onNextWeek={() => setWeekAnchor((current) => addDays(current, 7))}
          onCellSelect={openCellChoice}
          onAddItem={(date, slot) => setModal({ kind: 'scheduleItem', date, slot })}
          onEditItem={(item) => setModal({ kind: 'scheduleItem', item })}
          onRemoveItem={requestDeleteScheduleItemDraft}
          onEditSchedule={() => setModal({ kind: 'schedule', item: selectedSchedule })}
          onSaveDraft={saveDraft}
          onPublish={publishSchedule}
          onUnpublish={unpublishSchedule}
        />
      )}

      {modal?.kind === 'cellChoice' && (
        <CellChoiceModal
          modal={modal}
          conflicts={conflicts}
          onClose={() => setModal(null)}
          onAdd={() => setModal({ kind: 'scheduleItem', date: modal.date, slot: modal.slot })}
          onEdit={(item) => setModal({ kind: 'scheduleItem', item })}
          onDelete={requestDeleteScheduleItemDraft}
        />
      )}

      {modal && modal.kind !== 'cellChoice' && (
        <ScheduleSettingsModal
          modal={modal}
          academicYears={academicYears}
          modules={modules}
          programmes={programmes}
          courses={courses}
          groups={groups}
          selectedProgramme={selectedProgramme}
          selectedGroup={selectedGroup}
          selectedModule={selectedModule}
          buildings={buildings}
          rooms={rooms}
          employees={employees}
          onClose={() => setModal(null)}
          onSaveSimple={saveSimple}
          onCreateSchedule={createSchedule}
          onSaveScheduleItem={saveScheduleItem}
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

function CatalogWidget({ title, addActions = [], rows, columns, filters, total, page, onPageChange, onFilterChange, onEdit, onRemove, isLoading }) {
  const template = `${columns.map((column) => (column.key === 'id' ? '12ch' : column.width || '1fr')).join(' ')} 116px`;
  return (
    <Panel
      title={title}
      className="booking-settings-widget"
      action={addActions.length ? (
        <div className="widget-actions">
          {addActions.map((action) => {
            const normalized = Array.isArray(action)
              ? { label: action[0], onClick: action[1], disabled: false }
              : action;
            return (
              <button
                className="button button--primary"
                type="button"
                onClick={normalized.onClick}
                disabled={normalized.disabled}
                title={normalized.disabled ? 'Сначала добавьте связанные сущности' : undefined}
                key={normalized.label}
              >
                <Plus size={15} />
                {normalized.label}
              </button>
            );
          })}
        </div>
      ) : null}
    >
      <div className="user-table schedule-settings-table">
        <div className="user-table__head" style={{ gridTemplateColumns: template }}>
          {columns.map((column) => (
            <div className="user-table__head-cell" key={column.key}>
              <span>{column.label}</span>
              {column.filterKey && (
                column.filterType === 'status' ? (
                  <select value={filters[column.filterKey] || ''} onChange={(event) => onFilterChange(column.filterKey, event.target.value)}>
                    <option value="">Все</option>
                    <option value="true">Опубликовано</option>
                    <option value="false">Черновик</option>
                  </select>
                ) : (
                  <input value={filters[column.filterKey] || ''} onChange={(event) => onFilterChange(column.filterKey, event.target.value)} />
                )
              )}
            </div>
          ))}
          <div className="user-table__head-cell"><span>Действия</span></div>
        </div>
        {isLoading ? (
          <SkeletonRows rows={5} />
        ) : rows.length ? rows.map((row) => (
          <div className="user-table__row" style={{ gridTemplateColumns: template }} key={`${row.rowKind || 'row'}-${row.id}`}>
            {columns.map((column) => <div key={column.key}>{column.render ? column.render(row) : row[column.key]}</div>)}
            <div className="table-actions">
              <button className="action-button action-button--edit" type="button" onClick={() => onEdit(row)} aria-label="Редактировать">
                <Edit3 size={15} />
              </button>
              <button className="action-button action-button--delete" type="button" onClick={() => onRemove(row)} aria-label="Удалить">
                <Trash2 size={15} />
              </button>
            </div>
          </div>
        )) : <div className="user-table__empty">Нет данных</div>}
      </div>
      <Pagination page={page} total={total} onPageChange={onPageChange} />
    </Panel>
  );
}

function ScheduleWorkspaceModal({
  schedules,
  selectedSchedule,
  selectedScheduleId,
  selectedProgrammeId,
  selectedGroupId,
  selectedModuleId,
  selectedModule,
  programmes,
  courses,
  groups,
  modules,
  filteredGroups,
  filteredCourses,
  currentItems,
  visibleCalendarItems,
  conflicts,
  weekDates,
  weekAnchor,
  hasConflicts,
  hasMissing,
  hasDraftChanges,
  canPublish,
  notice,
  onClose,
  onProgrammeChange,
  onGroupChange,
  onModuleChange,
  onScheduleChange,
  onCellSelect,
  onAddItem,
  onEditItem,
  onRemoveItem,
  onEditSchedule,
  onSaveDraft,
  onPublish,
  onUnpublish
}) {
  const selectedGroup = groups.find((group) => Number(group.id) === Number(selectedGroupId));
  const groupOptions = filteredGroups.length ? filteredGroups : groups;
  const scheduleStatus = selectedSchedule?.is_published ? 'Опубликовано' : 'Черновик';

  return (
    <div className="modal-backdrop">
      <div className="user-modal schedule-workspace-modal">
        <div className="schedule-workspace-header">
          <div>
            <span>Конструктор расписаний</span>
            <h2>{selectedSchedule?.name || 'Расписание'}</h2>
            <p>{selectedGroup?.name || 'Группа не выбрана'} / {selectedModule?.name || 'Модуль не выбран'} / {scheduleStatus}</p>
          </div>
          <div className="schedule-workspace-actions">
            <button className="button button--ghost" type="button" onClick={onEditSchedule}>
              <Edit3 size={15} />
              Параметры
            </button>
            <button className="icon-ghost" type="button" onClick={onClose} aria-label="Закрыть">
              <X size={20} />
            </button>
          </div>
        </div>

        {notice && <div className="modal-error">{notice}</div>}

        <div className="schedule-builder-controls">
          <label>
            <span>Программа</span>
            <select value={selectedProgrammeId || ''} onChange={(event) => onProgrammeChange(Number(event.target.value))}>
              {programmes.map((programme) => <option value={programme.id} key={programme.id}>{programme.name}</option>)}
            </select>
          </label>
          <label>
            <span>Группа</span>
            <select value={selectedGroupId || ''} onChange={(event) => onGroupChange(Number(event.target.value))}>
              {groupOptions.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}
            </select>
          </label>
          <label>
            <span>Модуль</span>
            <select value={selectedModuleId || ''} onChange={(event) => onModuleChange(Number(event.target.value))}>
              {modules.map((module) => <option value={module.id} key={module.id}>{module.name}</option>)}
            </select>
          </label>
          <label>
            <span>Расписание</span>
            <select value={selectedScheduleId || ''} onChange={(event) => onScheduleChange(Number(event.target.value))}>
              {schedules.map((schedule) => <option value={schedule.id} key={schedule.id}>{schedule.name}</option>)}
            </select>
          </label>
        </div>

        <ScheduleCalendar
          items={visibleCalendarItems}
          conflicts={conflicts}
          weekDates={weekDates}
          weekAnchor={weekAnchor}
          canEdit={Boolean(selectedSchedule)}
          onCellSelect={onCellSelect}
          onAdd={onAddItem}
          onEdit={onEditItem}
          onRemove={onRemoveItem}
        />

        <div className="schedule-publish-bar">
          <span>
            {hasDraftChanges ? 'Есть несохраненные изменения черновика.' : hasConflicts ? 'Есть конфликты с бронированиями или другими занятиями.' : hasMissing ? 'Есть занятия с незаполненными обязательными полями.' : selectedSchedule?.is_published ? 'Расписание опубликовано.' : 'Расписание можно опубликовать после заполнения занятий.'}
          </span>
          <div className="schedule-publish-actions">
            <button className="button button--ghost" type="button" disabled={!hasDraftChanges} onClick={onSaveDraft}>
              Сохранить черновик
            </button>
            <button className="button button--primary" type="button" disabled={!canPublish} onClick={onPublish}>
              Опубликовать
            </button>
            {selectedSchedule?.is_published && (
              <button className="button button--danger" type="button" disabled={hasDraftChanges} onClick={onUnpublish}>
                Снять с публикации
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Pagination({ page, total, onPageChange }) {
  const pages = totalPages(total);
  return (
    <div className="user-pagination">
      <span>{total ? `${(page - 1) * pageSize + 1}-${Math.min(page * pageSize, total)} из ${total}` : '0 из 0'}</span>
      <div className="user-pagination__buttons">
        <button className="icon-ghost" type="button" disabled={page === 1} onClick={() => onPageChange(Math.max(1, page - 1))}><ChevronLeft size={18} /></button>
        <span>{page} / {pages}</span>
        <button className="icon-ghost" type="button" disabled={page === pages} onClick={() => onPageChange(Math.min(pages, page + 1))}><ChevronRight size={18} /></button>
      </div>
    </div>
  );
}

function CellChoiceModal({ modal, conflicts, onClose, onAdd, onEdit, onDelete }) {
  return (
    <div className="modal-backdrop">
      <div className="user-modal schedule-choice-modal">
        <h2>Занятия в ячейке</h2>
        <p className="schedule-choice-modal__hint">{weekDays[dayIndex(modal.date)]}, {modal.slot}</p>
        <div className="schedule-choice-list">
          {modal.items.map((item) => {
            const conflict = conflicts[item.id || `${item.date}-${item.time_slot}`];
            return (
              <div
                className={`schedule-choice-item ${conflict ? 'has-conflict' : ''}`}
                key={item.id || `${item.date}-${item.time_slot}-${item.title}`}
              >
                <strong>{item.title}</strong>
                <span>{itemTypeLabels[item.item_type] || item.item_type} / {formatDate(item.date)}</span>
                <span>{item.building_address || '-'}, ауд. {item.room_number || '-'}</span>
                <span>{item.instructor_name || 'Преподаватель не указан'}</span>
                {conflict && <em>Есть бронирование на эту дату</em>}
                {!item.__booking && (
                  <span className="schedule-choice-item__actions">
                    <button className="button button--ghost" type="button" onClick={() => onEdit(item)}>Редактировать</button>
                    <button className="button button--danger" type="button" onClick={() => onDelete(item)}>Удалить</button>
                  </span>
                )}
              </div>
            );
          })}
        </div>
        <div className="modal-actions">
          <button className="button button--danger" type="button" onClick={onClose}>Отменить</button>
          <button className="button button--primary" type="button" onClick={onAdd}>Добавить</button>
        </div>
      </div>
    </div>
  );
}

function ScheduleCalendar({ items, conflicts, weekDates, weekAnchor, canEdit, onCellSelect, onAdd, onEdit, onRemove }) {
  const allGroupsBySignature = useMemo(() => {
    const grouped = new Map();
    items.forEach((item) => {
      const groupKey = itemGroupKey(item);
      const group = grouped.get(groupKey) || { representative: item, dates: [], items: [], hasConflict: false };
      group.items.push(item);
      group.dates.push(item.date);
      group.hasConflict = group.hasConflict || Boolean(conflicts[item.id || `${item.date}-${item.time_slot}`]);
      grouped.set(groupKey, group);
    });
    return grouped;
  }, [items, conflicts]);

  const itemsByCell = useMemo(() => {
    const map = new Map();
    items.forEach((item) => {
      const index = dayIndex(item.date);
      if (index < 0) return;
      const key = `${index}-${item.time_slot}`;
      map.set(key, [...(map.get(key) || []), item]);
    });
    map.forEach((cellItems, key) => {
      map.set(key, cellItems.sort((left, right) => isoDate(left.date).localeCompare(isoDate(right.date))));
    });
    return map;
  }, [items]);

  const groupsByCell = useMemo(() => {
    const map = new Map();
    itemsByCell.forEach((cellItems, key) => {
      const grouped = new Map();
      cellItems.forEach((item) => {
        const groupKey = itemGroupKey(item);
        grouped.set(groupKey, allGroupsBySignature.get(groupKey) || {
          representative: item,
          dates: [item.date],
          items: [item],
          hasConflict: Boolean(conflicts[item.id || `${item.date}-${item.time_slot}`])
        });
      });
      map.set(key, Array.from(grouped.values()));
    });
    return map;
  }, [itemsByCell, allGroupsBySignature, conflicts]);

  return (
    <section className="schedule-panel schedule-panel--embedded">
      <div className="schedule-grid">
        <div className="schedule-grid__header">Время</div>
        {weekDays.map((day) => <div className="schedule-grid__header" key={day}>{day}</div>)}
        {timeSlots.map((slot) => (
          <div className="schedule-grid-row" key={slot}>
            <div className="schedule-cell schedule-time">{slot}</div>
            {weekDates.map((date, index) => {
              const cellKey = `${index}-${slot}`;
              const cellItems = itemsByCell.get(cellKey) || [];
              const itemGroups = groupsByCell.get(cellKey) || [];
              const conflict = itemGroups.some((group) => group.hasConflict);
              return (
                <div className={`schedule-cell schedule-empty ${cellItems.length ? 'has-item' : ''} ${conflict ? 'has-conflict' : ''}`} key={`${date}-${slot}`}>
                  {cellItems.length ? (
                    <button type="button" className="schedule-cell__content" onClick={() => onCellSelect(date, slot, cellItems)}>
                      {itemGroups.map((group) => (
                        <span className={`schedule-item-card ${group.hasConflict ? 'has-conflict' : ''}`} key={itemGroupKey(group.representative)}>
                          <strong>{group.representative.title}</strong>
                          <span>{itemTypeLabels[group.representative.item_type] || group.representative.item_type}</span>
                          <span>{group.representative.building_address || '-'}, ауд. {group.representative.room_number || '-'}</span>
                          <span>{group.representative.instructor_name || 'Преподаватель не указан'}</span>
                          <span className="schedule-cell-tooltip">
                            {group.hasConflict && <em>Есть бронирование на эту дату</em>}
                            {group.dates.sort().map((itemDate) => <small key={itemDate}>{formatDate(itemDate)}</small>)}
                          </span>
                        </span>
                      ))}
                    </button>
                  ) : canEdit ? (
                    <button type="button" aria-label="Добавить занятие" onClick={() => onAdd(date, slot)} />
                  ) : null}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </section>
  );
}

function ScheduleSettingsModal({ modal, academicYears, modules, programmes, courses, groups, selectedProgramme, selectedGroup, selectedModule, buildings, rooms, employees, onClose, onSaveSimple, onCreateSchedule, onSaveScheduleItem }) {
  const [form, setForm] = useState(() => initialForm(modal, { academicYears, modules, programmes, courses, selectedProgramme, selectedGroup, selectedModule, buildings, rooms, employees }));
  const [error, setError] = useState('');
  const activeRooms = rooms.filter((room) => String(room.building_id) === String(form.building_id) && room.is_active !== false);
  function update(key, value) {
    setForm((current) => {
      const next = { ...current, [key]: value, ...(key === 'building_id' ? { room_id: activeRooms[0]?.id || '' } : {}) };
      if (key === 'course_id') {
        const course = courses.find((row) => Number(row.id) === Number(value));
        const instructor = course?.instructors?.[0];
        next.title = course?.name || next.title;
        next.instructor_id = instructor?.instructor_id || next.instructor_id;
        next.instructor_name = instructor?.instructor_name || next.instructor_name;
      }
      if (key === 'instructor_id') {
        const instructor = employees.find((employee) => Number(employee.id) === Number(value));
        next.instructor_name = fullName(instructor);
      }
      return next;
    });
    setError('');
  }
  async function submit() {
    try {
      if (modal.kind === 'schedule') {
        await onCreateSchedule(form, modal.item);
      } else if (modal.kind === 'scheduleItem') {
        await onSaveScheduleItem(form, modal.item);
      } else {
        await onSaveSimple(modal.kind, payloadFor(modal.kind, form), modal.item);
      }
    } catch (err) {
      setError(err.message || 'Не удалось сохранить');
    }
  }
  return (
    <div className="modal-backdrop">
      <div className="user-modal schedule-modal">
        <h2>{modalTitle(modal.kind, Boolean(modal.item))}</h2>
        <div className="user-form-grid schedule-form-grid">
          {modalFields(modal.kind, { academicYears, modules, programmes, courses, groups, selectedProgramme, buildings, rooms: activeRooms, employees }).map((field) => (
            <label key={field.key} className={field.type === 'textarea' ? 'is-wide' : ''}>
              <span>{field.label}</span>
              {field.type === 'select' ? (
                <select value={form[field.key] || ''} onChange={(event) => update(field.key, event.target.value)}>
                  {(field.options || []).map((option) => <option value={option.value} key={option.value}>{option.label}</option>)}
                </select>
              ) : field.type === 'textarea' ? (
                <textarea value={form[field.key] || ''} onChange={(event) => update(field.key, event.target.value)} />
              ) : (
                <input type={field.type || 'text'} value={form[field.key] || ''} onChange={(event) => update(field.key, event.target.value)} />
              )}
            </label>
          ))}
        </div>
        {error && <div className="modal-error">{error}</div>}
        <div className="modal-actions">
          <button className="button button--danger" type="button" onClick={onClose}>Отменить</button>
          <button className="button button--primary" type="button" onClick={submit}>Сохранить</button>
        </div>
      </div>
    </div>
  );
}

function initialForm(modal, context) {
  const item = modal.item || {};
  if (modal.kind === 'academicYear') return { name: item.name || '', start_date: item.start_date || '', end_date: item.end_date || '' };
  if (modal.kind === 'module') return { name: item.name || '', start_date: item.start_date || '', end_date: item.end_date || '', academic_year_id: item.academic_year_id || context.academicYears[0]?.id || '' };
  if (modal.kind === 'holiday') return { name: item.name || '', description: item.description || '', date: item.date || '', academic_year_id: item.academic_year_id || context.academicYears[0]?.id || '' };
  if (modal.kind === 'programme') return { name: item.name || '', description: item.description || '' };
  if (modal.kind === 'course') {
    const instructor = item.instructors?.[0];
    return {
      name: item.name || '',
      description: item.description || '',
      programme_id: item.programme_id || context.selectedProgramme?.id || context.programmes[0]?.id || '',
      instructor_id: instructor?.instructor_id || context.employees[0]?.id || '',
      instructor_name: instructor?.instructor_name || fullName(context.employees[0])
    };
  }
  if (modal.kind === 'group') return { name: item.name || '', email: item.email || '', programme_id: item.programme_id || context.selectedProgramme?.id || context.programmes[0]?.id || '' };
  if (modal.kind === 'schedule') return { name: item.name || `${context.selectedGroup?.name || 'Группа'} / ${context.selectedModule?.name || 'Модуль'}`, module_id: item.module_id || context.selectedModule?.id || context.modules[0]?.id || '', group_id: item.group_id || context.selectedGroup?.id || '' };
  const course = context.courses.find((row) => Number(row.id) === Number(item.course_id)) || context.courses.find((row) => Number(row.programme_id) === Number(context.selectedProgramme?.id)) || context.courses[0];
  const courseInstructor = course?.instructors?.[0];
  return {
    title: item.title || course?.name || '',
    item_type: item.item_type || 'lecture',
    course_id: item.course_id || course?.id || '',
    instructor_id: item.instructor_id || courseInstructor?.instructor_id || context.employees[0]?.id || '',
    instructor_name: item.instructor_name || courseInstructor?.instructor_name || '',
    building_id: item.building_id || context.buildings[0]?.id || '',
    building_address: item.building_address || context.buildings[0]?.address || '',
    room_id: item.room_id || context.rooms[0]?.id || '',
    room_number: item.room_number || context.rooms[0]?.room_number || '',
    date: item.date || modal.date || context.selectedModule?.start_date || '',
    time_slot: item.time_slot || modal.slot || timeSlots[0],
    recurrence: item.id ? 'single' : 'single',
    specific_dates: ''
  };
}

function payloadFor(kind, form) {
  if (kind === 'academicYear') return { name: form.name, start_date: form.start_date, end_date: form.end_date };
  if (kind === 'module') return { name: form.name, start_date: form.start_date, end_date: form.end_date, academic_year_id: Number(form.academic_year_id) };
  if (kind === 'holiday') return { name: form.name, description: form.description, date: form.date, academic_year_id: Number(form.academic_year_id) };
  if (kind === 'programme') return { name: form.name, description: form.description };
  if (kind === 'course') return {
    name: form.name,
    description: form.description,
    programme_id: Number(form.programme_id),
    instructors: [{
      instructor_id: Number(form.instructor_id),
      instructor_name: form.instructor_name
    }]
  };
  if (kind === 'group') return { name: form.name, email: form.email, programme_id: Number(form.programme_id) };
  return form;
}

function modalTitle(kind, isEdit) {
  const titles = {
    academicYear: 'учебный год',
    module: 'модуль',
    holiday: 'праздник',
    programme: 'программу',
    course: 'курс',
    group: 'группу',
    schedule: 'расписание',
    scheduleItem: 'занятие'
  };
  return `${isEdit ? 'Редактировать' : 'Добавить'} ${titles[kind]}`;
}

function optionList(rows = [], label, value = 'id') {
  return rows.map((row) => ({ value: row[value], label: label(row) }));
}

function modalFields(kind, context) {
  if (kind === 'academicYear') return [
    { key: 'name', label: 'Название' },
    { key: 'start_date', label: 'Начало', type: 'date' },
    { key: 'end_date', label: 'Окончание', type: 'date' }
  ];
  if (kind === 'module') return [
    { key: 'name', label: 'Название' },
    { key: 'academic_year_id', label: 'Учебный год', type: 'select', options: optionList(context.academicYears, (row) => row.name) },
    { key: 'start_date', label: 'Начало', type: 'date' },
    { key: 'end_date', label: 'Окончание', type: 'date' }
  ];
  if (kind === 'holiday') return [
    { key: 'name', label: 'Название' },
    { key: 'academic_year_id', label: 'Учебный год', type: 'select', options: optionList(context.academicYears, (row) => row.name) },
    { key: 'date', label: 'Дата', type: 'date' },
    { key: 'description', label: 'Описание', type: 'textarea' }
  ];
  if (kind === 'programme') return [
    { key: 'name', label: 'Название' },
    { key: 'description', label: 'Описание', type: 'textarea' }
  ];
  if (kind === 'course') return [
    { key: 'name', label: 'Название' },
    { key: 'programme_id', label: 'Программа', type: 'select', options: optionList(context.programmes, (row) => row.name) },
    { key: 'instructor_id', label: 'Преподаватель', type: 'select', options: optionList(context.employees, fullName) },
    { key: 'description', label: 'Описание', type: 'textarea' }
  ];
  if (kind === 'group') return [
    { key: 'name', label: 'Название' },
    { key: 'email', label: 'Email', type: 'email' },
    { key: 'programme_id', label: 'Программа', type: 'select', options: optionList(context.programmes, (row) => row.name) }
  ];
  if (kind === 'schedule') return [
    { key: 'name', label: 'Название' },
    { key: 'module_id', label: 'Модуль', type: 'select', options: optionList(context.modules, (row) => row.name) },
    { key: 'group_id', label: 'Группа', type: 'select', options: optionList(context.groups, (row) => row.name) }
  ];
  return [
    { key: 'course_id', label: 'Курс', type: 'select', options: optionList(context.courses.filter((course) => Number(course.programme_id) === Number(context.selectedProgramme?.id)), (row) => row.name) },
    { key: 'title', label: 'Название' },
    { key: 'item_type', label: 'Тип', type: 'select', options: itemTypes.map((type) => ({ value: type, label: itemTypeLabels[type] || type })) },
    { key: 'instructor_id', label: 'Преподаватель', type: 'select', options: optionList(context.employees, fullName) },
    { key: 'building_id', label: 'Корпус', type: 'select', options: optionList(context.buildings, (row) => row.name) },
    { key: 'room_id', label: 'Аудитория', type: 'select', options: optionList(context.rooms, (row) => row.room_number) },
    { key: 'date', label: 'Дата', type: 'date' },
    { key: 'time_slot', label: 'Слот', type: 'select', options: timeSlots.map((slot) => ({ value: slot, label: slot })) },
    { key: 'recurrence', label: 'Повтор', type: 'select', options: [
      { value: 'single', label: 'Один раз' },
      { value: 'weekly', label: 'Каждую неделю' },
      { value: 'biweekly', label: 'Раз в две недели' },
      { value: 'specific', label: 'Конкретные даты' }
    ] },
    { key: 'specific_dates', label: 'Даты через запятую', type: 'textarea' }
  ];
}
